# Architecture Map: TDS + Kreativ Unified System

Este documento define a arquitetura de microserviços e o fluxo de dados do ecossistema TDS (Kreativ-Education), projetado para ser multi-tenant e escalável no Dokploy.

## 1. Core Services (The "Engine Room")

| Serviço | Função | Tecnologias | Orquestração |
| :--- | :--- | :--- | :--- |
| **LMS Lite** | Portal do Aluno (Interface Web) | Next.js / Tailwind / React | Dokploy (Docker) |
| **Evolution API** | Mensageria WhatsApp (Gateway) | Node.js | Dokploy (Docker) |
| **AnythingLLM** | Motor de RAG e Inteligência Artificial | Node.js / VectorDB | Dokploy (Docker) |
| **n8n** | Orquestrador de Fluxos e "Unified API" | Node.js / Low-Code | Dokploy (Docker) |
| **Chatwoot** | Atendimento Humano + Transbordo Bot | Ruby on Rails | Dokploy (Docker) |
| **Frappe LMS** | Gestão Acadêmica (Registros Legais) — **FASE FUTURA** | Python / ERPNext | Dokploy (Docker) |

## 2. Fluxo de Inteligência (RAG)

1.  **Ingestão:** O `n8n` monitora pastas ou bancos de dados e sincroniza documentos com o **AnythingLLM**.
2.  **Processamento:** O `AnythingLLM` usa **OpenRouter** como gateway LLM (modelo free em testes, pago em produção).
3.  **Entrega:** O aluno interage via **WhatsApp (Evolution API)** ou **LMS Lite**. O `n8n` atua como middleware, enviando a pergunta para o AnythingLLM e retornando a resposta formatada.

## 3. Estrutura Multi-tenancy

O sistema é desenhado para suportar múltiplos domínios (Ex: `ead.ipex.org`, `ead.fapto.org`) na mesma infraestrutura:

-   **Nível de Rede:** O Traefik (gerenciado pelo Dokploy) roteia o tráfego baseado nos domínios configurados.
-   **Nível de Aplicação:** O `n8n` identifica o `origin_domain` da requisição e seleciona a "Workspace" correspondente no `AnythingLLM` e o "Bot" correto no `Typebot`.
-   **Nível de Dados:** Cada inquilino (tenant) possui um identificador único (`tenant_id`) no banco de dados centralizado ou instâncias de banco isoladas via Dokploy stacks.

## 4. Pontos Críticos de Conexão (API Mesh)

-   **n8n <-> AnythingLLM:** Comunicação via API REST (`/api/v1/workspace/{slug}/chat`).
-   **n8n <-> Evolution API:** Webhooks para recebimento de mensagens e chamadas POST para envio.
-   **n8n <-> Frappe:** RESERVADO — integração de matrícula e registros legais (fase futura).
-   **n8n <-> PostgreSQL:** Registra progresso de quizzes, pontuações e emissão de certificados (fase atual).
