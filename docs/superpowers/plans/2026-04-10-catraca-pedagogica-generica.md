# Catraca Pedagógica Genérica — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Criar um único workflow N8N "TDS — Catraca Pedagógica" que entrega conteúdo estruturado (leitura + MCQ) via WhatsApp para todos os 7 cursos TDS, ativado por keywords `/[curso]`.

**Architecture:** O Enrollment Gateway existente (`xRyfmH3HTSKGSirt`) ganha um branch de detecção de mensagens iniciadas com `/`. Esse branch chama o novo workflow genérico via Execute Workflow, que faz lookup no TDS Aluno (Frappe), executa a state machine e responde via Chatwoot. Estado do aluno persiste em campos custom no TDS Aluno doctype.

**Tech Stack:** N8N 2.13.4 (MCP tools), Frappe LMS REST API, Chatwoot API, AnythingLLM API, PostgreSQL (kreativ_edu)

**Spec:** `docs/superpowers/specs/2026-04-10-catraca-pedagogica-generica-design.md`

**Credenciais** (todas em `/root/kreativ-setup/.env.real`):
- Frappe: `Authorization: token 056681de29fce7a:7a0dd3d5f006a3e`
- Frappe base URL: `https://lms.ipexdesenvolvimento.cloud`
- Chatwoot API key: `w8BYLTQc1s5VMowjQw433rGy` (24 chars — sem C extra)
- Chatwoot account ID: 1
- Chatwoot base URL: `https://chat.ipexdesenvolvimento.cloud`
- AnythingLLM API key: `W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0`
- AnythingLLM base URL: `https://rag.ipexdesenvolvimento.cloud`
- N8N API key: ver .env.real (`N8N_API_KEY`)

---

## Task 1: Verificar campos catraca existentes no TDS Aluno

**Files:**
- None (API calls only)

- [ ] **Step 1: Verificar quais campos catraca já existem**

```bash
curl -s "https://lms.ipexdesenvolvimento.cloud/api/resource/DocType/TDS%20Aluno" \
  -H "Authorization: token 056681de29fce7a:7a0dd3d5f006a3e" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); fields=[f['fieldname'] for f in d.get('data',{}).get('fields',[])]; print('\n'.join(f for f in fields if any(k in f for k in ['catraca','modulo','secao','respostas','concluidos','ultimo_acesso','curso_ativo'])))"
```

Campos esperados: `estado_catraca`, `modulo_atual`, `secao_atual`, `respostas_mcq`, `modulos_concluidos`, `data_ultimo_acesso_whatsapp`, `curso_ativo`.

Se a lista retornar vazia ou incompleta, prosseguir para os Steps 2-8 para cada campo faltante. Se todos existirem, marcar Task 1 como concluída e pular para Task 2.

- [ ] **Step 2: Criar campo estado_catraca (se faltante)**

```bash
curl -s -X POST "https://lms.ipexdesenvolvimento.cloud/api/resource/Custom%20Field" \
  -H "Authorization: token 056681de29fce7a:7a0dd3d5f006a3e" \
  -H "Content-Type: application/json" \
  -d '{
    "dt": "TDS Aluno",
    "fieldname": "estado_catraca",
    "fieldtype": "Select",
    "label": "Estado Catraca",
    "options": "inativo\naguardando_leitura\naguardando_mcq\nmodulo_completo\ncertificado_emitido",
    "default": "inativo"
  }'
```

Esperado: `{"data": {"name": "TDS Aluno-estado_catraca", ...}}`

- [ ] **Step 3: Criar campo modulo_atual (se faltante)**

```bash
curl -s -X POST "https://lms.ipexdesenvolvimento.cloud/api/resource/Custom%20Field" \
  -H "Authorization: token 056681de29fce7a:7a0dd3d5f006a3e" \
  -H "Content-Type: application/json" \
  -d '{
    "dt": "TDS Aluno",
    "fieldname": "modulo_atual",
    "fieldtype": "Int",
    "label": "Módulo Atual",
    "default": "0"
  }'
```

- [ ] **Step 4: Criar campo secao_atual (se faltante)**

```bash
curl -s -X POST "https://lms.ipexdesenvolvimento.cloud/api/resource/Custom%20Field" \
  -H "Authorization: token 056681de29fce7a:7a0dd3d5f006a3e" \
  -H "Content-Type: application/json" \
  -d '{
    "dt": "TDS Aluno",
    "fieldname": "secao_atual",
    "fieldtype": "Int",
    "label": "Seção Atual",
    "default": "0"
  }'
```

- [ ] **Step 5: Criar campo respostas_mcq (se faltante)**

```bash
curl -s -X POST "https://lms.ipexdesenvolvimento.cloud/api/resource/Custom%20Field" \
  -H "Authorization: token 056681de29fce7a:7a0dd3d5f006a3e" \
  -H "Content-Type: application/json" \
  -d '{
    "dt": "TDS Aluno",
    "fieldname": "respostas_mcq",
    "fieldtype": "Small Text",
    "label": "Respostas MCQ (JSON)",
    "default": "{}"
  }'
```

- [ ] **Step 6: Criar campo modulos_concluidos (se faltante)**

```bash
curl -s -X POST "https://lms.ipexdesenvolvimento.cloud/api/resource/Custom%20Field" \
  -H "Authorization: token 056681de29fce7a:7a0dd3d5f006a3e" \
  -H "Content-Type: application/json" \
  -d '{
    "dt": "TDS Aluno",
    "fieldname": "modulos_concluidos",
    "fieldtype": "Small Text",
    "label": "Módulos Concluídos (JSON)",
    "default": "[]"
  }'
```

- [ ] **Step 7: Criar campo data_ultimo_acesso_whatsapp (se faltante)**

```bash
curl -s -X POST "https://lms.ipexdesenvolvimento.cloud/api/resource/Custom%20Field" \
  -H "Authorization: token 056681de29fce7a:7a0dd3d5f006a3e" \
  -H "Content-Type: application/json" \
  -d '{
    "dt": "TDS Aluno",
    "fieldname": "data_ultimo_acesso_whatsapp",
    "fieldtype": "Datetime",
    "label": "Último Acesso WhatsApp"
  }'
```

- [ ] **Step 8: Verificar campos criados**

```bash
curl -s "https://lms.ipexdesenvolvimento.cloud/api/resource/DocType/TDS%20Aluno" \
  -H "Authorization: token 056681de29fce7a:7a0dd3d5f006a3e" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); fields=[f['fieldname'] for f in d.get('data',{}).get('fields',[])]; expected=['estado_catraca','modulo_atual','secao_atual','respostas_mcq','modulos_concluidos','data_ultimo_acesso_whatsapp']; missing=[e for e in expected if e not in fields]; print('OK' if not missing else 'FALTANDO: '+str(missing))"
```

Esperado: `OK`

- [ ] **Step 9: Commit**

```bash
cd /root/projeto-tds && git add -A && git commit -m "chore: campos catraca verificados/criados no TDS Aluno"
```

---

## Task 2: Criar campo curso_ativo no TDS Aluno

**Files:**
- None (API call only)

- [ ] **Step 1: Criar o campo**

```bash
curl -s -X POST "https://lms.ipexdesenvolvimento.cloud/api/resource/Custom%20Field" \
  -H "Authorization: token 056681de29fce7a:7a0dd3d5f006a3e" \
  -H "Content-Type: application/json" \
  -d '{
    "dt": "TDS Aluno",
    "fieldname": "curso_ativo",
    "fieldtype": "Data",
    "label": "Curso Ativo (keyword)",
    "description": "Keyword do curso em andamento: audiovisual, agricultura, financas, educacao, associa, ia, sim"
  }'
```

Esperado: `{"data": {"name": "TDS Aluno-curso_ativo", ...}}`

- [ ] **Step 2: Verificar o campo**

```bash
curl -s "https://lms.ipexdesenvolvimento.cloud/api/resource/DocType/TDS%20Aluno" \
  -H "Authorization: token 056681de29fce7a:7a0dd3d5f006a3e" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); fields=[f['fieldname'] for f in d.get('data',{}).get('fields',[])]; print('OK' if 'curso_ativo' in fields else 'FALTANDO curso_ativo')"
```

Esperado: `OK`

---

## Task 3: Construir workflow "TDS — Catraca Pedagógica" no N8N

**Files:**
- Create: `scripts/n8n/catraca-pedagogica.js` — SDK code para referência e redeployment

- [ ] **Step 1: Ler a referência do SDK N8N**

Usar a tool MCP `mcp__claude_ai_n8n__get_sdk_reference` com `sections: ["overview", "nodes", "guidelines", "design"]` para entender a sintaxe completa do SDK antes de escrever o código.

- [ ] **Step 2: Descobrir os nodes necessários**

Usar `mcp__claude_ai_n8n__search_nodes` com queries:
- `["http request"]` — para chamadas Frappe, Chatwoot, AnythingLLM
- `["switch"]` — para roteamento por estado
- `["if"]` — para condicionais
- `["set"]` — para manipulação de dados
- `["code"]` — para lógica JavaScript complexa (state machine)
- `["execute workflow"]` — para ser chamado pelo gateway

Anotar os `nodeType` IDs retornados.

- [ ] **Step 3: Obter definições de tipos dos nodes**

Usar `mcp__claude_ai_n8n__get_node_types` com todos os IDs coletados no Step 2.

- [ ] **Step 4: Escrever o código do workflow**

Criar `/root/projeto-tds/scripts/n8n/catraca-pedagogica.js` com o seguinte conteúdo (completar com sintaxe exata do SDK obtida nos Steps 1-3):

```javascript
// TDS — Catraca Pedagógica
// Workflow genérico para todos os 7 cursos TDS via keyword trigger

const FRAPPE_BASE = 'https://lms.ipexdesenvolvimento.cloud';
const FRAPPE_TOKEN = 'token 056681de29fce7a:7a0dd3d5f006a3e';
const CHATWOOT_BASE = 'https://chat.ipexdesenvolvimento.cloud';
const CHATWOOT_KEY = 'w8BYLTQc1s5VMowjQw433rGy';
const ANYTHINGLLM_BASE = 'https://rag.ipexdesenvolvimento.cloud';
const ANYTHINGLLM_KEY = 'W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0';

const CONFIRMATION_WORDS = ['li', 'ok', 'pronto', 'entendi', 'sim', 'certo',
                             'combinado', 'feito', 'lido', 'claro'];

const CURSOS_JSON = {
  audiovisual: {
    nome: 'Audiovisual e Produção de Conteúdo Digital',
    workspace_slug: 'tds-audiovisual-e-conteudo',
    modulos: [
      // CONTEÚDO A SER FORNECIDO PELA EQUIPE PEDAGÓGICA
      // Estrutura esperada:
      // {
      //   titulo: 'Módulo 1 — ...',
      //   secoes: [
      //     {
      //       texto: '...',
      //       pergunta: '...',
      //       opcoes: { A: '...', B: '...', C: '...', D: '...' }
      //     }
      //   ]
      // }
    ]
  },
  agricultura: {
    nome: 'Agricultura Sustentável — SAFs',
    workspace_slug: 'tds-agricultura-sustentavel',
    modulos: []
  },
  financas: {
    nome: 'Finanças e Empreendedorismo',
    workspace_slug: 'tds-financas-e-empreendedorismo',
    modulos: []
  },
  educacao: {
    nome: 'Educação Financeira Melhor Idade',
    workspace_slug: 'tds-educacao-financeira-terceira-idade',
    modulos: []
  },
  associa: {
    nome: 'Associativismo e Cooperativismo',
    workspace_slug: 'tds-associativismo-e-cooperativismo',
    modulos: []
  },
  ia: {
    nome: 'IA no meu Bolso',
    workspace_slug: 'tds-ia-no-meu-bolso',
    modulos: []
  },
  sim: {
    nome: 'SIM — Serviço de Inspeção Municipal',
    workspace_slug: 'tds-sim',
    modulos: []
  }
};

// --- LÓGICA DA STATE MACHINE (Code node) ---
// Input: { phone, keyword, message, aluno, cursoData }
// Output: { nextState, nextModulo, nextSecao, response, updateAluno, doRAG, doCertificate }
function processStateMachine(input) {
  const { phone, keyword, message, aluno, cursoData } = input;
  const msg = message.trim().toLowerCase();
  const estado = aluno.estado_catraca || 'inativo';
  const modulo = parseInt(aluno.modulo_atual) || 0;
  const secao = parseInt(aluno.secao_atual) || 0;
  const cursoAtivo = aluno.curso_ativo || '';
  const modulos = cursoData.modulos || [];

  // Troca de curso enquanto está em andamento
  if (cursoAtivo && cursoAtivo !== keyword && estado !== 'inativo') {
    if (['sim', 's', 'yes', '1'].includes(msg)) {
      // Confirmar troca
      return {
        nextState: 'aguardando_leitura',
        nextModulo: 1, nextSecao: 1,
        cursoAtivo: keyword,
        response: `✅ Tudo bem! Iniciando *${cursoData.nome}* do zero.\n\n` + getSecaoTexto(modulos, 1, 1),
        updateAluno: true
      };
    }
    if (['nao', 'não', 'n', 'no', '2'].includes(msg)) {
      return {
        nextState: estado, nextModulo: modulo, nextSecao: secao,
        cursoAtivo: cursoAtivo,
        response: `Ok! Continuando em *${CURSOS_JSON[cursoAtivo]?.nome || cursoAtivo}*.`,
        updateAluno: false
      };
    }
    return {
      nextState: estado, nextModulo: modulo, nextSecao: secao,
      cursoAtivo: cursoAtivo,
      response: `Você está no curso *${CURSOS_JSON[cursoAtivo]?.nome || cursoAtivo}*.\n\nDeseja trocar para *${cursoData.nome}*? Responda *SIM* ou *NÃO*.`,
      updateAluno: false
    };
  }

  // Início de novo curso
  if (estado === 'inativo' || !cursoAtivo) {
    if (modulos.length === 0) {
      return {
        nextState: 'inativo', nextModulo: 0, nextSecao: 0,
        cursoAtivo: keyword,
        response: `📚 O curso *${cursoData.nome}* estará disponível em breve! Fique atento.`,
        updateAluno: false
      };
    }
    return {
      nextState: 'aguardando_leitura',
      nextModulo: 1, nextSecao: 1,
      cursoAtivo: keyword,
      response: `🎓 Bem-vindo ao curso *${cursoData.nome}*!\n\nVou guiar você pelo Módulo 1 agora.\n\n` + getSecaoTexto(modulos, 1, 1),
      updateAluno: true
    };
  }

  // Aguardando confirmação de leitura
  if (estado === 'aguardando_leitura') {
    if (CONFIRMATION_WORDS.includes(msg)) {
      const pergunta = getPerguntaTexto(modulos, modulo, secao);
      return {
        nextState: 'aguardando_mcq',
        nextModulo: modulo, nextSecao: secao,
        cursoAtivo: keyword,
        response: pergunta,
        updateAluno: true
      };
    }
    // Não é confirmação — reenvia seção
    return {
      nextState: 'aguardando_leitura',
      nextModulo: modulo, nextSecao: secao,
      cursoAtivo: keyword,
      response: `Por favor, leia o conteúdo acima e responda *LI* quando terminar.\n\n` + getSecaoTexto(modulos, modulo, secao),
      updateAluno: false
    };
  }

  // Aguardando resposta MCQ
  if (estado === 'aguardando_mcq') {
    const opcoes = ['a', 'b', 'c', 'd'];
    if (opcoes.includes(msg)) {
      // Registra resposta (qualquer resposta vale — inclusivo)
      const respostas = JSON.parse(aluno.respostas_mcq || '{}');
      if (!respostas[`mod${modulo}`]) respostas[`mod${modulo}`] = {};
      respostas[`mod${modulo}`][`sec${secao}`] = msg.toUpperCase();

      // Calcula próximo estado
      const modData = modulos[modulo - 1];
      const totalSecoes = modData ? modData.secoes.length : 0;
      const totalModulos = modulos.length;

      if (secao < totalSecoes) {
        // Próxima seção
        return {
          nextState: 'aguardando_leitura',
          nextModulo: modulo, nextSecao: secao + 1,
          cursoAtivo: keyword,
          respostas_mcq: JSON.stringify(respostas),
          response: `✅ Resposta registrada!\n\n` + getSecaoTexto(modulos, modulo, secao + 1),
          updateAluno: true
        };
      } else if (modulo < totalModulos) {
        // Próximo módulo
        const concluidos = JSON.parse(aluno.modulos_concluidos || '[]');
        concluidos.push(modulo);
        return {
          nextState: 'aguardando_leitura',
          nextModulo: modulo + 1, nextSecao: 1,
          cursoAtivo: keyword,
          respostas_mcq: JSON.stringify(respostas),
          modulos_concluidos: JSON.stringify(concluidos),
          response: `🎉 Parabéns! Você concluiu o *${modData.titulo}*!\n\nVamos para o próximo módulo.\n\n` + getSecaoTexto(modulos, modulo + 1, 1),
          updateAluno: true
        };
      } else {
        // Curso completo
        const concluidos = JSON.parse(aluno.modulos_concluidos || '[]');
        concluidos.push(modulo);
        return {
          nextState: 'certificado_emitido',
          nextModulo: modulo, nextSecao: secao,
          cursoAtivo: keyword,
          respostas_mcq: JSON.stringify(respostas),
          modulos_concluidos: JSON.stringify(concluidos),
          response: null, // certificado handler cuida da resposta
          updateAluno: true,
          doCertificate: true
        };
      }
    }
    // Não é A/B/C/D — pergunta livre → RAG
    return {
      nextState: 'aguardando_mcq',
      nextModulo: modulo, nextSecao: secao,
      cursoAtivo: keyword,
      updateAluno: false,
      doRAG: true,
      ragWorkspace: cursoData.workspace_slug
    };
  }

  // Certificado já emitido
  if (estado === 'certificado_emitido') {
    return {
      nextState: 'certificado_emitido',
      nextModulo: modulo, nextSecao: secao,
      cursoAtivo: keyword,
      response: `🏆 Você já concluiu o curso *${cursoData.nome}*!\nSeu certificado: https://lms.ipexdesenvolvimento.cloud/lms/certification/${aluno.nome}`,
      updateAluno: false
    };
  }

  return {
    nextState: 'inativo', response: 'Estado desconhecido. Digite /audiovisual para reiniciar.',
    updateAluno: false
  };
}

function getSecaoTexto(modulos, modulo, secao) {
  const mod = modulos[modulo - 1];
  if (!mod) return '[Módulo não encontrado]';
  const sec = mod.secoes[secao - 1];
  if (!sec) return '[Seção não encontrada]';
  return `📖 *${mod.titulo} — Parte ${secao}*\n\n${sec.texto}\n\nQuando terminar, responda *LI*.`;
}

function getPerguntaTexto(modulos, modulo, secao) {
  const mod = modulos[modulo - 1];
  if (!mod) return '[Módulo não encontrado]';
  const sec = mod.secoes[secao - 1];
  if (!sec) return '[Seção não encontrada]';
  return `❓ *Pergunta:*\n${sec.pergunta}\n\n*A)* ${sec.opcoes.A}\n*B)* ${sec.opcoes.B}\n*C)* ${sec.opcoes.C}\n*D)* ${sec.opcoes.D}\n\nResponda com a letra (A, B, C ou D).`;
}
```

- [ ] **Step 5: Validar o workflow**

Usar `mcp__claude_ai_n8n__validate_workflow` com o código completo do Step 4 (convertido para formato SDK conforme referência obtida no Step 1). Corrigir todos os erros antes de prosseguir.

- [ ] **Step 5b: Adicionar node de emissão de certificado no workflow**

Quando `doCertificate: true` na saída da state machine, o workflow deve:

```javascript
// Node HTTP Request: "Emitir Certificado"
// Executado apenas quando doCertificate === true
// POST https://lms.ipexdesenvolvimento.cloud/api/resource/LMS Certificate
// Headers: Authorization: token 056681de29fce7a:7a0dd3d5f006a3e
// Body:
{
  "member": "{{ $json.aluno.email }}", // email do aluno no Frappe
  "course": "audiovisual-e-produ-o-de-conte-do-digital", // slug do curso
  "issue_date": "{{ $now.toISODate() }}"
}
// Após emissão, montar a resposta:
// "🏆 Parabéns [nome]! Você concluiu o curso [nome do curso]!\nSeu certificado: https://lms.ipexdesenvolvimento.cloud/lms/certification/[certificate_id]"
```

**Nota:** O campo `member` no LMS Certificate usa o email do aluno, não o WhatsApp. Certifique-se de que o TDS Aluno tem campo `email` preenchido. Se não tiver, usar `whatsapp@tds.local` como fallback e registrar o certificado manualmente.

- [ ] **Step 6: Criar o workflow no N8N**

Usar `mcp__claude_ai_n8n__create_workflow_from_code` com:
- `name`: `"TDS — Catraca Pedagógica"`
- `description`: `"Workflow genérico que entrega conteúdo estruturado (leitura + MCQ) via WhatsApp para todos os 7 cursos TDS, ativado por keywords /audiovisual, /agricultura, etc."`
- `code`: código validado do Step 5

Anotar o `workflow_id` retornado.

- [ ] **Step 7: Ativar o workflow**

Usar `mcp__claude_ai_n8n__publish_workflow` com o ID do Step 6.

Verificar no N8N UI: `https://n8n.ipexdesenvolvimento.cloud` → workflow "TDS — Catraca Pedagógica" deve aparecer como **ACTIVE**.

- [ ] **Step 8: Commit**

```bash
cd /root/projeto-tds && git add scripts/n8n/catraca-pedagogica.js && git commit -m "feat: workflow TDS — Catraca Pedagógica (N8N SDK)"
```

---

## Task 4: Atualizar Enrollment Gateway com detecção de "/"

**Files:**
- Modify: Workflow N8N `xRyfmH3HTSKGSirt` (Enrollment Gateway v2)

- [ ] **Step 1: Obter detalhes do gateway atual**

Usar `mcp__claude_ai_n8n__get_workflow_details` com `workflow_id: "xRyfmH3HTSKGSirt"`.

Identificar os primeiros nodes do workflow (Webhook trigger e o roteador inicial).

- [ ] **Step 2: Entender o payload Chatwoot que chega no gateway**

O webhook recebe o payload completo do Chatwoot. O campo `message` com o texto da mensagem está em:
```
$json.body.messages[0].content
```
(ou equivalente conforme o node de extração existente)

Verificar no workflow atual qual expression é usada para extrair o texto da mensagem. Procurar nodes "Extrair Dados" ou similares.

- [ ] **Step 3: Escrever o código do gateway atualizado**

Criar `/root/projeto-tds/scripts/n8n/gateway-update.js` com a lógica do novo branch:

```javascript
// Lógica a adicionar no Enrollment Gateway
// Adicionar ANTES do roteador RAG/enrollment atual

// Node IF a adicionar: "É comando /?"
// Condition: {{ $json.message.startsWith('/') }}

// Node SET a adicionar: "Extrair keyword"
// keyword = $json.message.slice(1).toLowerCase().trim()
// ex: "/audiovisual" → "audiovisual"

const VALID_KEYWORDS = ['audiovisual', 'agricultura', 'financas', 'educacao', 'associa', 'ia', 'sim'];

// Se keyword está na lista → Execute Workflow: TDS — Catraca Pedagógica
// com input: { phone: $json.phone, keyword: $json.keyword, message: $json.message }

// Se keyword não está na lista → resposta de ajuda
const helpMessage = `Comandos disponíveis:\n/audiovisual — Produção de Conteúdo Digital\n/agricultura — Agricultura Sustentável\n/financas — Finanças e Empreendedorismo\n/educacao — Educação Financeira\n/associa — Associativismo\n/ia — IA no meu Bolso\n/sim — Serviço de Inspeção Municipal`;
```

- [ ] **Step 4: Obter node types para o IF e Execute Workflow**

Usar `mcp__claude_ai_n8n__get_node_types` com os node IDs de:
- `n8n-nodes-base.if`
- `n8n-nodes-base.executeWorkflow`
- `n8n-nodes-base.set`

- [ ] **Step 5: Atualizar o gateway via MCP**

Usar `mcp__claude_ai_n8n__update_workflow` com `workflow_id: "xRyfmH3HTSKGSirt"` e o código atualizado que inclui:
1. Node IF: verifica se mensagem começa com `/`
2. Branch SIM → Node Set extrai keyword → Node IF verifica se keyword é válido
   - Branch VÁLIDO → Execute Workflow com ID do workflow criado na Task 3
   - Branch INVÁLIDO → Chatwoot: envia mensagem de ajuda com lista de comandos
3. Branch NÃO → fluxo original (RAG / enrollment)

Usar `mcp__claude_ai_n8n__validate_workflow` antes de atualizar.

- [ ] **Step 6: Reativar o gateway**

N8N cacheia o workflow ativo em memória. Após update, desativar e reativar:

Usar `mcp__claude_ai_n8n__unpublish_workflow` com `workflow_id: "xRyfmH3HTSKGSirt"`.
Aguardar 3 segundos.
Usar `mcp__claude_ai_n8n__publish_workflow` com `workflow_id: "xRyfmH3HTSKGSirt"`.

- [ ] **Step 7: Commit**

```bash
cd /root/projeto-tds && git add scripts/n8n/gateway-update.js && git commit -m "feat: enrollment gateway detecta /keyword e chama catraca"
```

---

## Task 5: Adicionar conteúdo pedagógico do curso Audiovisual

**Files:**
- Create: `scripts/n8n/conteudo-audiovisual.js` — JSON do curso para copiar no workflow

**Pré-requisito:** Rafael/equipe pedagógica deve fornecer o conteúdo (textos dos módulos + perguntas MCQ). Enquanto o conteúdo não estiver disponível, o workflow responde `"📚 O curso Audiovisual estará disponível em breve!"` (já tratado na state machine).

Quando o conteúdo estiver disponível:

- [ ] **Step 1: Criar arquivo de conteúdo**

Criar `/root/projeto-tds/scripts/n8n/conteudo-audiovisual.js` preenchendo o array `modulos` do CURSOS_JSON com o conteúdo fornecido pela equipe:

```javascript
// Conteúdo pedagógico — Audiovisual e Produção de Conteúdo Digital
// Preencher com conteúdo fornecido por pedroh@ipexdesenvolvimento.cloud

const MODULOS_AUDIOVISUAL = [
  {
    titulo: 'Módulo 1 — [TÍTULO]',
    secoes: [
      {
        texto: '[TEXTO DA CARTILHA — máx. 1500 chars para caber no WhatsApp]',
        pergunta: '[PERGUNTA MCQ]',
        opcoes: {
          A: '[OPÇÃO A]',
          B: '[OPÇÃO B]',
          C: '[OPÇÃO C]',
          D: '[OPÇÃO D]'
        }
      }
      // adicionar mais seções conforme necessário
    ]
  }
  // adicionar mais módulos conforme necessário
];
```

- [ ] **Step 2: Atualizar o CURSOS_JSON no workflow**

Usar `mcp__claude_ai_n8n__update_workflow` com o `workflow_id` da Catraca Pedagógica para substituir `modulos: []` do `audiovisual` pelo array `MODULOS_AUDIOVISUAL` preenchido.

Validar antes de atualizar.

- [ ] **Step 3: Commit**

```bash
cd /root/projeto-tds && git add scripts/n8n/conteudo-audiovisual.js && git commit -m "feat: conteúdo pedagógico audiovisual no workflow catraca"
```

---

## Task 6: Teste end-to-end

**Files:**
- None (testes manuais via API + WhatsApp)

- [ ] **Step 1: Verificar se o aluno de teste existe no Frappe**

```bash
curl -s "https://lms.ipexdesenvolvimento.cloud/api/resource/TDS%20Aluno?filters=%5B%5B%22whatsapp%22%2C%22%3D%22%2C%2263999374165%22%5D%5D&fields=%5B%22name%22%2C%22whatsapp%22%2C%22full_name%22%2C%22estado_catraca%22%2C%22curso_ativo%22%5D" \
  -H "Authorization: token 056681de29fce7a:7a0dd3d5f006a3e"
```

Esperado: objeto com `estado_catraca: "inativo"` ou vazio.

Se o aluno não existir, criar via:
```bash
curl -s -X POST "https://lms.ipexdesenvolvimento.cloud/api/resource/TDS%20Aluno" \
  -H "Authorization: token 056681de29fce7a:7a0dd3d5f006a3e" \
  -H "Content-Type: application/json" \
  -d '{"whatsapp": "63999374165", "full_name": "Aluno Teste TDS", "estado_catraca": "inativo"}'
```

- [ ] **Step 2: Obter contact_id do aluno de teste no Chatwoot**

```bash
# Buscar contato pelo número de telefone
curl -s "https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/contacts/search?q=63999374165" \
  -H "api_access_token: w8BYLTQc1s5VMowjQw433rGy" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); cs=d.get('payload',[{}]); print(cs[0].get('id','NÃO ENCONTRADO') if cs else 'VAZIO')"
```

Se não encontrado, criar o contato:
```bash
curl -s -X POST "https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/contacts" \
  -H "api_access_token: w8BYLTQc1s5VMowjQw433rGy" \
  -H "Content-Type: application/json" \
  -d '{"name": "Aluno Teste TDS", "phone_number": "+5563999374165"}'
```

Anotar o `contact_id`.

- [ ] **Step 2b: Criar conversa de teste no Chatwoot (inbox 1 — API sandbox)**

```bash
curl -s -X POST "https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/conversations" \
  -H "api_access_token: w8BYLTQc1s5VMowjQw433rGy" \
  -H "Content-Type: application/json" \
  -d "{\"inbox_id\": 1, \"contact_id\": {CONTACT_ID}}"
```

Substituir `{CONTACT_ID}` pelo ID obtido acima. Anotar o `conversation_id`.

- [ ] **Step 3: Enviar mensagem de teste**

```bash
curl -s -X POST "https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/conversations/{CONVERSATION_ID}/messages" \
  -H "api_access_token: w8BYLTQc1s5VMowjQw433rGy" \
  -H "Content-Type: application/json" \
  -d '{"content": "/audiovisual", "message_type": "incoming"}'
```

Substituir `{CONVERSATION_ID}` pelo ID do Step 2.

- [ ] **Step 4: Verificar resposta**

Aguardar 5 segundos e verificar as mensagens da conversa:

```bash
curl -s "https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/conversations/{CONVERSATION_ID}/messages" \
  -H "api_access_token: w8BYLTQc1s5VMowjQw433rGy" \
  | python3 -c "import json,sys; msgs=json.load(sys.stdin)['data']['payload']; [print(m['content'][:100]) for m in msgs if m.get('message_type')==1]"
```

Esperado: mensagem de boas-vindas com o primeiro módulo OU `"📚 O curso Audiovisual estará disponível em breve!"` se `modulos: []`.

- [ ] **Step 5: Verificar estado atualizado no Frappe**

```bash
curl -s "https://lms.ipexdesenvolvimento.cloud/api/resource/TDS%20Aluno?filters=%5B%5B%22whatsapp%22%2C%22%3D%22%2C%2263999374165%22%5D%5D&fields=%5B%22estado_catraca%22%2C%22curso_ativo%22%2C%22modulo_atual%22%2C%22secao_atual%22%5D" \
  -H "Authorization: token 056681de29fce7a:7a0dd3d5f006a3e"
```

Esperado: `curso_ativo: "audiovisual"` e `estado_catraca: "aguardando_leitura"` (se tiver conteúdo) ou `"inativo"` (se `modulos: []`).

- [ ] **Step 6: Testar comando inválido**

```bash
curl -s -X POST "https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/conversations/{CONVERSATION_ID}/messages" \
  -H "api_access_token: w8BYLTQc1s5VMowjQw433rGy" \
  -H "Content-Type: application/json" \
  -d '{"content": "/invalido", "message_type": "incoming"}'
```

Aguardar 5s e verificar: deve retornar a lista de comandos válidos.

- [ ] **Step 7: Commit final**

```bash
cd /root/projeto-tds && git add -A && git commit -m "test: catraca pedagógica end-to-end validado"
```

---

## Checklist de Dependências

```
Task 1 (campos catraca)  → independente, executar primeiro
Task 2 (curso_ativo)     → independente, executar com Task 1
Task 3 (workflow catraca) → depende Tasks 1+2 (campos devem existir antes)
Task 4 (gateway update)  → depende Task 3 (precisa do workflow_id)
Task 5 (conteúdo)        → depende Task 3 + conteúdo da equipe pedagógica
Task 6 (teste)           → depende Tasks 3+4
```

## Notas de Produção

- **Bug conhecido N8N:** Após `update_workflow`, o workflow ativo em memória não atualiza. Sempre fazer `unpublish` + `publish` após qualquer update.
- **Chatwoot API key:** Usar `w8BYLTQc1s5VMowjQw433rGy` (24 chars). A versão com `C` extra (`w8BYLTQc1s5VMowjQw433rGyC`) está errada.
- **Frappe URL encoding:** Espaços nos nomes de DocType devem ser `%20` nas URLs.
- **Conteúdo audiovisual:** Tutora responsável é `pedroh@ipexdesenvolvimento.cloud`. Contatar para obter cartilha e MCQs.
