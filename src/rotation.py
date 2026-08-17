"""Rodízio determinístico de combinações (nicho, cidade) baseado na data.

Não depende de estado salvo entre execuções: cada dia calcula, a partir do
calendário, qual fatia do rodízio nacional deve rodar. Isso é essencial porque
a automação roda em uma rotina agendada na nuvem — cada disparo é um ambiente
isolado, sem memória do que rodou no dia anterior.
"""
import hashlib
import itertools
from datetime import date

from .cities import CIDADES
from .niches import NICHOS

_EPOCH = date(2026, 1, 1)
_SEED = "maps-lead-miner-v1"


def _seeded_shuffle(items: list, seed: str) -> list:
    return sorted(items, key=lambda item: hashlib.sha256(f"{seed}:{item}".encode()).hexdigest())


def build_combo_pool() -> list[tuple[str, str]]:
    """Todas as combinações (nicho, cidade) possíveis, em ordem embaralhada
    de forma estável (mesma ordem sempre, mas não previsível/sequencial)."""
    combos = list(itertools.product(NICHOS, CIDADES))
    return _seeded_shuffle(combos, _SEED)


def todays_combos(run_date: date | None = None, max_combos: int = 8) -> list[tuple[str, str]]:
    """Retorna até `max_combos` combinações (nicho, cidade) para o dia informado,
    avançando pelo pool de rodízio a cada dia sem repetir por muito tempo."""
    run_date = run_date or date.today()
    pool = build_combo_pool()
    day_index = (run_date - _EPOCH).days
    start = day_index % len(pool)
    ordered = pool[start:] + pool[:start]
    return ordered[:max_combos]
