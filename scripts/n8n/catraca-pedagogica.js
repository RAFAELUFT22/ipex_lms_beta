/**
 * TDS — Catraca Pedagogica
 *
 * Sub-workflow que entrega conteudo estruturado (leitura + MCQ) via WhatsApp
 * para todos os 7 cursos TDS, ativado por keywords /audiovisual, /agricultura, etc.
 *
 * Workflow ID: eCB2vMHb69W3Qgpp
 * Created: 2026-04-10
 *
 * States: inativo > aguardando_leitura > aguardando_mcq > certificado_emitido | aguardando_confirmacao_troca
 * Input: { phone, keyword, message, conversation_id }
 *
 * IMPORTANT: After updating this workflow in N8N, always deactivate + reactivate
 * to clear the in-memory cache.
 *
 * Credentials to configure manually in N8N:
 * - "Frappe Header Auth" (httpHeaderAuth): Authorization = token 056681de29fce7a:7a0dd3d5f006a3e
 * - "Chatwoot Header Auth" (httpHeaderAuth): api_access_token = w8BYLTQc1s5VMowjQw433rGy
 * - "AnythingLLM Bearer" (httpBearerAuth): Bearer W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0
 */

import { workflow, node, trigger, sticky, ifElse, switchCase, expr } from '@n8n/workflow-sdk';

// ==================== TRIGGER ====================
const subWorkflowTrigger = trigger({
  type: 'n8n-nodes-base.executeWorkflowTrigger',
  version: 1.1,
  config: {
    name: 'Catraca Trigger',
    parameters: {
      inputSource: 'jsonExample',
      jsonExample: '{ "phone": "5563999999999", "keyword": "/audiovisual", "message": "li", "conversation_id": "123" }'
    },
    position: [240, 600]
  },
  output: [{ phone: '5563999999999', keyword: '/audiovisual', message: 'li', conversation_id: '123' }]
});

// ==================== EXTRACT INPUTS + CURSOS JSON ====================
const extractInputs = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'Extract Inputs + Cursos',
    parameters: {
      mode: 'manual',
      assignments: {
        assignments: [
          { id: 'a1', name: 'phone', value: expr('{{ $json.phone }}'), type: 'string' },
          { id: 'a2', name: 'keyword', value: expr('{{ $json.keyword.replace("/", "") }}'), type: 'string' },
          { id: 'a3', name: 'message', value: expr('{{ $json.message.trim().toLowerCase() }}'), type: 'string' },
          { id: 'a4', name: 'conversation_id', value: expr('{{ $json.conversation_id }}'), type: 'string' },
          { id: 'a5', name: 'cursos', value: expr('{{ JSON.parse(\'{"audiovisual":{"nome":"Audiovisual e Produção de Conteúdo Digital","workspace_slug":"tds-audiovisual-e-conteudo","certificate_slug":"audiovisual-e-produ-o-de-conte-do-digital","modulos":[]},"agricultura":{"nome":"Agricultura Sustentável — SAFs","workspace_slug":"tds-agricultura-sustentavel","certificate_slug":"agricultura-sustent-vel-sistemas-agroflorestais","modulos":[]},"financas":{"nome":"Finanças e Empreendedorismo","workspace_slug":"tds-financas-e-empreendedorismo","certificate_slug":"finan-as-e-empreendedorismo","modulos":[]},"educacao":{"nome":"Educação Financeira Melhor Idade","workspace_slug":"tds-educacao-financeira-terceira-idade","certificate_slug":"educa-o-financeira-para-a-melhor-idade","modulos":[]},"associa":{"nome":"Associativismo e Cooperativismo","workspace_slug":"tds-associativismo-e-cooperativismo","certificate_slug":"associativismo-e-cooperativismo-3","modulos":[]},"ia":{"nome":"IA no meu Bolso","workspace_slug":"tds-ia-no-meu-bolso","certificate_slug":"ia-no-meu-bolso-intelig-ncia-artificial-para-o-dia-a-dia","modulos":[]},"sim":{"nome":"SIM — Serviço de Inspeção Municipal","workspace_slug":"tds-sim","certificate_slug":"sim-servi-o-de-inspe-o-municipal-para-pequenos-produtores","modulos":[]}}\') }}'), type: 'object' }
        ]
      }
    },
    position: [500, 600]
  },
  output: [{
    phone: '5563999999999',
    keyword: 'audiovisual',
    message: 'li',
    conversation_id: '123',
    cursos: {
      audiovisual: { nome: 'Audiovisual e Produção de Conteúdo Digital', workspace_slug: 'tds-audiovisual-e-conteudo', modulos: [] },
      agricultura: { nome: 'Agricultura Sustentável — SAFs', workspace_slug: 'tds-agricultura-sustentavel', modulos: [] }
    }
  }]
});

// ==================== FRAPPE LOOKUP ====================
const lookupAluno = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Frappe GET TDS Aluno',
    parameters: {
      method: 'GET',
      url: expr('"https://lms.ipexdesenvolvimento.cloud/api/resource/TDS%20Aluno?filters=[[%22whatsapp%22,%22=%22,%22" + {{ $json.phone }} + "%22]]&fields=[%22name%22,%22full_name%22,%22whatsapp%22,%22email%22,%22estado_catraca%22,%22modulo_atual%22,%22secao_atual%22,%22respostas_mcq%22,%22modulos_concluidos%22,%22curso_ativo%22,%22keyword_pendente%22]"'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendHeaders: false,
      sendBody: false,
      sendQuery: false
    },
    credentials: { httpHeaderAuth: { id: 'frappe-header-auth', name: 'Frappe Header Auth' } },
    position: [760, 600]
  },
  output: [{ data: [{ name: 'TDS-ALU-00001', full_name: 'Maria Silva', whatsapp: '5563999999999', email: 'maria@test.com', estado_catraca: 'inativo', modulo_atual: 0, secao_atual: 0, respostas_mcq: '[]', modulos_concluidos: '[]', curso_ativo: '', keyword_pendente: '' }] }]
});

// ==================== IF: ALUNO FOUND? ====================
const ifAlunoFound = ifElse({
  version: 2.3,
  config: {
    name: 'Aluno encontrado?',
    parameters: {
      conditions: {
        conditions: [
          { leftValue: expr('{{ $json.data.length }}'), operator: { type: 'number', operation: 'gt' }, rightValue: 0 }
        ]
      }
    },
    position: [1020, 600]
  }
});

// ==================== NOT FOUND BRANCH ====================
const msgOrientacao = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'Msg Orientacao',
    parameters: {
      mode: 'manual',
      includeOtherFields: true,
      assignments: {
        assignments: [
          { id: 'b1', name: 'reply_text', value: expr('"Olá! 👋 Não encontrei seu cadastro no sistema TDS.\\n\\nPara se matricular, envie *oi* ou *quero me inscrever* e vamos iniciar sua pré-matrícula. Depois de concluí-la, volte aqui e envie o comando do curso desejado (ex: /audiovisual)."'), type: 'string' }
        ]
      }
    },
    position: [1280, 800]
  },
  output: [{ reply_text: 'Olá! ...', conversation_id: '123' }]
});

const chatwootSendOrientacao = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Chatwoot Orientacao',
    parameters: {
      method: 'POST',
      url: expr('"https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/conversations/" + {{ $("Extract Inputs + Cursos").item.json.conversation_id }} + "/messages"'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendHeaders: true,
      specifyHeaders: 'keypair',
      headerParameters: {
        parameters: [
          { name: 'Content-Type', value: 'application/json' }
        ]
      },
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('{{ JSON.stringify({ "content": $json.reply_text, "message_type": "outgoing" }) }}')
    },
    credentials: { httpHeaderAuth: { id: 'chatwoot-header-auth', name: 'Chatwoot Header Auth' } },
    position: [1540, 800]
  },
  output: [{ id: 1 }]
});

// ==================== FOUND BRANCH: EXTRACT ALUNO ====================
const extractAluno = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'Extract Aluno Fields',
    parameters: {
      mode: 'manual',
      includeOtherFields: true,
      include: 'selected',
      includeFields: '',
      assignments: {
        assignments: [
          { id: 'c1', name: 'aluno_name', value: expr('{{ $json.data[0].name }}'), type: 'string' },
          { id: 'c2', name: 'aluno_full_name', value: expr('{{ $json.data[0].full_name }}'), type: 'string' },
          { id: 'c3', name: 'aluno_email', value: expr('{{ $json.data[0].email }}'), type: 'string' },
          { id: 'c4', name: 'estado_catraca', value: expr('{{ $json.data[0].estado_catraca || "inativo" }}'), type: 'string' },
          { id: 'c5', name: 'modulo_atual', value: expr('{{ $json.data[0].modulo_atual || 0 }}'), type: 'number' },
          { id: 'c6', name: 'secao_atual', value: expr('{{ $json.data[0].secao_atual || 0 }}'), type: 'number' },
          { id: 'c7', name: 'respostas_mcq', value: expr('{{ $json.data[0].respostas_mcq || "[]" }}'), type: 'string' },
          { id: 'c8', name: 'modulos_concluidos', value: expr('{{ $json.data[0].modulos_concluidos || "[]" }}'), type: 'string' },
          { id: 'c9', name: 'curso_ativo', value: expr('{{ $json.data[0].curso_ativo || "" }}'), type: 'string' },
          { id: 'c10', name: 'keyword', value: expr('{{ $("Extract Inputs + Cursos").item.json.keyword }}'), type: 'string' },
          { id: 'c11', name: 'message', value: expr('{{ $("Extract Inputs + Cursos").item.json.message }}'), type: 'string' },
          { id: 'c12', name: 'conversation_id', value: expr('{{ $("Extract Inputs + Cursos").item.json.conversation_id }}'), type: 'string' },
          { id: 'c13', name: 'phone', value: expr('{{ $("Extract Inputs + Cursos").item.json.phone }}'), type: 'string' },
          { id: 'c14', name: 'cursos', value: expr('{{ $("Extract Inputs + Cursos").item.json.cursos }}'), type: 'object' },
          { id: 'c15', name: 'curso_obj', value: expr('{{ $("Extract Inputs + Cursos").item.json.cursos[$("Extract Inputs + Cursos").item.json.keyword] || {} }}'), type: 'object' },
          { id: 'c16', name: 'keyword_pendente', value: expr('{{ $json.data[0].keyword_pendente || "" }}'), type: 'string' }
        ]
      }
    },
    position: [1280, 500]
  },
  output: [{
    aluno_name: 'TDS-ALU-00001', aluno_full_name: 'Maria Silva', aluno_email: 'maria@test.com',
    estado_catraca: 'inativo', modulo_atual: 0, secao_atual: 0, respostas_mcq: '[]', modulos_concluidos: '[]',
    curso_ativo: '', keyword: 'audiovisual', message: 'li', conversation_id: '123', phone: '5563999999999',
    cursos: {}, curso_obj: { nome: 'Audiovisual e Produção de Conteúdo Digital', workspace_slug: 'tds-audiovisual-e-conteudo', modulos: [] },
    keyword_pendente: ''
  }]
});

// ==================== IF: DIFFERENT COURSE IN PROGRESS? ====================
const ifCursoDiferente = ifElse({
  version: 2.3,
  config: {
    name: 'Curso diferente em andamento?',
    parameters: {
      conditions: {
        conditions: [
          { leftValue: expr('{{ $json.curso_ativo }}'), operator: { type: 'string', operation: 'isNotEmpty' }, rightValue: '' },
          { leftValue: expr('{{ $json.curso_ativo }}'), operator: { type: 'string', operation: 'notEquals' }, rightValue: expr('{{ $json.keyword }}') },
          { leftValue: expr('{{ $json.estado_catraca }}'), operator: { type: 'string', operation: 'notEquals' }, rightValue: 'inativo' },
          { leftValue: expr('{{ $json.estado_catraca }}'), operator: { type: 'string', operation: 'notEquals' }, rightValue: 'certificado_emitido' }
        ]
      }
    },
    position: [1540, 500]
  }
});

// ==================== COURSE SWITCH: send "Deseja trocar?" and set pending state ====================
const msgTrocaCurso = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'Msg Troca Curso',
    parameters: {
      mode: 'manual',
      includeOtherFields: true,
      assignments: {
        assignments: [
          { id: 'd1', name: 'reply_text', value: expr('"⚠️ Você já está cursando *" + {{ $json.cursos[$json.curso_ativo] ? $json.cursos[$json.curso_ativo].nome : $json.curso_ativo }} + "*.\\n\\nDeseja trocar para *" + {{ $json.curso_obj.nome || $json.keyword }} + "*? Isso vai zerar seu progresso no curso atual.\\n\\nResponda *sim* para confirmar ou *não* para cancelar."'), type: 'string' }
        ]
      }
    },
    position: [1800, 300]
  },
  output: [{ reply_text: 'Voce ja esta cursando...', conversation_id: '123' }]
});

const patchAlunoPendingSwitch = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'PATCH Aluno Aguardando Troca',
    parameters: {
      method: 'PUT',
      url: expr('"https://lms.ipexdesenvolvimento.cloud/api/resource/TDS%20Aluno/" + {{ $json.aluno_name }}'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendHeaders: true,
      specifyHeaders: 'keypair',
      headerParameters: { parameters: [{ name: 'Content-Type', value: 'application/json' }] },
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('{{ JSON.stringify({ "estado_catraca": "aguardando_confirmacao_troca", "keyword_pendente": $json.keyword, "data_ultimo_acesso_whatsapp": $now.toFormat("yyyy-MM-dd HH:mm:ss") }) }}')
    },
    credentials: { httpHeaderAuth: { id: 'frappe-header-auth', name: 'Frappe Header Auth' } },
    position: [2060, 300]
  },
  output: [{ data: { name: 'TDS-ALU-00001' } }]
});

const chatwootSendTroca = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Chatwoot Troca Curso',
    parameters: {
      method: 'POST',
      url: expr('"https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/conversations/" + {{ $("Extract Aluno Fields").item.json.conversation_id }} + "/messages"'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendHeaders: true,
      specifyHeaders: 'keypair',
      headerParameters: { parameters: [{ name: 'Content-Type', value: 'application/json' }] },
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('{{ JSON.stringify({ "content": $("Msg Troca Curso").item.json.reply_text, "message_type": "outgoing" }) }}')
    },
    credentials: { httpHeaderAuth: { id: 'chatwoot-header-auth', name: 'Chatwoot Header Auth' } },
    position: [2320, 300]
  },
  output: [{ id: 2 }]
});

// ==================== AGUARDANDO CONFIRMACAO TROCA BRANCH ====================
const ifConfirmTroca = ifElse({
  version: 2.3,
  config: {
    name: 'Confirma troca?',
    parameters: {
      conditions: {
        conditions: [
          { leftValue: expr('{{ ["sim","s","1","ok","quero","trocar"].includes($json.message) }}'), operator: { type: 'boolean', operation: 'true' }, rightValue: '' }
        ]
      }
    },
    position: [2060, 1800]
  }
});

// --- CONFIRMED SWITCH: initialize new course using keyword_pendente ---
const setInitNewCourse = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'Inicializa Novo Curso',
    parameters: {
      mode: 'manual',
      includeOtherFields: true,
      assignments: {
        assignments: [
          { id: 'e1', name: 'new_estado', value: 'aguardando_leitura', type: 'string' },
          { id: 'e2', name: 'new_modulo', value: 1, type: 'number' },
          { id: 'e3', name: 'new_secao', value: 1, type: 'number' },
          { id: 'e4', name: 'new_curso_ativo', value: expr('{{ $json.keyword_pendente || $json.keyword }}'), type: 'string' },
          { id: 'e5', name: 'new_respostas', value: '[]', type: 'string' },
          { id: 'e6', name: 'new_modulos_concluidos', value: '[]', type: 'string' },
          { id: 'e7', name: 'new_curso_obj', value: expr('{{ $json.cursos[$json.keyword_pendente || $json.keyword] || {} }}'), type: 'object' }
        ]
      }
    },
    position: [2320, 1700]
  },
  output: [{ new_estado: 'aguardando_leitura', new_modulo: 1, new_secao: 1, new_curso_ativo: 'audiovisual', new_respostas: '[]', new_modulos_concluidos: '[]', aluno_name: 'TDS-ALU-00001', conversation_id: '123', new_curso_obj: {} }]
});

const patchAlunoNewCourse = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'PATCH Aluno Novo Curso',
    parameters: {
      method: 'PUT',
      url: expr('"https://lms.ipexdesenvolvimento.cloud/api/resource/TDS%20Aluno/" + {{ $json.aluno_name }}'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendHeaders: true,
      specifyHeaders: 'keypair',
      headerParameters: { parameters: [{ name: 'Content-Type', value: 'application/json' }] },
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('{{ JSON.stringify({ "estado_catraca": $json.new_estado, "modulo_atual": $json.new_modulo, "secao_atual": $json.new_secao, "curso_ativo": $json.new_curso_ativo, "respostas_mcq": $json.new_respostas, "modulos_concluidos": $json.new_modulos_concluidos, "keyword_pendente": "", "data_ultimo_acesso_whatsapp": $now.toFormat("yyyy-MM-dd HH:mm:ss") }) }}')
    },
    credentials: { httpHeaderAuth: { id: 'frappe-header-auth', name: 'Frappe Header Auth' } },
    position: [2580, 1700]
  },
  output: [{ data: { name: 'TDS-ALU-00001' } }]
});

// Issue 6: After course switch, check if modules exist and send first section content
const ifModulosExistNewCourse = ifElse({
  version: 2.3,
  config: {
    name: 'Modulos disponiveis novo curso?',
    parameters: {
      conditions: {
        conditions: [
          { leftValue: expr('{{ (($("Inicializa Novo Curso").item.json.new_curso_obj || {}).modulos || []).length }}'), operator: { type: 'number', operation: 'gt' }, rightValue: 0 }
        ]
      }
    },
    position: [2840, 1700]
  }
});

const chatwootNewCourseSection = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Chatwoot Secao 1 Novo Curso',
    parameters: {
      method: 'POST',
      url: expr('"https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/conversations/" + {{ $("Extract Aluno Fields").item.json.conversation_id }} + "/messages"'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendHeaders: true,
      specifyHeaders: 'keypair',
      headerParameters: { parameters: [{ name: 'Content-Type', value: 'application/json' }] },
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('"{ \\"content\\": \\"🔄 Curso trocado! Agora você está em *" + {{ $("Inicializa Novo Curso").item.json.new_curso_obj.nome || "novo curso" }} + "*.\\\\n\\\\nO conteúdo será enviado em partes. Após cada leitura, responda *LI* para avançar.\\\\n\\\\nVamos começar!\\", \\"message_type\\": \\"outgoing\\" }"')
    },
    credentials: { httpHeaderAuth: { id: 'chatwoot-header-auth', name: 'Chatwoot Header Auth' } },
    position: [3100, 1600]
  },
  output: [{ id: 3 }]
});

const chatwootNewCourseEmBreve = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Chatwoot Novo Curso Em Breve',
    parameters: {
      method: 'POST',
      url: expr('"https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/conversations/" + {{ $("Extract Aluno Fields").item.json.conversation_id }} + "/messages"'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendHeaders: true,
      specifyHeaders: 'keypair',
      headerParameters: { parameters: [{ name: 'Content-Type', value: 'application/json' }] },
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('"{ \\"content\\": \\"🔄 Curso trocado! Agora você está em *" + {{ $("Inicializa Novo Curso").item.json.new_curso_obj.nome || "novo curso" }} + "*.\\\\n\\\\nO conteúdo será disponibilizado em breve. Fique atento(a)! 📚\\", \\"message_type\\": \\"outgoing\\" }"')
    },
    credentials: { httpHeaderAuth: { id: 'chatwoot-header-auth', name: 'Chatwoot Header Auth' } },
    position: [3100, 1800]
  },
  output: [{ id: 15 }]
});

// --- NOT CONFIRMED (nao/cancel): revert to previous state ---
const patchAlunoCancelSwitch = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'PATCH Aluno Cancela Troca',
    parameters: {
      method: 'PUT',
      url: expr('"https://lms.ipexdesenvolvimento.cloud/api/resource/TDS%20Aluno/" + {{ $json.aluno_name }}'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendHeaders: true,
      specifyHeaders: 'keypair',
      headerParameters: { parameters: [{ name: 'Content-Type', value: 'application/json' }] },
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('{{ JSON.stringify({ "estado_catraca": "aguardando_leitura", "keyword_pendente": "", "data_ultimo_acesso_whatsapp": $now.toFormat("yyyy-MM-dd HH:mm:ss") }) }}')
    },
    credentials: { httpHeaderAuth: { id: 'frappe-header-auth', name: 'Frappe Header Auth' } },
    position: [2320, 1950]
  },
  output: [{ data: { name: 'TDS-ALU-00001' } }]
});

const chatwootCancelSwitch = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Chatwoot Cancela Troca',
    parameters: {
      method: 'POST',
      url: expr('"https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/conversations/" + {{ $("Extract Aluno Fields").item.json.conversation_id }} + "/messages"'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendHeaders: true,
      specifyHeaders: 'keypair',
      headerParameters: { parameters: [{ name: 'Content-Type', value: 'application/json' }] },
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('{{ JSON.stringify({ "content": "👍 Tudo bem! Você continua no curso atual. Pode seguir de onde parou.", "message_type": "outgoing" }) }}')
    },
    credentials: { httpHeaderAuth: { id: 'chatwoot-header-auth', name: 'Chatwoot Header Auth' } },
    position: [2580, 1950]
  },
  output: [{ id: 16 }]
});

// ==================== SAME COURSE / INACTIVE: STATE MACHINE ====================
const switchEstado = switchCase({
  version: 3.4,
  config: {
    name: 'Switch Estado Catraca',
    parameters: {
      mode: 'rules',
      rules: {
        values: [
          {
            conditions: {
              conditions: [{ leftValue: expr('{{ $json.estado_catraca }}'), operator: { type: 'string', operation: 'equals' }, rightValue: 'inativo' }]
            },
            renameOutput: true,
            outputKey: 'inativo'
          },
          {
            conditions: {
              conditions: [{ leftValue: expr('{{ $json.estado_catraca }}'), operator: { type: 'string', operation: 'equals' }, rightValue: 'aguardando_leitura' }]
            },
            renameOutput: true,
            outputKey: 'aguardando_leitura'
          },
          {
            conditions: {
              conditions: [{ leftValue: expr('{{ $json.estado_catraca }}'), operator: { type: 'string', operation: 'equals' }, rightValue: 'aguardando_mcq' }]
            },
            renameOutput: true,
            outputKey: 'aguardando_mcq'
          },
          {
            conditions: {
              conditions: [{ leftValue: expr('{{ $json.estado_catraca }}'), operator: { type: 'string', operation: 'equals' }, rightValue: 'certificado_emitido' }]
            },
            renameOutput: true,
            outputKey: 'certificado_emitido'
          },
          {
            conditions: {
              conditions: [{ leftValue: expr('{{ $json.estado_catraca }}'), operator: { type: 'string', operation: 'equals' }, rightValue: 'aguardando_confirmacao_troca' }]
            },
            renameOutput: true,
            outputKey: 'aguardando_confirmacao_troca'
          }
        ]
      },
      options: {
        fallbackOutput: 'extra',
        renameFallbackOutput: 'fallback'
      }
    },
    position: [1800, 600]
  }
});

// ==================== INATIVO BRANCH ====================
const ifModulosExist = ifElse({
  version: 2.3,
  config: {
    name: 'Modulos disponíveis?',
    parameters: {
      conditions: {
        conditions: [
          { leftValue: expr('{{ ($json.curso_obj.modulos || []).length }}'), operator: { type: 'number', operation: 'gt' }, rightValue: 0 }
        ]
      }
    },
    position: [2060, 600]
  }
});

// No modules -> "em breve"
const msgEmBreve = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'Msg Em Breve',
    parameters: {
      mode: 'manual',
      includeOtherFields: true,
      assignments: {
        assignments: [
          { id: 'f1', name: 'reply_text', value: expr('"Olá, " + {{ $json.aluno_full_name }} + "! 😊\\n\\nO curso *" + {{ $json.curso_obj.nome || $json.keyword }} + "* está sendo preparado e o conteúdo será disponibilizado em breve.\\n\\nAssim que estiver pronto, enviaremos a primeira lição diretamente aqui no WhatsApp. Fique atento(a)! 📚"'), type: 'string' }
        ]
      }
    },
    position: [2320, 700]
  },
  output: [{ reply_text: 'Ola Maria! O curso...', conversation_id: '123' }]
});

const chatwootEmBreve = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Chatwoot Em Breve',
    parameters: {
      method: 'POST',
      url: expr('"https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/conversations/" + {{ $json.conversation_id }} + "/messages"'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendHeaders: true,
      specifyHeaders: 'keypair',
      headerParameters: { parameters: [{ name: 'Content-Type', value: 'application/json' }] },
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('{{ JSON.stringify({ "content": $json.reply_text, "message_type": "outgoing" }) }}')
    },
    credentials: { httpHeaderAuth: { id: 'chatwoot-header-auth', name: 'Chatwoot Header Auth' } },
    position: [2580, 700]
  },
  output: [{ id: 4 }]
});

// Has modules -> initialize state
const setInitEstado = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'Inicializa Estado',
    parameters: {
      mode: 'manual',
      includeOtherFields: true,
      assignments: {
        assignments: [
          { id: 'g1', name: 'new_estado', value: 'aguardando_leitura', type: 'string' },
          { id: 'g2', name: 'new_modulo', value: 1, type: 'number' },
          { id: 'g3', name: 'new_secao', value: 1, type: 'number' },
          { id: 'g4', name: 'new_curso_ativo', value: expr('{{ $json.keyword }}'), type: 'string' }
        ]
      }
    },
    position: [2320, 500]
  },
  output: [{ new_estado: 'aguardando_leitura', new_modulo: 1, new_secao: 1, new_curso_ativo: 'audiovisual', aluno_name: 'TDS-ALU-00001', conversation_id: '123', curso_obj: {} }]
});

const patchAlunoInit = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'PATCH Aluno Inicializa',
    parameters: {
      method: 'PUT',
      url: expr('"https://lms.ipexdesenvolvimento.cloud/api/resource/TDS%20Aluno/" + {{ $json.aluno_name }}'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendHeaders: true,
      specifyHeaders: 'keypair',
      headerParameters: { parameters: [{ name: 'Content-Type', value: 'application/json' }] },
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('{{ JSON.stringify({ "estado_catraca": $json.new_estado, "modulo_atual": $json.new_modulo, "secao_atual": $json.new_secao, "curso_ativo": $json.new_curso_ativo, "respostas_mcq": "[]", "modulos_concluidos": $json.modulos_concluidos || "[]", "data_ultimo_acesso_whatsapp": $now.toFormat("yyyy-MM-dd HH:mm:ss") }) }}')
    },
    credentials: { httpHeaderAuth: { id: 'frappe-header-auth', name: 'Frappe Header Auth' } },
    position: [2580, 500]
  },
  output: [{ data: { name: 'TDS-ALU-00001' } }]
});

const chatwootSecao1Init = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Chatwoot Secao 1 Init',
    parameters: {
      method: 'POST',
      url: expr('"https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/conversations/" + {{ $("Extract Aluno Fields").item.json.conversation_id }} + "/messages"'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendHeaders: true,
      specifyHeaders: 'keypair',
      headerParameters: { parameters: [{ name: 'Content-Type', value: 'application/json' }] },
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('"{ \\"content\\": \\"🎓 Bem-vindo(a) ao curso *" + {{ $("Extract Aluno Fields").item.json.curso_obj.nome || "curso" }} + "*, " + {{ $("Extract Aluno Fields").item.json.aluno_full_name }} + "!\\\\n\\\\nO conteúdo será enviado em partes. Após cada leitura, responda *LI* para avançar.\\\\n\\\\nVamos começar! O conteúdo da primeira seção será enviado em breve.\\", \\"message_type\\": \\"outgoing\\" }"')
    },
    credentials: { httpHeaderAuth: { id: 'chatwoot-header-auth', name: 'Chatwoot Header Auth' } },
    position: [2840, 500]
  },
  output: [{ id: 5 }]
});

// ==================== AGUARDANDO LEITURA BRANCH ====================
const ifConfirmLeitura = ifElse({
  version: 2.3,
  config: {
    name: 'Msg é confirmacao leitura?',
    parameters: {
      conditions: {
        conditions: [
          { leftValue: expr('{{ ["li","ok","pronto","entendi","sim","certo","combinado","feito","lido","claro"].includes($json.message) }}'), operator: { type: 'boolean', operation: 'true' }, rightValue: '' }
        ]
      }
    },
    position: [2060, 900]
  }
});

// Not confirmed -> resend section
const chatwootReenviaSecao = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Chatwoot Reenvia Secao',
    parameters: {
      method: 'POST',
      url: expr('"https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/conversations/" + {{ $json.conversation_id }} + "/messages"'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendHeaders: true,
      specifyHeaders: 'keypair',
      headerParameters: { parameters: [{ name: 'Content-Type', value: 'application/json' }] },
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('{{ JSON.stringify({ "content": "📖 Quando terminar de ler o conteúdo acima, responda *LI* para avançar para a pergunta. 😊", "message_type": "outgoing" }) }}')
    },
    credentials: { httpHeaderAuth: { id: 'chatwoot-header-auth', name: 'Chatwoot Header Auth' } },
    position: [2320, 1000]
  },
  output: [{ id: 6 }]
});

// Confirmed -> advance to MCQ
const setAdvanceMCQ = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'Avanca para MCQ',
    parameters: {
      mode: 'manual',
      includeOtherFields: true,
      assignments: {
        assignments: [
          { id: 'h1', name: 'new_estado', value: 'aguardando_mcq', type: 'string' }
        ]
      }
    },
    position: [2320, 800]
  },
  output: [{ new_estado: 'aguardando_mcq', aluno_name: 'TDS-ALU-00001', conversation_id: '123', modulo_atual: 1, secao_atual: 1, curso_ativo: 'audiovisual', curso_obj: {} }]
});

const patchAlunoMCQ = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'PATCH Aluno MCQ',
    parameters: {
      method: 'PUT',
      url: expr('"https://lms.ipexdesenvolvimento.cloud/api/resource/TDS%20Aluno/" + {{ $json.aluno_name }}'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendHeaders: true,
      specifyHeaders: 'keypair',
      headerParameters: { parameters: [{ name: 'Content-Type', value: 'application/json' }] },
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('{{ JSON.stringify({ "estado_catraca": "aguardando_mcq", "modulo_atual": $json.modulo_atual, "secao_atual": $json.secao_atual, "curso_ativo": $json.curso_ativo, "data_ultimo_acesso_whatsapp": $now.toFormat("yyyy-MM-dd HH:mm:ss") }) }}')
    },
    credentials: { httpHeaderAuth: { id: 'frappe-header-auth', name: 'Frappe Header Auth' } },
    position: [2580, 800]
  },
  output: [{ data: { name: 'TDS-ALU-00001' } }]
});

const chatwootPergunta = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Chatwoot Pergunta MCQ',
    parameters: {
      method: 'POST',
      url: expr('"https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/conversations/" + {{ $("Extract Aluno Fields").item.json.conversation_id }} + "/messages"'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendHeaders: true,
      specifyHeaders: 'keypair',
      headerParameters: { parameters: [{ name: 'Content-Type', value: 'application/json' }] },
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('{{ JSON.stringify({ "content": "✅ Ótimo! Agora vamos à pergunta sobre o que você acabou de ler.\\n\\nAs perguntas serão enviadas assim que o conteúdo do módulo estiver disponível. Aguarde! 📝", "message_type": "outgoing" }) }}')
    },
    credentials: { httpHeaderAuth: { id: 'chatwoot-header-auth', name: 'Chatwoot Header Auth' } },
    position: [2840, 800]
  },
  output: [{ id: 7 }]
});

// ==================== AGUARDANDO MCQ BRANCH ====================
const ifMsgABCD = ifElse({
  version: 2.3,
  config: {
    name: 'Msg e A/B/C/D?',
    parameters: {
      conditions: {
        conditions: [
          { leftValue: expr('{{ ["a","b","c","d"].includes($json.message) }}'), operator: { type: 'boolean', operation: 'true' }, rightValue: '' }
        ]
      }
    },
    position: [2060, 1200]
  }
});

// Not A/B/C/D -> RAG query
const ragQuery = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'AnythingLLM RAG',
    parameters: {
      method: 'POST',
      url: expr('"https://rag.ipexdesenvolvimento.cloud/api/v1/workspace/" + {{ $json.curso_obj.workspace_slug || "tds" }} + "/chat"'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpBearerAuth',
      sendHeaders: true,
      specifyHeaders: 'keypair',
      headerParameters: { parameters: [{ name: 'Content-Type', value: 'application/json' }] },
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('{{ JSON.stringify({ "message": $("Extract Aluno Fields").item.json.message, "mode": "chat" }) }}')
    },
    credentials: { httpBearerAuth: { id: 'anythingllm-bearer', name: 'AnythingLLM Bearer' } },
    position: [2320, 1300]
  },
  output: [{ textResponse: 'A resposta correta seria a alternativa B...' }]
});

const chatwootRAG = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Chatwoot RAG Response',
    parameters: {
      method: 'POST',
      url: expr('"https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/conversations/" + {{ $("Extract Aluno Fields").item.json.conversation_id }} + "/messages"'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendHeaders: true,
      specifyHeaders: 'keypair',
      headerParameters: { parameters: [{ name: 'Content-Type', value: 'application/json' }] },
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('{{ JSON.stringify({ "content": ($json.textResponse || "Desculpe, não consegui processar sua dúvida.") + "\\n\\n📝 Lembre-se: para responder a pergunta, envie apenas a letra (*A*, *B*, *C* ou *D*).", "message_type": "outgoing" }) }}')
    },
    credentials: { httpHeaderAuth: { id: 'chatwoot-header-auth', name: 'Chatwoot Header Auth' } },
    position: [2580, 1300]
  },
  output: [{ id: 8 }]
});

// A/B/C/D answer -> Code node calculates next state
const codeCalcNextState = node({
  type: 'n8n-nodes-base.code',
  version: 2,
  config: {
    name: 'Calcula Proximo Estado',
    parameters: {
      mode: 'runOnceForAllItems',
      language: 'javaScript',
      jsCode: `
const items = $input.all();
const item = items[0];
const j = item.json;

const COURSE_SLUGS = {
  audiovisual: 'audiovisual-e-produ-o-de-conte-do-digital',
  agricultura: 'agricultura-sustent-vel-sistemas-agroflorestais',
  financas: 'finan-as-e-empreendedorismo',
  educacao: 'educa-o-financeira-para-a-melhor-idade',
  associa: 'associativismo-e-cooperativismo-3',
  ia: 'ia-no-meu-bolso-intelig-ncia-artificial-para-o-dia-a-dia',
  sim: 'sim-servi-o-de-inspe-o-municipal-para-pequenos-produtores'
};

const modulos = j.curso_obj?.modulos || [];
const modulo = j.modulo_atual || 1;
const secao = j.secao_atual || 1;
const resposta = j.message?.toUpperCase();
const mod = modulos[modulo - 1];
const sec = mod?.secoes?.[secao - 1];
const correta = sec?.correta || 'X';
const acertou = (resposta === correta);

let respostas = [];
try {
  const parsed = JSON.parse(j.respostas_mcq || '[]');
  respostas = Array.isArray(parsed) ? parsed : [];
} catch(e) { respostas = []; }
respostas.push({ modulo: modulo, secao: secao, resposta: resposta, correta: correta, acertou: acertou });

let modulosConcluidos = [];
try { modulosConcluidos = JSON.parse(j.modulos_concluidos || '[]'); } catch(e) { modulosConcluidos = []; }

let nextModulo = modulo;
let nextSecao = secao + 1;
let nextEstado = 'aguardando_leitura';
let doCertificate = false;
let replyText = '';

if (mod && nextSecao > mod.secoes.length) {
  modulosConcluidos.push(modulo);
  nextModulo = modulo + 1;
  nextSecao = 1;

  if (nextModulo > modulos.length) {
    nextEstado = 'certificado_emitido';
    doCertificate = true;
    replyText = acertou
      ? '✅ Resposta correta! 🎉\\n\\n🏆 *Parabéns! Você concluiu todos os módulos do curso!*\\nSeu certificado está sendo gerado...'
      : '❌ A resposta correta era *' + correta + '*.\\n\\n🏆 *Parabéns! Você concluiu todos os módulos do curso!*\\nSeu certificado está sendo gerado...';
  } else {
    replyText = acertou
      ? '✅ Resposta correta! Módulo ' + modulo + ' concluído! 🎉\\n\\nVamos ao próximo módulo. O conteúdo será enviado em breve.'
      : '❌ A resposta correta era *' + correta + '*. Módulo ' + modulo + ' concluído!\\n\\nVamos ao próximo módulo. O conteúdo será enviado em breve.';
  }
} else {
  replyText = acertou
    ? '✅ Resposta correta! Vamos à próxima seção. 📖'
    : '❌ A resposta correta era *' + correta + '*. Vamos à próxima seção. 📖';
}

const certificateCourseSlug = j.curso_obj?.certificate_slug || COURSE_SLUGS[j.curso_ativo] || COURSE_SLUGS[j.keyword] || '';

return [{
  json: {
    ...j,
    new_estado: nextEstado,
    new_modulo: nextModulo,
    new_secao: nextSecao,
    new_respostas: JSON.stringify(respostas),
    new_modulos_concluidos: JSON.stringify(modulosConcluidos),
    doCertificate: doCertificate,
    certificate_course_slug: certificateCourseSlug,
    reply_text: replyText,
    acertou: acertou
  }
}];
`
    },
    position: [2320, 1100]
  },
  output: [{
    new_estado: 'aguardando_leitura', new_modulo: 1, new_secao: 2, new_respostas: '[]',
    new_modulos_concluidos: '[]', doCertificate: false, reply_text: 'Resposta correta!',
    aluno_name: 'TDS-ALU-00001', conversation_id: '123', aluno_email: 'maria@test.com',
    keyword: 'audiovisual', curso_obj: {}
  }]
});

const patchAlunoAnswer = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'PATCH Aluno Resposta',
    parameters: {
      method: 'PUT',
      url: expr('"https://lms.ipexdesenvolvimento.cloud/api/resource/TDS%20Aluno/" + {{ $json.aluno_name }}'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendHeaders: true,
      specifyHeaders: 'keypair',
      headerParameters: { parameters: [{ name: 'Content-Type', value: 'application/json' }] },
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('{{ JSON.stringify({ "estado_catraca": $json.new_estado, "modulo_atual": $json.new_modulo, "secao_atual": $json.new_secao, "curso_ativo": $json.curso_ativo, "respostas_mcq": $json.new_respostas, "modulos_concluidos": $json.new_modulos_concluidos, "data_ultimo_acesso_whatsapp": $now.toFormat("yyyy-MM-dd HH:mm:ss") }) }}')
    },
    credentials: { httpHeaderAuth: { id: 'frappe-header-auth', name: 'Frappe Header Auth' } },
    position: [2580, 1100]
  },
  output: [{ data: { name: 'TDS-ALU-00001' } }]
});

// IF: doCertificate?
const ifDoCertificate = ifElse({
  version: 2.3,
  config: {
    name: 'Emitir certificado?',
    parameters: {
      conditions: {
        conditions: [
          { leftValue: expr('{{ $("Calcula Proximo Estado").item.json.doCertificate }}'), operator: { type: 'boolean', operation: 'true' }, rightValue: '' }
        ]
      }
    },
    position: [2840, 1100]
  }
});

// Certificate YES
const postCertificate = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'POST LMS Certificate',
    parameters: {
      method: 'POST',
      url: 'https://lms.ipexdesenvolvimento.cloud/api/resource/LMS%20Certificate',
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendHeaders: true,
      specifyHeaders: 'keypair',
      headerParameters: { parameters: [{ name: 'Content-Type', value: 'application/json' }] },
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('{{ JSON.stringify({ "member": $("Calcula Proximo Estado").item.json.aluno_email || ($("Calcula Proximo Estado").item.json.phone + "@tds.local"), "course": $("Calcula Proximo Estado").item.json.certificate_course_slug, "issue_date": $now.toFormat("yyyy-MM-dd") }) }}'),
      options: {
        response: { response: { neverError: true } }
      }
    },
    credentials: { httpHeaderAuth: { id: 'frappe-header-auth', name: 'Frappe Header Auth' } },
    position: [3100, 1000]
  },
  output: [{ data: { name: 'LMS-CERT-00001' } }]
});

const chatwootCertificado = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Chatwoot Certificado',
    parameters: {
      method: 'POST',
      url: expr('"https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/conversations/" + {{ $("Extract Aluno Fields").item.json.conversation_id }} + "/messages"'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendHeaders: true,
      specifyHeaders: 'keypair',
      headerParameters: { parameters: [{ name: 'Content-Type', value: 'application/json' }] },
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('{{ JSON.stringify({ "content": $("Calcula Proximo Estado").item.json.reply_text + "\\n\\n🎓 Certificado emitido! Acesse: https://lms.ipexdesenvolvimento.cloud/lms/certification/" + $("POST LMS Certificate").item.json.data.name, "message_type": "outgoing" }) }}')
    },
    credentials: { httpHeaderAuth: { id: 'chatwoot-header-auth', name: 'Chatwoot Header Auth' } },
    position: [3360, 1000]
  },
  output: [{ id: 9 }]
});

// Certificate NO -> send next section message
const chatwootNextSection = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Chatwoot Proxima Secao',
    parameters: {
      method: 'POST',
      url: expr('"https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/conversations/" + {{ $("Extract Aluno Fields").item.json.conversation_id }} + "/messages"'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendHeaders: true,
      specifyHeaders: 'keypair',
      headerParameters: { parameters: [{ name: 'Content-Type', value: 'application/json' }] },
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('{{ JSON.stringify({ "content": $("Calcula Proximo Estado").item.json.reply_text, "message_type": "outgoing" }) }}')
    },
    credentials: { httpHeaderAuth: { id: 'chatwoot-header-auth', name: 'Chatwoot Header Auth' } },
    position: [3100, 1200]
  },
  output: [{ id: 10 }]
});

// ==================== CERTIFICADO EMITIDO BRANCH ====================
const ifNovoCursoPosCert = ifElse({
  version: 2.3,
  config: {
    name: 'Novo curso pos certificado?',
    parameters: {
      conditions: {
        conditions: [
          { leftValue: expr('{{ $json.keyword }}'), operator: { type: 'string', operation: 'notEquals' }, rightValue: expr('{{ $json.curso_ativo }}') }
        ]
      }
    },
    position: [2060, 1500]
  }
});

const chatwootJaConcluiu = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Chatwoot Ja Concluiu',
    parameters: {
      method: 'POST',
      url: expr('"https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/conversations/" + {{ $json.conversation_id }} + "/messages"'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendHeaders: true,
      specifyHeaders: 'keypair',
      headerParameters: { parameters: [{ name: 'Content-Type', value: 'application/json' }] },
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('{{ JSON.stringify({ "content": "🎓 Você já concluiu este curso e seu certificado foi emitido!\\n\\nAcesse seus certificados em: https://lms.ipexdesenvolvimento.cloud/certificates\\n\\nQue tal experimentar outro curso? Envie o comando correspondente (ex: /agricultura, /financas, /ia).", "message_type": "outgoing" }) }}')
    },
    credentials: { httpHeaderAuth: { id: 'chatwoot-header-auth', name: 'Chatwoot Header Auth' } },
    position: [2320, 1600]
  },
  output: [{ id: 11 }]
});

// Certificado emitido + different keyword -> initialize new course directly
const ifModulosExistPosCert = ifElse({
  version: 2.3,
  config: {
    name: 'Modulos disponiveis pos cert?',
    parameters: {
      conditions: {
        conditions: [
          { leftValue: expr('{{ ($json.curso_obj.modulos || []).length }}'), operator: { type: 'number', operation: 'gt' }, rightValue: 0 }
        ]
      }
    },
    position: [2320, 1400]
  }
});

const setInitPosCert = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'Inicializa Pos Certificado',
    parameters: {
      mode: 'manual',
      includeOtherFields: true,
      assignments: {
        assignments: [
          { id: 'pc1', name: 'new_estado', value: 'aguardando_leitura', type: 'string' },
          { id: 'pc2', name: 'new_modulo', value: 1, type: 'number' },
          { id: 'pc3', name: 'new_secao', value: 1, type: 'number' },
          { id: 'pc4', name: 'new_curso_ativo', value: expr('{{ $json.keyword }}'), type: 'string' }
        ]
      }
    },
    position: [2580, 1300]
  },
  output: [{ new_estado: 'aguardando_leitura', new_modulo: 1, new_secao: 1, new_curso_ativo: 'audiovisual', aluno_name: 'TDS-ALU-00001', conversation_id: '123', curso_obj: {} }]
});

const patchAlunoPosCert = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'PATCH Aluno Pos Certificado',
    parameters: {
      method: 'PUT',
      url: expr('"https://lms.ipexdesenvolvimento.cloud/api/resource/TDS%20Aluno/" + {{ $json.aluno_name }}'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendHeaders: true,
      specifyHeaders: 'keypair',
      headerParameters: { parameters: [{ name: 'Content-Type', value: 'application/json' }] },
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('{{ JSON.stringify({ "estado_catraca": $json.new_estado, "modulo_atual": $json.new_modulo, "secao_atual": $json.new_secao, "curso_ativo": $json.new_curso_ativo, "respostas_mcq": "[]", "modulos_concluidos": $json.modulos_concluidos || "[]", "data_ultimo_acesso_whatsapp": $now.toFormat("yyyy-MM-dd HH:mm:ss") }) }}')
    },
    credentials: { httpHeaderAuth: { id: 'frappe-header-auth', name: 'Frappe Header Auth' } },
    position: [2840, 1300]
  },
  output: [{ data: { name: 'TDS-ALU-00001' } }]
});

const chatwootSecao1PosCert = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Chatwoot Secao 1 Pos Cert',
    parameters: {
      method: 'POST',
      url: expr('"https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/conversations/" + {{ $("Extract Aluno Fields").item.json.conversation_id }} + "/messages"'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendHeaders: true,
      specifyHeaders: 'keypair',
      headerParameters: { parameters: [{ name: 'Content-Type', value: 'application/json' }] },
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('"{ \\"content\\": \\"🎓 Parabéns por concluir o curso anterior! Agora você está em *" + {{ $("Extract Aluno Fields").item.json.curso_obj.nome || "novo curso" }} + "*.\\\\n\\\\nO conteúdo será enviado em partes. Após cada leitura, responda *LI* para avançar.\\\\n\\\\nVamos começar!\\", \\"message_type\\": \\"outgoing\\" }"')
    },
    credentials: { httpHeaderAuth: { id: 'chatwoot-header-auth', name: 'Chatwoot Header Auth' } },
    position: [3100, 1300]
  },
  output: [{ id: 13 }]
});

const msgEmBrevePosCert = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'Msg Em Breve Pos Cert',
    parameters: {
      mode: 'manual',
      includeOtherFields: true,
      assignments: {
        assignments: [
          { id: 'pb1', name: 'reply_text', value: expr('"🎓 Parabéns por concluir o curso anterior!\\n\\nO curso *" + {{ $json.curso_obj.nome || $json.keyword }} + "* está sendo preparado e o conteúdo será disponibilizado em breve.\\n\\nFique atento(a)! 📚"'), type: 'string' }
        ]
      }
    },
    position: [2580, 1500]
  },
  output: [{ reply_text: 'Parabens! O curso...', conversation_id: '123' }]
});

const chatwootEmBrevePosCert = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Chatwoot Em Breve Pos Cert',
    parameters: {
      method: 'POST',
      url: expr('"https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/conversations/" + {{ $json.conversation_id }} + "/messages"'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendHeaders: true,
      specifyHeaders: 'keypair',
      headerParameters: { parameters: [{ name: 'Content-Type', value: 'application/json' }] },
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('{{ JSON.stringify({ "content": $json.reply_text, "message_type": "outgoing" }) }}')
    },
    credentials: { httpHeaderAuth: { id: 'chatwoot-header-auth', name: 'Chatwoot Header Auth' } },
    position: [2840, 1500]
  },
  output: [{ id: 14 }]
});

// ==================== FALLBACK (unknown state) ====================
const chatwootFallback = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'Chatwoot Fallback',
    parameters: {
      method: 'POST',
      url: expr('"https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/conversations/" + {{ $json.conversation_id }} + "/messages"'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendHeaders: true,
      specifyHeaders: 'keypair',
      headerParameters: { parameters: [{ name: 'Content-Type', value: 'application/json' }] },
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('{{ JSON.stringify({ "content": "⚠️ Ocorreu um erro no processamento. Por favor, tente novamente ou envie *oi* para recomeçar.", "message_type": "outgoing" }) }}')
    },
    credentials: { httpHeaderAuth: { id: 'chatwoot-header-auth', name: 'Chatwoot Header Auth' } },
    position: [2060, 1700]
  },
  output: [{ id: 12 }]
});

// ==================== STICKY NOTES ====================
const stickyOverview = sticky(
  '## TDS Catraca Pedagogica\n\nSub-workflow que entrega conteudo estruturado (leitura + MCQ) via WhatsApp.\n\nEstados: inativo > aguardando_leitura > aguardando_mcq > certificado_emitido | aguardando_confirmacao_troca\n\nRecebe: { phone, keyword, message, conversation_id }',
  [subWorkflowTrigger],
  { color: 4 }
);

// ==================== COMPOSE WORKFLOW ====================
export default workflow('catraca-pedagogica', 'TDS — Catraca Pedagogica')
  .add(subWorkflowTrigger)
  .to(extractInputs)
  .to(lookupAluno)
  .to(ifAlunoFound
    .onFalse(msgOrientacao.to(chatwootSendOrientacao))
    .onTrue(extractAluno
      .to(ifCursoDiferente
        .onTrue(msgTrocaCurso.to(patchAlunoPendingSwitch.to(chatwootSendTroca)))
        .onFalse(switchEstado
          .onCase(0, ifModulosExist
            .onFalse(msgEmBreve.to(chatwootEmBreve))
            .onTrue(setInitEstado.to(patchAlunoInit.to(chatwootSecao1Init)))
          )
          .onCase(1, ifConfirmLeitura
            .onFalse(chatwootReenviaSecao)
            .onTrue(setAdvanceMCQ.to(patchAlunoMCQ.to(chatwootPergunta)))
          )
          .onCase(2, ifMsgABCD
            .onFalse(ragQuery.to(chatwootRAG))
            .onTrue(codeCalcNextState.to(patchAlunoAnswer.to(ifDoCertificate
              .onTrue(postCertificate.to(chatwootCertificado))
              .onFalse(chatwootNextSection)
            )))
          )
          .onCase(3, ifNovoCursoPosCert
            .onTrue(ifModulosExistPosCert
              .onFalse(msgEmBrevePosCert.to(chatwootEmBrevePosCert))
              .onTrue(setInitPosCert.to(patchAlunoPosCert.to(chatwootSecao1PosCert)))
            )
            .onFalse(chatwootJaConcluiu)
          )
          .onCase(4, ifConfirmTroca
            .onTrue(setInitNewCourse.to(patchAlunoNewCourse.to(ifModulosExistNewCourse
              .onTrue(chatwootNewCourseSection)
              .onFalse(chatwootNewCourseEmBreve)
            )))
            .onFalse(patchAlunoCancelSwitch.to(chatwootCancelSwitch))
          )
          .onCase(5, chatwootFallback)
        )
      )
    )
  );
