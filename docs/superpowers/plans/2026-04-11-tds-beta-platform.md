# TDS Beta Platform Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix broadcasts com variáveis reais, portal do aluno com OTP via WhatsApp, certificados com QR code, e tutores com feedback de erro real — tudo usando `lms_lite_api.py` como backend.

**Architecture:** `lms_lite_api.py` (FastAPI) é a fonte da verdade para alunos, cursos e certificados. O frontend React chama esse backend via HTTP. Nenhuma chamada ao Supabase no caminho crítico do usuário. Autenticação no portal: OTP de 6 dígitos enviado via Evolution API → lms_lite valida → retorna token UUID de sessão.

**Tech Stack:** Python 3.12 + FastAPI (já no container), React + Vite, Evolution API (WhatsApp), `qrcode.react` (novo)

---

## File Map

### Criar
- `projeto-tds/dashboard-tds/src/pages/ValidateCert.jsx` — Página pública de validação de certificado por hash

### Modificar
- `projeto-tds/lms_lite_api.py` — Migrar para FastAPI, adicionar OTP/sessões, corrigir URL de validação
- `projeto-tds/dashboard-tds/src/api/lms_lite.js` — Trocar Supabase por chamadas HTTP ao lms_lite_api
- `projeto-tds/dashboard-tds/src/components/BroadcastCenter.jsx` — Trocar Supabase direto por `lmsLiteApi`
- `projeto-tds/dashboard-tds/src/components/TutorsManager.jsx` — Feedback de erro real + log por etapa
- `projeto-tds/dashboard-tds/src/components/StudentPortal.jsx` — Fluxo OTP + QR code do certificado
- `projeto-tds/dashboard-tds/src/App.jsx` — Adicionar rota pública `/validate/:hash`
- `projeto-tds/dashboard-tds/package.json` — Adicionar `qrcode.react`

---

## Task 1: Migrar `lms_lite_api.py` para FastAPI com OTP e sessões

**Files:**
- Modify: `projeto-tds/lms_lite_api.py`

O container já tem FastAPI e uvicorn instalados (`Dockerfile.api` linha 3). A migração elimina o código de roteamento manual e permite adicionar OTP e sessões de forma limpa.

- [ ] **Step 1: Substituir o conteúdo de `lms_lite_api.py` pelo código abaixo**

```python
import hashlib
import json
import os
import random
import secrets
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- CONFIG ---
DB_FILE = "/app/lms_lite_db.json"
COURSES_FILE = "/app/courses/tds/tds-courses-2026.json"
TDS_SECRET = os.getenv("CERT_SALT", "TDS_SECRET_2026")
EVOLUTION_URL = os.getenv("EVOLUTION_URL", "https://evolution.ipexdesenvolvimento.cloud")
EVOLUTION_KEY = os.getenv("EVOLUTION_KEY", "")
EVOLUTION_INSTANCE = os.getenv("EVOLUTION_INSTANCE", "tds_suporte_audiovisual")
VALIDATION_BASE_URL = os.getenv("VALIDATION_BASE_URL", "https://ops.ipexdesenvolvimento.cloud")

# In-memory stores (reset on restart — ok for beta)
_otp_store: dict = {}   # phone -> {"code": "123456", "expires": timestamp, "attempts": 0}
_sessions: dict = {}     # token -> {"phone": "556399...", "expires": timestamp}

app = FastAPI(title="TDS LMS Lite API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- DB HELPERS ---
def load_db() -> dict:
    if not Path(DB_FILE).exists():
        return {"students": {}, "certificates": {}}
    with open(DB_FILE) as f:
        db = json.load(f)
    db.setdefault("students", {})
    db.setdefault("certificates", {})
    return db


def save_db(db: dict):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)


def load_courses() -> list:
    try:
        with open(COURSES_FILE) as f:
            return json.load(f)
    except Exception:
        return []


def course_title(slug: str) -> str:
    for c in load_courses():
        if c.get("slug") == slug:
            return c.get("title", slug)
    return slug


def generate_cert_hash(whatsapp: str, course_slug: str) -> str:
    raw = f"{whatsapp}:{course_slug}:{TDS_SECRET}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def build_student_response(whatsapp: str, s: dict) -> dict:
    """Return student object with normalized enrollments list."""
    course_slug = s.get("current_course", "")
    progress = s.get("progress", 0)
    status = "completed" if progress >= 100 else "active"

    # Look up cert hash if course is complete
    cert_hash = None
    if status == "completed" and course_slug:
        cert_hash = generate_cert_hash(whatsapp, course_slug)

    enrollments = []
    if course_slug:
        enrollments.append({
            "id": f"{whatsapp}:{course_slug}",
            "status": status,
            "progress_percent": progress,
            "certificate_hash": cert_hash,
            "course": {
                "slug": course_slug,
                "title": course_title(course_slug),
            },
        })

    sisec = s.get("sisec_data", {})
    return {
        "whatsapp": whatsapp,
        "name": s.get("name", ""),
        "full_name": s.get("full_name") or s.get("name", ""),
        "cpf": s.get("cpf", ""),
        "localidade": s.get("localidade") or sisec.get("localidade", ""),
        "city": s.get("city") or sisec.get("localidade", ""),
        "role": s.get("role", "student"),
        "enrollments": enrollments,
    }


# --- MODELS ---
class OtpSendRequest(BaseModel):
    phone: str

class OtpVerifyRequest(BaseModel):
    phone: str
    code: str

class StudentCreate(BaseModel):
    whatsapp: str
    name: Optional[str] = None
    full_name: Optional[str] = None
    cpf: Optional[str] = None
    localidade: Optional[str] = None
    city: Optional[str] = None
    role: Optional[str] = "student"

class ProgressUpdate(BaseModel):
    whatsapp: str
    course_slug: str
    progress: int

class IssueCertRequest(BaseModel):
    whatsapp: str
    course_slug: str


# --- AUTH HELPER ---
def get_session(authorization: Optional[str]) -> Optional[str]:
    """Return phone from valid session token, or None."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    session = _sessions.get(token)
    if not session:
        return None
    if time.time() > session["expires"]:
        del _sessions[token]
        return None
    return session["phone"]


# --- ROUTES ---

@app.get("/health")
def health():
    return {"status": "ok"}


# Students
@app.get("/students")
def list_students():
    db = load_db()
    return [
        build_student_response(phone, s)
        for phone, s in db["students"].items()
    ]


@app.get("/student/{phone}")
def get_student(phone: str):
    db = load_db()
    s = db["students"].get(phone)
    if not s:
        raise HTTPException(404, "Aluno não encontrado")
    return build_student_response(phone, s)


@app.post("/student")
def upsert_student(body: StudentCreate):
    db = load_db()
    existing = db["students"].get(body.whatsapp, {})
    existing.update({k: v for k, v in body.dict().items() if v is not None})
    db["students"][body.whatsapp] = existing
    save_db(db)
    return {"status": "ok"}


@app.post("/update_progress")
def update_progress(body: ProgressUpdate):
    db = load_db()
    s = db["students"].get(body.whatsapp, {})
    s["progress"] = body.progress
    s["current_course"] = body.course_slug
    db["students"][body.whatsapp] = s
    save_db(db)
    return {"new_progress": body.progress}


# Courses
@app.get("/courses")
def get_courses():
    return load_courses()


# Certificates
@app.post("/issue_cert")
def issue_cert(body: IssueCertRequest):
    db = load_db()
    s = db["students"].get(body.whatsapp)
    if not s:
        raise HTTPException(404, "Aluno não encontrado")

    cert_hash = generate_cert_hash(body.whatsapp, body.course_slug)
    issue_date = datetime.now().strftime("%d/%m/%Y %H:%M")

    cert_data = {
        "cert_id": cert_hash,
        "student_name": s.get("full_name") or s.get("name", ""),
        "whatsapp": body.whatsapp,
        "course": body.course_slug,
        "course_title": course_title(body.course_slug),
        "issue_date": issue_date,
        "validation_url": f"{VALIDATION_BASE_URL}/validate/{cert_hash}",
    }
    db["certificates"][cert_hash] = cert_data
    save_db(db)
    return cert_data


@app.get("/validate_cert/{cert_hash}")
def validate_cert(cert_hash: str):
    db = load_db()
    cert = db["certificates"].get(cert_hash)
    if not cert:
        raise HTTPException(404, detail={"valid": False})
    return {"valid": True, **cert}


# OTP
@app.post("/otp/send")
def otp_send(body: OtpSendRequest):
    phone = body.phone.strip()
    # Rate-limit: ignore if sent < 60s ago
    existing = _otp_store.get(phone)
    if existing and time.time() < existing["expires"] - 240:
        return {"sent": True, "note": "already_sent"}

    code = str(random.randint(100000, 999999))
    _otp_store[phone] = {"code": code, "expires": time.time() + 300, "attempts": 0}

    # Send via Evolution API
    if EVOLUTION_KEY:
        try:
            requests.post(
                f"{EVOLUTION_URL}/message/sendText/{EVOLUTION_INSTANCE}",
                json={"number": phone, "text": f"🔐 Seu código TDS: *{code}*\n\nVálido por 5 minutos. Não compartilhe."},
                headers={"apikey": EVOLUTION_KEY},
                timeout=10,
            )
        except Exception as e:
            print(f"[OTP] Falha ao enviar via Evolution: {e}")
    else:
        print(f"[OTP DEV] Código para {phone}: {code}")

    return {"sent": True}


@app.post("/otp/verify")
def otp_verify(body: OtpVerifyRequest):
    phone = body.phone.strip()
    entry = _otp_store.get(phone)

    if not entry:
        raise HTTPException(400, "Nenhum código ativo. Solicite um novo.")
    if time.time() > entry["expires"]:
        del _otp_store[phone]
        raise HTTPException(400, "Código expirado. Solicite um novo.")
    if entry["attempts"] >= 3:
        del _otp_store[phone]
        raise HTTPException(429, "Muitas tentativas. Solicite um novo código.")

    if body.code.strip() != entry["code"]:
        _otp_store[phone]["attempts"] += 1
        raise HTTPException(400, "Código incorreto.")

    del _otp_store[phone]

    # Create session (8h TTL)
    token = secrets.token_urlsafe(32)
    _sessions[token] = {"phone": phone, "expires": time.time() + 28800}

    db = load_db()
    s = db["students"].get(phone)
    student = build_student_response(phone, s) if s else None

    return {"token": token, "student": student}


@app.get("/session/me")
def session_me(authorization: Optional[str] = Header(default=None)):
    phone = get_session(authorization)
    if not phone:
        raise HTTPException(401, "Sessão inválida ou expirada")
    db = load_db()
    s = db["students"].get(phone)
    if not s:
        raise HTTPException(404, "Aluno não encontrado")
    return build_student_response(phone, s)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
```

- [ ] **Step 2: Testar a API localmente**

```bash
cd /root/projeto-tds
docker compose -f docker-compose.lite.yml up -d --build lms-lite-api
sleep 5
curl -s https://api-lms.ipexdesenvolvimento.cloud/health | python3 -m json.tool
curl -s https://api-lms.ipexdesenvolvimento.cloud/students | python3 -m json.tool
curl -s https://api-lms.ipexdesenvolvimento.cloud/student/5563999374165 | python3 -m json.tool
```

Esperado: `{"status":"ok"}`, lista com 1 aluno, aluno com campo `enrollments`.

- [ ] **Step 3: Verificar endpoint de validação**

```bash
# Primeiro emitir um certificado de teste
curl -s -X POST https://api-lms.ipexdesenvolvimento.cloud/issue_cert \
  -H "Content-Type: application/json" \
  -d '{"whatsapp":"5563999374165","course_slug":"audiovisual-e-produ-o-de-conte-do-digital-2"}' \
  | python3 -m json.tool
```

Esperado: JSON com `cert_id`, `validation_url` contendo `ops.ipexdesenvolvimento.cloud/validate/...`

- [ ] **Step 4: Commit**

```bash
cd /root/projeto-tds
git add lms_lite_api.py
git commit -m "feat(api): migrate lms_lite to FastAPI with OTP, sessions, and cert validation"
```

---

## Task 2: Reescrever `src/api/lms_lite.js` — Supabase → HTTP API

**Files:**
- Modify: `projeto-tds/dashboard-tds/src/api/lms_lite.js`

- [ ] **Step 1: Substituir o conteúdo do arquivo**

```javascript
const API_BASE = import.meta.env.VITE_LMS_API_URL || 'https://api-lms.ipexdesenvolvimento.cloud';

async function apiFetch(path, options = {}) {
  const token = sessionStorage.getItem('tds_student_token');
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const lmsLiteApi = {
  getStudents: () => apiFetch('/students'),

  getStudent: (phone) => apiFetch(`/student/${phone}`),

  sendOtp: (phone) =>
    apiFetch('/otp/send', {
      method: 'POST',
      body: JSON.stringify({ phone }),
    }),

  verifyOtp: (phone, code) =>
    apiFetch('/otp/verify', {
      method: 'POST',
      body: JSON.stringify({ phone, code }),
    }),

  getMe: () => apiFetch('/session/me'),

  getCourses: () => apiFetch('/courses'),

  issueCert: (whatsapp, course_slug) =>
    apiFetch('/issue_cert', {
      method: 'POST',
      body: JSON.stringify({ whatsapp, course_slug }),
    }),

  validateCert: (hash) => apiFetch(`/validate_cert/${hash}`),
};
```

- [ ] **Step 2: Testar que a função getStudents resolve corretamente**

No browser, abrir o dashboard admin (`ops.ipexdesenvolvimento.cloud`), abrir console e rodar:

```javascript
import('/api/lms_lite.js').then(m => m.lmsLiteApi.getStudents().then(console.log))
```

Ou simplesmente verificar que o BroadcastCenter (próxima task) funciona após o rebuild.

- [ ] **Step 3: Commit**

```bash
cd /root/projeto-tds
git add dashboard-tds/src/api/lms_lite.js
git commit -m "feat(frontend): rewire lms_lite.js from Supabase to HTTP API"
```

---

## Task 3: Corrigir `BroadcastCenter.jsx` — variáveis reais

**Files:**
- Modify: `projeto-tds/dashboard-tds/src/components/BroadcastCenter.jsx`

- [ ] **Step 1: Remover o import do Supabase e substituir `startBroadcast`**

Localizar e remover a linha:
```javascript
import { supabase } from '../lib/supabase';
```

Adicionar no topo (junto com os outros imports):
```javascript
import { lmsLiteApi } from '../api/lms_lite';
```

- [ ] **Step 2: Substituir a função `startBroadcast` inteira**

Substituir de `const startBroadcast = async () => {` até o `};` fechador por:

```javascript
  const startBroadcast = async () => {
    const list = numbers.split('\n').map(n => n.trim()).filter(Boolean);
    setIsSending(true);
    setProgress({ current: 0, total: list.length });

    // Batch fetch: get all students from lms_lite
    let allStudents = [];
    try {
      allStudents = await lmsLiteApi.getStudents();
    } catch (e) {
      setLogs(prev => [`[${new Date().toLocaleTimeString()}] ❌ Erro ao buscar perfis: ${e.message}`, ...prev]);
    }

    const profileMap = allStudents.reduce((acc, s) => ({ ...acc, [s.whatsapp]: s }), {});

    for (let i = 0; i < list.length; i++) {
      const num = list[i];
      const studentProfile = profileMap[num] || {};
      const personalizedMessage = replaceVariables(message, studentProfile);

      try {
        await evolutionApi.sendMessage("tds_suporte_audiovisual", num, personalizedMessage);
        setLogs(prev => [`[${new Date().toLocaleTimeString()}] ✅ Enviado para ${studentProfile.full_name || studentProfile.name || num}`, ...prev]);
      } catch (e) {
        setLogs(prev => [`[${new Date().toLocaleTimeString()}] ❌ Erro para ${num}: ${e.message}`, ...prev]);
      }

      setProgress(prev => ({ ...prev, current: i + 1 }));

      if (i < list.length - 1) {
        const waitTime = delay * 1000 * (0.85 + Math.random() * 0.3);
        await new Promise(resolve => setTimeout(resolve, waitTime));
      }
    }

    setIsSending(false);
  };
```

- [ ] **Step 3: Commit**

```bash
cd /root/projeto-tds
git add dashboard-tds/src/components/BroadcastCenter.jsx
git commit -m "fix(broadcast): replace Supabase with lms_lite API for real variable replacement"
```

---

## Task 4: Corrigir `TutorsManager.jsx` — feedback de erro real

**Files:**
- Modify: `projeto-tds/dashboard-tds/src/components/TutorsManager.jsx`

- [ ] **Step 1: Adicionar estado `stepLogs` e substituir a função `createTutor`**

Após `const [status, setStatus] = useState(null);` adicionar:
```javascript
  const [stepLogs, setStepLogs] = useState([]);
  const addLog = (msg) => setStepLogs(prev => [...prev, `${new Date().toLocaleTimeString()} ${msg}`]);
```

- [ ] **Step 2: Substituir a função `createTutor` inteira**

```javascript
  const createTutor = async () => {
    setIsLoading(true);
    setStepLogs([]);
    setStatus(null);
    try {
      const instanceName = `tutor_${newTutorName.toLowerCase().replace(/\s/g, '_')}`;

      addLog('⏳ Criando instância na Evolution API...');
      await evolutionApi.createInstance(instanceName);
      addLog(`✅ Instância "${instanceName}" criada.`);

      addLog('⏳ Criando Inbox no Chatwoot...');
      const inbox = await chatwootApi.createInbox(`Tutor - ${newTutorName}`);
      addLog(`✅ Inbox criada (ID: ${inbox.id}).`);

      addLog('⏳ Vinculando Chatwoot na Evolution...');
      await evolutionApi.setChatwoot(instanceName, {
        enabled: true,
        accountId: "1",
        token: "w8BYLTQc1s5VMowjQw433rGy",
        url: "https://chat.ipexdesenvolvimento.cloud",
        inboxId: String(inbox.id),
        signMsg: true,
        reopenConversation: true,
        conversationPending: false,
      });
      addLog('✅ Chatwoot vinculado. Escaneie o QR Code para ativar.');

      setStatus({ type: 'success', message: `Tutor "${newTutorName}" provisionado! Escaneie o QR Code para ativar.` });
      setNewTutorName('');
      loadInstances();
    } catch (e) {
      const detail = e.response?.data?.message || e.message || 'Erro desconhecido';
      addLog(`❌ Falhou: ${detail}`);
      setStatus({ type: 'error', message: `Erro no provisionamento: ${detail}` });
    }
    setIsLoading(false);
  };
```

- [ ] **Step 3: Substituir a função `runFullHandoffTest` inteira**

```javascript
  const runFullHandoffTest = async () => {
    setIsAutoTesting(true);
    setStepLogs([]);
    setStatus(null);
    const targetPhone = "5563999374165";
    try {
      addLog(`⏳ Buscando contato ${targetPhone} no Chatwoot...`);
      await chatwootApi.assignAndGreet(targetPhone, "Rafael Tutor Senior");
      addLog('✅ Contato encontrado. Conversa assumida e apresentação enviada.');
      setStatus({ type: 'success', message: 'Tutor assumiu a conversa! Aguardando 3s para devolver ao bot...' });

      await new Promise(r => setTimeout(r, 3000));

      addLog('⏳ Resolvendo conversa e reativando bot...');
      await chatwootApi.resolveAndReturnToBot(targetPhone);
      addLog('✅ Atendimento resolvido. Bot reativado.');
      setStatus({ type: 'success', message: 'Ciclo completo! Bot reativado com sucesso.' });
    } catch (e) {
      const detail = e.message || 'Erro desconhecido';
      addLog(`❌ Falhou: ${detail}`);
      setStatus({ type: 'error', message: `Falha no teste: ${detail}` });
    }
    setIsAutoTesting(false);
  };
```

- [ ] **Step 4: Adicionar painel de logs no JSX — inserir antes do bloco `{status && ...}`**

Localizar o trecho `{status && (` e inserir antes dele:

```jsx
      {stepLogs.length > 0 && (
        <div className="glass-card p-4 font-mono text-xs space-y-1">
          <p className="text-text-muted uppercase tracking-widest text-[10px] mb-2">Log de Operação</p>
          {stepLogs.map((l, i) => (
            <div key={i} className="py-0.5 border-b border-white/5 text-text-dim">{l}</div>
          ))}
        </div>
      )}
```

- [ ] **Step 5: Commit**

```bash
cd /root/projeto-tds
git add dashboard-tds/src/components/TutorsManager.jsx
git commit -m "fix(tutors): add real error propagation and step-by-step operation log"
```

---

## Task 5: Adicionar `qrcode.react` ao package.json

**Files:**
- Modify: `projeto-tds/dashboard-tds/package.json`

- [ ] **Step 1: Adicionar a dependência**

No arquivo `package.json`, dentro de `"dependencies"`, adicionar após `"lucide-react": "..."`:

```json
    "qrcode.react": "^4.2.0",
```

- [ ] **Step 2: Commit**

```bash
cd /root/projeto-tds
git add dashboard-tds/package.json
git commit -m "chore: add qrcode.react dependency for certificate QR codes"
```

---

## Task 6: Reescrever `StudentPortal.jsx` — OTP + QR code do certificado

**Files:**
- Modify: `projeto-tds/dashboard-tds/src/components/StudentPortal.jsx`

- [ ] **Step 1: Substituir o conteúdo completo do arquivo**

```jsx
import React, { useState, useEffect } from 'react';
import { BookOpen, GraduationCap, Award, MessageSquare, Download, CheckCircle, Clock, Send, RefreshCw } from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';
import { lmsLiteApi } from '../api/lms_lite';
import CertificatePreview from './CertificatePreview';

export default function StudentPortal() {
  const [step, setStep] = useState('phone'); // 'phone' | 'otp' | 'portal'
  const [phone, setPhone] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [student, setStudent] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [certPreview, setCertPreview] = useState(null);

  // Restore session on mount
  useEffect(() => {
    const token = sessionStorage.getItem('tds_student_token');
    if (token) {
      lmsLiteApi.getMe()
        .then(data => { setStudent(data); setStep('portal'); })
        .catch(() => sessionStorage.removeItem('tds_student_token'));
    }
  }, []);

  const handleSendOtp = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await lmsLiteApi.sendOtp(phone.trim());
      setStep('otp');
    } catch (err) {
      setError(err.message || 'Erro ao enviar código. Tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const { token, student: s } = await lmsLiteApi.verifyOtp(phone.trim(), otpCode.trim());
      sessionStorage.setItem('tds_student_token', token);
      setStudent(s);
      setStep('portal');
    } catch (err) {
      setError(err.message || 'Código inválido. Tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    sessionStorage.removeItem('tds_student_token');
    setStudent(null);
    setPhone('');
    setOtpCode('');
    setStep('phone');
  };

  // --- LOGIN: Phone step ---
  if (step === 'phone') {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="glass-card p-8 max-w-md w-full">
          <div className="flex flex-col items-center mb-8">
            <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center text-primary mb-4">
              <GraduationCap size={32} />
            </div>
            <h2 className="text-2xl font-bold">Portal do Aluno TDS</h2>
            <p className="text-text-dim text-sm text-center mt-2">
              Informe seu número de WhatsApp para receber um código de acesso.
            </p>
          </div>
          <form onSubmit={handleSendOtp} className="space-y-4">
            <div className="input-group">
              <label className="input-label">WhatsApp (com código do país)</label>
              <input
                type="tel"
                className="w-full"
                placeholder="Ex: 5563999999999"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                required
              />
            </div>
            {error && <p className="text-red-500 text-xs italic">{error}</p>}
            <button type="submit" className="btn btn-primary w-full py-3" disabled={loading}>
              {loading ? 'Enviando...' : <><Send size={16} className="inline mr-2" />Receber Código por WhatsApp</>}
            </button>
          </form>
        </div>
      </div>
    );
  }

  // --- LOGIN: OTP step ---
  if (step === 'otp') {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="glass-card p-8 max-w-md w-full">
          <div className="flex flex-col items-center mb-8">
            <div className="w-16 h-16 bg-secondary/10 rounded-full flex items-center justify-center text-secondary mb-4">
              <Send size={32} />
            </div>
            <h2 className="text-2xl font-bold">Código Enviado!</h2>
            <p className="text-text-dim text-sm text-center mt-2">
              Verifique o WhatsApp de <strong>{phone}</strong> e insira o código de 6 dígitos abaixo.
            </p>
          </div>
          <form onSubmit={handleVerifyOtp} className="space-y-4">
            <div className="input-group">
              <label className="input-label">Código de Acesso</label>
              <input
                type="text"
                className="w-full text-center text-2xl tracking-widest font-mono"
                placeholder="000000"
                maxLength={6}
                value={otpCode}
                onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ''))}
                required
              />
            </div>
            {error && <p className="text-red-500 text-xs italic">{error}</p>}
            <button type="submit" className="btn btn-primary w-full py-3" disabled={loading}>
              {loading ? 'Verificando...' : 'Entrar no Portal'}
            </button>
            <button
              type="button"
              className="text-xs text-text-muted hover:text-primary underline w-full text-center"
              onClick={() => { setStep('phone'); setError(''); setOtpCode(''); }}
            >
              <RefreshCw size={12} className="inline mr-1" />Usar outro número
            </button>
          </form>
        </div>
      </div>
    );
  }

  // --- PORTAL ---
  if (!student) return null;

  const completedEnrollment = student.enrollments?.find(e => e.status === 'completed');

  return (
    <div className="space-y-8 animate-fade">
      {certPreview && (
        <CertificatePreview
          student={student}
          enrollment={certPreview}
          onClose={() => setCertPreview(null)}
        />
      )}

      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-text-main">
            Olá, {student.full_name || student.name}!
          </h2>
          <p className="text-text-dim">Bem-vindo à sua trilha de desenvolvimento.</p>
        </div>
        <button onClick={handleLogout} className="text-xs text-text-muted hover:text-red-500 underline">
          Sair do Portal
        </button>
      </div>

      {/* Minha Trilha */}
      <div className="glass-card p-6">
        <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
          <BookOpen size={20} className="text-primary" />
          Minha Trilha de Aprendizado
        </h3>
        <div className="space-y-6">
          {student.enrollments?.map((enroll) => (
            <div key={enroll.id} className="bg-white/5 border border-white/5 rounded-2xl p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h4 className="font-bold text-lg">{enroll.course?.title}</h4>
                  <p className="text-xs text-text-dim uppercase tracking-widest">{enroll.status}</p>
                </div>
                {enroll.status === 'completed' ? (
                  <span className="bg-emerald-500/20 text-emerald-500 px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1">
                    <CheckCircle size={14} /> Concluído
                  </span>
                ) : (
                  <span className="bg-primary/20 text-primary px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1">
                    <Clock size={14} /> Em Andamento
                  </span>
                )}
              </div>
              <div className="space-y-2 mb-6">
                <div className="flex justify-between text-xs font-bold">
                  <span>Progresso</span>
                  <span>{enroll.progress_percent}%</span>
                </div>
                <div className="w-full bg-white/10 h-2 rounded-full overflow-hidden">
                  <div className="bg-primary h-full transition-all duration-1000" style={{ width: `${enroll.progress_percent}%` }} />
                </div>
              </div>
              <div className="flex gap-3">
                <a
                  href="https://wa.me/5563999374165?text=/ajuda"
                  target="_blank"
                  rel="noreferrer"
                  className="btn btn-outline flex-1 py-2 text-sm gap-2"
                >
                  <MessageSquare size={16} /> Falar com Tutor
                </a>
                {enroll.status === 'completed' && (
                  <button
                    className="btn btn-primary flex-1 py-2 text-sm gap-2"
                    onClick={() => setCertPreview(enroll)}
                  >
                    <Download size={16} /> Ver Certificado
                  </button>
                )}
              </div>
            </div>
          ))}
          {(!student.enrollments || student.enrollments.length === 0) && (
            <p className="text-center text-text-dim italic">Nenhuma matrícula encontrada.</p>
          )}
        </div>
      </div>

      {/* Certificado com QR Code */}
      {completedEnrollment?.certificate_hash && (
        <div className="glass-card p-6 border-amber-500/20 bg-amber-500/5">
          <h3 className="text-xl font-bold text-amber-500 flex items-center gap-2 mb-4">
            <Award size={24} /> Certificado Validado
          </h3>
          <div className="flex flex-col md:flex-row gap-6 items-center">
            <div className="bg-white p-3 rounded-xl">
              <QRCodeSVG
                value={`https://ops.ipexdesenvolvimento.cloud/validate/${completedEnrollment.certificate_hash}`}
                size={140}
              />
            </div>
            <div className="flex-1">
              <p className="text-sm text-text-dim mb-2">
                Escaneie o QR code para verificar a autenticidade deste certificado.
              </p>
              <p className="font-mono text-xs text-text-muted break-all">
                Hash: {completedEnrollment.certificate_hash}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Guia */}
      <div className="glass-card p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <BookOpen size={18} className="text-primary" /> Como Usar o TDS
        </h3>
        {[
          { step: '1', title: 'Fale com o robô', desc: 'Envie uma mensagem para nosso WhatsApp. O assistente vai te guiar no curso.' },
          { step: '2', title: 'Peça ajuda humana', desc: 'A qualquer momento, envie "/ajuda" para ser atendido por um tutor real.' },
          { step: '3', title: 'Obtenha seu certificado', desc: 'Ao concluir o curso, envie "/certificado" e receba aqui no portal.' },
        ].map(({ step, title, desc }) => (
          <div key={step} className="flex gap-4 mb-4">
            <div className="w-8 h-8 rounded-full bg-primary/20 text-primary flex items-center justify-center font-bold text-sm shrink-0">
              {step}
            </div>
            <div>
              <p className="font-semibold text-sm">{title}</p>
              <p className="text-xs text-text-dim">{desc}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
cd /root/projeto-tds
git add dashboard-tds/src/components/StudentPortal.jsx
git commit -m "feat(portal): OTP login flow, QR code certificate, and guide section"
```

---

## Task 7: Criar página pública `ValidateCert.jsx`

**Files:**
- Create: `projeto-tds/dashboard-tds/src/pages/ValidateCert.jsx`

- [ ] **Step 1: Criar o arquivo**

```jsx
import React, { useState, useEffect } from 'react';
import { CheckCircle, XCircle, Loader } from 'lucide-react';
import { lmsLiteApi } from '../api/lms_lite';

export default function ValidateCert({ hash }) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!hash) { setLoading(false); return; }
    lmsLiteApi.validateCert(hash)
      .then(data => setResult(data))
      .catch(() => setResult({ valid: false }))
      .finally(() => setLoading(false));
  }, [hash]);

  if (loading) return (
    <div className="flex items-center justify-center min-h-screen bg-deep">
      <Loader className="animate-spin text-primary" size={40} />
    </div>
  );

  return (
    <div className="flex items-center justify-center min-h-screen bg-deep p-4">
      <div className="glass-card p-8 max-w-md w-full text-center">
        {result?.valid ? (
          <>
            <CheckCircle size={56} className="text-emerald-500 mx-auto mb-4" />
            <h1 className="text-2xl font-bold text-emerald-500 mb-2">Certificado Válido</h1>
            <p className="text-text-dim text-sm mb-6">Este certificado é autêntico e foi emitido pelo TDS.</p>
            <div className="bg-white/5 rounded-xl p-4 text-left space-y-2 text-sm">
              <div><span className="text-text-muted">Aluno:</span> <span className="font-bold">{result.student_name}</span></div>
              <div><span className="text-text-muted">Curso:</span> <span className="font-bold">{result.course_title || result.course}</span></div>
              <div><span className="text-text-muted">Emitido em:</span> <span className="font-bold">{result.issue_date}</span></div>
              <div><span className="text-text-muted">Hash:</span> <span className="font-mono text-xs text-text-muted">{hash}</span></div>
            </div>
          </>
        ) : (
          <>
            <XCircle size={56} className="text-red-500 mx-auto mb-4" />
            <h1 className="text-2xl font-bold text-red-500 mb-2">Certificado Inválido</h1>
            <p className="text-text-dim text-sm">Este hash não corresponde a nenhum certificado emitido pelo TDS.</p>
          </>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
cd /root/projeto-tds
git add dashboard-tds/src/pages/ValidateCert.jsx
git commit -m "feat(portal): public certificate validation page"
```

---

## Task 8: Adicionar rota `/validate/:hash` em `App.jsx`

**Files:**
- Modify: `projeto-tds/dashboard-tds/src/App.jsx`

- [ ] **Step 1: Adicionar import do ValidateCert**

Após `import StudentPortal from './components/StudentPortal';` adicionar:

```javascript
import ValidateCert from './pages/ValidateCert';
```

- [ ] **Step 2: Adicionar detecção de rota de validação no topo do componente `App`**

Logo após `export default function App() {`, antes de qualquer `useState`, adicionar:

```javascript
  // Public route: certificate validation
  const urlHash = window.location.pathname.match(/^\/validate\/([a-f0-9]+)$/)?.[1];
  if (urlHash) return <ValidateCert hash={urlHash} />;
```

- [ ] **Step 3: Commit**

```bash
cd /root/projeto-tds
git add dashboard-tds/src/App.jsx
git commit -m "feat(routing): add public /validate/:hash route for certificate verification"
```

---

## Task 9: Rebuild dos containers

- [ ] **Step 1: Rebuild do dashboard**

```bash
cd /root/projeto-tds
docker compose -f docker-compose.lite.yml up -d --build lms-lite-dashboard
```

Esperado: build completo (não cached — package.json mudou), container subindo.

- [ ] **Step 2: Verificar que o dashboard subiu corretamente**

```bash
docker logs lms-lite-dashboard --tail 20
curl -s -o /dev/null -w "%{http_code}" https://ops.ipexdesenvolvimento.cloud
```

Esperado: logs de nginx, código HTTP `200`.

- [ ] **Step 3: Testar o portal do aluno**

Acessar `https://ops.ipexdesenvolvimento.cloud`, clicar no ícone de capelo (Visão Aluno), e verificar que a tela de OTP aparece.

- [ ] **Step 4: Testar a validação pública**

```bash
# Pegar o cert_hash do certificado emitido na Task 1
HASH=$(curl -s https://api-lms.ipexdesenvolvimento.cloud/validate_cert/ | python3 -c "import sys,json; certs=json.load(sys.stdin); print(list(certs.keys())[0] if certs else 'none')" 2>/dev/null)
# Ou usar o hash gerado na Task 1, Step 3
curl -s https://api-lms.ipexdesenvolvimento.cloud/validate_cert/$HASH | python3 -m json.tool
```

Esperado: JSON com `valid: true`, nome do aluno, curso e data.

- [ ] **Step 5: Commit final de verificação**

```bash
cd /root/projeto-tds
git log --oneline -8
```

---

## Checklist de cobertura do spec

| Requisito | Task |
|---|---|
| OTP via WhatsApp (lms_lite_api.py) | Task 1 |
| JWT de sessão (token UUID) | Task 1 |
| Portal: Home + progresso | Task 6 |
| Portal: Certificado + QR code | Task 6 |
| Portal: Guia simples | Task 6 |
| Broadcast com variáveis reais | Task 2 + Task 3 |
| Certificado SHA-256 real | Task 1 (`generate_cert_hash`) |
| Endpoint `/validate_cert/:hash` | Task 1 |
| Página pública de validação | Task 7 + Task 8 |
| Tutores com erro real | Task 4 |
| Tutores com log por etapa | Task 4 |
