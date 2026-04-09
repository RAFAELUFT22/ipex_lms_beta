# Dicionário de Variáveis de Ambiente (ENV Template)

Este documento define as chaves essenciais para a operação do ecossistema. Use estes templates para configurar os serviços no Dokploy.

## 1. Gateway de IA (AnythingLLM)

A configuração global do AnythingLLM exige o motor do Gemini.

| Chave | Valor de Exemplo / Origem |
| :--- | :--- |
| `LLM_PROVIDER` | `google` |
| `GOOGLE_MODEL_API_KEY` | `Sua_Chave_Gemini_Pro_ou_Flash` |
| `GOOGLE_MODEL_NAME` | `gemini-1.5-flash` |
| `VECTOR_DB` | `lancedb` (ou `pgvector` se escalável) |
| `ANYTHINGLLM_API_KEY` | `Gerar no painel do AnythingLLM` |

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
| `FRAPPE_API_KEY` | `Sua_Chave_Frappe` |

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
