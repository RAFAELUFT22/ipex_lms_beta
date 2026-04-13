# TDS LMS Lite — Production-Ready: Design Spec

**Data:** 2026-04-12
**Autor:** Arquiteto TDS (AI) + Claude Code
**Status:** Aprovado

---

## 1. Contexto e Objetivo

O TDS LMS Lite é um sistema de gestão de aprendizagem focado em mobilidade e acessibilidade via WhatsApp. Stack: FastAPI (Python), React/Vite (dashboard), AnythingLLM (RAG), Evolution API / WhatsApp Cloud API, banco de dados JSON (modo lite).

Este documento especifica as melhorias necessárias para levar o sistema ao estado **Production-Ready**, organizadas em 4 eixos:

1. **Segurança** — Middleware real, remoção de chaves hardcoded, validação de webhook
2. **Robustez de Dados** — `DatabaseManager` com file locking, atomic write e backup automático
3. **UX de Sessão** — Refresh silencioso de token, feedback semântico de OTP expirado
4. **Documentação** — Guias em PT-BR para admin, aluno e integrador técnico

---

## 2. Abordagem Geral

**Abordagem B — Módulo Core Extraído:**

- Criar `lms_lite_core.py` com `AdminMiddleware` e `DatabaseManager`
- `lms_lite_api.py` e `lms_lite_v2_routes.py` importam do core
- Sem reorganização de pacotes (sem risco ao Dockerfile/Dokploy)
- As funções `load_db()` / `save_db()` originais ficam como aliases temporários durante transição

---

## 3. Segurança

### 3.1 AdminMiddleware (FastAPI BaseHTTPMiddleware)

**Problema:** `require_admin()` é uma função manual — novas rotas adicionadas sem chamá-la ficam desprotegidas silenciosamente.

**Solução:**

```python
# lms_lite_core.py
from starlette.middleware.base import BaseHTTPMiddleware

class AdminMiddleware(BaseHTTPMiddleware):
    """Protege automaticamente todas as rotas /admin/* e /settings/*."""
    async def dispatch(self, request, call_next):
        protected = request.url.path.startswith(("/admin", "/settings"))
        if protected:
            key = request.headers.get("X-Admin-Key", "")
            expected = os.getenv("ADMIN_KEY")  # sem fallback hardcoded
            if not expected or key != expected:
                return JSONResponse({"detail": "unauthorized"}, status_code=401)
        return await call_next(request)
```

Registrado em `lms_lite_api.py`:
```python
app.add_middleware(AdminMiddleware)
```

A função `require_admin()` existente é **removida**. Qualquer rota que a chamava manualmente não precisa mais fazer isso.

### 3.2 Remoção de Chaves Hardcoded

| Localização | Problema | Correção |
|---|---|---|
| `lms_lite_api.py:36` | `os.getenv("ADMIN_KEY", "admin-tds-2026")` | Remover default — app recusa subir sem a variável |
| `dashboard-tds/src/lms_lite.js:2` | `ADMIN_KEY = 'admin-tds-2026'` | Trocar por `import.meta.env.VITE_ADMIN_KEY` |
| `dashboard-tds/src/App.jsx` | Comparação hardcoded em localStorage | Trocar por `import.meta.env.VITE_ADMIN_KEY` |
| `.env.tds` | Adicionar `ADMIN_KEY=<valor seguro>` | — |
| `dashboard-tds/.env` | Adicionar `VITE_ADMIN_KEY=<mesmo valor>` | — |

**Regra:** Se `ADMIN_KEY` não estiver definida no ambiente, a aplicação lança `ValueError` na inicialização. Sem fallbacks.

### 3.3 Validação de Assinatura do Webhook WhatsApp

**Problema:** `POST /whatsapp/webhook` é público — qualquer agente externo pode postar payloads e acionar queries ao AnythingLLM (custo de tokens).

**Solução:**

- **Evolution API (Baileys):** verificar header configurável via `WEBHOOK_SECRET` env var. Se `WEBHOOK_SECRET` não estiver definido, webhook aceita qualquer requisição com log de aviso.
- **WhatsApp Cloud API (Meta):** validar `X-Hub-Signature-256` usando HMAC-SHA256 com `WEBHOOK_SECRET`. Requisições sem assinatura válida retornam `HTTP 403`.

### 3.4 CORS Restrito

Trocar `allow_origins=["*"]` por lista configurável:

```python
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, ...)
```

Em produção, `.env.tds` define:
```
CORS_ORIGINS=https://dashboard.ipexdesenvolvimento.cloud,https://ops.ipexdesenvolvimento.cloud
```

---

## 4. DatabaseManager

### 4.1 Interface (Wrapper JSON — Abordagem A)

**Objetivo:** API limpa que abstrai leitura/escrita do JSON. Mesma semântica; troca interna por SQL no futuro sem alterar as rotas.

```python
# lms_lite_core.py
import threading, json, shutil
from pathlib import Path
from datetime import datetime

class DatabaseManager:
    MAX_BACKUPS = 10
    MAX_WEBHOOK_EVENTS = 100

    def __init__(self, db_path: str = "lms_lite_db.json",
                 backup_dir: str = "backups"):
        self.db_path = Path(db_path)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        self._lock = threading.Lock()
        self._defaults = {
            "students": {}, "certificates": {}, "communities": {},
            "webhook_events": [], "bot_group_links": {},
            "course_workspace_links": {}
        }

    def _load(self) -> dict:
        if not self.db_path.exists():
            return dict(self._defaults)
        with open(self.db_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for key, val in self._defaults.items():
            data.setdefault(key, val)
        return data

    def _save(self, data: dict) -> None:
        """Backup → atomic write (temp file + rename)."""
        # Backup
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"lms_lite_db_{ts}.json"
        if self.db_path.exists():
            shutil.copy2(self.db_path, backup_path)
        # Rotação: mantém apenas os últimos MAX_BACKUPS
        backups = sorted(self.backup_dir.glob("lms_lite_db_*.json"))
        for old in backups[:-self.MAX_BACKUPS]:
            old.unlink()
        # Atomic write
        tmp = self.db_path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        tmp.replace(self.db_path)

    # --- API pública ---

    def get_student(self, phone: str) -> dict | None:
        with self._lock:
            return self._load()["students"].get(phone)

    def save_student(self, phone: str, student_data: dict) -> None:
        with self._lock:
            data = self._load()
            data["students"][phone] = student_data
            self._save(data)

    def get_all_students(self) -> dict:
        with self._lock:
            return self._load()["students"]

    def get_certificates(self) -> dict:
        with self._lock:
            return self._load()["certificates"]

    def save_certificate(self, cert_hash: str, cert_data: dict) -> None:
        with self._lock:
            data = self._load()
            data["certificates"][cert_hash] = cert_data
            self._save(data)

    # Nota: settings continuam gerenciados pelo settings.json existente.
    # get_settings/save_settings operam em lms_lite_db.json["settings"]
    # e são reservados para uso futuro — fora do escopo desta iteração.
    def get_settings(self) -> dict:
        with self._lock:
            return self._load().get("settings", {})

    def save_settings(self, settings: dict) -> None:
        with self._lock:
            data = self._load()
            data["settings"] = settings
            self._save(data)

    def append_webhook_event(self, payload: dict) -> None:
        with self._lock:
            data = self._load()
            events = data.setdefault("webhook_events", [])
            events.append({"received_at": datetime.utcnow().isoformat(), "payload": payload})
            data["webhook_events"] = events[-self.MAX_WEBHOOK_EVENTS:]
            self._save(data)

    def get_bot_group_links(self) -> dict:
        with self._lock:
            return self._load().get("bot_group_links", {})

    def get_course_workspace_links(self) -> dict:
        with self._lock:
            return self._load().get("course_workspace_links", {})

    def save_course_workspace_link(self, course_slug: str, workspace_slug: str) -> None:
        with self._lock:
            data = self._load()
            data.setdefault("course_workspace_links", {})[course_slug] = workspace_slug
            self._save(data)
```

### 4.2 Instância Singleton

```python
# lms_lite_core.py (final do arquivo)
db = DatabaseManager()
```

Em `lms_lite_api.py` e `lms_lite_v2_routes.py`:
```python
from lms_lite_core import db
```

### 4.3 Aliases de Compatibilidade (Transição)

```python
# lms_lite_api.py — manter temporariamente para não quebrar chamadas existentes
# ATENÇÃO: save_db() chama db._save() que SEMPRE gera um backup antes de escrever.
# Isso é intencional: qualquer write via alias também é protegido.
def load_db():
    return db._load()

def save_db(data):
    db._save(data)
```

---

## 5. UX de Sessão e OTP

### 5.1 Códigos de Erro Semânticos (Backend)

| Situação | HTTP Status | `detail` | Significado |
|---|---|---|---|
| Token expirado | 401 | `"session_expired"` | Tentar refresh |
| Token inválido | 401 | `"unauthorized"` | Logout forçado |
| OTP expirado | 400 | `"otp_expired"` | Solicitar novo código |
| OTP incorreto | 400 | `"otp_invalid"` | Tentar novamente (até 3x) |

### 5.2 Endpoint de Refresh (Backend)

```
POST /auth/refresh
Header: Authorization: Bearer <token_atual>
Response 200: { "session_token": "<novo_token>", "expires_in": 28800 }
Response 401: { "detail": "session_expired" }
```

- Token atual ainda deve existir em `_sessions`
- Novo token gerado com `exp = now + 8h`
- Token antigo é removido de `_sessions`

### 5.3 Interceptor Global (Frontend — lms_lite.js)

```javascript
// Decodifica exp do JWT sem biblioteca (base64 do payload)
function getTokenExp(token) {
  try {
    return JSON.parse(atob(token.split('.')[1])).exp * 1000;
  } catch { return 0; }
}

async function apiFetch(path, options = {}) {
  const token = sessionStorage.getItem('session_token');

  // Pre-emptive refresh: se restar < 30 min, tenta renovar antes
  if (token) {
    const remaining = getTokenExp(token) - Date.now();
    if (remaining > 0 && remaining < 30 * 60 * 1000) {
      await tryRefresh(token); // silencioso, não bloqueia
    }
  }

  let res = await fetch(BASE_URL + path, addAuthHeaders(options, token));

  // Interceptor reativo: 401 session_expired → tenta refresh → repete
  if (res.status === 401) {
    const body = await res.json();
    if (body.detail === 'session_expired') {
      const refreshed = await tryRefresh(token);
      if (refreshed) {
        res = await fetch(BASE_URL + path, addAuthHeaders(options, refreshed));
      } else {
        sessionStorage.clear();
        showSessionExpiredModal(); // modal com botão "Fazer login novamente"
        throw new Error('session_expired');
      }
    }
  }
  return res;
}
```

### 5.4 Feedback OTP no Frontend

- Resposta `"otp_expired"` → mensagem: _"Código expirado. Solicite um novo código."_ + botão "Reenviar"
- Resposta `"otp_invalid"` → mensagem: _"Código incorreto. Você tem X tentativas restantes."_
- Após 3 tentativas inválidas → mensagem: _"Número de tentativas esgotado. Solicite um novo código."_

---

## 6. Documentação (PT-BR)

### 6.1 Arquivos a Criar

| Arquivo | Localização | Audiência |
|---|---|---|
| `README.md` | raiz do projeto | Dev / Ops |
| `docs/GUIA_ADMIN.md` | docs/ | Administrador TDS |
| `docs/GUIA_ALUNO.md` | docs/ | Aluno / usuário final |
| `docs/API_REFERENCE.md` | docs/ | Dev integrador |

### 6.2 README.md — Quick Start

Seções:
1. Pré-requisitos (Docker, Docker Compose, `.env.tds` preenchido)
2. Variáveis de ambiente obrigatórias (tabela: nome, descrição, exemplo)
3. Subir o ambiente (`docker compose -f docker-compose.lite.yml up -d`)
4. Verificar saúde (`curl http://localhost:8081/health`)
5. Acessar o dashboard (`http://localhost:5173`)

### 6.3 GUIA_ADMIN.md

Seções:
1. Vincular curso ao AnythingLLM Workspace (`POST /admin/courses/link_workspace`)
2. Conectar nova instância WhatsApp — Baileys vs Cloud API (comparativo + passos)
3. Exportar relatório de progresso dos alunos (CSV)
4. Rotacionar a `ADMIN_KEY` sem downtime
5. Restaurar backup do banco de dados
6. Checklist "Antes de ir para produção" (variáveis obrigatórias)

### 6.4 GUIA_ALUNO.md

Seções:
1. Como fazer login (fluxo OTP pelo WhatsApp)
2. Comandos do bot (tabela: `/duvida`, `/resumo`, `/progresso`, `/certificado`)
3. Acessar o portal web
4. FAQ (código expirado, curso não aparece, certificado não gerou)

### 6.5 API_REFERENCE.md

Gerado a partir do `/openapi.json` do FastAPI, organizado por grupos:
- **Auth:** `/auth/otp/request`, `/auth/otp/verify`, `/auth/refresh`
- **Aluno:** `/students/me`, `/students/progress`, `/courses`
- **Admin:** `/admin/students`, `/admin/courses/link_workspace`, `/admin/export/csv`
- **Webhook:** `/whatsapp/webhook`
- **Settings:** `/settings`

Cada endpoint documenta: método, path, headers, corpo JSON (entrada), exemplo de resposta (200 e erros).

---

## 7. Auditoria de Chaves (Tarefa 4)

### 7.1 Varredura Sistemática

Grep por padrões: strings com `key`, `token`, `secret`, `password`, `api_key` que não sejam `os.getenv()`.

### 7.2 Tabela de Mapeamento Completo

| Variável no Código | Env Var | Arquivo `.env.tds` | Obrigatório |
|---|---|---|---|
| `ADMIN_KEY` | `ADMIN_KEY` | `.env.tds` | Sim |
| `CERT_SALT` | `CERT_SALT` | `.env.tds` | Sim |
| `EVOLUTION_URL` | `EVOLUTION_URL` | `.env.tds` | Se usar Baileys |
| `EVOLUTION_API_KEY` | `EVOLUTION_API_KEY` | `.env.tds` | Se usar Baileys |
| `ANYTHINGLLM_URL` | `ANYTHINGLLM_URL` | `.env.tds` | Se usar RAG |
| `ANYTHINGLLM_API_KEY` | `ANYTHINGLLM_API_KEY` | `.env.tds` | Se usar RAG |
| `WEBHOOK_SECRET` | `WEBHOOK_SECRET` | `.env.tds` | Recomendado |
| `CORS_ORIGINS` | `CORS_ORIGINS` | `.env.tds` | Sim (produção) |
| `VITE_ADMIN_KEY` | `VITE_ADMIN_KEY` | `dashboard-tds/.env` | Sim |

---

## 8. Arquivos Criados / Modificados

| Arquivo | Ação | Descrição |
|---|---|---|
| `lms_lite_core.py` | **Criar** | `AdminMiddleware` + `DatabaseManager` + instância `db` |
| `lms_lite_api.py` | **Modificar** | Registrar middleware, remover `require_admin()`, substituir `load_db`/`save_db`, endpoint `/auth/refresh`, CORS configurável, erros semânticos |
| `lms_lite_v2_routes.py` | **Modificar** | Substituir `load_db`/`save_db`, validação de assinatura do webhook, corrigir typo `KeyOptional` |
| `dashboard-tds/src/lms_lite.js` | **Modificar** | Remover `ADMIN_KEY` hardcoded, interceptor de sessão, pre-emptive refresh, modal de expiração |
| `dashboard-tds/src/App.jsx` | **Modificar** | Trocar hardcoded por `import.meta.env.VITE_ADMIN_KEY` |
| `.env.tds` | **Modificar** | Adicionar `ADMIN_KEY`, `WEBHOOK_SECRET`, `CORS_ORIGINS` |
| `dashboard-tds/.env` | **Modificar** | Adicionar `VITE_ADMIN_KEY` |
| `README.md` | **Modificar** | Quick Start Docker completo |
| `docs/GUIA_ADMIN.md` | **Criar** | Guia operacional em PT-BR |
| `docs/GUIA_ALUNO.md` | **Criar** | Manual do usuário em PT-BR |
| `docs/API_REFERENCE.md` | **Criar** | Referência técnica de endpoints |

---

## 9. Critérios de Sucesso

- [ ] `grep -r "admin-tds-2026" .` retorna zero resultados (exceto `.git/`)
- [ ] `POST /admin/students` sem header `X-Admin-Key` retorna `401`
- [ ] Webhook com assinatura inválida retorna `403`
- [ ] `lms_lite_db.json` tem backup em `backups/` após primeiro write
- [ ] Token expirado manualmente → frontend exibe modal, não tela quebrada
- [ ] OTP de 5+ minutos → resposta `"otp_expired"`, não `"otp_invalid"`
- [ ] `docker compose -f docker-compose.lite.yml up -d` → sistema funcional em < 5 min seguindo o README
