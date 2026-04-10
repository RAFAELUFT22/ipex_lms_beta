# Portal de Acompanhamento de Desempenho e Progresso

## Objetivo

Interface web (LMS Lite — Next.js) onde o aluno acompanha:
- Progresso nos cursos
- Histórico de quizzes
- Certificados emitidos e disponíveis para download

---

## 1. Rotas do Portal

| Rota | Componente | Descrição |
| :--- | :--- | :--- |
| `/` | `Home` | Site institucional + CTA de matrícula |
| `/login` | `Login` | Autenticação por telefone (WhatsApp OTP) |
| `/dashboard` | `Dashboard` | Visão geral do aluno logado |
| `/curso/[slug]` | `CourseDetail` | Detalhe do curso + lista de quizzes |
| `/quiz/[id]` | `QuizPlayer` | Interface de resposta do quiz |
| `/certificados` | `Certificates` | Lista de certificados do aluno |
| `/certificado/verificar` | `VerifyPublic` | Verificação pública (sem login) |

---

## 2. Componente Dashboard

```
┌─────────────────────────────────────────────────┐
│  Olá, [Nome do Aluno]          [Logo Parceiro]  │
├─────────────────────────────────────────────────┤
│  SEUS CURSOS                                    │
│  ┌────────────────────┐  ┌────────────────────┐ │
│  │ Gestão Financeira  │  │ Segurança Alimentar│ │
│  │ ████████░░  80%    │  │ ████░░░░░░  40%    │ │
│  │ [Continuar]        │  │ [Iniciar Quiz]     │ │
│  └────────────────────┘  └────────────────────┘ │
├─────────────────────────────────────────────────┤
│  CERTIFICADOS                                   │
│  ✓ Gestão Financeira — emitido 01/04/2026       │
│    [Baixar PDF]  [Compartilhar]                 │
└─────────────────────────────────────────────────┘
```

---

## 3. API Backend (n8n como "Backend for Frontend")

O portal Next.js consome endpoints do n8n via HTTP:

| Endpoint n8n | Método | Retorno |
| :--- | :--- | :--- |
| `/webhook/aluno/progresso` | GET | Lista de cursos + % concluído por aluno |
| `/webhook/aluno/quiz/[id]` | GET | Perguntas do quiz |
| `/webhook/aluno/quiz/[id]/responder` | POST | Resultado + salva no banco |
| `/webhook/aluno/certificados` | GET | Lista de certificados com URL do PDF |

**Autenticação:** JWT gerado pelo n8n no login via OTP WhatsApp.
Token com TTL de 7 dias, renovado automaticamente.

---

## 4. Autenticação por WhatsApp OTP

Fluxo de login sem senha:

```
1. Aluno informa telefone no /login
2. n8n envia código OTP via Evolution API (WhatsApp)
3. Aluno digita código no portal
4. n8n valida e retorna JWT
5. Portal armazena JWT no localStorage/cookie httpOnly
```

---

## 5. Barra de Progresso por Curso

Cálculo:

```
progresso = (quizzes_corretos / total_quizzes_curso) * 100
```

Exibido como barra colorida:
- `0–49%` → vermelho
- `50–69%` → amarelo
- `70–99%` → verde
- `100%` → azul (certificado disponível)

---

## 6. Stack Técnica do Portal

| Camada | Tecnologia |
| :--- | :--- |
| Frontend | Next.js 14 (App Router) + Tailwind CSS |
| Componentes UI | shadcn/ui |
| Gráficos de progresso | Recharts |
| Geração de PDF certificado | Gotenberg (serviço Docker) |
| Armazenamento de arquivos | MinIO (S3-compatible, self-hosted) |
| Auth | JWT via n8n + OTP WhatsApp |

---

## 7. Prioridade de Implementação

| # | Feature | Fase |
| :--- | :--- | :--- |
| 1 | Site institucional (`/`) | **MVP** |
| 2 | Login OTP WhatsApp | **MVP** |
| 3 | Dashboard com progresso | **MVP** |
| 4 | Quiz player | **MVP** |
| 5 | Certificados (PDF + download) | **MVP** |
| 6 | Página de verificação pública | MVP |
| 7 | Notificações push / e-mail | Fase 2 |
| 8 | Ranking / gamificação | Fase 2 |
