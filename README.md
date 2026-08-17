# Maps Lead Miner

Automação em Python que garimpa leads no Google Maps por nicho + localidade,
aplica um filtro estrito de qualificação (reputação mínima + ausência de site
próprio) e envia os leads qualificados para um CRM via webhook/API, com backup
local em JSON e CSV.

## Instalação

```bash
cd maps_lead_miner
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

## Configuração

Copie `.env.example` para `.env` e preencha:

```bash
copy .env.example .env
```

Campos principais:

| Variável | Descrição |
|---|---|
| `NICHO` | ex: `"consultor de RH"`, `"estética automotiva"`, `"dentista"` |
| `LOCALIDADE` | ex: `"Uberlândia, MG"` |
| `META_LEADS` | quantidade de leads qualificados a coletar |
| `CRM_WEBHOOK_URL` ou `CRM_API_URL` | endpoint de destino (webhook tem prioridade se ambos forem preenchidos) |
| `CRM_API_KEY` | opcional; enviado como `Authorization: Bearer <token>` |

Todos os campos também podem ser passados via CLI (têm prioridade sobre o `.env`):

```bash
python main.py --nicho "dentista" --localidade "Uberlândia, MG" --meta-leads 20 --no-headless
```

## Regras de qualificação (todas obrigatórias)

1. Perfil ativo/listado no Maps (nome extraído com sucesso).
2. Nota média ≥ 4.0 **e** ≥ 5 avaliações.
3. Sem site próprio: ou não há link de website cadastrado, ou o link aponta
   apenas para rede social/link-in-bio (`instagram.com`, `facebook.com`,
   `linktr.ee`, `wa.me`, `t.me`, `tiktok.com`, etc. — lista completa e
   editável em `src/qualifier.py`).

## Saída

- Envio automático (POST JSON) para `CRM_WEBHOOK_URL`/`CRM_API_URL`, com retry
  (3 tentativas, backoff exponencial).
- Backup local em `output/leads_qualificados.json` (lista) e `output/leads.csv`,
  deduplicados por `maps_url` — pode rodar a automação várias vezes sem duplicar.
- Log em console + arquivo `lead_scraper.log`.
- Resumo final: perfis analisados, descartados e qualificados/enviados.

### Payload enviado ao CRM

```json
{
  "nome": "string",
  "categoria": "string",
  "cidade": "string",
  "bairro": "string",
  "telefone": "string",
  "nota": 4.8,
  "total_avaliacoes": 24,
  "maps_url": "string",
  "motivo_qualificacao": "Sem site próprio cadastrado",
  "origem": "Prospecção Maps"
}
```

## Como funciona (resiliência anti-bloqueio)

- Playwright Chromium com user-agent realista rotativo, viewport/locale/timezone
  pt-BR, e patch de `navigator.webdriver` para reduzir sinais de automação.
- Delays randômicos entre ações (digitação, scroll, navegação entre perfis).
- Coleta os links de cada estabelecimento rolando o painel de resultados
  (`div[role="feed"]`) até atingir `META_LEADS × OVERSCAN_FACTOR` links (padrão:
  6x a meta, já que nem todo perfil analisado será qualificado) ou até o Maps
  sinalizar fim da lista.
- Cada perfil é aberto por navegação direta à URL do estabelecimento (mais
  robusto que clicar em cada card da lista) e os campos são extraídos com
  seletores em cascata (`data-item-id`, `aria-label`, `role`), priorizando
  atributos semânticos — mais estáveis que classes CSS ofuscadas do Maps, que
  mudam com frequência.
- Falha ao extrair um campo específico não derruba o perfil inteiro: o campo
  fica `None`/vazio e a qualificação trata isso como dado insuficiente (lead
  descartado, não uma exceção fatal).

## Limitações conhecidas

- O Google Maps não tem API pública de scraping — mudanças no HTML podem exigir
  ajuste dos seletores em `src/dom_extract.py`.
- Extração de bairro/cidade a partir do endereço é heurística (regex sobre o
  padrão comum `"Rua X, 123 - Bairro, Cidade - UF, CEP"`); endereços fora desse
  padrão caem no fallback `bairro=""`, `cidade=LOCALIDADE`.
- Uso deve respeitar os Termos de Serviço do Google Maps; recomenda-se volume
  moderado e uso para prospecção legítima B2B, não coleta massiva.
- Não há suporte a proxy/rotação de IP incluso — para volumes altos, considere
  adicionar um pool de proxies em `GoogleMapsScraper.run()`.
