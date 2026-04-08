# Design: Agente Inteligente WhatsApp TDS
**Data:** 2026-04-08  
**Status:** Aprovado para implementação  
**Executor:** Agente autônomo (sem contexto de conversa prévia)

---

## Contexto do Projeto

O Projeto TDS (Território de Desenvolvimento Social e Inclusão Produtiva) é uma plataforma de inclusão social da NERUDS/UFT via FAPTO (Bolsa nº 212/2026), coordenada por Juliana Aguiar de Melo. Atende 2.160 beneficiários do CadÚnico em até 36 municípios do Tocantins, majoritariamente mulheres (71,9%), adultos jovens, comunidades periféricas e rurais, incluindo quilombolas, indígenas e agricultores familiares.

O WhatsApp é o **canal primário** de entrega de conteúdo educacional — não apenas suporte. O portal Frappe LMS (`lms.ipexdesenvolvimento.cloud`) é o repositório completo, acessível para quem tem computador/tablet.

**Perfil do público:** baixa literacia digital, móvel-first, conexão 4G potencialmente instável. Mensagens devem ser curtas, linguagem informal (você), tom acolhedor com exemplos do cotidiano do Tocantins/Bico do Papagaio. Emojis funcionais e moderados são aceitáveis.

---

## Arquitetura Atual (Estado em 08/04/2026)

### Containers em execução (servidor: 46.202.150.132)

| Container | Imagem | Status | IP interno |
|-----------|--------|--------|------------|
| `kreativ-rag` | mintplexlabs/anythingllm | ✅ healthy | dokploy-network |
| `kreativ-n8n` | n8nio/n8n | ⚠️ unhealthy | dokploy-network |
| `kreativ-chatwoot` | chatwoot/chatwoot:v4.11.0 | ⚠️ unhealthy | dokploy-network |
| `kreativ-chatwoot-sidekiq` | chatwoot/chatwoot:v4.11.0 | ✅ up | dokploy-network |
| `kreativ-postgres` | postgres:16-alpine | ✅ healthy | dokploy-network |
| `kreativ-redis` | redis:7-alpine | ✅ healthy | dokploy-network |
| `kreativ-mail` | analogic/poste.io | ✅ healthy | dokploy-network |
| `kreativ-ollama` | ollama/ollama | ⚠️ unhealthy | dokploy-network |
| `ollama` | ollama/ollama | ✅ up | dokploy-network |

> **Nota:** O status "unhealthy" do `kreativ-n8n` e `kreativ-chatwoot` provavelmente é falso positivo do health check — os serviços respondem normalmente via HTTPS. Verificar logs antes de tentar corrigir.

### URLs de produção

| Serviço | URL |
|---------|-----|
| Chatwoot | https://chat.ipexdesenvolvimento.cloud |
| N8N | https://n8n.ipexdesenvolvimento.cloud |
| AnythingLLM (RAG) | https://rag.ipexdesenvolvimento.cloud |
| Ollama (interno) | http://kreativ-ollama:11434 |

### Credenciais (todas em `/root/kreativ-setup/.env.real`)

| Variável | Valor |
|----------|-------|
| `CHATWOOT_ADMIN_EMAIL` | tdsdados@gmail.com |
| `CHATWOOT_ADMIN_PASSWORD` | 6QWuIKdZzYBmBdS3! |
| `CHATWOOT_API_KEY` (user token) | tbTMVRp2RwZNyGKKhRHUpNky |
| `CHATWOOT_ACCOUNT_ID` | 1 |
| `CHATWOOT_INBOX_ID` | 5 (nome: "Whatsapp - TDS", tipo: Channel::Whatsapp, Cloud API) |
| `N8N_API_KEY` | eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlMGQyZGM1Ni1mOTI3LTQ5YTMtOWEyOS0wYTI1OTE3N2E1ZWIiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiOTI1ZjhjNjMtMTNiZi00MzdhLWE0NGMtZGZmNTVhNmY5NWU5IiwiaWF0IjoxNzc1NDg4OTE2fQ.2ZHJeczWjGW8gWq7104Ga7kS5WwBcP3wjgysStBVliI |
| `ANYTHINGLLM_API_KEY` | W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0 |
| `GROQ_API_KEY` | gsk_REDACTED_GROQ_API_KEY |

### N8N — Workflow alvo

| Campo | Valor |
|-------|-------|
| ID | `XYcnRlPZSlfGXOWb` |
| Nome | "Kreativ TDS — Chatwoot RAG Flow" |
| Status | ACTIVE |
| Webhook path | `chatwoot-kreativ` |
| URL webhook completa | `https://n8n.ipexdesenvolvimento.cloud/webhook/chatwoot-kreativ` |

### AnythingLLM — Workspace alvo

| Campo | Valor |
|-------|-------|
| Slug | `tds` |
| Nome | "TDS — Tutor Cognitivo" |
| LLM atual | Gemini (gemini-2.5-flash) ← **precisa trocar para Groq** |
| Embedding | Ollama `nomic-embed-text` via `http://kreativ-ollama:11434` ← **manter** |
| Temperature | 0.4 |
| History | 20 mensagens |
| topN | 5 documentos |
| Endpoint de chat | `https://rag.ipexdesenvolvimento.cloud/api/v1/workspace/tds/chat` |

---

## Fluxo de Dados Completo

```
Aluno (WhatsApp)
      ↓
WhatsApp Cloud API
      ↓
Chatwoot inbox5 ("Whatsapp - TDS")
      ↓ Agent Bot webhook
      ↓ POST https://n8n.ipexdesenvolvimento.cloud/webhook/chatwoot-kreativ
N8N: "Kreativ TDS — Chatwoot RAG Flow"
      ↓
[Nó: Filtrar eventos]
  - Ignorar se event ≠ message_created
  - Ignorar se message_type ≠ incoming (ignorar mensagens do próprio bot)
  - Se content_type = audio → responder "não processo áudios, por favor digite"
  - Se content_type = image/file → responder "não processo arquivos, acesse o portal ou aguarde tutor"
      ↓
[Nó: Extrair dados]
  - conversationId = data.conversation.id
  - accountId = data.conversation.account_id (ou "1")
  - sessionId = data.meta.sender.identifier (telefone: "+5563...") — CHAVE para memória
  - contactName = data.meta.sender.name
  - messageText = data.content
  - route = handoff SE texto contém palavras-chave, SENÃO rag
      ↓
[Bifurcação: handoff ou rag?]

ROTA RAG:
  POST https://rag.ipexdesenvolvimento.cloud/api/v1/workspace/tds/chat
  Headers: { Authorization: "Bearer W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0" }
  Body: {
    "message": "<messageText>",
    "mode": "chat",
    "sessionId": "<sessionId>"
  }
  → Extrair campo "textResponse" da resposta
  → POST https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/conversations/<id>/messages
    Headers: { api_access_token: "tbTMVRp2RwZNyGKKhRHUpNky" }
    Body: { "content": "<textResponse>", "message_type": "outgoing" }

ROTA HANDOFF:
  → POST mensagem de handoff ao Chatwoot:
    "Um momento! Vou te conectar com um tutor humano. 👋"
  → POST https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/conversations/<id>/assignments
    Body: { "assignee_id": null }  (remove bot, libera para equipe humana)
```

**Reativação automática:** quando o tutor humano resolve/fecha a conversa no Chatwoot, a próxima mensagem do aluno abre nova conversa → Agent Bot assume automaticamente (comportamento nativo do Chatwoot Agent Bot).

---

## O Que Precisa Ser Feito

### Passo 1 — Trocar LLM do AnythingLLM: Gemini → Groq

**Modelo:** `llama-3.3-70b-versatile` (melhor equilíbrio qualidade/latência para português)

Chamada de API:
```bash
curl -X POST https://rag.ipexdesenvolvimento.cloud/api/v1/system/update-env \
  -H "Authorization: Bearer W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0" \
  -H "Content-Type: application/json" \
  -d '{
    "LLMProvider": "groq",
    "GroqApiKey": "gsk_REDACTED_GROQ_API_KEY",
    "GroqModelPref": "llama-3.3-70b-versatile"
  }'
```

Verificar após:
```bash
curl -s -H "Authorization: Bearer W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0" \
  https://rag.ipexdesenvolvimento.cloud/api/v1/system \
  | python3 -m json.tool | grep -E '"LLMProvider"|"LLMModel"'
```
Esperado: `"LLMProvider": "groq"` e `"LLMModel": "llama-3.3-70b-versatile"`

---

### Passo 2 — Criar Agent Bot no Chatwoot

```bash
curl -X POST https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/agent_bots \
  -H "api_access_token: tbTMVRp2RwZNyGKKhRHUpNky" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "TutorIA TDS",
    "description": "Tutor virtual do Projeto TDS — responde dúvidas sobre os cursos via RAG",
    "outgoing_url": "https://n8n.ipexdesenvolvimento.cloud/webhook/chatwoot-kreativ"
  }'
```

Salvar o `id` retornado (campo `"id"` no JSON de resposta). Usado no Passo 3.

---

### Passo 3 — Associar Agent Bot ao inbox5

Substituir `<AGENT_BOT_ID>` pelo id obtido no Passo 2:

```bash
curl -X POST https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/inboxes/5/set_agent_bot \
  -H "api_access_token: tbTMVRp2RwZNyGKKhRHUpNky" \
  -H "Content-Type: application/json" \
  -d '{ "agent_bot": <AGENT_BOT_ID> }'
```

Verificar:
```bash
curl -s -H "api_access_token: tbTMVRp2RwZNyGKKhRHUpNky" \
  "https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/inboxes/5/agent_bot" \
  | python3 -m json.tool
```
Esperado: retornar objeto com `"id"` e `"name": "TutorIA TDS"`

---

### Passo 4 — Atualizar o nó "Extrair Dados Chatwoot" no N8N

O nó atual **não extrai o sessionId (telefone)**. Substituir o código JavaScript do nó `Extrair Dados Chatwoot` (workflow `XYcnRlPZSlfGXOWb`) pelo seguinte:

```javascript
const input = $input.first().json;
const body = input.body || input;

// Ignorar eventos que não sejam criação de mensagem
if (body.event && body.event !== 'message_created') {
  return [];
}

// Ignorar mensagens enviadas pelo próprio bot (outgoing)
const msgType = String(body.message_type ?? body.message?.message_type ?? '');
if (msgType === 'outgoing' || msgType === '1') {
  return [];
}

// Ignorar mensagens de agentes humanos
const senderType = String(body.sender?.type ?? '');
if (senderType === 'agent_bot' || senderType === 'user') {
  return [];
}

// Detectar tipo de conteúdo
const contentType = String(body.content_type ?? body.message?.content_type ?? 'text');
const messageText = String(body.content || body.message?.content || '').trim();

// Áudio: pedir para digitar
if (contentType === 'audio' || contentType === 'voice') {
  return [{
    json: {
      conversationId: String(body.conversation?.id || ''),
      accountId: String(body.conversation?.account_id || '1'),
      sessionId: String(body.meta?.sender?.identifier || body.sender?.phone_number || body.conversation?.meta?.sender?.identifier || ''),
      contactName: String(body.meta?.sender?.name || body.sender?.name || ''),
      messageText: '',
      route: 'audio'
    }
  }];
}

// Imagem ou arquivo: redirecionar para portal
if (contentType === 'image' || contentType === 'file' || contentType === 'sticker') {
  return [{
    json: {
      conversationId: String(body.conversation?.id || ''),
      accountId: String(body.conversation?.account_id || '1'),
      sessionId: String(body.meta?.sender?.identifier || body.sender?.phone_number || body.conversation?.meta?.sender?.identifier || ''),
      contactName: String(body.meta?.sender?.name || body.sender?.name || ''),
      messageText: '',
      route: 'media'
    }
  }];
}

// Palavras-chave de handoff
const keywordPattern = /tutor|prova|exame|certificado|humano|operador|atendente|bolsa|cad[uú]nico|benefício|reclamação|ajuda humana|falar com alguém|não consigo|problema/i;
const route = keywordPattern.test(messageText) ? 'handoff' : 'rag';

return [{
  json: {
    conversationId: String(body.conversation?.id || ''),
    accountId: String(body.conversation?.account_id || '1'),
    sessionId: String(body.meta?.sender?.identifier || body.sender?.phone_number || body.conversation?.meta?.sender?.identifier || ''),
    contactName: String(body.meta?.sender?.name || body.sender?.name || ''),
    messageText: messageText,
    route: route
  }
}];
```

---

### Passo 5 — Adicionar ramos para áudio e mídia no workflow

Após o nó "É Prova/Tutor?", adicionar dois novos ramos de IF para `route === 'audio'` e `route === 'media'`, cada um conectado a um nó HTTP que envia mensagem fixa ao Chatwoot:

**Resposta para áudio:**
```
Oi! Ainda não consigo ouvir áudios, mas pode me digitar sua dúvida que respondo rapidinho 😊
```

**Resposta para imagem/arquivo:**
```
Não consigo processar arquivos por aqui. Para enviar documentos, acesse o portal: lms.ipexdesenvolvimento.cloud — ou aguarde um tutor humano te ajudar!
```

Ambos os nós usam:
```
POST https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/{{ $json.accountId }}/conversations/{{ $json.conversationId }}/messages
Headers: { api_access_token: tbTMVRp2RwZNyGKKhRHUpNky, Content-Type: application/json }
Body: { "content": "<mensagem fixa acima>", "message_type": "outgoing" }
```

---

### Passo 6 — Adicionar sessionId na chamada ao AnythingLLM

No nó "Consultar RAG" (tipo httpRequest), o body atual provavelmente não inclui `sessionId`. Atualizar para:

```json
{
  "message": "={{ $('Extrair Dados Chatwoot').item.json.messageText }}",
  "mode": "chat",
  "sessionId": "={{ $('Extrair Dados Chatwoot').item.json.sessionId }}"
}
```

O `sessionId` vinculado ao número de telefone garante que o AnythingLLM mantenha histórico de conversa por aluno (memória stateful).

---

### Passo 7 — Verificar rota de handoff (assign → null)

O nó "Transbordo Humano" atual provavelmente só envia mensagem. Adicionar chamada de atribuição para liberar a conversa para a fila humana:

```
POST https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/{{ $json.accountId }}/conversations/{{ $json.conversationId }}/assignments
Headers: { api_access_token: tbTMVRp2RwZNyGKKhRHUpNky, Content-Type: application/json }
Body: { "assignee_id": null }
```

---

## Verificação Final (Checklist)

```
[ ] AnythingLLM responde via Groq:
    curl -s -H "Authorization: Bearer W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0" \
      https://rag.ipexdesenvolvimento.cloud/api/v1/system \
      | python3 -m json.tool | grep LLMProvider
    Esperado: "LLMProvider": "groq"

[ ] Agent Bot criado no Chatwoot:
    curl -s -H "api_access_token: tbTMVRp2RwZNyGKKhRHUpNky" \
      https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/agent_bots \
      | python3 -m json.tool
    Esperado: array com objeto "TutorIA TDS"

[ ] Agent Bot associado ao inbox5:
    curl -s -H "api_access_token: tbTMVRp2RwZNyGKKhRHUpNky" \
      https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/inboxes/5/agent_bot \
      | python3 -m json.tool
    Esperado: objeto com name "TutorIA TDS"

[ ] N8N workflow atualizado — teste de payload manual:
    curl -X POST https://n8n.ipexdesenvolvimento.cloud/webhook/chatwoot-kreativ \
      -H "Content-Type: application/json" \
      -d '{
        "event": "message_created",
        "message_type": "incoming",
        "content": "O que é cooperativismo?",
        "content_type": "text",
        "conversation": { "id": 999, "account_id": 1 },
        "meta": { "sender": { "name": "Teste", "identifier": "+5563999999999" } },
        "sender": { "type": "contact" }
      }'
    Esperado: N8N processa, AnythingLLM retorna resposta, Chatwoot recebe mensagem na conversa 999

[ ] Teste de handoff:
    Mesmo payload, trocar content para "quero falar com um tutor"
    Esperado: mensagem de handoff enviada + conversa liberada para fila humana

[ ] Teste de áudio:
    Mesmo payload, trocar content_type para "audio"
    Esperado: mensagem "Ainda não consigo ouvir áudios..."
```

---

## Contexto Pedagógico para o System Prompt (já configurado, NÃO alterar)

O workspace `tds` no AnythingLLM já possui system prompt em português com:
- Apresentação do tutor como virtual do Projeto TDS/Tocantins
- Perfil do público (71,9% mulheres, comunidades periféricas, Bico do Papagaio)
- Lista dos 5 cursos disponíveis
- Instruções de estilo (linguagem informal, respostas curtas, exemplos locais)
- Resposta de recusa: "Não encontrei essa informação nos materiais do TDS. Posso te conectar com um tutor humano — só digitar 'tutor'!"

**NÃO modificar o system prompt existente.**

---

## O Que Este Spec NÃO Cobre (fora do escopo)

- Horário de atendimento dos tutores humanos (a definir pela coordenação UFT/FAPTO)
- Nome final do bot (TutorIA TDS é placeholder; a equipe TDS pode renomear)
- Critérios formais de aprovação nos cursos (a definir pela coordenação pedagógica)
- Notificações proativas (nudges a cada 48h para alunos inativos) — sprint futuro
- Quizzes inline via WhatsApp — sprint futuro
- Integração com Frappe LMS para progresso/matrícula — sprint futuro
- Certificados via WhatsApp — sprint futuro
