# Prompt para Antigravity Agent — Design de UI via Stitch MCP
**Data:** 2026-04-11  
**Para:** Agente Antigravity (BPM Designer)  
**Via:** Stitch MCP  
**Contexto:** LMS Lite v2 — TDS (Território de Desenvolvimento Social)

---

## Sua Missão

Você é o Antigravity Agent, responsável pelo design visual e especificação de componentes do **TDS LMS Lite v2**. Use o MCP do Stitch para criar mockups de alta fidelidade das páginas listadas abaixo, seguindo rigorosamente o sistema de design "Aurora" já estabelecido no projeto.

**Seu output deve ser:**
1. Mockups criados no Stitch (via ferramentas MCP)
2. Um documento de especificação salvo em `docs/specs/2026-04-11-lms-lite-ui-components.md`

---

## Sistema de Design — Aurora Tokens

Todos os mockups devem usar estes tokens exatos:

```css
/* Cores */
--bg-deep:       #000a14   /* Background principal (mais escuro) */
--bg-surface:    #001529   /* Surface de painéis/sidebar */
--primary:       #003366   /* Azul primário (botões, destaques) */
--primary-light: #004d99   /* Hover de primário */
--secondary:     #008080   /* Teal (ação principal, CTA, ativo) */
--accent:        #f4bf00   /* Amarelo dourado (progresso, conquistas) */
--text-main:     #f8fafc   /* Texto principal */
--text-dim:      #94a3b8   /* Texto secundário */
--text-muted:    #64748b   /* Labels e placeholders */
--border:        rgba(255,255,255,0.08)
--glass:         rgba(255,255,255,0.03)  /* Glassmorphism */

/* Tipografia */
Headings: Lexend (600–800 weight, letter-spacing: -0.02em)
Body:     Inter (400–600 weight)

/* Componentes estabelecidos */
.glass-card   → border-radius: 24px, backdrop-blur: 10px
.glass-panel  → border-radius: 24px, backdrop-blur: 12px
.btn-aurora   → bg: teal, border-radius: 100px, font-weight: 700
Hover cards   → translateY(-4px) + box-shadow com teal glow
```

---

## Contexto do Produto

O TDS LMS Lite é uma plataforma educacional para beneficiários CadÚnico em Tocantins.
- **2.160 alunos** em 36 municípios, acesso via WhatsApp
- **7 cursos**: Agricultura, Audiovisual, Finanças, Melhor Idade, Cooperativismo, IA, Inspeção Municipal
- **Stack atual**: React + Tailwind + Framer Motion (dashboard admin); FastAPI (backend); AnythingLLM (RAG)
- **Domínio**: `ipexdesenvolvimento.cloud`

### Componentes Admin já existentes (NÃO redesenhar):
- `GroupManager` — Gestão de grupos/turmas WhatsApp
- `BroadcastCenter` — Envio em massa
- `AIInsight` — Insights do RAG AnythingLLM
- `MetricsView` — Métricas operacionais
- `TutorsManager` — Gestão de tutores
- `KnowledgeBase` — Base de conhecimento RAG
- `StudentPortal` — Portal do aluno (versão simples atual)
- `SettingsPanel` — Configurações de API
- `LmsLiteManager` — Gestão de alunos (lista básica)

---

## Páginas e Componentes para Projetar

### BLOCO A — Novas Abas no Dashboard Admin

#### A1. Aba "Comunidades"
**Propósito:** Gerenciar grupos WhatsApp de avisos gerais (sem curso específico).

Elementos necessários:
- Cards de comunidade com: título, ID do grupo WhatsApp, contagem de membros, descrição
- Botão "Criar Comunidade" → modal com campos: título, descrição, ID do grupo WhatsApp
- Badge de status (ativo/inativo) em teal/vermelho
- Botão "Enviar Aviso" por comunidade → abre BroadcastCenter filtrado
- Empty state com ícone de megafone e CTA

Layout sugerido: grid 2 colunas de cards com glassmorphism, header com botão de criação.

#### A2. Aba "Monitor WhatsApp" (substituir/expandir LmsLiteManager)
**Propósito:** Visualizar mensagens recebidas via webhook em tempo real.

Elementos necessários:
- Feed de eventos em tempo real (lista vertical, mais recente no topo)
- Cada evento: avatar circular com inicial do número, número de telefone, mensagem truncada, timestamp relativo, badge de status (bot/humano/novo)
- Filtros: todos / aguardando bot / em atendimento humano / resolvidos
- Toggle rápido Bot→Humano por conversa (inline)
- Painel lateral (slide-in) com histórico completo de conversa ao clicar
- Indicador de CPU/latência no header (badge numérico)

Layout: lista full-width com sidebar colapsável de detalhes.

#### A3. Aprimoramento do "Gestão de Grupos" (GroupManager)
**Propósito:** Adicionar vinculação com cursos e workspaces AnythingLLM.

Novos campos/elementos:
- Campo "Workspace RAG" (dropdown com os 7 workspaces)
- Campo "WhatsApp Group ID" (input com botão de testar conexão)
- Campo "Modo do Chatbot": dropdown Bot / Humano / Híbrido
- Progresso médio da turma (barra de progresso em --accent)
- Lista de alunos collapsível dentro de cada card de grupo

---

### BLOCO B — Portal do Aluno (Acesso via Browser)

Este é um portal separado que o aluno acessa pelo celular. Design deve ser **mobile-first** (max-width: 390px como referência). Textura dark Aurora mantida.

#### B1. Página `/login`
**Propósito:** Autenticação por telefone (o aluno digita o WhatsApp; recebe OTP).

Elementos:
- Logo TDS centralizado + tagline "Sua jornada de aprendizado"
- Input de telefone com máscara brasileira (+55)
- Botão "Receber código via WhatsApp" em teal
- Campo OTP (6 dígitos, auto-focus em cada dígito)
- Link "Ainda não sou aluno" → matrícula via WhatsApp
- Footer: "Programa TDS — NERUDS/UFT via FAPTO"

#### B2. Página `/dashboard` (Visão do Aluno)
**Propósito:** Hub central do aluno com progresso e atalhos.

Seções:
1. **Header personalizado**: "Olá, [Nome]! 👋" + subtítulo motivacional em Paulo Freire style
2. **Meu Curso Ativo**: Card grande com nome do curso, barra de progresso (--accent), % concluído, botão "Continuar"
3. **Minhas Conquistas**: Row de badges (quiz 1 concluído, 50% trilha, certificado emitido) em glassmorphism
4. **Histórico de Conversas**: Lista compacta das últimas 5 interações com o tutor IA (mensagem + data)
5. **Próximo Passo**: Card de CTA para próxima atividade
6. **Suporte**: Botão flutuante WhatsApp para contato com tutor humano

#### B3. Página `/curso/[slug]`
**Propósito:** Detalhe do curso com módulos e quizzes.

Seções:
1. **Hero do Curso**: Imagem/ícone do curso, título, instrutor, duração estimada
2. **Barra de Progresso Geral**: Linear com % e texto "X de Y atividades"
3. **Módulos**: Acordeão expansível — cada módulo tem status (bloqueado/disponível/concluído), duração, ícone de tipo (leitura/quiz/vídeo)
4. **Quiz Disponível**: Card destacado em --accent quando há quiz liberado
5. **Certificado**: Card de desbloqueio com cadeado → desbloqueia ao 100%

#### B4. Página `/quiz/[id]`
**Propósito:** Interface de resposta de quiz — simples e acessível para baixa literacia digital.

Elementos:
- Progresso do quiz no topo (1 de 5 perguntas)
- Pergunta em fonte grande (Lexend 20px+), fundo glassmorphism card
- Opções de resposta: botões grandes full-width, clara distinção visual ao selecionar
- Botão "Próxima" em teal, desabilitado até selecionar resposta
- Feedback imediato (correto em verde, errado em vermelho) antes de avançar
- Tela final: pontuação, badge de conquista se passou, botão "Ver Certificado" se 100%

#### B5. Página `/certificados`
**Propósito:** Lista de certificados do aluno.

Elementos:
- Grid de certificados (card por curso concluído)
- Cada card: nome do curso, data de emissão, botão "Baixar PDF", botão "Compartilhar"
- Hash de verificação visível (truncado) com link para verificação pública
- Estado vazio: ilustração + "Complete sua primeira trilha para receber seu certificado"

---

### BLOCO C — Componentes Reutilizáveis a Especificar

Documente os seguintes componentes para uso no código:

| Componente | Uso |
|---|---|
| `<ProgressBar value={n} />` | Barra de progresso com cor --accent, animação de fill |
| `<StudentBadge phone={...} name={...} mode={...} />` | Avatar + nome + badge de modo (bot/humano) |
| `<CourseCard course={...} />` | Card de curso com glassmorphism e hover lift |
| `<QuizOption text={...} selected={...} correct={...} />` | Opção de quiz com estados visuais |
| `<CertCard cert={...} />` | Card de certificado com ações |
| `<WebhookEventRow event={...} />` | Linha do monitor de mensagens |
| `<ModeToggle studentId={...} />` | Toggle Bot/Humano inline |

---

## Instruções para o Stitch MCP

1. **Crie um projeto** chamado `"TDS LMS Lite v2"`
2. **Configure o Design System** com os tokens Aurora acima
3. **Para cada página** (B1 a B5) e cada aba admin (A1, A2, A3):
   - Crie um frame com o nome da página
   - Mobile-first para Portal Aluno (390×844px)
   - Desktop para Dashboard Admin (1440×900px)
4. **Use os componentes Aurora** já estabelecidos: glassmorphism cards, teal CTAs, gradientes radiais
5. **Exporte as especificações** de cada componente (medidas, espaçamento, cores exatas)

---

## Output Esperado

Ao final da sessão de design, salve em `docs/specs/2026-04-11-lms-lite-ui-components.md`:

```markdown
# Especificação de UI — LMS Lite v2

## Design System
[tokens confirmados]

## Páginas
### [Nome da Página]
- URL: ...
- Descrição: ...
- Componentes: [lista]
- Stitch Frame: [link ou referência]
- Notas de implementação: ...

## Componentes Reutilizáveis
### [NomeDoComponente]
- Props: ...
- Estados: ...
- Variantes visuais: ...
```

**Lembre-se:** Você é o BPM Designer. Não implemente código. Entregue especificações aprovadas para o Claude Code Agent implementar.
