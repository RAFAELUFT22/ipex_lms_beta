# TDS — Páginas Institucionais e Guias de Uso — Design Spec

**Data:** 2026-04-09  
**Aprovado por:** Rafael Luciano (admin@neruds.org)  
**Contexto:** Frappe LMS em produção — `https://lms.ipexdesenvolvimento.cloud`

---

## Objetivo

Criar presença institucional pública no LMS do TDS com landing page, páginas de suporte e 3 guias de uso (aluno, tutor, gestor), integrar chatbot Chatwoot com RAG/AnythingLLM, e limpar o catálogo de cursos do LMS.

---

## Decisões de Design

### Abordagem: Híbrido C
Páginas web estáticas via Frappe CMS (Web Page doctype), públicas sem login, servidas no mesmo domínio do LMS. Guias como web pages independentes — sem necessidade de criar cursos meta.

### Estrutura de páginas

| Rota | Título | Audiência |
|------|--------|-----------|
| `/` (home) | TDS — Inclusão Produtiva no Tocantins | Todos |
| `/sobre` | Sobre o Programa TDS | Gestores, parceiros |
| `/guia-aluno` | Guia do Aluno | Beneficiários CadÚnico |
| `/guia-tutor` | Guia do Tutor/Instrutor | Instrutores, tutores |
| `/guia-gestor` | Guia do Gestor | NERUDS/UFT/FAPTO/MDS |

### Landing Page — Seções (A + C híbrido)
1. **Nav**: Logo TDS · Sobre · Cursos · Municípios · Guias · CTA "Acessar Plataforma"
2. **Hero**: Headline sem mencionar WhatsApp como canal único + 4 estatísticas (2.160 beneficiários, 36 municípios, 5 eixos, 3 modalidades)
3. **Modalidades**: 3 cards — Presencial · Online · Mista
4. **Faixa equipe**: Professores UFT · Pós-graduandos · Mestrandos · Graduandos · Instrutores · Estagiários
5. **Cursos por Eixo**: 5 eixos TDS com cursos associados (dados do projeto)
6. **Como funciona**: 3 passos (Identificação → Matrícula → Capacitação/Certificado)
7. **Sobre**: Contexto NERUDS/UFT/FAPTO/MDS/Programa Acredita + mapa placeholder
8. **Parceiros**: NERUDS/UFT · FAPTO · Ipex · MDS/Acredita
9. **Footer**: Links para guias + institucional

### 5 Eixos e Cursos Associados (fonte: RAG TDS)

| Eixo | Cursos |
|------|--------|
| 1 — Empreendedorismo Popular e Gestão de Negócios | Finanças e Empreendedorismo · Ed. Financeira Melhor Idade · IA no meu Bolso · Audiovisual |
| 2 — Formação Cooperativista Popular | Associativismo e Cooperativismo |
| 3 — Agricultura Familiar e Políticas Públicas | SIM — Serviço de Inspeção Municipal |
| 4 — Sistemas Produtivos Sustentáveis | Agricultura Sustentável — SAFs |
| 5 — Inovação e Certificação Agroecológica | (em desenvolvimento) |

### Chatbot Chatwoot
- **Inbox**: ID 7 "Tutor TDS — Site" (Channel::WebWidget)
- **Token**: `HwBawyqmiKTAbNzF8yAnzHCD`
- **Bot**: "Tutor IA" (ID 1) → N8N webhook → AnythingLLM RAG (workspace `tds`)
- **Banner beta**: visível no header do widget; avisa que desenvolvedor monitora conversas
- **Embutido em**: todas as 5 páginas via script Chatwoot SDK

### Guias de Uso

**Guia do Aluno** (`/guia-aluno`): FAQ acessível para beneficiários CadÚnico. Linguagem simples. Seções: O que é o TDS · Quem pode · Como funciona (3 modalidades) · Certificado · Perguntas frequentes · Contato.

**Guia do Tutor** (`/guia-tutor`): Manual step-by-step do LMS para instrutores. Seções: Login · Visão do curso · Editar aulas · Gerenciar turma · Progresso dos alunos · Avaliações · Suporte.

**Guia do Gestor** (`/guia-gestor`): Visão executiva para NERUDS/UFT/FAPTO/MDS. Seções: Arquitetura tecnológica · Fluxo completo do beneficiário · Métricas e relatórios · Equipe e responsabilidades · Política de dados · Contato técnico.

---

## Limpeza do LMS

### Cursos a MANTER (com conteúdo)
- `agricultura-sustent-vel-sistemas-agroflorestais-2` (4 cap, 9 aulas)
- `audiovisual-e-produ-o-de-conte-do-digital-2` (4 cap, 12 aulas)
- `finan-as-e-empreendedorismo-2` (4 cap, 9 aulas)
- `ia-no-meu-bolso-intelig-ncia-artificial-para-o-dia-a-dia-2` (4 cap, 9 aulas)
- `sim-servi-o-de-inspe-o-municipal-para-pequenos-produtores-2` (4 cap, 8 aulas)
- `associativismo-e-cooperativismo-4` (3 cap, 7 aulas)
- `educa-o-financeira-para-a-melhor-idade` (3 cap, 7 aulas)
- `trilha-1` a `trilha-5` (estrutura das Trilhas)

### Ações de limpeza
- Unpublish: `a-guide-to-frappe-learning` (demo)
- Unpublish: versões antigas dos 7 cursos (sem sufixo ou com sufixo mais baixo que o keeper)
- Manter sub-cursos publicados (potencial conteúdo futuro dos eixos)

### Fix N8N — Strip `<think>` tags
Adicionar Code node no workflow `XYcnRlPZSlfGXOWb` entre o output do RAG e o envio ao Chatwoot, strippando `<think>...</think>` da `textResponse`.

### Healthchecks (já corrigidos no docker-compose.yml)
- Chatwoot: `curl` → `wget -q --spider http://localhost:3000/`
- N8N: `curl` → `wget -q --spider http://localhost:5678/healthz`
- Aplicar via: recreate dos containers específicos

---

## Stack Técnico
- **Frappe LMS**: v2.45.2, site `lms.ipexdesenvolvimento.cloud`
- **Auth API Frappe**: `token 056681de29fce7a:7c78dcba6e3c5d1`
- **Chatwoot**: v4.11.0 — `https://chat.ipexdesenvolvimento.cloud`
- **N8N**: v2.13.4 — `https://n8n.ipexdesenvolvimento.cloud`
- **AnythingLLM**: workspace `tds`, API key `W5M4VV3-DVQMN22-M2QF6JE-R5KFJP0`
- **Docker Compose**: `/etc/dokploy/compose/compose-parse-primary-array-kmj9v7/code/`
