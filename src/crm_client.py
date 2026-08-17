"""Envio dos leads qualificados para o CRM via webhook/API REST, com retry."""
import logging
import time

import requests


class CRMClient:
    def __init__(
        self,
        webhook_url: str | None,
        api_url: str | None,
        api_key: str | None,
        logger: logging.Logger,
        timeout: int = 15,
        max_retries: int = 3,
    ):
        self.url = webhook_url or api_url
        self.api_key = api_key
        self.logger = logger
        self.timeout = timeout
        self.max_retries = max_retries

    def send_lead(self, payload: dict) -> bool:
        if not self.url:
            self.logger.warning(
                "Nenhum CRM_WEBHOOK_URL/CRM_API_URL configurado — lead não enviado (apenas backup local)."
            )
            return False

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["x-api-key"] = self.api_key

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = requests.post(self.url, json=payload, headers=headers, timeout=self.timeout)
                if 200 <= resp.status_code < 300:
                    return True
                self.logger.warning(
                    f"CRM retornou status {resp.status_code} (tentativa {attempt}/{self.max_retries}): "
                    f"{resp.text[:300]}"
                )
            except requests.RequestException as exc:
                self.logger.warning(
                    f"Erro de rede ao enviar lead ao CRM (tentativa {attempt}/{self.max_retries}): {exc}"
                )
            if attempt < self.max_retries:
                time.sleep(min(2 ** attempt, 10))

        self.logger.error(f"Falha ao enviar lead ao CRM após {self.max_retries} tentativas: {payload.get('nome')}")
        return False
