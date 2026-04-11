# Especificação de UI — LMS Lite v2

## Design System: Aurora
O sistema de design Aurora foi desenvolvido para transmitir exclusividade, foco e tecnologia, utilizando uma paleta escura com transparências e reflexos que lembram o céu noturno e o progresso digital.

### Core Tokens
- **Background (Deep):** `#000a14` (Base de todas as páginas)
- **Surface (Panel):** `#001529` (Cards e painéis secundários)
- **Primary Blue:** `#003366` (Identidade e elementos estruturais)
- **Action Teal:** `#008080` (Destaque principal, CTAs e estados ativos)
- **Gold Accent:** `#f4bf00` (Progresso, recompensas e gamificação)
- **Typography:**
    - **Headings:** Lexend (SemiBold-ExtraBold, -0.02em spacing)
    - **Body/UI:** Inter (400-600 weight)

---

## Páginas Projetadas (Stitch)
Projeto: `TDS LMS Lite v2` (ID: `11352380544449777314`)

### Bloco A — Dashboard Admin
| Nome no Stitch | Descrição |
|---|---|
| **Dashboard - Comunidades** | Gestão de grupos WhatsApp de avisos gerais com cards glassmorphism. |
| **Monitor WhatsApp - TDS LMS Lite** | Feed em tempo real de mensagens com filtros de status e toggle bot/humano. |
| **Gestão de Grupos v2** | Atualização do GroupManager com vínculos RAG e progresso de turmas. |

### Bloco B — Portal do Aluno (Mobile-first)
| Nome no Stitch | Descrição |
|---|---|
| **Login - Portal do Aluno TDS** | Autenticação simples via WhatsApp/OTP com brand hero central. |
| **Dashboard do Aluno** | Hub central com progresso do curso atual e conquistas. |
| **Detalhes do Curso - TDS LMS** | Visualização de módulos por acordeão e status de quiz. |
| **Quiz - TDS LMS Lite v2** | UX focada em acessibilidade com botões grandes e feedback imediato. |
| **Meus Certificados (B5)** | Galeria de diplomas emitidos com hash de autenticidade e botões de compartilhamento. |

---

## Componentes Reutilizáveis

### `<ProgressBar value={number} />`
- **Uso:** Indica conclusão de módulos e progresso geral em Gold Accent.
- **Props:** `value` (0-100), `label` (opcional).
- **Estilo:** Height 8px, background `#ffffff08`, fill `{--accent}`, rounded 100px.

### `<StudentBadge {...props} />`
- **Uso:** Identificação rápida de alunos no monitor admin.
- **Props:** `phone`, `name`, `status` (novo/bot/humano).
- **Estilo:** Avatar circular 40px com indicador de status circular no canto inferior.

### `<CourseCard course={course} />`
- **Uso:** Listagem de trilhas no portal do aluno.
- **Visual:** Glassmorphism (`rgba(255,255,255,0.03)`), blur 10px, radius 24px.
- **Efeito:** Hover lift -4px com sombra teal difusa.

### `<QuizOption text={string} />`
- **Uso:** Botões de resposta em quizzes.
- **Visual:** Pill shape, width 100%, background semi-transparente.
- **Estados:** `selected` (border teal 2px), `correct` (green glow), `incorrect` (red glow).

### `<WebhookEventRow event={event} />`
- **Uso:** Linhas do Monitor WhatsApp.
- **Funcionalidade:** Exibe número, prévia da mensagem e toggle Bot/Humano.

### `<CertCard cert={cert} />`
- **Uso:** Card de certificado na lista de conquistas.
- **Visual:** Horizontal, com ícone de medalha em Gold e botão 'Baixar' em Teal.

---

## Notas de Implementação
1. **Glassmorphism:** Use `backdrop-filter: blur(10px)` em todos os cards de surface.
2. **Sombras Neon:** Utilize `box-shadow: 0 0 20px rgba(0, 128, 128, 0.15)` para elementos em foco (Teal).
3. **Responsividade:** O Portal do Aluno deve ser restrito a 400px de largura máxima em telas desktop para simular experiência mobile nativa.
4. **Animações:** Use `framer-motion` para transições de entrada dos cards (fade + slide up).
