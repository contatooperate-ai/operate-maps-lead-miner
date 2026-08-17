"""Helpers: delays humanizados, user-agents realistas e parsing heurístico de endereço BR."""
import asyncio
import random
import re

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
    " Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
    " Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)"
    " Chrome/125.0.0.0 Safari/537.36",
]


async def human_delay(min_s: float = 0.8, max_s: float = 2.0) -> None:
    await asyncio.sleep(random.uniform(min_s, max_s))


# Endereços do Google Maps no Brasil costumam vir como:
#   "R. Exemplo, 123 - Bairro, Cidade - UF, 00000-000"
# Isto é uma heurística best-effort; nem todo endereço bate no padrão.
_ADDRESS_RE = re.compile(r"-\s*([^,]+),\s*([^,-]+)\s*-\s*[A-Z]{2}")


def parse_bairro_cidade(endereco: str | None, fallback_cidade: str) -> tuple[str, str]:
    if not endereco:
        return "", fallback_cidade
    match = _ADDRESS_RE.search(endereco)
    if match:
        bairro = match.group(1).strip()
        cidade = match.group(2).strip()
        return bairro, cidade
    return "", fallback_cidade
