# Design Spec: TDS-LMS Lite (Supabase-First Architecture)

**Status:** Draft  
**Data:** 2026-04-11  
**Autor:** Gemini CLI + Rafael  
**Contexto:** Transição do LMS baseado em Frappe/JSON para uma arquitetura desacoplada, moderna e em tempo real usando Supabase como Core.

---

## 1. Visão Geral
O TDS-LMS Lite visa fornecer uma experiência de aprendizado fluida, onde o progresso do aluno via WhatsApp é refletido instantaneamente em um Dashboard Web. A arquitetura remove a dependência direta do Frappe para operações críticas, utilizando o Supabase para Banco de Dados (Postgres), Autenticação (Magic Link/OTP) e Eventos em Tempo Real.

## 2. Arquitetura do Sistema

### 2.1 Infraestrutura (Self-Hosted)
- **Método:** Docker Compose Nativo (contornando limitações de API do Dokploy).
- **Rede:** Integrado à `kreativ_education_net`.
- **Porta Externa (Kong):** `8001` (para evitar conflito com Frappe na `8000`).
- **URL da API:** `https://api-lms.ipexdesenvolvimento.cloud` (via Traefik/Dokploy).
- **URL do Dashboard:** `https://ops.ipexdesenvolvimento.cloud` (via Traefik/Dokploy).

### 2.2 Componentes
1.  **Supabase Core:** PostgreSQL, GoTrue (Auth), PostgREST, Realtime.
2.  **Dashboard (Front):** SPA em Vite + React + Tailwind CSS.
3.  **Orquestrador (n8n):** Responsável por processar webhooks do WhatsApp/Chatwoot e atualizar o Supabase.

---

## 3. Modelo de Dados (Schema)

### 3.1 Tabelas Principais
- **`profiles`**: Dados do usuário (id, whatsapp, name, role).
- **`courses`**: Catálogo de cursos (id, slug, title, description, metadata).
- **`enrollments`**: Matrículas e progresso (id, student_id, course_id, status, progress_percent).
- **`learning_logs`**: Tabela de auditoria e DLQ.
    - `id`, `student_id`, `type` (ex: `whatsapp_msg`, `quiz_done`), `payload` (JSONB), `status` (success, error), `error_message`, `created_at`.

---

## 4. Fluxos e Segurança

### 4.1 Segurança (RLS & Keys)
- **Row Level Security (RLS):** Ativo em todas as tabelas. Alunos (`authenticated`) só leem seus próprios dados.
- **ANON_KEY:** Usada no Dashboard Client.
- **SERVICE_ROLE_KEY:** Usada exclusivamente pelo n8n para bypass de RLS e atualizações de sistema.
- **Mapeamento de Identidade:** O n8n deve sempre validar o `whatsapp_number` contra a tabela `profiles` para obter o `user_id` antes de qualquer operação de escrita.

### 4.2 Fluxo da "Catraca Pedagógica"
1.  WhatsApp envia evento (via Chatwoot) ➡️ n8n Webhook.
2.  n8n insere entrada em `learning_logs` (status: `pending`).
3.  n8n valida aluno e lógica de progresso.
4.  n8n atualiza `enrollments` via `SERVICE_ROLE`.
5.  n8n marca log como `success`.
6.  Supabase Realtime dispara evento para o Dashboard do aluno.

---

## 5. Estratégia de Implementação (Fases)

### Fase 1: Infraestrutura e Base
- Provisionamento do Supabase via Docker Nativo.
- Configuração de DNS e Traefik no Dokploy.
- Criação do Schema e Políticas RLS.

### Fase 2: Dashboard e Auth
- Setup do projeto Vite.
- Implementação do Magic Link via WhatsApp (n8n gerando link de Auth do Supabase).
- Tela básica de progresso consumindo Realtime.

### Fase 3: Automação e Auditoria
- Migração dos workflows da "Catraca" para o novo schema.
- Implementação do sistema de Dead-Letter nas tabelas de Log.

---

## 6. Riscos e Mitigações
- **Consumo de Recursos:** Monitorar RAM do servidor (atualmente com 16GB livres).
- **Conflito de Portas:** Garantir que o mapeamento `8001:8000` do Kong esteja isolado.
- **Segurança da Key:** Nunca vazar a `SERVICE_ROLE_KEY` no bundle do Frontend.
