"""Orquestra a navegação no Google Maps com Playwright: busca, scroll de resultados,
extração de cada perfil, qualificação e envio ao CRM + backup local."""
import logging
import random

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError, async_playwright

from .config import Settings
from .crm_client import CRMClient
from .dom_extract import (
    extract_address,
    extract_category,
    extract_name,
    extract_phone,
    extract_rating_reviews,
    extract_website,
)
from .qualifier import qualify
from .rotation import todays_combos
from .storage import save_csv, save_json
from .utils import USER_AGENTS, human_delay, parse_bairro_cidade

CONSENT_SELECTORS = [
    "button:has-text('Aceitar tudo')",
    "button:has-text('Accept all')",
    "button:has-text('I agree')",
    "#L2AGLb",
]

# O Google muda o id do campo de busca periodicamente (ex: deixou de usar
# "#searchboxinput" fixo, hoje gera algo como "ucc-1"). Priorizamos atributos
# semânticos (role/name) que tendem a sobreviver a essas mudanças de layout.
SEARCH_INPUT_SELECTORS = [
    "input#searchboxinput",
    "input[name='q'][role='combobox']",
    "input[role='combobox']",
]


class GoogleMapsScraper:
    def __init__(self, settings: Settings, logger: logging.Logger, crm_client: CRMClient):
        self.settings = settings
        self.logger = logger
        self.crm_client = crm_client

    def _build_combo_list(self) -> list[tuple[str, str]]:
        if not self.settings.modo_rodizio:
            return [(self.settings.nicho, self.settings.localidade)]
        combos = todays_combos(max_combos=self.settings.max_combos_per_dia)
        self.logger.info(
            f"Modo rodízio nacional — combinações de hoje: "
            + "; ".join(f"{n} @ {c}" for n, c in combos)
        )
        return combos

    async def run(self) -> dict:
        stats = {"analisados": 0, "descartados": 0, "qualificados": 0, "combos_tentados": 0}
        combos = self._build_combo_list()

        json_path = self.settings.output_dir / "leads_qualificados.json"
        csv_path = self.settings.output_dir / "leads.csv"

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.settings.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                ],
            )
            context = await browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport={"width": 1366, "height": 768},
                locale="pt-BR",
                timezone_id="America/Sao_Paulo",
            )
            await context.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
            )
            page = await context.new_page()

            for nicho, cidade in combos:
                if stats["qualificados"] >= self.settings.meta_leads:
                    break

                stats["combos_tentados"] += 1
                self.logger.info(f"--- Buscando: {nicho} em {cidade} ---")
                remaining = self.settings.meta_leads - stats["qualificados"]
                needed_hrefs = max(remaining * self.settings.overscan_factor, remaining)

                try:
                    hrefs = await self._collect_result_links(page, f"{nicho} em {cidade}", needed_hrefs)
                except Exception as exc:
                    self.logger.error(f"Falha ao coletar resultados de busca ({nicho} em {cidade}): {exc}")
                    continue

                self.logger.info(f"{len(hrefs)} estabelecimento(s) encontrados para análise.")

                for href in hrefs:
                    if stats["qualificados"] >= self.settings.meta_leads:
                        break

                    stats["analisados"] += 1
                    try:
                        lead_raw = await self._extract_lead(page, href, fallback_cidade=cidade)
                    except Exception as exc:
                        self.logger.warning(f"[{stats['analisados']}] Erro ao extrair perfil ({href}): {exc}")
                        stats["descartados"] += 1
                        continue

                    if lead_raw is None:
                        self.logger.info(f"[{stats['analisados']}] Perfil inacessível/sem dados suficientes: {href}")
                        stats["descartados"] += 1
                        continue

                    ok, motivo = qualify(lead_raw)
                    if not ok:
                        self.logger.info(f"[{stats['analisados']}] Descartado — {lead_raw.get('nome')}: {motivo}")
                        stats["descartados"] += 1
                        continue

                    payload = self._build_crm_payload(lead_raw, motivo, fallback_cidade=cidade)
                    sent = self.crm_client.send_lead(payload)
                    save_json(payload, json_path)
                    save_csv(payload, csv_path)

                    stats["qualificados"] += 1
                    status = "enviado ao CRM" if sent else "backup local apenas (falha/sem CRM configurado)"
                    self.logger.info(
                        f"[{stats['analisados']}] Qualificado ({stats['qualificados']}/{self.settings.meta_leads}) "
                        f"— {lead_raw.get('nome')} — {status}"
                    )

                    await human_delay(1.5, 3.5)

            await browser.close()

        return stats

    async def _handle_consent(self, page: Page) -> None:
        for sel in CONSENT_SELECTORS:
            try:
                btn = page.locator(sel)
                if await btn.count() > 0:
                    await btn.first.click(timeout=3000)
                    await human_delay(0.5, 1.2)
                    return
            except Exception:
                continue

    async def _find_search_input(self, page: Page):
        last_exc: Exception | None = None
        for sel in SEARCH_INPUT_SELECTORS:
            try:
                loc = page.locator(sel).first
                await loc.wait_for(state="visible", timeout=8000)
                return loc
            except Exception as exc:
                last_exc = exc
                continue
        raise last_exc or RuntimeError("Campo de busca do Google Maps não encontrado")

    async def _collect_result_links(self, page: Page, query: str, needed: int) -> list[str]:
        await page.goto("https://www.google.com/maps?hl=pt-BR", wait_until="domcontentloaded", timeout=45000)
        await human_delay(1.0, 2.0)
        await self._handle_consent(page)

        search_input = await self._find_search_input(page)
        await search_input.click()
        await search_input.type(query, delay=random.randint(40, 110))
        await human_delay(0.3, 0.8)
        await page.keyboard.press("Enter")

        feed = page.locator('div[role="feed"]')
        await feed.wait_for(state="visible", timeout=20000)
        await human_delay(1.0, 1.5)

        hrefs: list[str] = []
        seen: set[str] = set()
        stagnant = 0
        rounds = 0

        while len(hrefs) < needed and rounds < self.settings.max_scroll_rounds and stagnant < 4:
            rounds += 1
            raw = await page.eval_on_selector_all(
                'a.hfpxzc, a[href*="/maps/place/"]', "els => els.map(e => e.href)"
            )
            new_count = 0
            for h in raw:
                if h not in seen:
                    seen.add(h)
                    hrefs.append(h)
                    new_count += 1

            stagnant = stagnant + 1 if new_count == 0 else 0

            try:
                end_reached = await feed.evaluate(
                    "el => { const t = el.innerText.toLowerCase();"
                    " return t.includes('chegou ao final da lista') || t.includes(\"you've reached the end\"); }"
                )
            except Exception:
                end_reached = False

            if end_reached or len(hrefs) >= needed:
                break

            try:
                await feed.evaluate("el => el.scrollBy(0, 900)")
            except Exception:
                break
            await human_delay(0.8, 1.8)

        return hrefs[:needed]

    async def _extract_lead(self, page: Page, href: str, fallback_cidade: str) -> dict | None:
        await page.goto(href, wait_until="domcontentloaded", timeout=30000)
        await human_delay(1.0, 2.2)

        try:
            await page.wait_for_selector("h1", timeout=10000)
        except PlaywrightTimeoutError:
            return None

        nome = await extract_name(page)
        if not nome:
            return None

        nota, total_avaliacoes = await extract_rating_reviews(page)
        categoria = await extract_category(page)
        endereco = await extract_address(page)
        telefone = await extract_phone(page)
        website = await extract_website(page)

        bairro, cidade = parse_bairro_cidade(endereco, fallback_cidade=fallback_cidade)

        return {
            "nome": nome,
            "categoria": categoria,
            "endereco_completo": endereco,
            "bairro": bairro,
            "cidade": cidade,
            "telefone": telefone,
            "nota": nota,
            "total_avaliacoes": total_avaliacoes,
            "website": website,
            "maps_url": href,
        }

    def _build_crm_payload(self, lead: dict, motivo: str, fallback_cidade: str) -> dict:
        return {
            "nome": lead.get("nome"),
            "categoria": lead.get("categoria"),
            "cidade": lead.get("cidade") or fallback_cidade,
            "bairro": lead.get("bairro") or "",
            "telefone": lead.get("telefone") or "",
            "nota": lead.get("nota"),
            "total_avaliacoes": lead.get("total_avaliacoes"),
            "maps_url": lead.get("maps_url"),
            "motivo_qualificacao": motivo,
            "origem": "Prospecção Maps",
        }
