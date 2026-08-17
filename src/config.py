"""Carrega configuração a partir de .env e/ou argumentos de CLI (CLI tem prioridade)."""
import argparse
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class Settings:
    nicho: str | None
    localidade: str | None
    meta_leads: int
    crm_webhook_url: str | None
    crm_api_url: str | None
    crm_api_key: str | None
    headless: bool
    overscan_factor: int
    max_scroll_rounds: int
    max_combos_per_dia: int
    output_dir: Path

    @property
    def modo_rodizio(self) -> bool:
        """Sem nicho/localidade explícitos, roda em rodízio nacional (nicho x cidade)."""
        return not (self.nicho and self.localidade)


def _env_bool(name: str, default: str = "true") -> bool:
    return os.getenv(name, default).strip().lower() not in ("false", "0", "no")


def load_settings(argv: list[str] | None = None) -> Settings:
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Garimpeiro de leads no Google Maps com envio automático para CRM."
    )
    parser.add_argument(
        "--nicho", default=os.getenv("NICHO") or None,
        help='ex: "dentista". Se omitido (junto com --localidade), roda em modo rodízio nacional.',
    )
    parser.add_argument("--localidade", default=os.getenv("LOCALIDADE") or None, help='ex: "Uberlândia, MG"')
    parser.add_argument("--meta-leads", type=int, default=int(os.getenv("META_LEADS", "10")))
    parser.add_argument("--crm-webhook-url", default=os.getenv("CRM_WEBHOOK_URL") or None)
    parser.add_argument("--crm-api-url", default=os.getenv("CRM_API_URL") or None)
    parser.add_argument("--crm-api-key", default=os.getenv("CRM_API_KEY") or None)
    parser.add_argument("--headless", dest="headless", action="store_true", default=_env_bool("HEADLESS"))
    parser.add_argument("--no-headless", dest="headless", action="store_false")
    parser.add_argument("--overscan-factor", type=int, default=int(os.getenv("OVERSCAN_FACTOR", "6")))
    parser.add_argument("--max-scroll-rounds", type=int, default=int(os.getenv("MAX_SCROLL_ROUNDS", "40")))
    parser.add_argument(
        "--max-combos-por-dia", type=int, default=int(os.getenv("MAX_COMBOS_POR_DIA", "8")),
        help="Nº máximo de combinações nicho+cidade tentadas por execução em modo rodízio.",
    )
    parser.add_argument("--output-dir", default=os.getenv("OUTPUT_DIR", "output"))

    args = parser.parse_args(argv)

    # nicho/localidade podem vir ambos preenchidos (modo único) ou ambos ausentes
    # (modo rodízio nacional). Um preenchido e o outro não é configuração inválida.
    if bool(args.nicho) != bool(args.localidade):
        parser.error("--nicho e --localidade devem ser usados juntos, ou nenhum dos dois (modo rodízio).")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not args.crm_webhook_url and not args.crm_api_url:
        # Não é fatal: a automação continua rodando e salva os backups locais,
        # apenas não terá para onde enviar via API.
        print(
            "[AVISO] Nenhum CRM_WEBHOOK_URL/CRM_API_URL configurado. "
            "Os leads serão apenas salvos localmente."
        )

    return Settings(
        nicho=args.nicho,
        localidade=args.localidade,
        meta_leads=args.meta_leads,
        crm_webhook_url=args.crm_webhook_url,
        crm_api_url=args.crm_api_url,
        crm_api_key=args.crm_api_key,
        headless=args.headless,
        overscan_factor=args.overscan_factor,
        max_scroll_rounds=args.max_scroll_rounds,
        max_combos_per_dia=args.max_combos_por_dia,
        output_dir=output_dir,
    )
