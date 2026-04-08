# Design: Implantação Plataforma TDS — Seguimento Completo

**Data:** 2026-04-08  
**Projeto:** Território de Desenvolvimento Social e Inclusão Produtiva (TDS)  
**Instituição:** NERUDS/UFT via FAPTO | Bolsa nº 212/2026  
**Coordenadora:** Juliana Aguiar de Melo  
**Responsável técnico:** Rafael Luciano (admin@neruds.org)  
**Domínio:** ipexdesenvolvimento.cloud

---

## Contexto

Plataforma de inclusão socioeducacional para 2.160 beneficiários do CadÚnico em 36 municípios do Tocantins (Bico do Papagaio e Jalapão). Canal principal: WhatsApp. Atividade de campo iniciou em 09/04/2026 com agentes mobilizadores coletando inscrições via Google Forms.

---

## Arquitetura Geral

```
[Beneficiário WhatsApp]
        ↕ Cloud API (Meta)
[Chatwoot Inbox TDS]
        ↓ mensagem nova
        ├── Agente Automático [n8n Webhook → AnythingLLM RAG → Gemini]
        │       - orienta preenchimento dos forms
        │       - responde dúvidas sobre cursos/trilhas
        │       - envia link de pré-matrícula
        │       - baixa confiança → escala para humano
        └── Estagiários (supervisão + atendimento manual)
                ↕ atualizam Sheets quando beneficiário informa dados

[Atividade de Campo]
  Google Forms (Pré-Matrícula + Baseline TDS)
        ↓ automático (Google Sheets nativo)
  Sheets: ABA INSCRITOS ← aplicadores preenchem ficha AppScript
                ↓
  Sheets: ABA REGISTROS_COMPLETOS
  Sheets: ABA CONTROLE_APLICADORES

[n8n Workflows]
  - webhook WhatsApp → RAG → resposta Chatwoot
  - futuro: Sheets → PostgreSQL kreativ_edu

[Frappe LMS] — Fase 2, sem container ainda
[Poste.io email] — Fase 2, corrigir MX + porta 25
```

---

## Fases de Implantação

### Fase 0 — HOJE (antes da atividade de campo de 09/04/2026)

**Objetivo:** canal WhatsApp funcional + RAG com contexto dos formulários.

#### 0.1 Corrigir infraestrutura

| Serviço | Problema | Ação |
|---|---|---|
| N8N | container unhealthy | verificar logs, reiniciar |
| Chatwoot | container unhealthy | verificar logs, reiniciar |
| Poste.io | sem MX + porta 25→2525 | fase 2 (não bloqueia MVP) |

#### 0.2 Configurar Chatwoot

- Conectar WhatsApp Cloud API (Meta) como inbox "TDS WhatsApp"
- Criar time "Equipe TDS":
  - Papel Supervisor: coordenadora (vê todas as conversas)
  - Papel Agente: cada estagiário com login próprio (`estag-[nome]@neruds.org`)
- Criar etiquetas: `pre-matricula`, `baseline`, `duvida-curso`, `escalonado`
- Regra de roteamento: mensagem nova → agente automático; tag `escalonado` → notifica time

#### 0.3 Carregar documentos no AnythingLLM (workspace `tds`)

Documentos já existentes:
- `Projeto_TDS_V3.pdf` ✅

Documentos a criar e fazer upload:

**`formulario-pre-matricula.md`**
- Estrutura das 4 seções do Google Form simplificado
- Link: https://forms.gle/SrtyUw8vmgKLWvuM6
- Dicas por campo (nome, data nascimento, CPF, telefone, endereço, curso, disponibilidade)

**`formulario-baseline-tds.md`**
- Estrutura dos 11 blocos / 18 seções do Baseline TDS
- Explicação dos termos técnicos: CadÚnico, NIS, DAP/CAF, PAA, PNAE, SINE, BPC, Bolsa Família, Tarifa Social, Pronaf B, ATER
- Exemplos de resposta para cada bloco

#### 0.4 Configurar agente automático no n8n

Workflow "TDS WhatsApp Agent":
- Trigger: Chatwoot **Agent Bot** webhook (configurado em Settings → Integrations → Agent Bots). O Chatwoot envia um POST para o n8n a cada mensagem nova na inbox TDS.
- Nó AnythingLLM: query no workspace `tds` com a mensagem do usuário
- Nó condição: o AnythingLLM retorna um campo `sources` — se `sources` vazio OU a resposta contiver "não encontrei" / "não tenho informação", considera baixa confiança → escala. Caso contrário → responde.
- Nó Chatwoot API: `POST /api/v1/accounts/{id}/conversations/{conv_id}/messages` com a resposta; se escalonando, também `POST` para adicionar etiqueta `escalonado` e remover atribuição do bot.

**Prompt base do agente:**
```
Você é o Assistente TDS, do Programa Territórios de Desenvolvimento 
Social e Inclusão Produtiva (UFT/IPEX/MDS/FAPTO).

Público: beneficiários do CadÚnico em 36 municípios do Tocantins 
(Bico do Papagaio e Jalapão).

Regras:
- Linguagem simples, acolhedora, sem jargões
- Nunca invente informações — se não souber, escale para humano
- Para inscrição: forms.gle/SrtyUw8vmgKLWvuM6
- Cursos: gratuitos, 40–80h, sem pré-requisitos, certificado UFT/MDS
- Elegibilidade: ser do CadÚnico, morar nos municípios atendidos, 18+
- Se não souber responder: diga "Vou conectar você com nossa equipe"
  e aplique a tag "escalonado"
```

#### 0.5 Teste end-to-end

- Enviar mensagem WhatsApp → verificar resposta do agente
- Simular dúvida sobre formulário → agente cita seção correta
- Simular dúvida sem resposta → agente escala, estagiário recebe notificação

---

### Fase 1 — Curto Prazo (dias após campo)

- Ingestão do conteúdo dos cursos no AnythingLLM (ementas PDF)
- Workflow n8n para notificações: novo form submetido → aviso no Chatwoot
- Adaptação do AppScript para estagiários (ver Seção abaixo)
- Refinamento do agente com base nas dúvidas reais do campo

---

### Fase 2 — Médio Prazo (semanas)

- Deploy Frappe LMS no Dokploy
- Integração Chatwoot → Frappe (matrícula automática)
- Corrigir Poste.io: MX record no DNS + mapear porta 25 corretamente
- Sync Google Sheets → PostgreSQL kreativ_edu via n8n

---

## Seção CRM: Google Sheets + AppScript

### Estrutura atual (mantida)

| Aba | Uso |
|---|---|
| `INSCRITOS` | Lista de inscritos, status de contato, aplicador responsável |
| `REGISTROS_COMPLETOS` | Dados completos dos 11 blocos do baseline |
| `CONTROLE_APLICADORES` | Painel de desempenho por aplicador |

### Status do inscrito (hierarquia)

```
Pendente → Em Contato → Contatado
                      → Atualização WhatsApp  (novo — estagiários)
```

Regra: `Atualização WhatsApp` não sobrescreve `Contatado`. Hierarquia:
`Contatado` > `Atualização WhatsApp` > `Em Contato` > `Pendente`

### Adaptações para estagiários (Fase 1)

#### Nova constante
```javascript
const STATUS_WA = 'Atualização WhatsApp';
```

#### Novo item de menu
```
📋 TDS Campo
  ├── 📝 Abrir Ficha do Inscrito        (campo presencial — fluxo atual)
  ├── 📱 Buscar Inscrito por WhatsApp   (novo — estagiários)
  ├── 📊 Relatório Geral
  └── 👥 Atualizar Controle Aplicadores
```

#### Nova função: buscarPorContato(query)
- Aceita: telefone (parcial), CPF, ou nome parcial
- Retorna: lista de matches ranqueados
- Se encontrar 1 resultado: abre ficha diretamente
- Se encontrar múltiplos: mostra lista para o estagiário escolher
- Se não encontrar: oferece criar pré-registro

#### Ficha no modo "Atualização WhatsApp"
- Badge `📱 Via WhatsApp` no topo da ficha
- Dados existentes pré-carregados (igual ao modo atual para registros existentes)
- Campo `Aplicador` pré-preenche com `Estag - [nome do estagiário]`
- Campo adicional: `Nota do contato WhatsApp` (textarea livre)
- Ao salvar: respeita hierarquia de status

#### Painel CONTROLE_APLICADORES com diferenciação por tipo

| Tipo | Identificador | Cor de fundo |
|---|---|---|
| Aplicador de campo | qualquer nome sem prefixo | branco |
| Estagiário | `Estag - [Nome]` | lilás `#ede7f6` |
| Bot/automático | `Bot TDS` | cinza `#f5f5f5` |

### Mudanças resumidas no AppScript

| Função | Alteração |
|---|---|
| `onOpen()` | Adiciona item "📱 Buscar por WhatsApp" |
| `buscarPorContato(query)` | **Nova** — busca por telefone/CPF/nome |
| `abrirFichaWhatsApp(linhaNum)` | **Nova** — wrapper com flag `modo='whatsapp'` |
| `getHtmlFicha(modo)` | Recebe parâmetro de modo, exibe badge e texto certo |
| `salvarFicha(p)` | Respeita hierarquia de status |
| `gerarControleAplicadores()` | Colore linhas por tipo de aplicador |

---

## Seção Agente WhatsApp: Fluxo de Decisão

```
Mensagem recebida no Chatwoot
        ↓
É saudação / "quero me inscrever" / "como faço"?
  → Apresenta o TDS em linguagem simples
  → Envia link: forms.gle/SrtyUw8vmgKLWvuM6

É dúvida sobre campo específico de formulário?
  → RAG: busca em formulario-pre-matricula.md ou formulario-baseline-tds.md
  → Explica o campo com exemplos (ex: "O que é NIS?" → explica + onde achar)

É dúvida sobre elegibilidade?
  → RAG: critérios (CadÚnico, municípios Bico do Papagaio/Jalapão, 18+)

É dúvida sobre curso?
  → RAG: nome do curso, carga horária (40–80h), o que aprende, certificado UFT

Confiança baixa (RAG sem fontes OU resposta contém "não tenho informação")
OU pergunta fora do escopo do TDS?
  → "Deixa eu conectar você com nossa equipe. Um estagiário responderá em breve."
  → Aplica etiqueta "escalonado" no Chatwoot
  → Remove atribuição do bot → notifica time "Equipe TDS"
```

---

## Documentos a criar para o RAG

### formulario-pre-matricula.md

Seções:
1. Dados pessoais (nome, nascimento, CPF, telefone/WhatsApp, gênero)
2. Endereço completo com CEP
3. Área/atividade de interesse (7 cursos disponíveis + descrição de cada)
4. Disponibilidade de horários

Link do formulário: https://forms.gle/SrtyUw8vmgKLWvuM6

### formulario-baseline-tds.md

Blocos B1–B11:
- B1: Dados do curso (qual curso, carga, datas, local)
- B2: Dados pessoais complementares (RG, naturalidade, estado civil, cor/raça, quilombola)
- B3: Educação e acessibilidade (escolaridade, deficiência, atendimento especial)
- B4: Perfil socioeconômico SISEC/MDS (15 perguntas Sim/Não + benefícios)
- B5: Composição familiar e habitação
- B6: Renda e ocupação
- B7: Atividade produtiva (só se desenvolver)
- B8: Acesso a crédito
- B9: Saúde e uso de tecnologia
- B10: Território e políticas públicas
- B11: Histórico profissional e expectativas

Glossário de termos técnicos a incluir:
- CadÚnico / NIS: Cadastro Único para Programas Sociais do Governo Federal
- DAP/CAF: Declaração de Aptidão ao Pronaf / Cadastro da Agricultura Familiar
- PAA: Programa de Aquisição de Alimentos
- PNAE: Programa Nacional de Alimentação Escolar
- SINE: Sistema Nacional de Emprego
- BPC: Benefício de Prestação Continuada
- Pronaf B: linha de crédito rural para pequenos agricultores
- ATER: Assistência Técnica e Extensão Rural

---

## Configuração Chatwoot — Detalhamento

### Inbox
- Nome: "TDS WhatsApp"
- Tipo: WhatsApp Cloud API (Meta)
- Número: número Business verificado (a ser configurado)

### Time
- Nome: "Equipe TDS"
- Supervisores: coordenadores com acesso a todas as conversas
- Agentes: estagiários — cada um com conta própria

### Etiquetas
| Etiqueta | Quando aplicar |
|---|---|
| `pre-matricula` | Pessoa quer saber sobre inscrição/pré-matrícula |
| `baseline` | Dúvida sobre formulário extenso (18 seções) |
| `duvida-curso` | Pergunta sobre conteúdo dos cursos |
| `escalonado` | Agente não soube responder → precisa de humano |
| `resolvido` | Dúvida solucionada |

### Regras de automação
1. Mensagem nova → atribuir ao agente automático (bot)
2. Tag `escalonado` adicionada → notificar time "Equipe TDS"
3. Conversa sem resposta há 30min com tag `escalonado` → notificar supervisor

---

## Decisões de Design

| Decisão | Escolha | Motivo |
|---|---|---|
| Canal principal MVP | WhatsApp | Público sem app/browser, urgência |
| Provedor WhatsApp | Cloud API (Meta) | Mais estável que Baileys, já disponível |
| CRM imediato | Google Sheets + AppScript | Funciona amanhã, sem setup |
| CRM futuro | PostgreSQL kreativ_edu | n8n sync, fase 2 |
| LLM do agente | Gemini 1.5 Flash (via AnythingLLM) | Já configurado, custo baixo |
| LLM backup | Groq (llama-3.3-70b) | Já configurado no RAG |
| LMS | Frappe | Fase 2, após MVP estável |

---

## Riscos e Mitigações

| Risco | Probabilidade | Mitigação |
|---|---|---|
| N8N/Chatwoot não sobem hoje | Média | Investigar logs antes de qualquer outra coisa |
| WhatsApp Cloud API não configurada a tempo | Alta | Ter número Business pronto; fallback: estagiários respondem manualmente via Chatwoot |
| RAG sem conteúdo dos forms antes do campo | Alta | Criar e fazer upload dos 2 docs hoje |
| Estagiários sem treinamento no Chatwoot | Média | Tutorial de 10min no onboarding |
| Beneficiários sem WhatsApp | Baixa | Forms presenciais continuam funcionando |
