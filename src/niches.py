"""Termos de nicho para o rodízio nacional, agrupados como fornecido pelo usuário.
Cada grupo prioriza negócios pequenos/médios com alta chance de não terem site próprio."""

NICHE_GROUPS: dict[str, list[str]] = {
    "urgencia_domestica": [
        "encanador",
        "eletricista",
        "chaveiro",
        "dedetizadora",
        "desentupidora",
        "assistência técnica de ar-condicionado",
        "vidraçaria",
    ],
    "servico_manual_alto_padrao": [
        "marcenaria sob medida",
        "tapeçaria e estofados",
        "serralheria",
        "jardinagem e paisagismo",
        "manutenção de piscinas",
    ],
    "saude_bem_estar": [
        "fisioterapeuta",
        "psicólogo",
        "nutricionista",
        "dentista",
        "clínica veterinária",
        "esteticista",
        "personal trainer",
    ],
    "comercio_servico_bairro": [
        "padaria",
        "hortifruti",
        "salão de beleza",
        "barbearia",
        "oficina mecânica",
        "borracharia",
        "floricultura",
    ],
    "profissional_liberal": [
        "contador",
        "advogado",
        "despachante",
        "corretor de imóveis autônomo",
        "consultor de RH",
    ],
    "construcao_reforma": [
        "pedreiro e mestre de obras",
        "pintor residencial",
        "gesseiro",
        "marido de aluguel",
        "construtora pequena",
    ],
    "eventos_locais": [
        "buffet de eventos",
        "decoração de festas",
        "DJ e som para eventos",
        "espaço para eventos",
        "fotógrafo de casamento",
    ],
    "b2b_recorrente": [
        "locação de equipamentos",
        "dedetização industrial",
        "limpeza predial",
        "segurança patrimonial",
        "transportadora de frete local",
    ],
}

NICHOS: list[str] = [nicho for grupo in NICHE_GROUPS.values() for nicho in grupo]
