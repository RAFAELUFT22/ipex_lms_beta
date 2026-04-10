# Repertório de Contexto Mestre — TDS / Kreativ

> Cole este README no início de qualquer sessão com um agente para que ele
> tenha o mapa completo do projeto antes de agir.

## Estado Atual do Projeto

| Componente | Status | Prioridade |
| :--- | :--- | :--- |
| Site Institucional (Next.js) | A implementar | MVP |
| Portal do Aluno + Dashboard | A implementar | MVP |
| Quiz Player + Progresso | A implementar | MVP |
| Certificado automático (PDF) | A implementar | MVP |
| Chatwoot + Operadores | A configurar | MVP |
| AnythingLLM + OpenRouter | Configurar LLM provider | MVP |
| n8n — fluxo RAG WhatsApp | Existente (revisar) | MVP |
| Frappe LMS | CONGELADO | Fase Futura |

## IA: OpenRouter (migrado — chave ativa no Dokploy)

- **Chave:** salva no Dokploy env como `OPENROUTER_API_KEY` e `OPENAI_API_KEY`
- **Modelo testes:** `google/gemini-2.0-flash-lite:free`
- **Modelo produção:** `google/gemini-2.0-flash-001` (com crédito)
- **Base URL:** `https://openrouter.ai/api/v1` (padrão OpenAI)
- Script de migração: `scripts/switch_to_openrouter.py`

## Certificados

Emitidos automaticamente quando o aluno completa **100% dos quizzes** do
curso com nota mínima de **70%**. Lógica completa em `CERTIFICATE_LOGIC.md`.

## Documentos deste Repertório

| Arquivo | Conteúdo |
| :--- | :--- |
| `ARCH_MAP.md` | Arquitetura geral dos microserviços |
| `MULTITENANCY_GUIDE.md` | Como adicionar novos domínios/parceiros |
| `ENV_DICTIONARY.md` | Todas as variáveis de ambiente necessárias |
| `DOKPLOY_BLUEPRINT.json` | Estrutura das stacks no Dokploy |
| `CERTIFICATE_LOGIC.md` | SQL + fluxo n8n para emissão de certificados |
| `PORTAL_DESEMPENHO.md` | Spec do portal web (rotas, componentes, API) |
| `SITE_INSTITUCIONAL.md` | Conteúdo e instruções do site institucional |
| `CHATWOOT_OPERATORS.md` | Passo a passo de configuração dos operadores |
| `ANYTHINGLLM_SETUP.md` | Uso inteligente do AnythingLLM para coordenadores |
| `PROMPT_PAULO_FREIRE.md` | System prompt do tutor — linguagem CadÚnico/Freire |
| `TYPEBOT_REGISTRATION.md` | Fluxo de matrícula via Typebot sem perda de dados |

## VPS

- IP: `147.93.102.246`
- Painel: Dokploy
- Domínio base: `ipexdesenvolvimento.cloud`
