# TDS Beta Platform — Design Spec
**Data:** 2026-04-11  
**Status:** Aprovado

---

## Contexto

O TDS (Territórios de Desenvolvimento Social) é uma plataforma LMS de inclusão social que usa WhatsApp como interface principal para alunos. O sistema atual tem 5 pilares (Evolution API, n8n, AnythingLLM, Chatwoot, Dashboard Admin React), mas carece de:

1. Portal do aluno acessível
2. Login sem senha para alunos
3. Broadcast com variáveis reais (hoje ficam em branco)
4. Certificados com validação real (SHA-256)
5. Tutores provisionados sem erro + feedback visual correto

**Decisão de escopo beta:** Usar `lms_lite_api.py` (FastAPI + `lms_lite_db.json`) como fonte da verdade. Frappe LMS excluído desta fase.

---

## Arquitetura

```
┌─────────────────────────────────────────────────────────┐
│                    ALUNO (WhatsApp)                     │
└────────────────────────┬────────────────────────────────┘
                         │
                    Evolution API
                         │
              ┌──────────┴───────────┐
              │         n8n          │
              │  (OTP gerado aqui)   │
              └──────────┬───────────┘
                         │
          ┌──────────────┼──────────────┐
          ↓              ↓              ↓
   lms_lite_api     Supabase Auth   AnythingLLM
   (dados beta)     (JWT/sessão)    (RAG tutor)
          ↓              ↓
   lms_lite_db.json    token JWT
          ↓              ↓
          └──────────────┘
                  ↓
         Portal do Aluno (React)
         ops.ipexdesenvolvimento.cloud/portal
```

### Responsabilidades por serviço

| Serviço | Responsabilidade |
|---|---|
| `lms_lite_api.py` | Alunos, cursos, matrículas, certificados, OTP, JWT, validação |
| Evolution API | Envio de mensagens WhatsApp (OTP, broadcast, certificado) |
| n8n | Orquestração: OTP flow, broadcast, handoff |
| Chatwoot | Inbox humana para tutores |
| Dashboard React | Admin panel + Portal do aluno (`/portal`) |

**Nota sobre Supabase:** O phone auth do Supabase requer Twilio (pago). Para o beta WhatsApp-first, o JWT é emitido diretamente pelo `lms_lite_api.py` (via `PyJWT`). Supabase pode ser adicionado como camada de Auth na fase pós-beta se necessário.

---

## Funcionalidade 1 — Login do Aluno (OTP via WhatsApp)

### Fluxo

```
1. Aluno acessa /portal → informa número WhatsApp
2. Portal chama POST /api/otp/send { phone }
3. lms_lite_api gera código 6 dígitos, salva em memória com TTL 5min
4. n8n (via webhook) envia código pelo Evolution API ao aluno
5. Aluno digita código no portal
6. Portal chama POST /api/otp/verify { phone, code }
7. lms_lite_api valida → gera JWT assinado com PyJWT (payload: phone, exp: 8h)
8. Retorna JWT → salvo em sessionStorage
9. Portal carrega dados do aluno via GET /api/students/{phone}
```

### Endpoints novos em lms_lite_api.py

```
POST /api/otp/send    { phone: str } → { sent: true }
POST /api/otp/verify  { phone: str, code: str } → { token: str, student: obj }
```

### Segurança
- OTP expira em 5 minutos
- Máximo 3 tentativas por número (bloqueio 15min)
- OTP armazenado em dict em memória (suficiente para beta)

---

## Funcionalidade 2 — Portal do Aluno

**Rota:** `ops.ipexdesenvolvimento.cloud/portal`  
**Componente:** `src/pages/StudentPortal.jsx` (novo arquivo)  
**Auth:** JWT no sessionStorage, verificado a cada rota

### Telas

#### 2.1 Home
- Nome do aluno (de `lms_lite_db.json`)
- Curso atual + barra de progresso (`progress_percent`)
- Botão "Falar com Tutor" → abre `wa.me/` com número da instância do tutor

#### 2.2 Meu Certificado
- Exibe certificado se `enrollment.status == 'completed'`
- Botão "Baixar PDF" (html2canvas + jsPDF, já existente em `CertificatePreview.jsx`)
- QR Code gerado na tela apontando para `/validate/{hash}`
- Mensagem de encorajamento se ainda em andamento

#### 2.3 Guia
- Conteúdo estático em JSON (sem Supabase knowledge_base nesta fase)
- Três seções: "Como usar o robô", "Como pedir ajuda", "Como obter o certificado"
- Accordion mobile-first, linguagem simples

#### 2.4 Logout
- Limpa sessionStorage, redireciona para `/portal`

### Design
- Mobile-first (320px mínimo)
- Reutiliza CSS classes existentes do dashboard (`glass-card`, `btn`, `btn-primary`)
- Dependência nova: `qrcode.react` (verificar se já existe no `package.json`; caso não, adicionar)

---

## Funcionalidade 3 — Certificado com SHA-256 Real

### Geração (lms_lite_api.py)

```python
import hashlib, os

SECRET_SALT = os.getenv("CERT_SALT", "tds-beta-salt-2026")

def generate_cert_hash(student_id: str, course_id: str, issue_date: str) -> str:
    raw = f"{student_id}:{course_id}:{issue_date}:{SECRET_SALT}"
    return hashlib.sha256(raw.encode()).hexdigest()
```

Hash salvo em `enrollments[].certificate_hash` no `lms_lite_db.json`.

### Endpoint de validação pública

```
GET /validate/{hash}
→ 200: { valid: true, student_name, course_title, completion_date }
→ 404: { valid: false }
```

URL no QR Code: `https://ops.ipexdesenvolvimento.cloud/validate/{hash}`

### Endpoint de emissão

```
POST /issue_cert { student_id, course_id }
→ Gera hash real
→ Salva no JSON
→ Retorna { cert_hash, issue_date }
```

---

## Funcionalidade 4 — Broadcast com Variáveis Reais

### Problema atual
`BroadcastCenter.jsx` chama `supabase.from('profiles')` → retorna vazio porque Supabase não tem dados.

### Correção
Substituir chamada Supabase por `lmsLiteApi.getStudents()` (já existe em `src/api/lms_lite.js`).

O `variableReplacer.js` já funciona corretamente — só precisa receber o objeto de perfil populado.

### Mapeamento de campos

| Variável no template | Campo em lms_lite_db.json |
|---|---|
| `{nome}` / `{name}` | `student.name` |
| `{whatsapp}` | `student.whatsapp` |
| `{cpf}` | `student.cpf` |
| `{localidade}` / `{cidade}` | `student.localidade` |
| `{curso}` | `course.title` (via enrollment) |

---

## Funcionalidade 5 — Tutores: Feedback Real de Erro

### Problema atual
`TutorsManager.jsx` chama `setStatus({ type: 'success' })` independente do resultado da API.

### Correção
- Envolver todas as chamadas de API em try/catch com propagação real do erro
- Exibir mensagem de erro específica da resposta HTTP (ex: "401 Unauthorized", "Inbox já existe")
- Adicionar estado `errorDetail` separado do `status` genérico
- Botão "Executar Teste": mostrar log de cada etapa (✓ Contato encontrado → ✓ Conversa aberta → ✓ Mensagem enviada)

---

## Funcionalidade 6 — Rota de Validação Pública

```
GET /validate/{hash}
```

Rota pública (sem auth) no `lms_lite_api.py`.  
Também acessível via página React simples em `/validate/:hash` para renderizar o certificado no browser.

---

## O que NÃO entra nesta fase beta

- Quizzes/provas no portal
- Sincronização com Frappe LMS
- Email / SMTP
- Push notifications
- Multi-idioma

---

## Ordem de implementação sugerida

1. `lms_lite_api.py` — endpoints OTP + SHA-256 + validação
2. `BroadcastCenter.jsx` — trocar fonte de dados Supabase → lms_lite
3. `TutorsManager.jsx` — corrigir feedback de erro real
4. `StudentPortal.jsx` — portal do aluno (Home + Certificado + Guia)
5. `App.jsx` — adicionar rota `/portal` e `/validate/:hash`
6. Rebuild do container dashboard
