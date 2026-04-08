# Design: Agente Inteligente WhatsApp TDS
**Data:** 2026-04-08  
**Status:** Aprovado para implementação  
**Executor:** Agente autônomo (sem contexto de conversa prévia)

---

## Contexto do Projeto

O Projeto TDS (Território de Desenvolvimento Social e Inclusão Produtiva) é uma plataforma de inclusão social da NERUDS/UFT via FAPTO (Bolsa nº 212/2026), coordenada por Juliana Aguiar de Melo. Atende 2.160 beneficiários do CadÚnico em até 36 municípios do Tocantins, majoritariamente mulheres (71,9%), adultos jovens de comunidades periféricas e rurais do Bico do Papagaio (destaque: Itaguatins, Praia Norte, Araguatins) e Jalapão/Dianópolis, incluindo quilombolas, indígenas e agricultores familiares.

### Papel do WhatsApp

O WhatsApp é o **canal primário de aprendizagem** — não apenas suporte. Ele entrega conteúdo, conduz avaliações, informa progresso e emite certificados. O Frappe LMS e PostgreSQL operam na retaguarda gerindo armazenamento assíncrono e histórico metodológico.

### Perfil do público

- Baixa literacia digital, móvel-first, conectividade instável (municípios pequenos)
- Mensagens curtas, linguagem acessível mas com **postura acadêmica institucional** (bot representa UFT/FAPTO)
- Tom: `você` (informal no registro, mas com autoridade institucional)
- Geração X e Baby Boomers (~18%) necessitam de assistência humanizada → handoff prioritário
- Pico de acesso: **noturno em dias úteis** e **tardes de finais de semana**

### Jornada completa do aluno (5 ações de sistema)

```
1. check_student    → valida cadastro no CadÚnico / matrícula
2. get_module       → entrega conteúdo do módulo atual
3. submit_quiz      → IA gera 3 questões discursivas do módulo + avalia + feedback qualitativo
4. get_progress     → informa progresso acumulado
5. emit_certificate → verifica aprovação, gera PDF, persiste no PostgreSQL, devolve URL via WhatsApp
```

> ⚠️ As ações 1–5 dependem do **Frappe LMS** em produção. O container Frappe **não está rodando** em 08/04/2026. Sprint 1 entrega o canal de comunicação inteligente (RAG + handoff). Sprint 2 entrega as ações estruturadas.

### Identidade dos bots

| Instância | Nome | Função |
|-----------|------|--------|
| **Sprint 1** | Tutor IA | Atendimento direto ao aluno via WhatsApp |
| **Sprint 2** | Chatwoot Captain | Copiloto de respostas para tutores humanos no Chatwoot |

### Estrutura dos cursos

5 trilhas × 2 cursos × 80h (40h presencial + 20h remoto gravado + 20h mentoria) = 160h/trilha

| Trilha | Nome |
|--------|------|
| T1 | Empreendedorismo Popular e Gestão de Negócios |
| T2 | Formação Cooperativista Popular |
| T3 | Agricultura Familiar e Políticas Públicas Federais |
| T4 | Sistemas Produtivos Sustentáveis e Tecnologias Sociais |
| T5 | Inovação e Certificação Agroecológica |

**Unidade de avaliação:** módulo (não apenas ao final da trilha). A IA gera 3 questões discursivas estritamente baseadas no conteúdo do módulo e fornece feedback qualitativo por conceito — sem nota binária.

---

## Arquitetura Atual (Estado em 08/04/2026)

### Containers em execução (servidor: 46.202.150.132)

| Container | Imagem | Status |
|-----------|--------|--------|
| `kreativ-rag` | mintplexlabs/anythingllm | ✅ healthy |
| `kreativ-n8n` | n8nio/n8n | ⚠️ unhealthy (falso positivo — responde via HTTPS) |
| `kreativ-chatwoot` | chatwoot/chatwoot:v4.11.0 | ⚠️ unhealthy (falso positivo) |
| `kreativ-chatwoot-sidekiq` | chatwoot/chatwoot:v4.11.0 | ✅ up |
| `kreativ-postgres` | postgres:16-alpine | ✅ healthy |
| `kreativ-redis` | redis:7-alpine | ✅ healthy |
| `kreativ-mail` | analogic/poste.io | ✅ healthy |
| `kreativ-ollama` | ollama/ollama | ⚠️ unhealthy |
| `ollama` | ollama/ollama | ✅ up |

**NÃO há container do Frappe LMS rodando.** Sprint 1 não depende dele.

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
| `CHATWOOT_INBOX_ID` | 5 ("Whatsapp - TDS", Channel::Whatsapp, Cloud API) |
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

## Escopo do Sprint 1 (este spec)

**Entrega:** Canal WhatsApp → Tutor IA funcional com memória por aluno, handoff para humano e tratamento de mídia.

**Fora do escopo (Sprint 2+):**
- Ações estruturadas: `check_student`, `get_module`, `submit_quiz`, `get_progress`, `emit_certificate`
- Chatwoot Captain (copiloto para tutores)
- STT (Speech-to-Text) para áudios — Sprint 1 pede para digitar
- TTS (Text-to-Speech) para respostas em áudio
- Processamento de documentos/imagens enviados pelos alunos
- Typebot v6 para fluxos de quiz estruturado
- Notificações proativas (nudges a cada 48h)

---

## Fluxo de Dados — Sprint 1

```
Aluno (WhatsApp)
      ↓
WhatsApp Cloud API (Meta Cloud API)
      ↓
Chatwoot inbox5 ("Whatsapp - TDS", id=5)
      ↓ Agent Bot webhook
      ↓ POST https://n8n.ipexdesenvolvimento.cloud/webhook/chatwoot-kreativ
N8N: "Kreativ TDS — Chatwoot RAG Flow" (id: XYcnRlPZSlfGXOWb)
      ↓
[Filtrar eventos]
  - Ignorar se event ≠ message_created
  - Ignorar mensagens do bot (outgoing / sender.type = agent_bot ou user)
  - Detectar content_type: text | audio | image/file
      ↓
[Extrair dados]
  conversationId  = body.conversation.id
  accountId       = body.conversation.account_id  (fallback: "1")
  sessionId       = body.meta.sender.identifier   (telefone: "+5563...")  ← CHAVE DE MEMÓRIA
  contactName     = body.meta.sender.name
  messageText     = body.content
  route           = handoff | rag | audio | media
      ↓
[Bifurcação por rota]

ROTA audio:
  → "Oi! Ainda não consigo ouvir áudios, mas você pode digitar sua dúvida que respondo na hora! 😊"

ROTA media:
  → "Não consigo processar arquivos por aqui. Para enviar documentos, acesse o portal
     lms.ipexdesenvolvimento.cloud — ou aguarde um tutor humano te ajudar!"

ROTA handoff:
  → "Entendido! Vou conectar você com um tutor humano agora. 
     Nosso atendimento humano funciona principalmente à noite nos dias úteis 
     e nas tardes de fim de semana. Em breve alguém vai te responder! 👋"
  → POST /assignments  { "assignee_id": null }   ← libera para fila humana

ROTA rag:
  POST https://rag.ipexdesenvolvimento.cloud/api/v1/workspace/tds/chat
  Headers: { Authorization: "Bearer W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0" }
  Body: {
    "message":   "<messageText>",
    "mode":      "chat",
    "sessionId": "<sessionId>"       ← memória por aluno
  }
  → Extrair campo "textResponse"
  → POST /messages  { "content": "<textResponse>", "message_type": "outgoing" }
```

**Palavras-chave de handoff** (capturadas por regex no nó de extração):
```
tutor | prova | exame | certificado | humano | operador | atendente |
bolsa | cadúnico | cad único | benefício | reclamação | ajuda humana |
falar com alguém | não consigo | problema | gerações anteriores
```

**Reativação automática:** quando tutor fecha/resolve a conversa no Chatwoot, a próxima mensagem do aluno abre nova conversa → Agent Bot assume automaticamente (comportamento nativo do Chatwoot Agent Bot).

---

## Passos de Implementação

### Passo 1 — Trocar LLM do AnythingLLM: Gemini → Groq

**Modelo recomendado:** `llama-3.3-70b-versatile` (melhor compreensão de português + qualidade de raciocínio)

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

Verificar:
```bash
curl -s -H "Authorization: Bearer W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0" \
  https://rag.ipexdesenvolvimento.cloud/api/v1/system \
  | python3 -m json.tool | grep -E '"LLMProvider"|"LLMModel"'
# Esperado: "LLMProvider": "groq", "LLMModel": "llama-3.3-70b-versatile"
```

---

### Passo 2 — Atualizar System Prompt do workspace "tds"

O system prompt atual usa "linguagem informal". Deve refletir a **postura acadêmica institucional** do projeto, mantendo acessibilidade. Substituir via API:

```bash
curl -X POST https://rag.ipexdesenvolvimento.cloud/api/v1/workspace/tds/update \
  -H "Authorization: Bearer W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0" \
  -H "Content-Type: application/json" \
  -d '{
    "openAiPrompt": "Você é o Tutor IA do Projeto TDS — Território de Desenvolvimento Social e Inclusão Produtiva, iniciativa da Universidade Federal do Tocantins (UFT), FAPTO e IPEX, com apoio do Ministério do Desenvolvimento Social (MDS).\n\nSEU PAPEL: Tutora virtual oficial do projeto. Responda exclusivamente com base nos materiais dos cursos TDS (apostilas, ementas e plano de trabalho). Nunca invente informações.\n\nPÚBLICO: Beneficiários do CadÚnico em municípios do Tocantins (Bico do Papagaio, Jalapão/Dianópolis). Maioria mulheres, adultos jovens, com acesso móvel e conectividade limitada.\n\nCURSOS DISPONÍVEIS:\n1. Empreendedorismo Popular e Gestão de Negócios\n2. Formação Cooperativista Popular\n3. Agricultura Familiar e Políticas Públicas Federais\n4. Sistemas Produtivos Sustentáveis e Tecnologias Sociais\n5. Inovação e Certificação Agroecológica\n\nESTILO DE RESPOSTA:\n- Use \"você\" (nunca \"senhor/senhora\")\n- Linguagem direta e acessível, com autoridade de uma instituição de ensino\n- Respostas curtas (máximo 3 parágrafos)\n- Exemplos práticos do cotidiano do Tocantins e da realidade rural/periférica\n- Emojis funcionais e moderados são permitidos\n- Temas de empreendedorismo feminino e autonomia financeira têm prioridade temática\n\nQUANDO NÃO SOUBER: Diga exatamente: \"Não encontrei essa informação nos materiais do TDS. Você pode digitar tutor para falar com nossa equipe!\"\n\nJAMAIS responda sobre: benefícios do governo, questões pessoais de saúde, problemas com o Bolsa Família ou CadÚnico — esses casos devem ir para o tutor humano."
  }'
```

---

### Passo 3 — Criar Agent Bot no Chatwoot

```bash
curl -X POST https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/agent_bots \
  -H "api_access_token: tbTMVRp2RwZNyGKKhRHUpNky" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tutor IA",
    "description": "Tutor virtual oficial do Projeto TDS/UFT — atende dúvidas sobre os cursos via RAG",
    "outgoing_url": "https://n8n.ipexdesenvolvimento.cloud/webhook/chatwoot-kreativ"
  }'
```

**Salvar o `id` retornado.** Exemplo de resposta: `{"id": 1, "name": "Tutor IA", ...}`

---

### Passo 4 — Associar Agent Bot ao inbox5

Substituir `<AGENT_BOT_ID>` pelo id do Passo 3:

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
# Esperado: objeto com "name": "Tutor IA"
```

---

### Passo 5 — Substituir código do nó "Extrair Dados Chatwoot" no N8N

Workflow `XYcnRlPZSlfGXOWb` — nó `Extrair Dados Chatwoot` (tipo: Code). Substituir o JS inteiro por:

```javascript
const input = $input.first().json;
const body = input.body || input;

// Ignorar eventos que não sejam criação de mensagem
if (body.event && body.event !== 'message_created') {
  return [];
}

// Ignorar mensagens do bot ou de agentes humanos (só processar mensagens de contatos)
const msgType = String(body.message_type ?? body.message?.message_type ?? '');
if (msgType === 'outgoing' || msgType === '1') return [];

const senderType = String(body.sender?.type ?? '');
if (senderType === 'agent_bot' || senderType === 'user') return [];

// Extrair sessionId = número de telefone do contato (garante memória por aluno)
const sessionId = String(
  body.meta?.sender?.identifier ||
  body.sender?.phone_number ||
  body.conversation?.meta?.sender?.identifier ||
  body.contact?.phone_number ||
  ''
);

const conversationId = String(body.conversation?.id || '');
const accountId      = String(body.conversation?.account_id || '1');
const contactName    = String(body.meta?.sender?.name || body.sender?.name || '');
const contentType    = String(body.content_type ?? body.message?.content_type ?? 'text');
const messageText    = String(body.content || body.message?.content || '').trim();

// Áudio → rota especial (Sprint 2 terá STT; por ora pede para digitar)
if (contentType === 'audio' || contentType === 'voice') {
  return [{ json: { conversationId, accountId, sessionId, contactName, messageText: '', route: 'audio' } }];
}

// Imagem / arquivo → redirecionar para portal ou tutor
if (contentType === 'image' || contentType === 'file' || contentType === 'sticker') {
  return [{ json: { conversationId, accountId, sessionId, contactName, messageText: '', route: 'media' } }];
}

// Palavras-chave de handoff (inclui contexto social sensível)
const handoffPattern = /tutor|prova|exame|certificado|humano|operador|atendente|bolsa|cad[uú]nico|cad\s+[uú]nico|benef[ií]cio|reclama[cç][aã]o|ajuda humana|falar com algu[eé]m|n[aã]o consigo|problema/i;
const route = handoffPattern.test(messageText) ? 'handoff' : 'rag';

return [{ json: { conversationId, accountId, sessionId, contactName, messageText, route } }];
```

---

### Passo 6 — Adicionar ramos de IF para `audio` e `media` no workflow

O workflow atual só tem bifurcação handoff/rag. Adicionar dois novos ramos após o nó de extração:

**Ramo audio** — IF `route === 'audio'` → nó HTTP POST com body:
```json
{
  "content": "Oi! Ainda não consigo ouvir áudios, mas você pode digitar sua dúvida que respondo na hora! 😊",
  "message_type": "outgoing"
}
```

**Ramo media** — IF `route === 'media'` → nó HTTP POST com body:
```json
{
  "content": "Não consigo processar arquivos por aqui. Para enviar documentos, acesse o portal lms.ipexdesenvolvimento.cloud — ou aguarde um tutor humano te ajudar!",
  "message_type": "outgoing"
}
```

URL para ambos os nós:
```
https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/{{ $json.accountId }}/conversations/{{ $json.conversationId }}/messages
```
Header: `api_access_token: tbTMVRp2RwZNyGKKhRHUpNky`

---

### Passo 7 — Adicionar sessionId na chamada ao AnythingLLM (nó "Consultar RAG")

Atualizar o body do nó `Consultar RAG` (httpRequest):

```json
{
  "message":   "={{ $('Extrair Dados Chatwoot').item.json.messageText }}",
  "mode":      "chat",
  "sessionId": "={{ $('Extrair Dados Chatwoot').item.json.sessionId }}"
}
```

---

### Passo 8 — Completar nó "Transbordo Humano" (adicionar desatribuição)

O nó atual provavelmente só envia mensagem. Adicionar **segundo nó HTTP** após a mensagem de handoff:

**Mensagem de handoff** (já deve existir, verificar texto e atualizar):
```json
{
  "content": "Entendido! Vou conectar você com um tutor humano agora. Nosso atendimento humano funciona principalmente à noite nos dias úteis e nas tardes de fim de semana. Em breve alguém vai te responder! 👋",
  "message_type": "outgoing"
}
```

**Desatribuição** (novo nó após a mensagem):
```
POST https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/{{ $json.accountId }}/conversations/{{ $json.conversationId }}/assignments
Body: { "assignee_id": null }
```

---

## Checklist de Verificação

```
[ ] 1. AnythingLLM usando Groq:
       curl -s -H "Authorization: Bearer W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0" \
         https://rag.ipexdesenvolvimento.cloud/api/v1/system \
         | python3 -m json.tool | grep LLMProvider
       → "LLMProvider": "groq"

[ ] 2. System prompt atualizado no workspace tds:
       curl -s -H "Authorization: Bearer W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0" \
         https://rag.ipexdesenvolvimento.cloud/api/v1/workspaces \
         | python3 -m json.tool | grep -A2 "openAiPrompt"
       → prompt contém "Universidade Federal do Tocantins"

[ ] 3. Agent Bot "Tutor IA" criado:
       curl -s -H "api_access_token: tbTMVRp2RwZNyGKKhRHUpNky" \
         https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/agent_bots \
         | python3 -m json.tool
       → array com objeto name "Tutor IA"

[ ] 4. Agent Bot associado ao inbox5:
       curl -s -H "api_access_token: tbTMVRp2RwZNyGKKhRHUpNky" \
         https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/inboxes/5/agent_bot \
         | python3 -m json.tool
       → objeto com "name": "Tutor IA"

[ ] 5. Teste RAG com sessionId:
       curl -X POST https://n8n.ipexdesenvolvimento.cloud/webhook/chatwoot-kreativ \
         -H "Content-Type: application/json" \
         -d '{
           "event": "message_created",
           "message_type": "incoming",
           "content": "O que é cooperativismo?",
           "content_type": "text",
           "conversation": { "id": 999, "account_id": 1 },
           "meta": { "sender": { "name": "Maria", "identifier": "+5563999999999" } },
           "sender": { "type": "contact" }
         }'
       → N8N processa, Chatwoot recebe resposta sobre cooperativismo na conversa 999

[ ] 6. Teste de handoff:
       Mesmo payload, content: "quero falar com um tutor"
       → Chatwoot recebe mensagem de handoff + conversa liberada para fila humana

[ ] 7. Teste de áudio:
       Mesmo payload, content_type: "audio"
       → Chatwoot recebe "Ainda não consigo ouvir áudios..."

[ ] 8. Teste de memória (sessionId):
       Enviar 2 payloads sequenciais com mesmo identifier "+5563999999999"
       Segunda mensagem: "pode repetir o que disse antes?"
       → AnythingLLM deve responder usando contexto da primeira mensagem
```

---

## Roadmap Sprint 2+ (não implementar agora)

### Sprint 2 — Ações estruturadas (requer Frappe LMS em produção)

Implementar intent detection no N8N para rotear para ações específicas:

| Intent detectada | Ação N8N | Endpoint Frappe |
|-----------------|----------|-----------------|
| "quero começar o curso" / "próximo módulo" | `get_module` | `GET /api/resource/Course Lesson` |
| "já estudei, quero fazer a prova" | `submit_quiz` | IA gera 3 questões discursivas via AnythingLLM + avalia respostas |
| "qual meu progresso?" | `get_progress` | `GET /api/resource/LMS Enrollment` |
| "quero meu certificado" | `emit_certificate` | `POST /api/method/lms.emit_certificate` → URL do PDF |
| primeira mensagem de número novo | `check_student` | `GET /api/resource/LMS Enrollment?filters=[["student","=","..."]]` |

### Sprint 2 — Chatwoot Captain (copiloto para tutores)

Segundo Agent Bot que observa conversas abertas com agentes humanos e sugere respostas baseadas no RAG, sem intervir diretamente. Usa a mesma infraestrutura AnythingLLM/Groq.

### Sprint 3 — STT/TTS (acessibilidade)

- **STT:** Groq Whisper API (`POST https://api.groq.com/openai/v1/audio/transcriptions`) para transcrever áudios recebidos antes de enviar ao RAG
- **TTS:** Text-to-Speech para responder em áudio quando solicitado (biblioteca `pyttsx3` ou API externa)
- Objetivo: eliminar barreira de literacia digital para público com dificuldades de digitação

### Sprint 3 — Typebot v6

Para fluxos de quiz estruturado (múltipla escolha inline, botões interativos), integrar Typebot v6 como camada de UX entre o WhatsApp e o N8N. Atualmente não há container Typebot no servidor.
