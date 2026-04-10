# Dicionário de Variáveis de Ambiente (ENV Template)

Este documento define as chaves essenciais para a operação do ecossistema. Use estes templates para configurar os serviços no Dokploy.

## 1. Gateway de IA (AnythingLLM via OpenRouter)

O AnythingLLM usa OpenRouter como provedor LLM. Em testes, usar modelos `:free`.
Para produção, adicionar créditos e trocar pelo modelo premium equivalente.

| Chave | Valor (Teste — Free) | Valor (Produção) |
| :--- | :--- | :--- |
| `LLM_PROVIDER` | `openai` | `openai` |
| `OPENAI_API_KEY` | `sk-or-v1-...` (chave OpenRouter) | mesma chave, com crédito |
| `OPENAI_BASE_URL` | `https://openrouter.ai/api/v1` | `https://openrouter.ai/api/v1` |
| `OPENAI_MODEL_NAME` | `google/gemini-2.0-flash-lite:free` | `google/gemini-2.0-flash-001` |
| `OPENAI_MODEL_MAX_TOKENS` | `4096` | `8192` |
| `VECTOR_DB` | `lancedb` | `lancedb` |
| `ANYTHINGLLM_API_KEY` | `Gerar no painel AnythingLLM > API Keys` | idem |

**Modelos free alternativos para teste:**
- `deepseek/deepseek-r1:free` — raciocínio complexo
- `meta-llama/llama-3.3-70b-instruct:free` — geração de texto geral
- `mistralai/mistral-7b-instruct:free` — leve e rápido

> Troque `OPENAI_MODEL_NAME` no painel do AnythingLLM (Settings > LLM Provider) sem precisar restartar o container.

## 2. Mensageria (Evolution API)

Configurada para o WhatsApp via Webhook no n8n.

| Chave | Valor de Exemplo / Origem |
| :--- | :--- |
| `AUTHENTICATION_API_KEY` | `Sua_Chave_Segura_Evolution` |
| `DATABASE_URL` | `postgresql://user:pass@host:5432/evolution` |
| `S3_ENABLED` | `true` (Para MinIO ou AWS S3) |

## 3. Orquestrador (n8n)

O n8n precisa de acesso à API do Dokploy e das outras ferramentas.

| Chave | Valor de Exemplo / Origem |
| :--- | :--- |
| `DOKPLOY_API_KEY` | `Gerar no painel do Dokploy` |
| `ANYTHINGLLM_URL` | `https://ai.seuservidor.com` |
| `CHATWOOT_API_KEY` | `Sua_Chave_Chatwoot` |
| `FRAPPE_API_KEY` | `RESERVADO — edição futura` |

## 4. Banco de Dados Global (PostgreSQL)

Usado para o Multi-tenancy e logs.

| Chave | Valor de Exemplo / Origem |
| :--- | :--- |
| `POSTGRES_DB` | `kreativ_master` |
| `POSTGRES_USER` | `kreativ_admin` |
| `POSTGRES_PASSWORD` | `Sua_Senha_Forte` |

---

### IMPORTANTE: Segurança
NUNCA salve valores reais neste arquivo. Os segredos reais devem ser configurados diretamente no **Dashboard do Dokploy > Environment Variables** para cada serviço.
