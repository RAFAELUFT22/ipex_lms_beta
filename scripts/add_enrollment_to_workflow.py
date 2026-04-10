"""
add_enrollment_to_workflow.py
1. Cria tabela enrollment_drafts no PostgreSQL
2. Adiciona nós de matrícula ao workflow RAG existente (XYcnRlPZSlfGXOWb)
   sem quebrar os nós existentes.
"""
import requests, urllib3, json, copy
urllib3.disable_warnings()

N8N = "https://n8n.ipexdesenvolvimento.cloud"
WF_ID = "XYcnRlPZSlfGXOWb"
PG_CRED_ID = "dxU0dZ2Fe1yaJhGg"

# ── Login ──────────────────────────────────────────────────────────────────
session = requests.Session()
session.verify = False
r = session.post(f"{N8N}/rest/login",
    json={"emailOrLdapLoginId": "tdsdados@gmail.com", "password": "Admin@TDS2024"},
    timeout=15)
assert r.status_code == 200, f"Login falhou: {r.text}"
print("✅ Login n8n OK")

# ── 1. Criar tabela via workflow temporário ────────────────────────────────
CREATE_SQL = """
CREATE TABLE IF NOT EXISTS enrollment_drafts (
    id              SERIAL PRIMARY KEY,
    phone           VARCHAR(20) UNIQUE NOT NULL,
    tenant_id       VARCHAR(50) DEFAULT 'tds_001',
    nome            VARCHAR(255),
    cpf             VARCHAR(14),
    municipio       VARCHAR(100),
    renda_familiar  VARCHAR(80),
    curso_escolhido VARCHAR(200),
    workspace_slug  VARCHAR(100),
    estado          VARCHAR(30) DEFAULT 'novo',
    started_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_enrollment_phone ON enrollment_drafts(phone);
"""

temp_wf = {
    "name": "TDS — Create Enrollment Table (run-once)",
    "active": False,
    "nodes": [
        {
            "id": "setup-trigger",
            "name": "Execute Manually",
            "type": "n8n-nodes-base.manualTrigger",
            "typeVersion": 1,
            "position": [240, 300],
            "parameters": {}
        },
        {
            "id": "create-table",
            "name": "Create Enrollment Table",
            "type": "n8n-nodes-base.postgres",
            "typeVersion": 2,
            "position": [460, 300],
            "parameters": {
                "operation": "executeQuery",
                "query": CREATE_SQL
            },
            "credentials": {
                "postgres": {"id": PG_CRED_ID, "name": "PostgreSQL - Kreativ"}
            }
        }
    ],
    "connections": {
        "Execute Manually": {
            "main": [[{"node": "Create Enrollment Table", "type": "main", "index": 0}]]
        }
    },
    "settings": {"saveManualExecutions": False}
}

r_create = session.post(f"{N8N}/rest/workflows", json=temp_wf, timeout=15)
if r_create.status_code in (200, 201):
    temp_id = r_create.json().get("data", {}).get("id", r_create.json().get("id"))
    print(f"✅ Workflow temporário criado: {temp_id}")
    # Executar
    r_exec = session.post(f"{N8N}/rest/workflows/{temp_id}/run", json={}, timeout=30)
    print(f"   Execução: {r_exec.status_code} — {r_exec.text[:200]}")
else:
    print(f"⚠️  Workflow temporário: {r_create.status_code} — {r_create.text[:200]}")

# ── 2. Buscar workflow existente ───────────────────────────────────────────
r_wf = session.get(f"{N8N}/rest/workflows/{WF_ID}", timeout=15)
wf = r_wf.json().get("data", r_wf.json())
nodes = wf.get("nodes", [])
connections = wf.get("connections", {})
print(f"\n✅ Workflow '{wf['name']}' carregado ({len(nodes)} nós)")

# Verificar se nós já foram adicionados
if any(n.get("name") == "Verificar Matrícula" for n in nodes):
    print("⚠️  Nós de matrícula já existem no workflow. Abortando para evitar duplicata.")
    exit(0)

# ── 3. Definir novos nós ───────────────────────────────────────────────────
ENROLLMENT_STATE_CODE = r"""
const extrairNode = $('Extrair Dados Chatwoot').first().json;
const { sessionId, conversationId, accountId, messageText, contactName } = extrairNode;

// Pegar draft do Postgres (nó anterior)
let draft = {};
try {
  const pgData = $('Verificar Matrícula').first().json;
  if (pgData && pgData.phone) draft = pgData;
} catch(e) {}

const currentState = draft.estado || 'novo';
const phone = sessionId || '';

const CURSOS = [
  { nome: 'Agricultura Sustentável — Sistemas Agroflorestais', slug: 'tds-agricultura-sustentavel' },
  { nome: 'Audiovisual e Produção de Conteúdo Digital', slug: 'tds-audiovisual-e-conteudo' },
  { nome: 'Finanças e Empreendedorismo', slug: 'tds-financas-e-empreendedorismo' },
  { nome: 'Educação Financeira para a Melhor Idade', slug: 'tds-educacao-financeira-terceira-idade' },
  { nome: 'Associativismo e Cooperativismo', slug: 'tds-associativismo-e-cooperativismo' },
  { nome: 'IA no meu Bolso — Inteligência Artificial para o Dia a Dia', slug: 'tds-ia-no-meu-bolso' },
  { nome: 'SIM — Serviço de Inspeção Municipal para Pequenos Produtores', slug: 'tds-sim' }
];

let nextMessage = '';
let nextState = currentState;
let updates = {};
let isComplete = false;

const txt = (messageText || '').trim();

if (currentState === 'novo') {
  nextState = 'aguarda_nome';
  const primeiroNome = (contactName || '').split(' ')[0];
  const saudacao = primeiroNome ? `Olá, ${primeiroNome}! 👋` : 'Olá! 👋';
  nextMessage = `${saudacao}\n\nBem-vindo(a) ao *Programa TDS* — Transformação Digital para Inclusão Social! 🌱\n\nOfertamos cursos gratuitos com certificado, direto no seu WhatsApp, no seu ritmo.\n\nPra garantir sua vaga, preciso de algumas informações rápidas. Pode me dizer seu *nome completo*?`;

} else if (currentState === 'aguarda_nome') {
  if (txt.length >= 3 && txt.includes(' ')) {
    updates.nome = txt;
    nextState = 'aguarda_cpf';
    const primeiro = txt.split(' ')[0];
    nextMessage = `Prazer, ${primeiro}! 😊\n\nPreciso do seu *CPF* (somente os números, 11 dígitos).\n\n💡 Ele é necessário para emitir o certificado pelo IPEX. Seus dados ficam protegidos.`;
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
    nextMessage = `O CPF precisa ter 11 dígitos. Por favor, tente novamente (somente números):`;
  }

} else if (currentState === 'aguarda_municipio') {
  if (txt.length >= 2) {
    updates.municipio = txt;
    nextState = 'aguarda_renda';
    nextMessage = `📍 *${txt}* — anotado!\n\nA última pergunta sobre seu perfil:\n\nQual é a *renda mensal da sua família*? (A FAPTO — entidade que financia o programa — precisa dessa info. Não afeta sua matrícula!)\n\n1️⃣ Até R$ 218\n2️⃣ De R$ 218 a R$ 660\n3️⃣ De R$ 660 a R$ 2.640\n4️⃣ Acima de R$ 2.640\n5️⃣ Prefiro não informar\n\nDigite o número:`;
  } else {
    nextMessage = `Por favor, informe o nome do *município* onde você mora:`;
  }

} else if (currentState === 'aguarda_renda') {
  const rendaMap = { '1':'Até R$ 218 (extrema pobreza)', '2':'De R$ 218 a R$ 660 (pobreza)', '3':'De R$ 660 a R$ 2.640 (baixa renda)', '4':'Acima de R$ 2.640', '5':'Prefiro não informar' };
  const renda = rendaMap[txt] || txt;
  updates.renda_familiar = renda;
  nextState = 'aguarda_curso';
  const menu = CURSOS.map((c, i) => `${i+1}️⃣ ${c.nome}`).join('\n');
  nextMessage = `📚 Agora a melhor parte — escolha seu *curso*!\n\n${menu}\n\nDigite o número:`;

} else if (currentState === 'aguarda_curso') {
  const idx = parseInt(txt) - 1;
  if (idx >= 0 && idx < CURSOS.length) {
    const curso = CURSOS[idx];
    updates.curso_escolhido = curso.nome;
    updates.workspace_slug = curso.slug;
    updates.estado = 'completo';
    nextState = 'completo';
    isComplete = true;
    nextMessage = `🎉 *Matrícula confirmada!*\n\n📚 Curso: *${curso.nome}*\n\nSeu tutor de IA já está pronto para te acompanhar! Pode perguntar qualquer coisa sobre o curso agora mesmo.\n\nDica: digite *quiz* quando quiser testar seus conhecimentos e avançar para o certificado! 🏆`;
  } else {
    nextMessage = `Por favor, digite um número de 1 a ${CURSOS.length}:`;
  }
}

// Montar SQL de upsert
let upsertSql = '';
const allUpdates = { ...updates, estado: nextState, updated_at: 'NOW()' };
const setClause = Object.entries(allUpdates)
  .filter(([k]) => k !== 'updated_at')
  .map(([k, v]) => `${k} = '${String(v).replace(/'/g,"''")}'`)
  .join(', ');
const setClauseWithTs = setClause + ", updated_at = NOW()";

upsertSql = `INSERT INTO enrollment_drafts (phone, estado) VALUES ('${phone}', '${nextState}') ON CONFLICT (phone) DO UPDATE SET ${setClauseWithTs}`;

return [{ json: {
  nextMessage,
  nextState,
  upsertSql,
  isComplete,
  conversationId,
  accountId,
  phone
}}];
"""

new_nodes = [
    {
        "id": "verificar-matricula",
        "name": "Verificar Matrícula",
        "type": "n8n-nodes-base.postgres",
        "typeVersion": 2,
        "position": [900, 500],
        "parameters": {
            "operation": "executeQuery",
            "query": "SELECT * FROM enrollment_drafts WHERE phone = '{{ $json.sessionId }}' LIMIT 1"
        },
        "credentials": {
            "postgres": {"id": PG_CRED_ID, "name": "PostgreSQL - Kreativ"}
        },
        "continueOnFail": True
    },
    {
        "id": "e-matriculado",
        "name": "É Matriculado?",
        "type": "n8n-nodes-base.if",
        "typeVersion": 2,
        "position": [1120, 500],
        "parameters": {
            "conditions": {
                "options": {"caseSensitive": False},
                "combinator": "and",
                "conditions": [{
                    "id": "cond-enrolled",
                    "leftValue": "={{ $('Verificar Matrícula').first().json.estado }}",
                    "rightValue": "completo",
                    "operator": {"type": "string", "operation": "equals"}
                }]
            }
        }
    },
    {
        "id": "fluxo-matricula",
        "name": "Fluxo Matrícula",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [1340, 680],
        "parameters": {
            "jsCode": ENROLLMENT_STATE_CODE
        }
    },
    {
        "id": "salvar-draft",
        "name": "Salvar Draft",
        "type": "n8n-nodes-base.postgres",
        "typeVersion": 2,
        "position": [1560, 680],
        "parameters": {
            "operation": "executeQuery",
            "query": "={{ $json.upsertSql }}"
        },
        "credentials": {
            "postgres": {"id": PG_CRED_ID, "name": "PostgreSQL - Kreativ"}
        },
        "continueOnFail": True
    },
    {
        "id": "resposta-matricula",
        "name": "Resposta Matrícula",
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.1,
        "position": [1780, 680],
        "parameters": {
            "method": "POST",
            "url": "=https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/{{ $('Fluxo Matrícula').first().json.accountId }}/conversations/{{ $('Fluxo Matrícula').first().json.conversationId }}/messages",
            "authentication": "genericCredentialType",
            "genericAuthType": "httpHeaderAuth",
            "sendHeaders": True,
            "headerParameters": {
                "parameters": [
                    {"name": "api_access_token", "value": "w8BYLTQc1s5VMowjQw433rGyC"}
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
]

# ── 4. Modificar conexões ──────────────────────────────────────────────────
# Intercalar novos nós entre Extrair Dados e Roteador
new_connections = copy.deepcopy(connections)

# Extrair Dados → Verificar Matrícula (era: Roteador)
new_connections["Extrair Dados Chatwoot"] = {
    "main": [[{"node": "Verificar Matrícula", "type": "main", "index": 0}]]
}
# Verificar Matrícula → É Matriculado?
new_connections["Verificar Matrícula"] = {
    "main": [[{"node": "É Matriculado?", "type": "main", "index": 0}]]
}
# É Matriculado? true(0) → Roteador | false(1) → Fluxo Matrícula
new_connections["É Matriculado?"] = {
    "main": [
        [{"node": "Roteador de Mensagem", "type": "main", "index": 0}],  # true
        [{"node": "Fluxo Matrícula", "type": "main", "index": 0}]        # false
    ]
}
# Fluxo Matrícula → Salvar Draft → Resposta Matrícula
new_connections["Fluxo Matrícula"] = {
    "main": [[{"node": "Salvar Draft", "type": "main", "index": 0}]]
}
new_connections["Salvar Draft"] = {
    "main": [[{"node": "Resposta Matrícula", "type": "main", "index": 0}]]
}

# ── 5. Montar payload de update ────────────────────────────────────────────
updated_nodes = nodes + new_nodes
updated_wf = {
    "name": wf["name"],
    "active": wf.get("active", True),
    "nodes": updated_nodes,
    "connections": new_connections,
    "settings": wf.get("settings", {}),
    "staticData": wf.get("staticData"),
    "tags": wf.get("tags", [])
}

r_update = session.put(f"{N8N}/rest/workflows/{WF_ID}",
    json=updated_wf, timeout=30)
print(f"\nUpdate workflow: {r_update.status_code}")
if r_update.status_code == 200:
    print("✅ Workflow atualizado com nós de matrícula!")
    print(f"   Total de nós agora: {len(updated_nodes)}")
else:
    print(f"❌ Erro: {r_update.text[:500]}")
