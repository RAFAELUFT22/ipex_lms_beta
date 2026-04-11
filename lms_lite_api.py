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
DB_FILE = os.getenv("DB_FILE", "/app/lms_lite_db.json")
SETTINGS_FILE = os.getenv("SETTINGS_FILE", "/app/settings.json")
COURSES_FILE = os.getenv("COURSES_FILE", "/app/courses/tds/tds-courses-2026.json")

# Fallback paths for local development
if not Path(DB_FILE).parent.exists() and Path("./lms_lite_db.json").exists():
    DB_FILE = "./lms_lite_db.json"
if not Path(SETTINGS_FILE).parent.exists():
    if Path("./settings.json").exists():
        SETTINGS_FILE = "./settings.json"
    else:
        SETTINGS_FILE = "settings.json" # create in current dir if app dir missing

TDS_SECRET = os.getenv("CERT_SALT", "TDS_SECRET_2026")
ADMIN_KEY = os.getenv("ADMIN_KEY", "admin-tds-2026")

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


SETTINGS_DEFAULTS = {
    "anythingllm_url": "https://llm.ipexdesenvolvimento.cloud",
    "anythingllm_key": "",
    "anythingllm_workspace": "tds-lms-knowledge",
    "openrouter_key": "",
    "openrouter_model": "openai/gpt-4o-mini",
    "evolution_url": "https://evolution.ipexdesenvolvimento.cloud",
    "evolution_key": "",
    "evolution_instance": "tds_suporte_audiovisual",
    "chatwoot_url": "https://chat.ipexdesenvolvimento.cloud",
    "chatwoot_token": "",
    "chatwoot_inbox_id": "",
    "wa_cloud_token": "",
    "wa_phone_number_id": "",
    "wa_business_id": "",
    "supabase_url": "https://api-lms.ipexdesenvolvimento.cloud",
    "supabase_service_key": "",
    "chatwoot_website_token": "",
}


def load_settings() -> dict:
    if not Path(SETTINGS_FILE).exists():
        return dict(SETTINGS_DEFAULTS)
    with open(SETTINGS_FILE) as f:
        saved = json.load(f)
    result = dict(SETTINGS_DEFAULTS)
    result.update(saved)
    
    # Add Supabase if not present in defaults but in env
    if not result.get("supabase_url"):
        result["supabase_url"] = os.getenv("SUPABASE_URL", "https://api-lms.ipexdesenvolvimento.cloud")
    if not result.get("supabase_service_key"):
        result["supabase_service_key"] = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    return result


def save_settings(data: dict):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


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
        "catraca": {
            "estado": s.get("estado_catraca", "inativo"),
            "modulo": s.get("modulo_atual", 0),
            "secao": s.get("secao_atual", 0),
        }
    }


def get_supabase_client():
    settings = load_settings()
    url = settings.get("supabase_url")
    key = settings.get("supabase_service_key")
    if not url or not key:
        return None
    # Use direct requests to avoid adding big dependencies if possible
    # but for simplicity we assume the user might have supabase-py or we can just use headers
    return {"url": url, "headers": {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}}


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
    existing.update({k: v for k, v in body.model_dump().items() if v is not None})
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

    if s.get("progress", 0) < 100 or s.get("current_course") != body.course_slug:
        raise HTTPException(400, "Aluno não concluiu o curso.")

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
        return {"valid": False}
    return {"valid": True, **cert}


# OTP
@app.post("/otp/send")
def otp_send(body: OtpSendRequest):
    phone = body.phone.strip()
    existing = _otp_store.get(phone)
    if existing and time.time() < existing["expires"] - 240:
        return {"sent": True, "note": "already_sent"}

    code = str(random.randint(100000, 999999))
    _otp_store[phone] = {"code": code, "expires": time.time() + 300, "attempts": 0}

    settings = load_settings()
    evo_url = settings.get("evolution_url")
    evo_key = settings.get("evolution_key")
    evo_inst = settings.get("evolution_instance")

    if evo_key and evo_url:
        try:
            requests.post(
                f"{evo_url}/message/sendText/{evo_inst}",
                json={"number": phone, "text": f"🔐 Seu código TDS: *{code}*\n\nVálido por 5 minutos. Não compartilhe."},
                headers={"apikey": evo_key},
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


# Settings (admin only — requires X-Admin-Key header)
def require_admin(x_admin_key: Optional[str] = Header(default=None)):
    if x_admin_key != ADMIN_KEY:
        raise HTTPException(401, "Chave administrativa inválida")


@app.get("/settings")
def get_settings(x_admin_key: Optional[str] = Header(default=None)):
    require_admin(x_admin_key)
    return load_settings()


class SettingsUpdate(BaseModel):
    anythingllm_url: Optional[str] = None
    anythingllm_key: Optional[str] = None
    anythingllm_workspace: Optional[str] = None
    openrouter_key: Optional[str] = None
    openrouter_model: Optional[str] = None
    evolution_url: Optional[str] = None
    evolution_key: Optional[str] = None
    evolution_instance: Optional[str] = None
    chatwoot_url: Optional[str] = None
    chatwoot_token: Optional[str] = None
    chatwoot_inbox_id: Optional[str] = None
    wa_cloud_token: Optional[str] = None
    wa_phone_number_id: Optional[str] = None
    wa_business_id: Optional[str] = None
    supabase_url: Optional[str] = None
    supabase_service_key: Optional[str] = None
    chatwoot_website_token: Optional[str] = None


@app.put("/settings")
def put_settings(body: SettingsUpdate, x_admin_key: Optional[str] = Header(default=None)):
    require_admin(x_admin_key)
    current = load_settings()
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    current.update(updates)
    save_settings(current)
    return {"status": "saved"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
