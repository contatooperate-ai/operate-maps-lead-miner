"""Regras estritas de qualificação de lead (todas precisam ser satisfeitas)."""
from urllib.parse import urlparse

# Domínios que indicam "sem site profissional próprio" quando é tudo que o
# perfil tem cadastrado como link de website. Ajuste livremente conforme o ICP.
SOCIAL_DOMAINS = [
    "instagram.com",
    "facebook.com",
    "fb.com",
    "m.me",
    "linktr.ee",
    "linktree.com",
    "wa.me",
    "api.whatsapp.com",
    "whatsapp.com",
    "bio.link",
    "beacons.ai",
    "taplink.cc",
    "t.me",
    "tiktok.com",
    "x.com",
    "twitter.com",
]

MIN_RATING = 4.0
MIN_REVIEWS = 5


def extract_domain(url: str) -> str:
    netloc = urlparse(url).netloc.lower()
    return netloc[4:] if netloc.startswith("www.") else netloc


def is_social_domain(domain: str) -> bool:
    return any(domain == d or domain.endswith("." + d) for d in SOCIAL_DOMAINS)


def qualify(lead: dict) -> tuple[bool, str]:
    """Retorna (qualificado, motivo)."""
    if not lead.get("nome"):
        return False, "Perfil inválido ou sem dados suficientes para avaliação"

    rating = lead.get("nota")
    reviews = lead.get("total_avaliacoes")
    if rating is None or reviews is None:
        return False, "Não foi possível extrair reputação (nota/avaliações) do perfil"

    if rating < MIN_RATING or reviews < MIN_REVIEWS:
        return False, f"Reputação insuficiente (nota={rating}, avaliações={reviews})"

    website = lead.get("website")
    if website:
        domain = extract_domain(website)
        if not domain:
            return True, "Sem site próprio cadastrado"
        if is_social_domain(domain):
            return True, f"Sem site próprio (link cadastrado aponta apenas para rede social: {domain})"
        return False, f"Possui site próprio cadastrado ({domain})"

    return True, "Sem site próprio cadastrado"
