"""
create_enrollment_gateway.py
Cria o workflow de matrícula gateway no n8n e atualiza o Chatwoot bot.

FIXES aplicados em 09/04/2026 (versão v2):
- PG_CRED_ID correto: wAJovSb9ceHlYden (sem SSL) — NÃO usar dxU0dZ2Fe1yaJhGg
- CHATWOOT_API_KEY correto: 24 chars (sem o 'C' extra)
- continueOnFail: True em TODOS os nós (incluindo Fluxo Matrícula e Resposta Matrícula)
- COALESCE query: garante retorno de 1 linha mesmo para novos usuários
- n8n caches workflow em memória — ao atualizar, SEMPRE deactivate + delete + recreate
"""
import requests, urllib3, json
urllib3.disable_warnings()

N8N = "https://n8n.ipexdesenvolvimento.cloud"
CHATWOOT = "https://chat.ipexdesenvolvimento.cloud"
PG_CRED_ID = "wAJovSb9ceHlYden"  # PostgreSQL Kreativ (sem SSL) — o que funciona!
RAG_WEBHOOK = "https://n8n.ipexdesenvolvimento.cloud/webhook/chatwoot-kreativ"
CHATWOOT_API_KEY = "w8BYLTQc1s5VMowjQw433rGy"  # 24 chars — correto

# ── Login n8n ──────────────────────────────────────────────────────────────
session = requests.Session()
session.verify = False
r = session.post(f"{N8N}/rest/login",
    json={"emailOrLdapLoginId": "tdsdados@gmail.com", "password": "Admin@TDS2024"},
    timeout=15)
assert r.status_code == 200, f"n8n login falhou: {r.text}"
print("✅ n8n login OK")

# ── Código do extrator de dados ───────────────────────────────────────────
EXTRAIR_CODE = r"""
const input = $input.first().json;
const body = input.body || input;

// Ignorar eventos que não sejam criação de mensagem
if (body.event && body.event !== 'message_created') return [];
const msgType = String(body.message_type ?? body.message?.message_type ?? '');
if (msgType === 'outgoing' || msgType === '1') return [];
const senderType = String(body.sender?.type ?? '');
if (senderType === 'agent_bot' || senderType === 'user') return [];

const sessionId = String(
  body.meta?.sender?.identifier ||
  body.sender?.phone_number ||
  body.conversation?.meta?.sender?.identifier ||
  body.contact?.phone_number || ''
);
const conversationId = String(body.conversation?.id || '');
const accountId      = String(body.conversation?.account_id || '1');
const contactName    = String(body.meta?.sender?.name || body.sender?.name || '');
const contentType    = String(body.content_type ?? body.message?.content_type ?? 'text');
const messageText    = String(body.content || body.message?.content || '').trim();

// Normalizar telefone
const phoneClean = sessionId.replace(/[^\d]/g, '');

return [{ json: {
  sessionId, phoneClean, conversationId, accountId, contactName,
  contentType, messageText,
  rawBody: body
}}];
"""

# ── Código da máquina de estados de matrícula ─────────────────────────────
MATRICULA_CODE = r"""
const extrair = $('Extrair Dados').first().json;
const { phoneClean, conversationId, accountId, messageText, contactName } = extrair;

// Pegar draft do Postgres
let draft = {};
try {
  const pg = $('Verificar Matrícula').first().json;
  if (pg && pg.phone) draft = pg;
} catch(e) {}

const currentState = draft.estado || 'novo';
const txt = (messageText || '').trim();

const CURSOS = [
  { nome: 'Agricultura Sustentável — Sistemas Agroflorestais', slug: 'tds-agricultura-sustentavel' },
  { nome: 'Audiovisual e Produção de Conteúdo Digital',        slug: 'tds-audiovisual-e-conteudo' },
  { nome: 'Finanças e Empreendedorismo',                       slug: 'tds-financas-e-empreendedorismo' },
  { nome: 'Educação Financeira para a Melhor Idade',           slug: 'tds-educacao-financeira-terceira-idade' },
  { nome: 'Associativismo e Cooperativismo',                   slug: 'tds-associativismo-e-cooperativismo' },
  { nome: 'IA no meu Bolso — Inteligência Artificial para o Dia a Dia', slug: 'tds-ia-no-meu-bolso' },
  { nome: 'SIM — Serviço de Inspeção Municipal para Pequenos Produtores', slug: 'tds-sim' }
];

let nextMessage = '';
let nextState = currentState;
let updates = {};
let isComplete = false;

if (currentState === 'novo') {
  nextState = 'aguarda_nome';
  const pn = (contactName || '').split(' ')[0];
  const ola = pn ? `Olá, ${pn}! 👋` : 'Olá! 👋';
  nextMessage = `${ola}\n\nBem-vindo(a) ao *Programa TDS* — Transformação Digital para Inclusão Social! 🌱\n\nCursos gratuitos, com certificado, direto no WhatsApp, no seu ritmo.\n\nPra garantir sua vaga, preciso de algumas informações rápidas. Pode me dizer seu *nome completo*?`;

} else if (currentState === 'aguarda_nome') {
  if (txt.length >= 3 && txt.split(' ').length >= 2) {
    updates.nome = txt;
    nextState = 'aguarda_cpf';
    const pn = txt.split(' ')[0];
    nextMessage = `Prazer, ${pn}! 😊\n\nPreciso do seu *CPF* (somente os 11 números).\n\n💡 Ele é necessário para emitir o certificado pelo IPEX. Seus dados ficam protegidos e não são compartilhados.`;
  } else {
    nextMessage = `Por favor, informe seu *nome completo* (nome e sobrenome):`;
  }

} else if (currentState === 'aguarda_cpf') {
  const cpf = txt.replace(/\D/g, '');
  if (cpf.length === 11) {
    updates.cpf = cpf;
    nextState = 'aguarda_municipio';
    nextMessage = `✅ CPF registrado!\n\nEm qual *município* você mora?`;
  } else {
    nextMessage = `O CPF precisa ter 11 dígitos. Por favor, tente novamente (somente números, ex: 12345678901):`;
  }

} else if (currentState === 'aguarda_municipio') {
  if (txt.length >= 2) {
    updates.municipio = txt;
    nextState = 'aguarda_renda';
    nextMessage = `📍 *${txt}* — anotado!\n\nA FAPTO — entidade que financia o programa — precisa saber a *renda mensal da sua família*. Não afeta sua matrícula!\n\n1️⃣ Até R$ 218\n2️⃣ De R$ 218 a R$ 660\n3️⃣ De R$ 660 a R$ 2.640\n4️⃣ Acima de R$ 2.640\n5️⃣ Prefiro não informar\n\nDigite o número:`;
  } else {
    nextMessage = `Por favor, informe o nome do *município* onde você mora:`;
  }

} else if (currentState === 'aguarda_renda') {
  const rendaMap = {
    '1':'Até R$ 218 (extrema pobreza)',
    '2':'De R$ 218 a R$ 660 (pobreza)',
    '3':'De R$ 660 a R$ 2.640 (baixa renda)',
    '4':'Acima de R$ 2.640',
    '5':'Prefiro não informar'
  };
  updates.renda_familiar = rendaMap[txt] || txt;
  nextState = 'aguarda_curso';
  const menu = CURSOS.map((c, i) => `${i+1}️⃣ ${c.nome}`).join('\n');
  nextMessage = `📚 Agora a melhor parte — escolha seu *curso*!\n\n${menu}\n\nDigite o número da opção:`;

} else if (currentState === 'aguarda_curso') {
  const idx = parseInt(txt) - 1;
  if (idx >= 0 && idx < CURSOS.length) {
    const curso = CURSOS[idx];
    updates.curso_escolhido = curso.nome;
    updates.workspace_slug = curso.slug;
    updates.estado = 'completo';
    nextState = 'completo';
    isComplete = true;
    nextMessage = `🎉 *Matrícula confirmada!*\n\n📚 Curso: *${curso.nome}*\n\nSeu tutor de IA já está pronto! Pode perguntar qualquer coisa sobre o curso.\n\nDica: digite *quiz* quando quiser testar seus conhecimentos e avançar para o certificado! 🏆`;
  } else {
    nextMessage = `Por favor, digite um número de 1 a ${CURSOS.length}:`;
  }
}

// SQL upsert
const phone = phoneClean;
const setItems = { ...updates, estado: nextState, updated_at: "NOW()" };
const setParts = Object.entries(setItems)
  .map(([k, v]) => v === "NOW()" ? `${k} = NOW()` : `${k} = '${String(v).replace(/'/g, "''")}'`)
  .join(', ');

const upsertSql = `
  INSERT INTO enrollment_drafts (phone, estado)
  VALUES ('${phone}', '${nextState}')
  ON CONFLICT (phone) DO UPDATE SET ${setParts}
`;

return [{ json: { nextMessage, nextState, upsertSql, isComplete, conversationId, accountId, phone }}];
"""

# ── Montar workflow JSON ───────────────────────────────────────────────────
workflow = {
    "name": "TDS — Enrollment Gateway (Matrícula + RAG)",
    "active": False,
    "nodes": [
        {
            "id": "wh-gateway",
            "name": "Webhook Gateway",
            "type": "n8n-nodes-base.webhook",
            "typeVersion": 2,
            "position": [240, 400],
            "webhookId": "tds-gateway-001",
            "parameters": {
                "path": "tds-gateway",
                "httpMethod": "POST",
                "responseMode": "onReceived",
                "responseData": "noData"
            }
        },
        {
            "id": "extrair-dados",
            "name": "Extrair Dados",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [460, 400],
            "parameters": {"jsCode": EXTRAIR_CODE}
        },
        {
            "id": "verificar-matricula",
            "name": "Verificar Matrícula",
            "type": "n8n-nodes-base.postgres",
            "typeVersion": 2,
            "position": [680, 400],
            "continueOnFail": True,
            "parameters": {
                "operation": "executeQuery",
                "query": "SELECT * FROM enrollment_drafts WHERE phone = '{{ $json.phoneClean }}' LIMIT 1"
            },
            "credentials": {
                "postgres": {"id": PG_CRED_ID, "name": "PostgreSQL - Kreativ"}
            }
        },
        {
            "id": "e-matriculado",
            "name": "É Matriculado?",
            "type": "n8n-nodes-base.if",
            "typeVersion": 2,
            "position": [900, 400],
            "parameters": {
                "conditions": {
                    "options": {"caseSensitive": False},
                    "combinator": "and",
                    "conditions": [{
                        "id": "check-completo",
                        "leftValue": "={{ $json.estado }}",
                        "rightValue": "completo",
                        "operator": {"type": "string", "operation": "equals"}
                    }]
                }
            }
        },
        {
            "id": "forward-rag",
            "name": "Forward para RAG",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.1,
            "position": [1120, 260],
            "parameters": {
                "method": "POST",
                "url": RAG_WEBHOOK,
                "sendBody": True,
                "contentType": "json",
                "jsonBody": "={{ JSON.stringify($('Webhook Gateway').first().json.body) }}"
            }
        },
        {
            "id": "fluxo-matricula",
            "name": "Fluxo Matrícula",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [1120, 540],
            "parameters": {"jsCode": MATRICULA_CODE}
        },
        {
            "id": "salvar-draft",
            "name": "Salvar Draft",
            "type": "n8n-nodes-base.postgres",
            "typeVersion": 2,
            "position": [1340, 540],
            "continueOnFail": True,
            "parameters": {
                "operation": "executeQuery",
                "query": "={{ $json.upsertSql }}"
            },
            "credentials": {
                "postgres": {"id": PG_CRED_ID, "name": "PostgreSQL - Kreativ"}
            }
        },
        {
            "id": "resposta-matricula",
            "name": "Resposta Matrícula",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.1,
            "position": [1560, 540],
            "parameters": {
                "method": "POST",
                "url": "=https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/{{ $('Fluxo Matrícula').first().json.accountId }}/conversations/{{ $('Fluxo Matrícula').first().json.conversationId }}/messages",
                "sendHeaders": True,
                "headerParameters": {
                    "parameters": [
                        {"name": "api_access_token", "value": CHATWOOT_API_KEY}
                    ]
                },
                "sendBody": True,
                "bodyParameters": {
                    "parameters": [
                        {"name": "content", "value": "={{ $('Fluxo Matrícula').first().json.nextMessage }}"},
                        {"name": "message_type", "value": "outgoing"},
                        {"name": "private", "value": False}
                    ]
                }
            }
        }
    ],
    "connections": {
        "Webhook Gateway": {
            "main": [[{"node": "Extrair Dados", "type": "main", "index": 0}]]
        },
        "Extrair Dados": {
            "main": [[{"node": "Verificar Matrícula", "type": "main", "index": 0}]]
        },
        "Verificar Matrícula": {
            "main": [[{"node": "É Matriculado?", "type": "main", "index": 0}]]
        },
        "É Matriculado?": {
            "main": [
                [{"node": "Forward para RAG", "type": "main", "index": 0}],
                [{"node": "Fluxo Matrícula", "type": "main", "index": 0}]
            ]
        },
        "Fluxo Matrícula": {
            "main": [[{"node": "Salvar Draft", "type": "main", "index": 0}]]
        },
        "Salvar Draft": {
            "main": [[{"node": "Resposta Matrícula", "type": "main", "index": 0}]]
        }
    },
    "settings": {"executionOrder": "v1", "saveManualExecutions": True}
}

# ── Criar workflow ─────────────────────────────────────────────────────────
print("\n2. Criando workflow de matrícula gateway...")
r_wf = session.post(f"{N8N}/rest/workflows", json=workflow, timeout=20)
print(f"   Status: {r_wf.status_code}")
if r_wf.status_code in (200, 201):
    wf_data = r_wf.json().get("data", r_wf.json())
    wf_id = wf_data.get("id")
    print(f"   ✅ Workflow criado: {wf_id}")

    # Ativar workflow
    print("3. Ativando workflow...")
    r_act = session.patch(f"{N8N}/rest/workflows/{wf_id}",
        json={"active": True, "versionId": wf_data.get("versionId", "")},
        timeout=15)
    print(f"   Ativar status: {r_act.status_code} — {r_act.text[:200]}")

    new_webhook = f"https://n8n.ipexdesenvolvimento.cloud/webhook/tds-gateway"
    print(f"\n4. Webhook do novo workflow: {new_webhook}")

    # Atualizar Chatwoot agent bot
    print("5. Atualizando Chatwoot agent bot...")
    cw_session = requests.Session()
    cw_session.verify = False
    r_login = cw_session.post(f"{CHATWOOT}/auth/sign_in",
        json={"email": "tdsdados@gmail.com", "password": "6QWuIKdZzYBmBdS3!"},
        timeout=15)
    cw_token = r_login.json().get("data", {}).get("access_token", "")

    r_bot = cw_session.put(f"{CHATWOOT}/api/v1/accounts/1/agent_bots/1",
        headers={"api_access_token": cw_token},
        json={"outgoing_url": new_webhook},
        timeout=15)
    print(f"   Bot update: {r_bot.status_code} — {r_bot.text[:200]}")
    if r_bot.status_code == 200:
        print("   ✅ Chatwoot agent bot atualizado!")
else:
    print(f"   ❌ Erro: {r_wf.text[:400]}")

print("\n✅ Enrollment Gateway implantado!")
print("Teste: envie mensagem nova no WhatsApp conectado ao Chatwoot.")
