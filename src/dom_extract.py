"""
Extração resiliente de campos do painel de detalhes do Google Maps.

O HTML do Maps usa classes ofuscadas que mudam com frequência, então priorizamos
seletores baseados em atributos semânticos (data-item-id, aria-label, role) que
tendem a ser mais estáveis, com fallbacks em cascata. Qualquer falha de extração
de um campo específico é isolada (retorna None) e não derruba o restante da coleta.
"""
import re

from playwright.async_api import Page


async def safe_text(page: Page, selectors: list[str], timeout: int = 1500) -> str | None:
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            await loc.wait_for(state="attached", timeout=timeout)
            text = (await loc.inner_text()).strip()
            if text:
                return text
        except Exception:
            continue
    return None


async def extract_name(page: Page) -> str | None:
    return await safe_text(page, ["h1"])


async def extract_category(page: Page) -> str | None:
    return await safe_text(page, ["button.DkEaL", "button[jsaction*='category']"])


async def extract_rating_reviews(page: Page) -> tuple[float | None, int | None]:
    """Tenta extrair nota e nº de avaliações a partir do bloco de reputação (div.F7nice)
    ou, em último caso, de qualquer aria-label no formato 'X,X estrelas, Y avaliações'."""
    aria_candidates: list[str] = []

    try:
        aria = await page.locator("div.F7nice").first.get_attribute("aria-label")
        if aria:
            aria_candidates.append(aria)
    except Exception:
        pass

    try:
        aria2 = await page.locator(
            'span[role="img"][aria-label*="estrela"], span[role="img"][aria-label*="star"]'
        ).first.get_attribute("aria-label")
        if aria2:
            aria_candidates.append(aria2)
    except Exception:
        pass

    rating: float | None = None
    reviews: int | None = None

    for text in aria_candidates:
        if rating is None:
            m = re.search(r"(\d+[.,]\d+)", text)
            if m:
                rating = float(m.group(1).replace(",", "."))
        if reviews is None:
            m = re.search(r"([\d.,]+)\s*(avalia|review)", text, re.IGNORECASE)
            if m:
                reviews = int(re.sub(r"\D", "", m.group(1)))
        if rating is not None and reviews is not None:
            return rating, reviews

    # Fallback: elementos separados dentro de div.F7nice
    if rating is None:
        try:
            t = await page.locator('div.F7nice span[aria-hidden="true"]').first.inner_text()
            t = t.strip().replace(",", ".")
            if re.match(r"^\d+(\.\d+)?$", t):
                rating = float(t)
        except Exception:
            pass

    if reviews is None:
        try:
            t = await page.locator("div.F7nice span:has-text('(')").first.inner_text()
            digits = re.sub(r"\D", "", t)
            if digits:
                reviews = int(digits)
        except Exception:
            pass

    return rating, reviews


async def _extract_item_id_field(page: Page, selector: str, strip_prefixes: list[str]) -> str | None:
    try:
        el = page.locator(selector).first
        await el.wait_for(state="attached", timeout=1500)
        aria = await el.get_attribute("aria-label")
        if aria:
            for prefix in strip_prefixes:
                if aria.startswith(prefix):
                    return aria[len(prefix):].strip()
            return aria.strip()
        text = (await el.inner_text()).strip()
        return text or None
    except Exception:
        return None


async def extract_address(page: Page) -> str | None:
    return await _extract_item_id_field(
        page, '[data-item-id="address"]', ["Endereço: ", "Address: "]
    )


async def extract_phone(page: Page) -> str | None:
    return await _extract_item_id_field(
        page, '[data-item-id^="phone:tel:"]', ["Telefone: ", "Phone: "]
    )


async def extract_website(page: Page) -> str | None:
    try:
        el = page.locator('[data-item-id="authority"]').first
        await el.wait_for(state="attached", timeout=1500)
        href = await el.get_attribute("href")
        return href
    except Exception:
        return None
