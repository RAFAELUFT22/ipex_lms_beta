# TDS — Produção WhatsApp, Catraca Pedagógica e Infraestrutura Operacional

**Data:** 2026-04-09
**Aprovado por:** Rafael Luciano (admin@neruds.org)
**Contexto:** Sistema TDS em produção — `https://lms.ipexdesenvolvimento.cloud` / `https://chat.ipexdesenvolvimento.cloud`
**Abordagem:** A — "Freeze & Ship" (entregar sem reescrever Frappe)

---

## 1. Estratégia Frappe — Congelar e Estabilizar

### Decisão
Frappe LMS é congelado como infraestrutura de cursos. Nenhuma customização adicional além do kreativ_theme já existente. ERPNext está instalado e causa erro 500 em `/insights` — **não desinstalar** (risco de quebrar migrations). Solução: esconder o link do menu via CSS no kreativ_theme (1 regra CSS).

### O que o Frappe faz
- Hospedar os 7 cursos + 6 turmas TDS
- Manter perfis TDS Aluno (doctype com 124 campos)
- Receber cadastros via API REST (N8N → `POST /api/resource/TDS Aluno`)
- Servir `/lms/courses`, `/lms/batches`

### O que o Frappe não faz mais
- Home page institucional
- Páginas de instrução/guia
- Qualquer nova customização de tema

### Fix /insights
```css
/* kreativ_theme/public/css/custom.css */
a[href*="/insights"] { display: none !important; }
```

---

## 2. WhatsApp Cloud — Ativar Produção (Inbox 5)

### Estado atual
- Inbox 5 "Whatsapp - TDS": `phone_number: +351932439344`
- `provider: whatsapp_cloud` ✅
- `phone_number_id: 950152194854331` ✅
- `business_account_id: 2715233965500601` ✅
- `reauthorization_required: false` ✅
- Agent Bot "Tutor IA" (ID: 1) conectado ✅
- Callback webhook: `https://chat.ipexdesenvolvimento.cloud/webhooks/whatsapp/+351932439344`

### O que falta
1. **Verificar webhook no Meta Business Manager** — confirmar que o URL de callback está registrado e verificado no painel Meta
2. **Modo produção Meta** — número deve estar fora do sandbox (pode receber mensagens de qualquer pessoa, não apenas testadores aprovados)
3. **Filtro inbox no N8N** — adicionar nó IF no início do workflow principal para processar apenas mensagens da inbox 5 em produção; inbox 1 (Channel::Api) permanece como sandbox de testes

### Fluxo de verificação
```
Testar: enviar mensagem para +351932439344 de número não cadastrado como testador
→ Se Chatwoot recebe → produção OK
→ Se não recebe → verificar Meta Business Manager > WhatsApp > Configuração > Webhooks
```

---

## 3. SISEC via Google Form → N8N → Frappe

### Racional
SISEC (formulário MDS obrigatório, ~40 campos) substituirá o formulário papel. Estagiários preenchem o Google Form durante atendimento presencial. N8N recebe via Apps Script webhook e cria registro TDS Aluno no Frappe.

### Fluxo completo
```
Estagiário preenche Google Form SISEC
    → Google Sheets (destino automático do Form)
        → Apps Script: onFormSubmit → POST webhook N8N
            → N8N: mapeia campos → payload TDS Aluno
                → POST /api/resource/TDS Aluno (Frappe REST API)
                    → TDS Aluno criado (campos SISEC preenchidos)
                        → N8N: inicia conversa no Chatwoot (inbox 5)
                            → WhatsApp: "Olá [nome], sua inscrição no [curso] foi recebida! ..."
```

### Mapeamento de campos SISEC → TDS Aluno

| Campo SISEC | Campo TDS Aluno | Tipo |
|---|---|---|
| Nome Completo | `full_name` | Data |
| CPF | `cpf` | Data |
| Data de Nascimento | `data_de_nascimento` | Date |
| Mais de 60 anos | `mais_de_60_anos` | Check |
| Gênero | `genero` | Select |
| Étnico Racial | `etnia` | Select |
| Naturalidade | `naturalidade` | Data |
| Telefone/Celular | `whatsapp` | Data (chave identidade) |
| E-mail | `email` | Data |
| Endereço | `endereco` | Data |
| Número | `numero_endereco` | Data |
| Bairro | `bairro` | Data |
| Complemento | `complemento` | Data |
| CEP | `cep` | Data |
| Cidade/UF | `cidade_uf` | Data |
| Escolaridade | `escolaridade` | Select |
| Deficiência (Sim/Não) | `possui_deficiencia` | Check |
| Especificação deficiência | `tipo_deficiencia` | Data |
| Atendimento Especial | `atendimento_especial` | Data |
| Curso | `curso_inscrito` | Link |
| Carteira Assinada | `carteira_assinada` | Check |
| Seguro Desemprego | `seguro_desemprego` | Check |
| CadÚnico | `cadunico` | Check |
| SINE | `sine` | Check |
| Beneficiário políticas inclusão | `beneficiario_inclusao` | Check |
| Egresso sistema prisional | `egresso_prisional` | Check |
| Resgatado trabalho forçado | `resgatado_trabalho_forcado` | Check |
| Familiar trabalho infantil | `familiar_trabalho_infantil` | Check |
| Trabalhador setor estratégico | `trabalhador_estrategico` | Check |
| Cooperativado/associado/MEI | `trabalhador_cooperativado` | Check |
| Povos e Comunidades Tradicionais | `pct` | Check |
| Trabalhador rural | `trabalhador_rural` | Check |
| Pescador artesanal | `pescador_artesanal` | Check |
| Estagiário | `estagiario` | Check |
| Aprendiz | `aprendiz` | Check |
| Data inscrição | `data_inscricao` | Date |
| Responsável matrícula | `responsavel_matricula` | Data |

### Google Form
- Título: "SISEC/MDS — Ficha de Inscrição TDS"
- Seções: Identificação do Curso | Dados Pessoais | Endereço | Escolaridade e Acessibilidade | Perfil do Público | Declaração
- Acesso: apenas contas `@ipexdesenvolvimento.cloud` (restrito a estagiários/tutores)
- Destino: Google Sheets "SISEC TDS — Inscrições"

---

## 4. Páginas Instrucionais Estáticas

### Onde ficam
Web Pages no Frappe CMS (`DocType: Web Page`) — servidas pelo nginx do Frappe sem container adicional. HTML puro + Tailwind CDN no campo `main_section_edited`. Sem build, sem dependência de framework.

### Páginas

| URL | Audiência | Ação principal |
|---|---|---|
| `lms.ipexdesenvolvimento.cloud/guia-aluno` | Beneficiários CadÚnico | Botão WhatsApp + FAQ simples |
| `lms.ipexdesenvolvimento.cloud/guia-tutor` | Instrutores/Tutores | Login LMS + gerenciar turma |
| `lms.ipexdesenvolvimento.cloud/guia-gestor` | NERUDS/FAPTO/MDS | Arquitetura + métricas + contatos |
| `lms.ipexdesenvolvimento.cloud/sisec-info` | Estagiários | Instruções + link Google Form SISEC |

### Estrutura de cada página
- Header: logo TDS + nav mínima (Guias · LMS · WhatsApp)
- Corpo: conteúdo específico da audiência (linguagem adequada)
- Botão WhatsApp: `https://wa.me/351932439344` (fixo, floating mobile)
- Link LMS: `https://lms.ipexdesenvolvimento.cloud/lms/courses`
- Sem chatbot Chatwoot nas páginas internas (apenas na landing se houver)

---

## 5. Catraca Pedagógica WhatsApp

### Conceito
Quando o aluno envia mensagem para WhatsApp (inbox 5), o N8N verifica o estado do aluno no Frappe por número de telefone e o guia pelo módulo digital. Conclusão = todas as seções lidas (confirmação "li") + todos os MCQs respondidos. Critério inclusivo: qualquer resposta vale (não bloqueia por erro — só por omissão).

### Máquina de estados

```
INATIVO          → recebe mensagem → lookup Frappe por telefone
                                            ↓
                                     NÃO ENCONTRADO → mensagem de orientação + link guia-aluno
                                            ↓
                                     PRÉ-INSCRITO → confirma matrícula → estado: AGUARDANDO_LEITURA (seção 1)
                                            ↓
AGUARDANDO_LEITURA → envia texto da seção atual
                   → aguarda "li" / "ok" / "certo" / "sim"
                   → confirma → estado: AGUARDANDO_MCQ (mesma seção)

AGUARDANDO_MCQ   → envia pergunta + opções A / B / C / D
                 → recebe letra → registra resposta
                 → se há próxima seção → estado: AGUARDANDO_LEITURA (próxima seção)
                 → se fim do módulo → estado: MODULO_COMPLETO

MODULO_COMPLETO  → "Parabéns! Você concluiu [módulo X]."
                 → se há próximo módulo → libera acesso → AGUARDANDO_LEITURA (módulo +1, seção 1)
                 → se último módulo → trigger certificado → CERTIFICADO_EMITIDO

QUALQUER ESTADO + palavra handoff → transbordo humano (fluxo N8N existente)
```

### Palavras que ativam leitura confirmada
`li`, `ok`, `certo`, `sim`, `pronto`, `entendi`, `feito`, `lido`, `claro`, `combinado`

### Palavras de handoff (já no N8N)
`tutor|prova|exame|humano|operador|atendente|reclamação|ajuda humana|falar com alguém|não consigo|problema técnico`

### Campos novos no TDS Aluno (a criar via API)

| Campo | Tipo Frappe | Descrição |
|---|---|---|
| `estado_catraca` | Select | `inativo / aguardando_leitura / aguardando_mcq / modulo_completo / certificado_emitido` |
| `modulo_atual` | Int | Índice do módulo em progresso (1–N) |
| `secao_atual` | Int | Índice da seção dentro do módulo |
| `respostas_mcq` | Small Text (JSON) | `{"mod1":{"sec1":"A","sec2":"C"}}` |
| `modulos_concluidos` | Small Text (JSON) | `[1,2,3]` |
| `data_ultimo_acesso_whatsapp` | Datetime | Para analytics |

### Conteúdo das cartilhas no N8N
- Armazenado como JSON em node Set do N8N por curso
- Estrutura: `{curso: [{modulo, secoes: [{texto, pergunta, opcoes: {A,B,C,D}, resposta_correta}]}]}`
- AnythingLLM continua disponível para perguntas abertas fora do fluxo estruturado
- N8N detecta se a mensagem é resposta ao fluxo (letra A/B/C/D ou confirmação de leitura) ou pergunta livre → RAG

### Lookup por telefone no N8N
```
GET /api/resource/TDS Aluno?filters=[["whatsapp","=","+351XXXXXXXXX"]]
Authorization: token {FRAPPE_API_KEY}:{FRAPPE_API_SECRET}
```

---

## 6. Email — Gmail SMTP como Relay

### Decisão
Todos os serviços (Frappe, Chatwoot, N8N) usam Gmail SMTP como relay. Endereços `@ipexdesenvolvimento.cloud` são aliases de display. Poste.io permanece instalado mas não é o relay primário (porta 25 e MX não configurados).

### Configuração

| Serviço | SMTP Host | Porta | Usuário | De (alias) |
|---|---|---|---|---|
| Frappe | smtp.gmail.com | 587 | tdsdados@gmail.com | noreply@ipexdesenvolvimento.cloud |
| Chatwoot | smtp.gmail.com | 587 | tdsdados@gmail.com | atendimento@ipexdesenvolvimento.cloud |
| N8N | smtp.gmail.com | 587 | tdsdados@gmail.com | notificacoes@ipexdesenvolvimento.cloud |

**Pré-requisito:** Gmail App Password gerado em `myaccount.google.com/security` para tdsdados@gmail.com com 2FA ativo.

### Contas operacionais (display em Chatwoot)

| Conta | Display | Função |
|---|---|---|
| rafael@ipexdesenvolvimento.cloud | Rafael Luciano | Coordenação técnica |
| sofia@ipexdesenvolvimento.cloud | Sofia | Tutora — Associativismo |
| gabriela@ipexdesenvolvimento.cloud | Gabriela | Tutora — Finanças |
| valentine@ipexdesenvolvimento.cloud | Valentine | Tutor — Agricultura |
| pedroh@ipexdesenvolvimento.cloud | Pedro H. | Tutor — Audiovisual |
| sahaa@ipexdesenvolvimento.cloud | Sahaa | Tutora — SIM |

Todas as contas usam o mesmo SMTP relay (tdsdados@gmail.com) para envio real.

---

## 7. Continuidade de Sessão — HANDOFF.md no GitHub

### Problema
Claude Code perde contexto entre sessões e desconexões. Projeto com alta complexidade (7 serviços, múltiplas credenciais, decisões arquiteturais acumuladas).

### Solução
Arquivo `HANDOFF.md` na raiz de `/root/projeto-tds/`, commitado e pushado ao final de cada sessão de trabalho.

### Estrutura do HANDOFF.md

```markdown
# TDS — Handoff de Sessão
**Última atualização:** YYYY-MM-DD HH:MM (horário Brasília)
**Sessão:** [descrição breve do que foi feito]

## Serviços — Estado Atual
| Serviço | URL | Status |
|---------|-----|--------|
| N8N | https://n8n.ipexdesenvolvimento.cloud | ✅/❌ |
| ...

## Problemas em Aberto
- **[BLOCKER]** Descrição + contexto suficiente para retomar sem reler histórico
- **[PENDENTE]** ...

## Próximas 3 Tarefas (prioridade)
1. Tarefa concreta — arquivo/comando específico
2. ...
3. ...

## Decisões Tomadas (não rever)
- SISEC via Google Form (Abordagem A aprovada em 09/04/2026)
- ERPNext não desinstalar — esconder /insights via CSS
- WhatsApp número +351932439344 é o definitivo
- ...

## Credenciais desta sessão
- Novos tokens/keys gerados: [listar aqui]
- Arquivo de referência completo: /root/kreativ-setup/.env.real
```

### Workflow
- **Início de sessão:** ler HANDOFF.md antes de qualquer ação
- **Fim de sessão:** atualizar HANDOFF.md + `git commit -m "chore: handoff YYYY-MM-DD"` + `git push`
- **Prompt de retomada padrão:**
  > "Continuar projeto TDS. Ler /root/projeto-tds/HANDOFF.md antes de qualquer ação."

---

## Dependências e Ordem de Execução

```
1. Fix /insights CSS (kreativ_theme)          ← 5 min, sem risco
2. Verificar webhook Meta + inbox 5 produção  ← depende acesso Meta Business Manager
3. Gmail App Password + configurar SMTP       ← depende 2FA tdsdados@gmail.com
4. Campos catraca no TDS Aluno (Frappe API)   ← independente
5. Google Form SISEC + Apps Script webhook    ← independente
6. N8N: filtro inbox + workflow catraca       ← depende 4
7. Páginas instrucionais (Web Pages Frappe)   ← independente
8. HANDOFF.md inicial + push GitHub           ← último passo desta sessão
```

---

## O que NÃO está no escopo deste plano

- Desinstalar ERPNext do Frappe
- Substituir Poste.io por outro servidor de email
- Reescrever o tema kreativ_theme
- Implementar certificados (fase posterior)
- Integração Google Sheets → PostgreSQL (Fase 2)
- SPF/DKIM para domínio (Fase 2)
