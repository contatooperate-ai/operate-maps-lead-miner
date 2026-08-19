"""Cidades brasileiras de bom porte para o rodízio nacional — Google Maps exige uma
localidade concreta por busca, então giramos entre estas.

Manaus foi removida por pedido explícito (não deve ser buscada). A região Sul
(PR/SC/RS) tem representação ampliada de propósito — metade das cidades da lista
é do Sul — para dar mais peso a essa região no rodízio, mantendo alguma cobertura
das demais regiões do país."""

CIDADES: list[str] = [
    # Região Sul — representação ampliada de propósito (foco maior aqui)
    "Curitiba, PR",
    "Londrina, PR",
    "Maringá, PR",
    "Cascavel, PR",
    "Foz do Iguaçu, PR",
    "Ponta Grossa, PR",
    "Florianópolis, SC",
    "Joinville, SC",
    "Blumenau, SC",
    "Chapecó, SC",
    "Itajaí, SC",
    "Criciúma, SC",
    "Porto Alegre, RS",
    "Caxias do Sul, RS",
    "Pelotas, RS",
    "Santa Maria, RS",
    "Novo Hamburgo, RS",
    "Gravataí, RS",
    # Demais regiões — cobertura mais enxuta
    "São Paulo, SP",
    "Rio de Janeiro, RJ",
    "Belo Horizonte, MG",
    "Brasília, DF",
    "Salvador, BA",
    "Fortaleza, CE",
    "Recife, PE",
    "Goiânia, GO",
    "Campinas, SP",
    "Uberlândia, MG",
    "Vitória, ES",
    "Belém, PA",
    "Natal, RN",
    "João Pessoa, PB",
    "Maceió, AL",
    "Cuiabá, MT",
    "Campo Grande, MS",
    "Ribeirão Preto, SP",
]
