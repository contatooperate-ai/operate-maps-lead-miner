"""Ponto de entrada da automação de garimpo de leads no Google Maps -> CRM.

Uso:
    python main.py --nicho "dentista" --localidade "Uberlândia, MG" --meta-leads 20
ou configure tudo via .env (veja .env.example) e rode apenas:
    python main.py
"""
import asyncio

from src.config import load_settings
from src.crm_client import CRMClient
from src.logger_setup import get_logger
from src.scraper import GoogleMapsScraper


def main() -> None:
    settings = load_settings()
    logger = get_logger()

    logger.info(
        f"Iniciando prospecção — nicho='{settings.nicho}' localidade='{settings.localidade}' "
        f"meta_leads={settings.meta_leads} headless={settings.headless}"
    )

    crm_client = CRMClient(
        webhook_url=settings.crm_webhook_url,
        api_url=settings.crm_api_url,
        api_key=settings.crm_api_key,
        logger=logger,
    )

    scraper = GoogleMapsScraper(settings, logger, crm_client)
    stats = asyncio.run(scraper.run())

    logger.info("=" * 60)
    logger.info("RESUMO DA EXECUÇÃO")
    logger.info(f"Perfis analisados:              {stats['analisados']}")
    logger.info(f"Descartados (site/nota/baixa):  {stats['descartados']}")
    logger.info(f"Qualificados e enviados ao CRM: {stats['qualificados']}")
    logger.info(f"Backups salvos em: {settings.output_dir / 'leads_qualificados.json'} e {settings.output_dir / 'leads.csv'}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
