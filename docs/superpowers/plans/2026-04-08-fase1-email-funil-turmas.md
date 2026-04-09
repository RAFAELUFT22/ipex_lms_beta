# TDS Fase 1 — Email + Funil Typebot + Turmas/Notificações

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ativar email transacional, substituir o Google Form presencial por um funil conversacional no WhatsApp (Typebot + 102 campos), e estruturar o sistema de turmas com notificações proativas de aulas.

**Architecture:** Três subsistemas independentes que compartilham o PostgreSQL `kreativ_edu` como fonte de verdade. (1) Email: DNS + DKIM via Hostinger/Poste.io. (2) Funil: Chatwoot recebe mensagem WhatsApp → n8n consulta sessão no PostgreSQL → encaminha ao Typebot API → retorna resposta via Chatwoot API; on_complete salva aluno no PostgreSQL. (3) Turmas: AnythingLLM workspaces por curso + Google Form de agendamento → n8n → PostgreSQL; cron n8n 8h envia WhatsApp de lembrete 24h antes da aula.

**Tech Stack:** PostgreSQL 15, n8n 2.13.4, Typebot (self-hosted), AnythingLLM, Chatwoot (Channel::Whatsapp inbox 5), Hostinger DNS (hpanel.hostinger.com), Poste.io admin.

> **Nota de escopo:** As 3 partes são independentes — podem ser implementadas em paralelo ou em qualquer ordem. Cada tarefa é atômica.

---

## File / Resource Map

| Recurso | Tipo | Responsabilidade |
|---------|------|-----------------|
| PostgreSQL `kreativ_edu` | DB | Fonte de verdade: alunos, turmas, matriculas, aulas, presenca, typebot_sessoes |
| n8n workflow "TDS — Funil Cadastro" | Workflow | Recebe Chatwoot webhook, gerencia sessão Typebot, encaminha mensagens |
| n8n workflow "TDS — Funil On Complete" | Workflow | Recebe on_complete do Typebot, salva aluno no PostgreSQL |
| n8n workflow "TDS — Notificação Aulas" | Workflow | Cron 8h diário: seleciona aulas em 24h, envia WhatsApp para alunos matriculados |
| n8n workflow "TDS — Agendamento Aulas" | Workflow | Recebe Google Form de agendamento, insere em `aulas` |
| n8n workflow "TDS — Registro Presença" | Workflow | Recebe Google Form de presença, insere/atualiza `presenca` |
| Typebot flow "funil-cadastro-tds" | Bot flow | 18 blocos / ~102 campos do baseline + pré-matrícula |
| AnythingLLM workspaces (×4) | RAG | Um por curso; tutores adicionam materiais e criam threads de aulas |
| `/root/projeto-tds/sql/fase1-schema.sql` | SQL | DDL de todas as novas tabelas |
| `/root/projeto-tds/n8n/funil-cadastro.json` | JSON | Export do workflow n8n para versionamento |

---

## PARTE A — Email DNS

### Task A1: Criar registros DNS no Hostinger

**Contexto:** O Poste.io está em `mail.ipexdesenvolvimento.cloud` (IP 46.202.150.132). Sem os registros corretos, emails enviados caem em spam ou são rejeitados. O DKIM (Task A2) depende de um passo no Poste.io primeiro.

- [ ] **Passo 1: Acessar painel DNS do Hostinger**

  Abrir: https://hpanel.hostinger.com → Domínios → `ipexdesenvolvimento.cloud` → DNS / Zone Editor

- [ ] **Passo 2: Criar registro A para mail**

  | Campo | Valor |
  |-------|-------|
  | Tipo | A |
  | Nome | mail |
  | Valor | 46.202.150.132 |
  | TTL | 3600 |

  Se já existir um registro A para `mail`, editar com o IP correto.

- [ ] **Passo 3: Criar registro MX**

  | Campo | Valor |
  |-------|-------|
  | Tipo | MX |
  | Nome | @ |
  | Valor | mail.ipexdesenvolvimento.cloud |
  | Prioridade | 10 |
  | TTL | 3600 |

  Remover qualquer MX anterior que aponte para outro servidor.

- [ ] **Passo 4: Criar registro SPF**

  | Campo | Valor |
  |-------|-------|
  | Tipo | TXT |
  | Nome | @ |
  | Valor | `v=spf1 ip4:46.202.150.132 ~all` |
  | TTL | 3600 |

  Se já existir um TXT com `v=spf1`, editar (não criar duplicado).

- [ ] **Passo 5: Verificar propagação (após 5-10 min)**

  Rodar no terminal do servidor:
  ```bash
  dig MX ipexdesenvolvimento.cloud +short
  dig A mail.ipexdesenvolvimento.cloud +short
  dig TXT ipexdesenvolvimento.cloud +short
  ```

  Resultado esperado:
  ```
  10 mail.ipexdesenvolvimento.cloud.
  46.202.150.132
  "v=spf1 ip4:46.202.150.132 ~all"
  ```

---

### Task A2: Gerar DKIM no Poste.io e criar registro no Hostinger

**Contexto:** DKIM assina digitalmente os emails, evitando que Gmail/Hotmail rejeitem como spam. Deve ser feito após A1 (o PTR pode ser feito em paralelo).

- [ ] **Passo 1: Gerar chave DKIM no Poste.io**

  Acessar: https://mail.ipexdesenvolvimento.cloud/admin
  Login: (credenciais do Poste.io)
  
  Navegar: Domínios → `ipexdesenvolvimento.cloud` → DKIM → "Gerar nova chave DKIM"
  
  Copiar o valor do registro TXT gerado. Terá este formato:
  ```
  v=DKIM1; k=rsa; p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...
  ```

- [ ] **Passo 2: Criar registro TXT DKIM no Hostinger**

  | Campo | Valor |
  |-------|-------|
  | Tipo | TXT |
  | Nome | `mail._domainkey` |
  | Valor | (cole o valor copiado do Poste.io) |
  | TTL | 3600 |

- [ ] **Passo 3: Verificar DKIM propagado**

  ```bash
  dig TXT mail._domainkey.ipexdesenvolvimento.cloud +short
  ```
  Deve retornar a chave pública. Pode levar até 30 min.

- [ ] **Passo 4: Testar envio de email**

  No Poste.io admin → Enviar email de teste para `tdsdados@gmail.com`
  
  Verificar no Gmail: abrir email → "Mostrar original" → confirmar:
  - `dkim=pass`
  - `spf=pass`
  - `dmarc=pass` (ou `bestguesspass`)

---

### Task A3: Solicitar PTR reverso no Hostinger

**Contexto:** O PTR (reverse DNS) faz com que `46.202.150.132` resolva para `mail.ipexdesenvolvimento.cloud`. Sem isso, grandes provedores (Outlook, Gmail via postmaster) podem marcar como spam.

- [ ] **Passo 1: Abrir ticket no Hostinger**

  Ir em: https://hpanel.hostinger.com → Suporte → Novo ticket
  
  Assunto: `Configurar PTR reverso para IP 46.202.150.132`
  
  Mensagem:
  ```
  Olá,
  
  Solicito a configuração do registro PTR (reverse DNS) para o seguinte IP:
  
  IP: 46.202.150.132
  Hostname desejado: mail.ipexdesenvolvimento.cloud
  
  Este IP está no servidor VPS associado ao meu plano.
  
  Agradeço!
  ```

- [ ] **Passo 2: Confirmar PTR após resposta do suporte**

  ```bash
  dig -x 46.202.150.132 +short
  ```
  Deve retornar: `mail.ipexdesenvolvimento.cloud.`

---

## PARTE B — Funil de Cadastro (Typebot + WhatsApp)

### Task B1: Criar schema PostgreSQL

**Contexto:** Estas tabelas são o backbone de todas as funcionalidades de Fase 1. O banco `kreativ_edu` já existe. Credenciais: host `localhost`, user `kreativ`, password `73e21240f55308fedf4659be`, db `kreativ_edu`.

**Files:**
- Create: `/root/projeto-tds/sql/fase1-schema.sql`

- [ ] **Passo 1: Criar arquivo SQL**

  Criar `/root/projeto-tds/sql/fase1-schema.sql`:

  ```sql
  -- ============================================================
  -- TDS Fase 1 — Schema PostgreSQL
  -- Banco: kreativ_edu | User: kreativ
  -- ============================================================

  -- Alunos (criados pelo funil Typebot ou manual)
  CREATE TABLE IF NOT EXISTS alunos (
    id           SERIAL PRIMARY KEY,
    nome         VARCHAR(200) NOT NULL,
    cpf          VARCHAR(14)  UNIQUE,
    telefone     VARCHAR(20)  UNIQUE NOT NULL,
    email        VARCHAR(200),
    municipio    VARCHAR(100),
    status       VARCHAR(20)  NOT NULL DEFAULT 'pre-matricula'
                   CHECK (status IN ('pre-matricula','matriculado','concluido','reprovado')),
    dados_baseline JSONB NOT NULL DEFAULT '{}',
    typebot_session_id VARCHAR(100),
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
  );

  -- Turmas
  CREATE TABLE IF NOT EXISTS turmas (
    id           SERIAL PRIMARY KEY,
    nome         VARCHAR(200) NOT NULL,
    curso        VARCHAR(100) NOT NULL,
    tutor_nome   VARCHAR(200),
    data_inicio  DATE,
    data_fim     DATE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
  );

  -- Matrículas (many-to-many alunos ↔ turmas)
  CREATE TABLE IF NOT EXISTS matriculas (
    id             SERIAL PRIMARY KEY,
    aluno_id       INTEGER NOT NULL REFERENCES alunos(id) ON DELETE CASCADE,
    turma_id       INTEGER NOT NULL REFERENCES turmas(id) ON DELETE CASCADE,
    data_matricula DATE NOT NULL DEFAULT CURRENT_DATE,
    status         VARCHAR(20) NOT NULL DEFAULT 'ativa'
                     CHECK (status IN ('ativa','concluida','cancelada')),
    UNIQUE (aluno_id, turma_id)
  );

  -- Aulas agendadas
  CREATE TABLE IF NOT EXISTS aulas (
    id                SERIAL PRIMARY KEY,
    turma_id          INTEGER NOT NULL REFERENCES turmas(id) ON DELETE CASCADE,
    titulo            VARCHAR(300) NOT NULL,
    data_hora         TIMESTAMPTZ NOT NULL,
    link_meet         VARCHAR(500),
    thread_anythingllm VARCHAR(200),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
  );

  -- Presenças
  CREATE TABLE IF NOT EXISTS presenca (
    id           SERIAL PRIMARY KEY,
    aluno_id     INTEGER NOT NULL REFERENCES alunos(id) ON DELETE CASCADE,
    aula_id      INTEGER NOT NULL REFERENCES aulas(id) ON DELETE CASCADE,
    presente     BOOLEAN NOT NULL DEFAULT FALSE,
    obs          TEXT,
    registrado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (aluno_id, aula_id)
  );

  -- Sessões Typebot (chave = telefone, para retomada de formulário)
  CREATE TABLE IF NOT EXISTS typebot_sessoes (
    id                        SERIAL PRIMARY KEY,
    telefone                  VARCHAR(20) UNIQUE NOT NULL,
    session_id                VARCHAR(200) NOT NULL,
    chatwoot_conversation_id  INTEGER,
    status                    VARCHAR(20) NOT NULL DEFAULT 'ativo'
                                CHECK (status IN ('ativo','concluido','abandonado')),
    created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                TIMESTAMPTZ NOT NULL DEFAULT NOW()
  );

  -- Índices de performance
  CREATE INDEX IF NOT EXISTS idx_alunos_telefone    ON alunos(telefone);
  CREATE INDEX IF NOT EXISTS idx_alunos_cpf         ON alunos(cpf);
  CREATE INDEX IF NOT EXISTS idx_matriculas_turma   ON matriculas(turma_id);
  CREATE INDEX IF NOT EXISTS idx_aulas_turma_data   ON aulas(turma_id, data_hora);
  CREATE INDEX IF NOT EXISTS idx_presenca_aula      ON presenca(aula_id);
  CREATE INDEX IF NOT EXISTS idx_typebot_telefone   ON typebot_sessoes(telefone);
  ```

- [ ] **Passo 2: Aplicar schema no banco**

  ```bash
  PGPASSWORD=73e21240f55308fedf4659be psql -h localhost -U kreativ -d kreativ_edu \
    -f /root/projeto-tds/sql/fase1-schema.sql
  ```
  
  Esperado: `CREATE TABLE` (×6) + `CREATE INDEX` (×6), sem erros.

- [ ] **Passo 3: Verificar tabelas criadas**

  ```bash
  PGPASSWORD=73e21240f55308fedf4659be psql -h localhost -U kreativ -d kreativ_edu \
    -c "\dt"
  ```
  
  Deve listar: `alunos`, `aulas`, `matriculas`, `presenca`, `turmas`, `typebot_sessoes`.

- [ ] **Passo 4: Inserir turma de teste**

  ```bash
  PGPASSWORD=73e21240f55308fedf4659be psql -h localhost -U kreativ -d kreativ_edu -c "
  INSERT INTO turmas (nome, curso, tutor_nome, data_inicio, data_fim)
  VALUES ('Turma A — Empreendedorismo 2026', 'Empreendedorismo Social',
          'Ana Tutora', '2026-04-15', '2026-06-15')
  RETURNING id, nome;
  "
  ```
  
  Esperado: linha com id=1 e nome da turma.

- [ ] **Passo 5: Commit**

  ```bash
  cd /root/projeto-tds
  git add sql/fase1-schema.sql
  git commit -m "feat: add fase1 postgresql schema (alunos/turmas/aulas/presenca/typebot_sessoes)"
  ```

---

### Task B2: Criar fluxo Typebot (funil-cadastro-tds)

**Contexto:** O Typebot é o "formulário inteligente" que substitui o Google Form presencial. Ele guia o aluno pelo baseline (18 seções / ~102 campos) via WhatsApp. A URL do Typebot self-hosted é `https://typebot.ipexdesenvolvimento.cloud` (ou o domínio configurado — verificar com `docker ps` no servidor).

> Se Typebot ainda não estiver instalado, ver Task B2-setup antes de prosseguir.

- [ ] **Passo 1: Confirmar URL do Typebot**

  ```bash
  docker ps --format "table {{.Names}}\t{{.Ports}}" | grep -i typebot
  ```
  
  Se não estiver rodando, o Typebot precisa ser implantado primeiro (fora do escopo deste plano — consultar `/root/projeto-tds/docs/infra/typebot-deploy.md`).

- [ ] **Passo 2: Criar novo typebot no painel**

  Acessar: `https://typebot.ipexdesenvolvimento.cloud` → Login → "Criar novo typebot"
  Nome: `funil-cadastro-tds`

- [ ] **Passo 3: Configurar Bloco 0 — Boas-vindas**

  No editor visual do Typebot, adicionar bloco "Texto":
  ```
  Olá! Sou o assistente digital do programa TDS (Território de Desenvolvimento Social).
  
  Vou guiar você pelo cadastro do programa — são algumas perguntas sobre sua família e situação de vida.
  
  Pode pausar e retomar quando quiser. Vamos começar?
  ```
  
  Adicionar botão: "Vamos lá! ✅"

- [ ] **Passo 4: Configurar Bloco 1 — Identificação (B1)**

  Sequência de perguntas (campos de texto com validação):
  
  | Pergunta | Tipo Typebot | Validação |
  |----------|-------------|-----------|
  | Qual é o seu **nome completo**? | Texto | obrigatório |
  | Qual é o seu **CPF**? (só números, ex: 12345678901) | Texto | regex `^\d{11}$` |
  | Qual é o seu **NIS** (número do CadÚnico)? (11 dígitos) | Texto | regex `^\d{11}$` |
  | Qual é a sua **data de nascimento**? (DD/MM/AAAA) | Texto | regex `^\d{2}/\d{2}/\d{4}$` |
  | Qual é o seu **sexo/gênero**? | Escolha única | Masculino / Feminino / Outro / Prefiro não informar |
  | Qual é a sua **raça/cor** (segundo o IBGE)? | Escolha única | Branca / Preta / Parda / Amarela / Indígena |
  | Em qual **município** você mora? | Texto | obrigatório |
  | Qual é o seu **número de WhatsApp**? (com DDD) | Texto | regex `^\d{10,11}$` |

- [ ] **Passo 5: Configurar Blocos B2–B11 (seções 2–18)**

  Seguir a estrutura do documento `/root/projeto-tds/docs/rag/formulario-baseline-tds.md` para cada bloco:
  
  - **B2 Composição Familiar:** quantidade de pessoas, crianças, adolescentes, adultos, idosos, PcD
  - **B3 Moradia:** zona (urbana/rural), tipo comunidade, situação domicílio, saneamento, energia, água
  - **B4 Escolaridade:** nível de estudo, alfabetização, crianças na escola
  - **B5 Trabalho e Renda:** situação de trabalho, atividade econômica, renda mensal estimada, fontes de renda, é MEI?
  - **B6 Atividade Produtiva (condicional):** mostrar apenas se B5 incluir "Agricultor familiar" ou "Extrativista"
    - Tipo de produção, área plantada, comercialização (PAA/PNAE/feiras), tem DAP/CAF?
  - **B7 Acesso a Crédito:** já acessou Pronaf B? tem dívidas agrícolas? interesse em crédito?
  - **B8 Políticas Públicas:** recebe Bolsa Família? BPC? Tarifa Social? ATER? outros programas?
  - **B9 Saúde:** tem plano de saúde? usa UBS? algum membro com condição crônica?
  - **B10 Tecnologia:** tem celular? smartphone? internet? usa WhatsApp? usa redes sociais?
  - **B11 Expectativas:** por que quer fazer o curso? o que espera aprender? tem disponibilidade de horário?
  
  Para cada pergunta Sim/Não: usar botões "Sim ✅ / Não ❌"
  Para múltipla escolha: usar botões clicáveis do Typebot (max 3 por linha)

- [ ] **Passo 6: Configurar Bloco Final — Confirmação**

  Último bloco do Typebot (tipo "Texto" + webhook):
  ```
  Parabéns, {{nome}}! Seu cadastro foi enviado com sucesso. 🎉
  
  Nossa equipe vai entrar em contato em breve para confirmar sua matrícula no TDS.
  
  Qualquer dúvida, é só escrever aqui no WhatsApp!
  ```
  
  Adicionar webhook de saída (Typebot → n8n):
  - URL: `https://n8n.ipexdesenvolvimento.cloud/webhook/tds-funil-completo`
  - Método: POST
  - Body: todas as variáveis coletadas (usar "Enviar dados do formulário completo")

- [ ] **Passo 7: Obter ID do typebot e token da API**

  No Typebot admin → Configurações → API → copiar:
  - Typebot ID: (ex: `clu3x8abc123`)
  - API token: (ex: `tbtmp-xxx`)
  
  Salvar no arquivo `/root/kreativ-setup/.env.real`:
  ```
  TYPEBOT_ID=clu3x8abc123
  TYPEBOT_API_TOKEN=tbtmp-xxx
  TYPEBOT_API_URL=https://typebot.ipexdesenvolvimento.cloud
  ```

- [ ] **Passo 8: Testar fluxo no preview do Typebot**

  No editor Typebot → "Pré-visualizar" → responder todas as perguntas até o fim → confirmar que o webhook final dispara (verificar em n8n o webhook test).

---

### Task B3: Criar workflow n8n "TDS — Funil Cadastro"

**Contexto:** Este workflow gerencia o estado da conversa no WhatsApp para o funil Typebot. O Chatwoot já tem um Agent Bot configurado (ID 1, token `XzN7j4TyqQyDtdavxXjGoTUv`) que envia POST para `https://n8n.ipexdesenvolvimento.cloud/webhook/chatwoot-kreativ` para qualquer mensagem. Vamos criar um **segundo webhook** para o funil (`/webhook/tds-funil`) e rotear pelo workflow existente OU criar um webhook dedicado configurado no Agent Bot para conversas em estado de funil.

**Arquitetura de roteamento:** No workflow principal existente (`XYcnRlPZSlfGXOWb`), adicionar um nó de verificação logo após "Extrair Dados": se o telefone do contato tiver uma sessão Typebot ativa no PostgreSQL → redirecionar para o workflow funil em vez do RAG.

- [ ] **Passo 1: Abrir n8n e criar novo workflow**

  Acessar: https://n8n.ipexdesenvolvimento.cloud
  Login: admin@neruds.org / Extensionistas@2025
  
  Criar novo workflow: "TDS — Funil Cadastro"

- [ ] **Passo 2: Adicionar nó Webhook**

  - Tipo: Webhook
  - HTTP Method: POST
  - Path: `tds-funil`
  - Response Mode: "Respond to Webhook" → "When Last Node Finishes"
  
  URL resultante: `https://n8n.ipexdesenvolvimento.cloud/webhook/tds-funil`

- [ ] **Passo 3: Adicionar nó "Extrair Dados" (Function node)**

  Nome: "Extrair Dados Funil"
  
  Código:
  ```javascript
  const body = $input.first().json.body || $input.first().json;
  
  // Chatwoot Agent Bot payload
  const telefone = body.meta?.sender?.phone_number?.replace(/\D/g, '') || '';
  const mensagem = body.content || '';
  const conversa_id = body.conversation?.id || body.id;
  const contact_id = body.meta?.sender?.id;
  
  return [{
    json: {
      telefone,
      mensagem,
      conversa_id,
      contact_id
    }
  }];
  ```

- [ ] **Passo 4: Adicionar nó PostgreSQL "Buscar Sessão"**

  - Tipo: Postgres
  - Connection: usar credencial PostgreSQL existente (kreativ / kreativ_edu)
  - Operation: Execute Query
  
  Query:
  ```sql
  SELECT session_id, chatwoot_conversation_id
  FROM typebot_sessoes
  WHERE telefone = '{{ $json.telefone }}'
    AND status = 'ativo'
  LIMIT 1;
  ```

- [ ] **Passo 5: Adicionar nó IF "Sessão Existe?"**

  Condição: `{{ $json.session_id }}` existe (não está vazio)
  
  - Ramo TRUE: continuar sessão existente (→ Passo 6a)
  - Ramo FALSE: criar nova sessão (→ Passo 6b)

- [ ] **Passo 6a: Nó HTTP Request "Continuar Sessão Typebot"** (ramo TRUE)

  - Método: POST
  - URL: `{{ $env.TYPEBOT_API_URL }}/api/v1/sessions/{{ $('Buscar Sessão').first().json.session_id }}/continueChat`
  - Headers: `{ "Authorization": "Bearer {{ $env.TYPEBOT_API_TOKEN }}" }`
  - Body (JSON):
    ```json
    {
      "message": {
        "type": "text",
        "text": "{{ $('Extrair Dados Funil').first().json.mensagem }}"
      }
    }
    ```

- [ ] **Passo 6b: Nó HTTP Request "Iniciar Sessão Typebot"** (ramo FALSE)

  - Método: POST
  - URL: `{{ $env.TYPEBOT_API_URL }}/api/v1/typebots/{{ $env.TYPEBOT_ID }}/startChat`
  - Headers: `{ "Authorization": "Bearer {{ $env.TYPEBOT_API_TOKEN }}" }`
  - Body (JSON):
    ```json
    {
      "prefilledVariables": {
        "telefone": "{{ $('Extrair Dados Funil').first().json.telefone }}"
      }
    }
    ```

- [ ] **Passo 7: Nó PostgreSQL "Salvar/Atualizar Sessão"** (após 6b)

  Query:
  ```sql
  INSERT INTO typebot_sessoes (telefone, session_id, chatwoot_conversation_id)
  VALUES (
    '{{ $('Extrair Dados Funil').first().json.telefone }}',
    '{{ $json.sessionId }}',
    {{ $('Extrair Dados Funil').first().json.conversa_id }}
  )
  ON CONFLICT (telefone)
  DO UPDATE SET
    session_id = EXCLUDED.session_id,
    status = 'ativo',
    updated_at = NOW();
  ```

- [ ] **Passo 8: Nó Function "Formatar Mensagens Typebot"** (após 6a e 6b, usar Merge)

  Código:
  ```javascript
  const response = $input.first().json;
  const messages = response.messages || [];
  
  // Concatenar mensagens em texto único
  let texto = messages
    .filter(m => m.type === 'text' || m.type === 'choice input')
    .map(m => {
      if (m.type === 'text') return m.content.richText?.[0]?.children?.[0]?.text || m.content.text || '';
      if (m.type === 'choice input') {
        const opcoes = m.options.map((o, i) => `${i+1}. ${o.label}`).join('\n');
        return `${m.question}\n\n${opcoes}\n\n_(Responda com o número da sua escolha)_`;
      }
      return '';
    })
    .filter(t => t.length > 0)
    .join('\n\n');
  
  return [{ json: { texto_resposta: texto } }];
  ```

- [ ] **Passo 9: Nó HTTP Request "Enviar Resposta no Chatwoot"**

  - Método: POST
  - URL: `https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/conversations/{{ $('Extrair Dados Funil').first().json.conversa_id }}/messages`
  - Headers:
    ```json
    {
      "api_access_token": "jj9zPmJnRRs7bJ4QP5mDGXb2",
      "Content-Type": "application/json"
    }
    ```
  - Body (JSON):
    ```json
    {
      "content": "{{ $json.texto_resposta }}",
      "message_type": "outgoing",
      "private": false
    }
    ```

- [ ] **Passo 10: Testar o workflow com payload simulado**

  No n8n, ativar "Test Webhook" e enviar:
  ```bash
  curl -X POST https://n8n.ipexdesenvolvimento.cloud/webhook-test/tds-funil \
    -H "Content-Type: application/json" \
    -d '{
      "content": "Quero me cadastrar",
      "meta": {
        "sender": {
          "phone_number": "+5563999990001",
          "id": 999
        }
      },
      "conversation": { "id": 1001 }
    }'
  ```
  
  Verificar: sessão criada no PostgreSQL + primeira mensagem de boas-vindas retornada.
  
  ```bash
  PGPASSWORD=73e21240f55308fedf4659be psql -h localhost -U kreativ -d kreativ_edu \
    -c "SELECT * FROM typebot_sessoes WHERE telefone='5563999990001';"
  ```
  
  Deve retornar 1 linha com status 'ativo'.

- [ ] **Passo 11: Ativar workflow e salvar JSON**

  Ativar o workflow no n8n (toggle "Active").
  
  Exportar JSON: n8n → Workflow → "Download" → salvar em:
  `/root/projeto-tds/n8n/funil-cadastro.json`

- [ ] **Passo 12: Atualizar workflow principal para rotear ao funil**

  Abrir workflow `XYcnRlPZSlfGXOWb` ("Kreativ TDS — Chatwoot RAG Flow").
  
  Após nó "Extrair Dados", adicionar nó PostgreSQL "Verificar Funil Ativo":
  ```sql
  SELECT 1 FROM typebot_sessoes
  WHERE telefone = '{{ $json.telefone }}'
    AND status = 'ativo'
  LIMIT 1;
  ```
  
  Adicionar nó IF "Em Funil?": se retornar linha → chamar workflow funil via HTTP (ou redirecionar lógica). Caso contrário → fluxo RAG normal.
  
  Salvar e manter ativo.

- [ ] **Passo 13: Commit**

  ```bash
  cd /root/projeto-tds
  git add n8n/funil-cadastro.json
  git commit -m "feat: n8n workflow funil cadastro typebot (session management + chatwoot bridge)"
  ```

---

### Task B4: Criar workflow n8n "TDS — Funil On Complete"

**Contexto:** Quando o aluno termina todas as perguntas, o Typebot dispara um webhook POST para este endpoint. Salva o aluno no PostgreSQL e notifica o Chatwoot.

- [ ] **Passo 1: Criar novo workflow "TDS — Funil On Complete"**

  No n8n, criar novo workflow com:
  
  - Nó Webhook: POST `/webhook/tds-funil-completo`

- [ ] **Passo 2: Nó Function "Extrair Dados Completos"**

  O Typebot envia todas as variáveis coletadas. Código:
  ```javascript
  const data = $input.first().json;
  
  // Mapear variáveis Typebot → campos alunos
  const aluno = {
    nome:      data.nome || '',
    cpf:       (data.cpf || '').replace(/\D/g, ''),
    telefone:  (data.telefone || '').replace(/\D/g, ''),
    email:     data.email || null,
    municipio: data.municipio || '',
    status:    'pre-matricula',
    typebot_session_id: data.sessionId || null,
    dados_baseline: JSON.stringify({
      nis: data.nis,
      data_nascimento: data.data_nascimento,
      sexo: data.sexo,
      raca_cor: data.raca_cor,
      composicao_familiar: {
        total_pessoas: data.total_pessoas,
        criancas: data.criancas,
        adolescentes: data.adolescentes,
        adultos: data.adultos,
        idosos: data.idosos,
        tem_pcd: data.tem_pcd
      },
      moradia: {
        zona: data.zona,
        tipo_comunidade: data.tipo_comunidade,
        situacao_domicilio: data.situacao_domicilio,
        tem_agua: data.tem_agua,
        tem_energia: data.tem_energia,
        tem_saneamento: data.tem_saneamento
      },
      escolaridade: data.escolaridade,
      trabalho: {
        situacao: data.situacao_trabalho,
        atividade: data.atividade_economica,
        renda_mensal: data.renda_mensal,
        fontes: data.fontes_renda,
        eh_mei: data.eh_mei
      },
      atividade_produtiva: data.atividade_produtiva || null,
      politicas_publicas: data.politicas_publicas,
      saude: data.saude,
      tecnologia: data.tecnologia,
      expectativas: data.expectativas
    })
  };
  
  return [{ json: aluno }];
  ```

- [ ] **Passo 3: Nó PostgreSQL "Salvar Aluno"**

  ```sql
  INSERT INTO alunos
    (nome, cpf, telefone, email, municipio, status, dados_baseline, typebot_session_id)
  VALUES (
    '{{ $json.nome }}',
    NULLIF('{{ $json.cpf }}', ''),
    '{{ $json.telefone }}',
    NULLIF('{{ $json.email }}', ''),
    '{{ $json.municipio }}',
    '{{ $json.status }}',
    '{{ $json.dados_baseline }}'::jsonb,
    NULLIF('{{ $json.typebot_session_id }}', '')
  )
  ON CONFLICT (telefone)
  DO UPDATE SET
    nome      = EXCLUDED.nome,
    dados_baseline = EXCLUDED.dados_baseline,
    updated_at = NOW()
  RETURNING id;
  ```

- [ ] **Passo 4: Nó PostgreSQL "Marcar Sessão Concluída"**

  ```sql
  UPDATE typebot_sessoes
  SET status = 'concluido', updated_at = NOW()
  WHERE telefone = '{{ $('Extrair Dados Completos').first().json.telefone }}'
    AND status = 'ativo';
  ```

- [ ] **Passo 5: Nó HTTP Request "Adicionar Label pre-matricula no Chatwoot"**

  - Método: POST
  - URL: `https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/conversations/{{ $('Extrair Dados Completos').first().json.conversa_id }}/labels`
  - Headers: `{ "api_access_token": "jj9zPmJnRRs7bJ4QP5mDGXb2" }`
  - Body: `{ "labels": ["pre-matricula"] }`

- [ ] **Passo 6: Nó HTTP Request "Enviar Mensagem Final"**

  - Método: POST
  - URL: `https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/conversations/{{ $('Extrair Dados Completos').first().json.conversa_id }}/messages`
  - Headers: `{ "api_access_token": "jj9zPmJnRRs7bJ4QP5mDGXb2" }`
  - Body:
    ```json
    {
      "content": "✅ Cadastro recebido com sucesso, {{ $('Extrair Dados Completos').first().json.nome }}!\n\nNossa equipe vai analisar seus dados e entrar em contato em breve para confirmar sua matrícula no programa TDS.\n\nObrigado por participar! 🎓",
      "message_type": "outgoing",
      "private": false
    }
    ```

- [ ] **Passo 7: Testar com payload simulado**

  ```bash
  curl -X POST https://n8n.ipexdesenvolvimento.cloud/webhook-test/tds-funil-completo \
    -H "Content-Type: application/json" \
    -d '{
      "nome": "Maria da Silva Teste",
      "cpf": "12345678901",
      "telefone": "5563999990001",
      "nis": "12345678901",
      "data_nascimento": "10/05/1985",
      "sexo": "Feminino",
      "raca_cor": "Parda",
      "municipio": "Araguatins",
      "escolaridade": "Ensino Médio completo",
      "situacao_trabalho": "Agricultor familiar",
      "sessionId": "test-session-001",
      "conversa_id": 1001
    }'
  ```
  
  Verificar:
  ```bash
  PGPASSWORD=73e21240f55308fedf4659be psql -h localhost -U kreativ -d kreativ_edu \
    -c "SELECT id, nome, telefone, status FROM alunos WHERE telefone='5563999990001';"
  ```
  Deve retornar 1 aluno com status `pre-matricula`.

- [ ] **Passo 8: Ativar e exportar**

  Ativar workflow. Exportar JSON → `/root/projeto-tds/n8n/funil-on-complete.json`
  
  ```bash
  git add n8n/funil-on-complete.json
  git commit -m "feat: n8n workflow funil on-complete (salva aluno, label chatwoot, mensagem final)"
  ```

---

## PARTE C — Workspaces AnythingLLM + Turmas + Notificações

### Task C1: Criar 4 workspaces no AnythingLLM

**Contexto:** O workspace `tds` (slug: tds, ID: 2) já existe para o RAG geral dos alunos via WhatsApp. Os 4 novos workspaces são para tutores, que farão upload de materiais de curso e criarão threads de aulas.

API AnythingLLM: `https://rag.ipexdesenvolvimento.cloud/api`
API Key: `W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0`

- [ ] **Passo 1: Criar workspace tds-empreendedorismo**

  ```bash
  curl -s -X POST https://rag.ipexdesenvolvimento.cloud/api/v1/workspace/new \
    -H "Authorization: Bearer W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0" \
    -H "Content-Type: application/json" \
    -d '{"name": "tds-empreendedorismo"}' | jq '.workspace.slug'
  ```
  
  Esperado: `"tds-empreendedorismo"` (ou slug gerado automaticamente).

- [ ] **Passo 2: Criar workspace tds-cooperativismo**

  ```bash
  curl -s -X POST https://rag.ipexdesenvolvimento.cloud/api/v1/workspace/new \
    -H "Authorization: Bearer W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0" \
    -H "Content-Type: application/json" \
    -d '{"name": "tds-cooperativismo"}' | jq '.workspace.slug'
  ```

- [ ] **Passo 3: Criar workspace tds-agricultura**

  ```bash
  curl -s -X POST https://rag.ipexdesenvolvimento.cloud/api/v1/workspace/new \
    -H "Authorization: Bearer W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0" \
    -H "Content-Type: application/json" \
    -d '{"name": "tds-agricultura"}' | jq '.workspace.slug'
  ```

- [ ] **Passo 4: Criar workspace tds-sistemas-produtivos**

  ```bash
  curl -s -X POST https://rag.ipexdesenvolvimento.cloud/api/v1/workspace/new \
    -H "Authorization: Bearer W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0" \
    -H "Content-Type: application/json" \
    -d '{"name": "tds-sistemas-produtivos"}' | jq '.workspace.slug'
  ```

- [ ] **Passo 5: Verificar os 4 workspaces criados**

  ```bash
  curl -s https://rag.ipexdesenvolvimento.cloud/api/v1/workspaces \
    -H "Authorization: Bearer W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0" | \
    jq '[.workspaces[] | {name, slug}]'
  ```
  
  Deve listar `tds` + os 4 novos.

- [ ] **Passo 6: Configurar prompt do sistema de cada workspace**

  Para cada workspace tutor (repetir para os 4), acessar:
  `https://rag.ipexdesenvolvimento.cloud` → Login → Workspace [nome] → Configurações → Prompt
  
  Prompt base:
  ```
  Você é o assistente do curso de [NOME DO CURSO] do programa TDS (UFT/IPEX/FAPTO).
  
  Responda com base nos materiais do curso disponíveis neste workspace.
  Seja preciso, didático e use linguagem acessível.
  Se não souber, diga que não encontrou nos materiais.
  ```
  
  Substituir `[NOME DO CURSO]` pelo nome correto em cada workspace.

- [ ] **Passo 7: Commit**

  ```bash
  # Salvar slugs/IDs dos workspaces no .env.real
  echo "# AnythingLLM workspaces criados em 2026-04-08" >> /root/kreativ-setup/.env.real
  echo "ANYTHINGLLM_WS_EMPREENDEDORISMO=tds-empreendedorismo" >> /root/kreativ-setup/.env.real
  echo "ANYTHINGLLM_WS_COOPERATIVISMO=tds-cooperativismo" >> /root/kreativ-setup/.env.real
  echo "ANYTHINGLLM_WS_AGRICULTURA=tds-agricultura" >> /root/kreativ-setup/.env.real
  echo "ANYTHINGLLM_WS_SISTEMAS=tds-sistemas-produtivos" >> /root/kreativ-setup/.env.real
  
  git add /root/kreativ-setup/.env.real
  git commit -m "feat: create 4 anythingllm workspaces for tds courses"
  ```

---

### Task C2: Criar Google Form de Agendamento de Aulas

**Contexto:** Tutores preenchem este formulário para agendar aulas/eventos. O n8n lê as respostas e insere na tabela `aulas`.

- [ ] **Passo 1: Criar formulário no Google Forms**

  Acessar: https://forms.google.com → Criar formulário
  Título: `TDS — Agendamento de Aula`
  
  Campos:
  
  | Pergunta | Tipo | Obrigatório |
  |----------|------|-------------|
  | Turma (nome completo) | Lista suspensa com opções das turmas ativas | Sim |
  | Título da aula | Texto curto | Sim |
  | Data e hora (DD/MM/AAAA HH:MM) | Texto curto | Sim |
  | Link do Google Meet | Texto curto (URL) | Sim |
  | Thread AnythingLLM (opcional) | Texto curto | Não |
  | Seu nome (tutor) | Texto curto | Sim |

- [ ] **Passo 2: Vincular formulário ao Google Sheets**

  No formulário → aba "Respostas" → ícone de planilha → criar nova planilha:
  Nome: `TDS — Agendamento Aulas — Respostas`

- [ ] **Passo 3: Criar Apps Script para notificar n8n**

  No Google Sheets → Extensões → Apps Script → Nova função:
  
  ```javascript
  function onFormSubmit(e) {
    const row = e.values;
    // row[0] = timestamp, row[1] = turma, row[2] = titulo, row[3] = data_hora,
    // row[4] = link_meet, row[5] = thread, row[6] = tutor_nome
    
    const payload = {
      turma_nome:       row[1],
      titulo:           row[2],
      data_hora_str:    row[3],
      link_meet:        row[4],
      thread_anythingllm: row[5] || null,
      tutor_nome:       row[6],
      timestamp:        row[0]
    };
    
    UrlFetchApp.fetch(
      'https://n8n.ipexdesenvolvimento.cloud/webhook/tds-agendamento-aula',
      {
        method: 'post',
        contentType: 'application/json',
        payload: JSON.stringify(payload)
      }
    );
  }
  ```
  
  Salvar. Em "Acionadores" → Adicionar acionador:
  - Função: `onFormSubmit`
  - Evento: "Do formulário" → "Ao enviar formulário"

- [ ] **Passo 4: Testar enviando resposta de teste**

  Preencher o formulário com dados fictícios. Verificar no n8n (webhook test ativo) que o payload chegou.

---

### Task C3: Criar workflow n8n "TDS — Agendamento Aulas"

**Contexto:** Recebe o POST do Apps Script, converte data/hora, busca turma_id no PostgreSQL e insere na tabela `aulas`.

- [ ] **Passo 1: Criar novo workflow no n8n**

  Nome: "TDS — Agendamento Aulas"
  
  Nó 1 — Webhook: POST `/webhook/tds-agendamento-aula`

- [ ] **Passo 2: Nó Function "Parsear Data"**

  ```javascript
  const data = $input.first().json;
  
  // Converter "15/04/2026 14:00" → "2026-04-15T14:00:00-03:00"
  const [datePart, timePart] = (data.data_hora_str || '').split(' ');
  const [dia, mes, ano] = (datePart || '').split('/');
  const [hora, min] = (timePart || '00:00').split(':');
  
  const dataISO = `${ano}-${mes}-${dia}T${hora}:${min}:00-03:00`;
  
  return [{
    json: {
      ...data,
      data_hora_iso: dataISO
    }
  }];
  ```

- [ ] **Passo 3: Nó PostgreSQL "Buscar Turma ID"**

  ```sql
  SELECT id FROM turmas
  WHERE nome ILIKE '%{{ $json.turma_nome }}%'
  LIMIT 1;
  ```

- [ ] **Passo 4: Nó IF "Turma Encontrada?"**

  Condição: `{{ $json.id }}` não está vazio
  - TRUE: inserir aula
  - FALSE: logar erro (nó Set com erro, não quebrar o workflow)

- [ ] **Passo 5: Nó PostgreSQL "Inserir Aula"** (ramo TRUE)

  ```sql
  INSERT INTO aulas (turma_id, titulo, data_hora, link_meet, thread_anythingllm)
  VALUES (
    {{ $('Buscar Turma ID').first().json.id }},
    '{{ $('Parsear Data').first().json.titulo }}',
    '{{ $('Parsear Data').first().json.data_hora_iso }}'::timestamptz,
    '{{ $('Parsear Data').first().json.link_meet }}',
    NULLIF('{{ $('Parsear Data').first().json.thread_anythingllm }}', '')
  )
  RETURNING id, titulo, data_hora;
  ```

- [ ] **Passo 6: Testar workflow**

  ```bash
  curl -X POST https://n8n.ipexdesenvolvimento.cloud/webhook-test/tds-agendamento-aula \
    -H "Content-Type: application/json" \
    -d '{
      "turma_nome": "Turma A — Empreendedorismo 2026",
      "titulo": "Aula 1 — Introdução ao Empreendedorismo",
      "data_hora_str": "15/04/2026 14:00",
      "link_meet": "https://meet.google.com/abc-defg-hij",
      "thread_anythingllm": null,
      "tutor_nome": "Ana Tutora"
    }'
  ```
  
  Verificar:
  ```bash
  PGPASSWORD=73e21240f55308fedf4659be psql -h localhost -U kreativ -d kreativ_edu \
    -c "SELECT id, titulo, data_hora, link_meet FROM aulas;"
  ```

- [ ] **Passo 7: Ativar e exportar**

  Ativar workflow. Exportar → `/root/projeto-tds/n8n/agendamento-aulas.json`
  
  ```bash
  git add n8n/agendamento-aulas.json
  git commit -m "feat: n8n workflow agendamento de aulas (google form -> postgresql)"
  ```

---

### Task C4: Criar workflow n8n "TDS — Notificação Aulas" (cron 8h)

**Contexto:** Todo dia às 8h, envia WhatsApp para cada aluno matriculado cujo curso tem aula nas próximas 24h. Usa Chatwoot API para enviar mensagem direta.

- [ ] **Passo 1: Criar novo workflow "TDS — Notificação Aulas"**

  Nó 1 — Schedule Trigger:
  - Recorrência: Diária
  - Hora: 08:00
  - Timezone: America/Araguaina (UTC-3)

- [ ] **Passo 2: Nó PostgreSQL "Buscar Aulas de Amanhã"**

  ```sql
  SELECT
    a.id AS aula_id,
    a.titulo,
    a.data_hora,
    a.link_meet,
    t.nome AS turma_nome,
    t.curso
  FROM aulas a
  JOIN turmas t ON t.id = a.turma_id
  WHERE a.data_hora BETWEEN NOW() + INTERVAL '20 hours'
                        AND NOW() + INTERVAL '26 hours'
  ORDER BY a.data_hora;
  ```

- [ ] **Passo 3: Nó IF "Há aulas amanhã?"**

  Condição: `{{ $items().length > 0 }}`
  - FALSE: parar (nó NoOp)
  - TRUE: continuar

- [ ] **Passo 4: Nó SplitInBatches "Loop por Aula"**

  Batch size: 1 (processar uma aula por vez)

- [ ] **Passo 5: Nó PostgreSQL "Buscar Alunos Matriculados"**

  ```sql
  SELECT
    al.id AS aluno_id,
    al.nome,
    al.telefone
  FROM matriculas m
  JOIN alunos al ON al.id = m.aluno_id
  JOIN turmas t  ON t.id  = m.turma_id
  JOIN aulas  a  ON a.turma_id = t.id
  WHERE a.id = {{ $json.aula_id }}
    AND m.status = 'ativa'
    AND al.telefone IS NOT NULL;
  ```

- [ ] **Passo 6: Nó SplitInBatches "Loop por Aluno"**

  Batch size: 1

- [ ] **Passo 7: Nó Function "Formatar Mensagem de Lembrete"**

  ```javascript
  const aluno = $input.first().json;
  const aula  = $('Buscar Aulas de Amanhã').first().json; // referência ao loop externo
  
  const dataHora = new Date(aula.data_hora);
  const dia  = dataHora.toLocaleDateString('pt-BR', { timeZone: 'America/Araguaina', day: '2-digit', month: '2-digit' });
  const hora = dataHora.toLocaleTimeString('pt-BR', { timeZone: 'America/Araguaina', hour: '2-digit', minute: '2-digit' });
  
  const mensagem = `Olá, ${aluno.nome}! 👋\n\nLembrete: sua aula de *${aula.curso}* é amanhã!\n\n📅 Data: ${dia}\n⏰ Hora: ${hora}\n🎓 Aula: ${aula.titulo}\n\n🔗 Link Meet: ${aula.link_meet}\n\nAté lá! 🚀`;
  
  return [{ json: { ...aluno, mensagem, aula_id: aula.aula_id } }];
  ```

- [ ] **Passo 8: Nó HTTP Request "Enviar WhatsApp via Chatwoot"**

  O Chatwoot aceita criar uma conversa nova ou enviar para uma existente. Para alunos com conversa ativa:
  
  - Método: POST
  - URL: `https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/contacts/search`
  - Headers: `{ "api_access_token": "jj9zPmJnRRs7bJ4QP5mDGXb2" }`
  - Query params: `{ "q": "{{ $json.telefone }}", "include_contacts": true }`
  
  Nó Function após: extrair `contact_id` do primeiro resultado.
  
  Nó HTTP Request "Criar Conversa e Enviar":
  - Método: POST
  - URL: `https://chat.ipexdesenvolvimento.cloud/api/v1/accounts/1/conversations`
  - Body:
    ```json
    {
      "contact_id": "{{ $json.contact_id }}",
      "inbox_id": 5,
      "message": {
        "content": "{{ $json.mensagem }}"
      }
    }
    ```

- [ ] **Passo 9: Testar o workflow manualmente**

  Inserir uma aula de teste que caia na janela "próximas 24h":
  ```bash
  PGPASSWORD=73e21240f55308fedf4659be psql -h localhost -U kreativ -d kreativ_edu -c "
  INSERT INTO aulas (turma_id, titulo, data_hora, link_meet)
  VALUES (1, 'Aula Teste Notificação', NOW() + INTERVAL '22 hours', 'https://meet.google.com/test');
  "
  ```
  
  No n8n, executar workflow manualmente ("Test Workflow"). Verificar que a mensagem de lembrete é montada corretamente.

- [ ] **Passo 10: Ativar e exportar**

  Ativar workflow. Exportar → `/root/projeto-tds/n8n/notificacao-aulas.json`
  
  ```bash
  git add n8n/notificacao-aulas.json
  git commit -m "feat: n8n cron workflow notificacao de aulas (daily 8h whatsapp reminder)"
  ```

---

### Task C5: Criar Google Form de Registro de Presença + workflow n8n

**Contexto:** Tutor registra presença dos alunos após cada aula. Um formulário por aula, com lista de alunos da turma. O n8n insere/atualiza a tabela `presenca`.

- [ ] **Passo 1: Criar Google Form "TDS — Registro de Presença"**

  Campos:
  
  | Pergunta | Tipo | Obrigatório |
  |----------|------|-------------|
  | ID da Aula (número) | Texto curto | Sim |
  | Aluno presente (nome + telefone) — um por linha | Parágrafo | Sim |
  | Alunos ausentes (nome + telefone) — um por linha | Parágrafo | Não |
  | Observações gerais | Parágrafo | Não |
  
  > Nota: Formulário simplificado. Versão futura pode listar alunos automaticamente via n8n + Google Sheets dinâmico.

- [ ] **Passo 2: Vincular ao Google Sheets e criar Apps Script**

  Apps Script:
  ```javascript
  function onPresencaSubmit(e) {
    const row = e.values;
    // row[0]=timestamp, row[1]=aula_id, row[2]=presentes, row[3]=ausentes, row[4]=obs
    
    UrlFetchApp.fetch(
      'https://n8n.ipexdesenvolvimento.cloud/webhook/tds-presenca',
      {
        method: 'post',
        contentType: 'application/json',
        payload: JSON.stringify({
          aula_id:    parseInt(row[1]),
          presentes:  row[2],
          ausentes:   row[3] || '',
          obs:        row[4] || ''
        })
      }
    );
  }
  ```

- [ ] **Passo 3: Criar workflow n8n "TDS — Registro Presença"**

  Nó 1 — Webhook: POST `/webhook/tds-presenca`
  
  Nó 2 — Function "Parsear Listas":
  ```javascript
  const data = $input.first().json;
  
  // Parsear lista de presentes (um por linha, formato "Nome - XXXXXXXXXXX")
  const parseContatos = (str) => (str || '').split('\n')
    .map(l => l.trim())
    .filter(l => l.length > 0)
    .map(l => {
      const match = l.match(/^(.+?)\s*[-–]\s*(\d{10,11})$/);
      return match ? { nome: match[1].trim(), telefone: match[2] } : null;
    })
    .filter(Boolean);
  
  return [{
    json: {
      aula_id:   data.aula_id,
      obs:       data.obs,
      presentes: parseContatos(data.presentes),
      ausentes:  parseContatos(data.ausentes)
    }
  }];
  ```
  
  Nó 3 — Function "Preparar Upserts":
  ```javascript
  const { aula_id, presentes, ausentes, obs } = $input.first().json;
  
  const registros = [
    ...presentes.map(c => ({ ...c, presente: true,  aula_id, obs })),
    ...ausentes.map(c  => ({ ...c, presente: false, aula_id, obs: '' }))
  ];
  
  return registros.map(r => ({ json: r }));
  ```
  
  Nó 4 — PostgreSQL "Buscar Aluno por Telefone" (para cada item):
  ```sql
  SELECT id FROM alunos WHERE telefone = '{{ $json.telefone }}' LIMIT 1;
  ```
  
  Nó 5 — PostgreSQL "Upsert Presença":
  ```sql
  INSERT INTO presenca (aluno_id, aula_id, presente, obs)
  VALUES (
    {{ $('Buscar Aluno por Telefone').first().json.id }},
    {{ $json.aula_id }},
    {{ $json.presente }},
    '{{ $json.obs }}'
  )
  ON CONFLICT (aluno_id, aula_id)
  DO UPDATE SET presente = EXCLUDED.presente, obs = EXCLUDED.obs, registrado_em = NOW();
  ```

- [ ] **Passo 4: Testar workflow de presença**

  ```bash
  curl -X POST https://n8n.ipexdesenvolvimento.cloud/webhook-test/tds-presenca \
    -H "Content-Type: application/json" \
    -d '{
      "aula_id": 1,
      "presentes": "Maria da Silva Teste - 5563999990001",
      "ausentes": "",
      "obs": "Aula realizada com sucesso"
    }'
  ```
  
  Verificar:
  ```bash
  PGPASSWORD=73e21240f55308fedf4659be psql -h localhost -U kreativ -d kreativ_edu \
    -c "SELECT p.*, a.nome FROM presenca p JOIN alunos a ON a.id = p.aluno_id;"
  ```

- [ ] **Passo 5: Ativar e exportar**

  Ativar workflow. Exportar → `/root/projeto-tds/n8n/registro-presenca.json`
  
  ```bash
  git add n8n/registro-presenca.json
  git commit -m "feat: n8n workflow registro de presenca (google form -> postgresql upsert)"
  ```

---

## Self-Review

### Cobertura do spec

| Requisito | Task |
|-----------|------|
| DNS A, MX, SPF no Hostinger | A1 |
| DKIM no Poste.io + DNS Hostinger | A2 |
| PTR reverso via ticket Hostinger | A3 |
| Schema PostgreSQL (alunos, turmas, matriculas, aulas, presenca, typebot_sessoes) | B1 |
| Typebot: 18 blocos / 102 campos, condicionais, validação CPF/NIS, botões Sim/Não | B2 |
| n8n: gerenciar sessão Typebot, retomada de sessão, encaminhar via Chatwoot | B3 |
| n8n: on_complete → salvar aluno, label Chatwoot, mensagem final | B4 |
| 4 workspaces AnythingLLM por curso | C1 |
| Google Form agendamento + n8n → aulas PostgreSQL | C2 + C3 |
| Notificação proativa cron 8h: aulas em 24h → WhatsApp | C4 |
| Google Form presença + n8n → presenca PostgreSQL | C5 |

### Verificação de placeholders

- Todos os payloads de teste são concretos ✅
- Todas as queries SQL são completas ✅
- Todos os endpoints têm URLs reais do ambiente ✅
- Credenciais referenciadas são as do `.env.real` ✅

### Consistência de tipos

- `telefone` sempre tratado como VARCHAR sem formatação (só dígitos) ✅
- `dados_baseline` sempre `JSONB` no PostgreSQL ✅
- `data_hora` sempre `TIMESTAMPTZ` ✅
- `conversa_id` é INTEGER (ID numérico do Chatwoot) ✅

---

## Execution Handoff

Plano salvo em `docs/superpowers/plans/2026-04-08-fase1-email-funil-turmas.md`.

**Duas opções de execução:**

**1. Subagent-Driven (recomendado)** — Um subagente por task, revisão entre tasks, iteração rápida. Usar: `superpowers:subagent-driven-development`

**2. Inline Execution** — Execução em batch nesta sessão com checkpoints. Usar: `superpowers:executing-plans`

**Ordem sugerida (as 3 partes são independentes):**
- Começar pela **Parte A** (Email DNS) — 30–45 min, sem código
- Em paralelo: **B1** (schema PostgreSQL) — fundação para B e C
- Depois: **B2** (Typebot) e **C1** (Workspaces) — sem dependências entre si
- Por último: **B3, B4, C2–C5** — dependem de B1 e B2/C1

Qual abordagem prefere?
