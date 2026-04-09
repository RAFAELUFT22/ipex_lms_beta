# TDS — Handoff de Sessão
**Última atualização:** 2026-04-09 14:40 (horário Brasília)
**Sessão:** Brainstorming + design spec produção WhatsApp / catraca pedagógica / infraestrutura operacional. Frappe assets rebuilados (CSS + Vue frontend via docker update --memory=6g).

---

## Serviços — Estado Atual

| Serviço | URL | Status |
|---------|-----|--------|
| Frappe LMS | https://lms.ipexdesenvolvimento.cloud | ✅ live — HTTP 200 |
| N8N | https://n8n.ipexdesenvolvimento.cloud | ✅ healthy |
| AnythingLLM | https://rag.ipexdesenvolvimento.cloud | ✅ healthy |
| Chatwoot | https://chat.ipexdesenvolvimento.cloud | ✅ healthy |
| Poste.io | https://mail.ipexdesenvolvimento.cloud | ✅ online (não é relay primário) |
| Dokploy | https://ipexdesenvolvimento.cloud | ✅ |

---

## Problemas em Aberto

- **[BLOCKER]** WhatsApp inbox 5 — não confirmado se está em modo produção (qualquer pessoa pode mandar mensagem) ou ainda em sandbox Meta. Testar enviando de número não cadastrado para +351932439344.
- **[BLOCKER]** Gmail App Password não gerado — necessário para SMTP relay em Frappe, Chatwoot e N8N. Acessar: myaccount.google.com/security com tdsdados@gmail.com (2FA deve estar ativo).
- **[PENDENTE]** Campos catraca não criados no TDS Aluno (estado_catraca, modulo_atual, secao_atual, respostas_mcq, modulos_concluidos, data_ultimo_acesso_whatsapp).
- **[PENDENTE]** Google Form SISEC não criado (mapeamento completo em docs/superpowers/specs/2026-04-09-tds-producao-whatsapp-catraca-design.md seção 3).
- **[PENDENTE]** N8N workflow — falta filtro por inbox 5 + workflow catraca (máquina de estados).
- **[PENDENTE]** Páginas instrucionais não criadas (guia-aluno, guia-tutor, guia-gestor, sisec-info).
- **[PENDENTE]** Fix /insights no kreativ_theme (1 linha CSS).
- **[PENDENTE]** Contas operacionais não configuradas no Chatwoot (sofia@, gabriela@, valentine@, pedroh@, sahaa@).

---

## Próximas 3 Tarefas (prioridade)

1. **Gerar Gmail App Password** — Rafael precisa acessar myaccount.google.com/security > Segurança > Senhas de App > criar "TDS SMTP". Depois configurar em: Frappe (bench set-config), Chatwoot (Settings > Email), N8N (Credentials > SMTP).
2. **Verificar produção inbox 5** — enviar mensagem de número desconhecido para +351932439344 e confirmar chegada no Chatwoot. Se não chegar: Meta Business Manager > WhatsApp > Configuração > Webhooks > verificar URL `https://chat.ipexdesenvolvimento.cloud/webhooks/whatsapp/+351932439344`.
3. **Criar campos catraca no TDS Aluno** — via API Frappe (mesma abordagem usada para criar o doctype original). Endpoint: `POST /api/resource/DocType` ou `bench execute` para adicionar campos ao doctype existente.

---

## Decisões Tomadas (não rever)

- **Abordagem A "Freeze & Ship"** aprovada em 09/04/2026 — não reescrever Frappe, não desinstalar ERPNext
- **ERPNext** — não desinstalar (risco migrations). Esconder /insights via CSS kreativ_theme.
- **WhatsApp número** `+351932439344` — número definitivo do TDS (não é sandbox Meta)
- **SISEC** — via Google Form → Apps Script → N8N webhook → Frappe REST API
- **Páginas instrucionais** — Web Pages no Frappe CMS (HTML puro + Tailwind CDN), não container separado
- **Email SMTP** — Gmail relay (tdsdados@gmail.com). Poste.io não é relay primário.
- **Catraca pedagógica** — critério inclusivo: qualquer resposta MCQ vale; bloqueia apenas por omissão (não respondeu)
- **Conteúdo cartilhas** — armazenado como JSON em nodes Set do N8N por curso (não via AnythingLLM)

---

## Arquitetura resumida

```
WhatsApp (+351932439344)
    ↓ Meta Cloud API
Chatwoot Inbox 5 (Channel::Whatsapp)
    ↓ Agent Bot "Tutor IA" (ID:1)
N8N Webhook (https://n8n.ipexdesenvolvimento.cloud/webhook/chatwoot-kreativ)
    ↓ Filtro inbox 5
    ├── Catraca pedagógica (estado em Frappe TDS Aluno)
    │       ↓ AGUARDANDO_LEITURA: envia seção
    │       ↓ AGUARDANDO_MCQ: envia pergunta A/B/C/D
    │       ↓ MODULO_COMPLETO: parabéns / próximo módulo
    └── RAG livre (AnythingLLM workspace por curso)
            ↓ Groq llama-3.3-70b (fallback: chave 2)
        Chatwoot reply → WhatsApp

Estagiário → Google Form SISEC → Sheets → Apps Script → N8N → Frappe TDS Aluno → WhatsApp boas-vindas
```

---

## Credenciais críticas

- **Arquivo completo:** `/root/kreativ-setup/.env.real`
- **Chatwoot API:** rever token (401 com o antigo) — fazer login em https://chat.ipexdesenvolvimento.cloud com tdsdados@gmail.com / 6QWuIKdZzYBmBdS3! para obter novo token
- **Frappe API Key:** 056681de29fce7a | **Secret:** 7c78dcba6e3c5d1
- **AnythingLLM:** W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0
- **N8N API Key:** em .env.real

---

## Specs e Planos

- **Design spec desta sessão:** `docs/superpowers/specs/2026-04-09-tds-producao-whatsapp-catraca-design.md`
- **Spec implantação geral:** `docs/superpowers/specs/2026-04-08-tds-implantacao-design.md`
- **Plano Fase 0:** `docs/superpowers/plans/2026-04-08-fase0-whatsapp-mvp.md`
- **Plano AppScript estagiários:** `docs/superpowers/plans/2026-04-08-fase1-appscript-estagiarios.md`

---

## Prompt de retomada

Ao iniciar nova sessão colar:
> "Continuar projeto TDS. Ler /root/projeto-tds/HANDOFF.md antes de qualquer ação."
