import hashlib
import json
import os
import random
import secrets
import threading
import time
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal, Optional

import requests
import csv
import io
from fastapi import FastAPI, HTTPException, Header, File, UploadFile, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, Response
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from lms_lite_v2_routes import router as v2_router, send_unified_reply
from templates.certificate_template import generate_certificate_pdf

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
ADMIN_KEY = os.getenv("ADMIN_KEY")  # sem fallback — None faz admin routes retornarem 500
VALIDATION_BASE_URL = os.getenv("VALIDATION_BASE_URL", "https://ops.ipexdesenvolvimento.cloud")

# Google Sheets — service account key path
GOOGLE_KEY_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_PATH", "/app/google-service-account.json")
GOOGLE_SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive.readonly",
]

# In-memory stores (reset on restart — ok for beta)
_otp_store: dict = {}   # phone -> {"code": "123456", "expires": timestamp, "attempts": 0}
_sessions: dict = {}     # token -> {"phone": "556399...", "expires": timestamp}
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="otp/verify")

# Thread lock para operações de escrita no DB JSON
_db_lock = threading.Lock()

app = FastAPI(title="TDS LMS Lite API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v2_router)


# --- DB HELPERS ---
def load_db() -> dict:
    if not Path(DB_FILE).exists():
        return {"students": {}, "certificates": {}, "communities": {}, "webhook_events": [], "quiz_bank": {}, "notification_log": [], "tracking": [], "course_workspace_links": {}}
    with open(DB_FILE) as f:
        db = json.load(f)
    db.setdefault("students", {})
    db.setdefault("certificates", {})
    db.setdefault("communities", {})
    db.setdefault("webhook_events", [])
    db.setdefault("quiz_bank", {})
    db.setdefault("notification_log", [])
    db.setdefault("tracking", [])
    db.setdefault("course_workspace_links", {})
    return db


def save_db(db: dict):
    """Atomic write via temp file + rename para evitar JSON corrompido em crash."""
    with _db_lock:
        tmp = Path(DB_FILE + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=2, ensure_ascii=False)
        tmp.replace(Path(DB_FILE))


SETTINGS_DEFAULTS = {
    "anythingllm_url": "https://llm.ipexdesenvolvimento.cloud",
    "anythingllm_key": "",
    "anythingllm_workspace": "tds",
    "openrouter_key": "",
    "openrouter_model": "google/gemini-2.0-flash-lite-001",
    "evolution_url": "https://evolution.ipexdesenvolvimento.cloud",
    "evolution_key": "",
    "evolution_instance": "tds_suporte_audiovisual",
    "chatwoot_url": "https://chat.ipexdesenvolvimento.cloud",
    "chatwoot_token": "",
    "theme_primary": "#6366f1",
    "theme_secondary": "#f43f5e",
    "logo_url": "https://ipexdesenvolvimento.cloud/logo.png",
    "company_name": "TDS - Territórios de Desenvolvimento Social",
    "chatwoot_website_token": "",
    "google_sheets_url": "",
    "google_sheets_tab": "Sheet1",
    "google_service_account_path": "",
}


def load_settings() -> dict:
    if not Path(SETTINGS_FILE).exists():
        return dict(SETTINGS_DEFAULTS)
    with open(SETTINGS_FILE) as f:
        saved = json.load(f)
    result = dict(SETTINGS_DEFAULTS)
    result.update(saved)
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
        quiz_results = s.get("enrollments", {}).get(course_slug, {}).get("quiz_results")
        enrollments.append({
            "id": f"{whatsapp}:{course_slug}",
            "status": status,
            "progress_percent": progress,
            "certificate_hash": cert_hash,
            "quiz_results": quiz_results,
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
        "last_activity_at": s.get("last_activity_at"),
        "enrollments": enrollments,
        "catraca": {
            "estado": s.get("estado_catraca", "inativo"),
            "modulo": s.get("modulo_atual", 0),
            "secao": s.get("secao_atual", 0),
        }
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
    last_activity_at: Optional[str] = None
    sisec_data: Optional[dict] = Field(default_factory=dict)

class SisecUpdate(BaseModel):
    whatsapp: str
    data: dict

class EvolutionGroupCreate(BaseModel):
    groupName: str
    description: Optional[str] = ""
    participants: list[str] = []

class ProgressUpdate(BaseModel):
    whatsapp: str
    course_slug: str
    progress: int

class IssueCertRequest(BaseModel):
    whatsapp: str
    course_slug: str

class QuizSubmit(BaseModel):
    phone: str
    course_slug: str
    answers: list[int]


class QuizQuestion(BaseModel):
    text: str
    options: list[str]
    correct: int


class QuizCreateRequest(BaseModel):
    questions: list[QuizQuestion]


class BulkStudentItem(BaseModel):
    whatsapp: str
    full_name: str
    cpf: Optional[str] = None
    localidade: Optional[str] = None
    course_slug: Optional[str] = None


class BulkStudentsRequest(BaseModel):
    students: list[BulkStudentItem] = Field(default_factory=list)


class EnrollmentRequest(BaseModel):
    whatsapp: str
    full_name: str
    cpf: Optional[str] = None
    localidade: Optional[str] = None
    course_slug: str


class NotifyRequest(BaseModel):
    target: str
    message: str
    channel: Literal["whatsapp", "telegram", "both"] = "whatsapp"


class NotifyScheduleRequest(NotifyRequest):
    delay_minutes: int


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


def get_current_student(token: str) -> dict:
    session = _sessions.get(token)
    if not session or time.time() > session["expires"]:
        raise HTTPException(401, "Sessão inválida ou expirada")
    db = load_db()
    phone = session["phone"]
    student = db["students"].get(phone)
    if not student:
        raise HTTPException(404, "Aluno não encontrado")
    return {"whatsapp": phone, **student}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_iso_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except Exception:
        return None


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
    existing["updated_at"] = now_iso()
    existing.setdefault("created_at", now_iso())
    db["students"][body.whatsapp] = existing
    save_db(db)
    return {"status": "ok"}


@app.post("/update_progress")
def update_progress(body: ProgressUpdate):
    db = load_db()
    s = db["students"].get(body.whatsapp, {})
    s["progress"] = body.progress
    s["current_course"] = body.course_slug
    s["last_activity_at"] = now_iso()
    s["updated_at"] = now_iso()
    db["students"][body.whatsapp] = s
    tracking = db.setdefault("tracking", [])
    tracking.append({
        "type": "lesson_view",
        "whatsapp": body.whatsapp,
        "course_slug": body.course_slug,
        "progress": body.progress,
        "timestamp": now_iso(),
    })
    save_db(db)
    return {"new_progress": body.progress}


@app.post("/admin/courses/{course_slug}/quiz")
def save_course_quiz(course_slug: str, body: QuizCreateRequest, x_admin_key: Optional[str] = Header(default=None)):
    require_admin(x_admin_key)
    db = load_db()
    db["quiz_bank"][course_slug] = [q.model_dump() for q in body.questions]
    save_db(db)
    return {"status": "saved", "course_slug": course_slug, "questions": len(body.questions)}


@app.get("/quiz/{course_slug}")
def get_course_quiz(course_slug: str):
    db = load_db()
    questions = db.get("quiz_bank", {}).get(course_slug, [])
    sanitized = [{"text": q.get("text", ""), "options": q.get("options", [])} for q in questions]
    return {"course_slug": course_slug, "questions": sanitized}


@app.post("/quiz/submit")
async def submit_quiz(data: QuizSubmit, token: str = Depends(oauth2_scheme)):
    student = get_current_student(token)
    if student["whatsapp"] != data.phone:
        raise HTTPException(403, "Você só pode enviar o quiz da sua própria conta.")

    db = load_db()
    questions = db.get("quiz_bank", {}).get(data.course_slug)
    if not questions:
        raise HTTPException(404, "Quiz não encontrado para este curso")

    correct = sum(
        1 for i, q in enumerate(questions)
        if i < len(data.answers) and data.answers[i] == q["correct"]
    )
    total = len(questions)
    passed = correct >= math.ceil(total / 2)

    student_record = db["students"].setdefault(data.phone, {})
    enrollments = student_record.setdefault("enrollments", {})
    course_enrollment = enrollments.setdefault(data.course_slug, {})
    course_enrollment["quiz_results"] = {
        "score": correct,
        "total": total,
        "passed": passed,
        "updated_at": now_iso(),
    }
    student_record["last_activity_at"] = now_iso()
    db["students"][data.phone] = student_record
    save_db(db)
    return {"status": "ok", "score": correct, "total": total, "passed": passed, "quiz_results": course_enrollment["quiz_results"]}


@app.get("/student/me/quiz/{course_slug}")
def get_my_quiz_result(course_slug: str, token: str = Depends(oauth2_scheme)):
    student = get_current_student(token)
    enrollments = student.get("enrollments", {})
    quiz_results = enrollments.get(course_slug, {}).get("quiz_results")
    return {"course_slug": course_slug, "quiz_results": quiz_results}


@app.post("/enrollment/request")
def enrollment_request(body: EnrollmentRequest):
    db = load_db()
    existing = db["students"].get(body.whatsapp, {})
    existing.update({
        "whatsapp": body.whatsapp,
        "name": body.full_name,
        "full_name": body.full_name,
        "cpf": body.cpf or existing.get("cpf", ""),
        "localidade": body.localidade or existing.get("localidade", ""),
        "current_course": body.course_slug,
    })
    existing.setdefault("progress", 0)
    existing.setdefault("consent_date", now_iso())
    existing.setdefault("created_at", now_iso())
    existing["updated_at"] = now_iso()
    db["students"][body.whatsapp] = existing
    save_db(db)

    # Auto-provision AnythingLLM account (non-blocking, best-effort)
    llm_credentials = None
    try:
        from lms_lite_v2_routes import (
            _provision_llm_account, resolve_workspace, load_settings as v2_load_settings
        )
        v2_settings = v2_load_settings()
        workspace_slug = resolve_workspace(db, body.course_slug,
                                           fallback=v2_settings.get("anythingllm_workspace", "tds"))
        result = _provision_llm_account(body.whatsapp, body.full_name, workspace_slug, v2_settings)
        if result["ok"]:
            db["students"][body.whatsapp].setdefault("llm_account", {}).update({
                "username": result["username"],
                "workspace_slug": workspace_slug,
                "llm_url": result["llm_url"],
                "provisioned_at": now_iso(),
            })
            save_db(db)
            llm_credentials = {
                "username": result["username"],
                "password": result["password"],
                "llm_url": result["llm_url"],
            }
    except Exception as exc:
        print(f"[enrollment] LLM provision skipped: {exc}")

    return {"ok": True, "whatsapp": body.whatsapp, "consent_date": existing["consent_date"],
            "llm_account": llm_credentials}


def _resolve_notification_recipients(db: dict, target: str) -> list[str]:
    students = db.get("students", {})
    if target == "all":
        return list(students.keys())
    if target.startswith("course:"):
        slug = target.split(":", 1)[1]
        recipients = []
        for phone, s in students.items():
            enrollments = s.get("enrollments", {})
            if slug in enrollments or s.get("current_course") == slug:
                recipients.append(phone)
        return recipients
    if target.startswith("inactive:"):
        try:
            days = int(target.split(":", 1)[1])
        except ValueError as exc:
            raise HTTPException(400, "Target inactive inválido. Ex.: inactive:7") from exc
        threshold = datetime.now(timezone.utc) - timedelta(days=days)
        recipients = []
        for phone, s in students.items():
            raw = s.get("last_activity_at")
            if not raw:
                continue
            try:
                last_activity = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            except ValueError:
                continue
            if last_activity < threshold:
                recipients.append(phone)
        return recipients
    raise HTTPException(400, "Target inválido. Use all, course:{slug} ou inactive:{days}")


def _send_notification(body: NotifyRequest) -> dict:
    db = load_db()
    recipients = _resolve_notification_recipients(db, body.target)
    sent = 0
    failed = 0
    for phone in recipients:
        try:
            send_unified_reply(phone=phone, message=body.message, channel=body.channel)
            sent += 1
        except Exception:
            failed += 1

    log_entry = {
        "target": body.target,
        "message": body.message,
        "channel": body.channel,
        "sent": sent,
        "failed": failed,
        "recipients": recipients,
        "sent_at": now_iso(),
    }
    db.setdefault("notification_log", [])
    db["notification_log"] = ([log_entry] + db["notification_log"])[:10]
    save_db(db)
    return {"sent": sent, "failed": failed, "recipients": recipients}


@app.post("/admin/notify")
def admin_notify(body: NotifyRequest, x_admin_key: Optional[str] = Header(default=None)):
    require_admin(x_admin_key)
    return _send_notification(body)


@app.post("/admin/notify/schedule")
def admin_notify_schedule(body: NotifyScheduleRequest, x_admin_key: Optional[str] = Header(default=None)):
    require_admin(x_admin_key)
    if body.delay_minutes < 0:
        raise HTTPException(400, "delay_minutes deve ser >= 0")
    payload = NotifyRequest(target=body.target, message=body.message, channel=body.channel)
    timer = threading.Timer(body.delay_minutes * 60, _send_notification, args=[payload])
    timer.daemon = True
    timer.start()
    return {"status": "scheduled", "delay_minutes": body.delay_minutes}


@app.get("/admin/notify/log")
def list_notify_log(x_admin_key: Optional[str] = Header(default=None)):
    require_admin(x_admin_key)
    db = load_db()
    return {"items": db.get("notification_log", [])[:10]}


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


@app.get("/cert/{cert_hash}/pdf")
def download_certificate_pdf(cert_hash: str):
    db = load_db()
    cert = db["certificates"].get(cert_hash)
    if not cert:
        raise HTTPException(404, "Certificado não encontrado")
    pdf_bytes = generate_certificate_pdf(cert)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="certificado_{cert_hash}.pdf"'},
    )


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

    n8n_url = settings.get("n8n_webhook_url", "")
    if n8n_url:
        try:
            requests.post(n8n_url, json={"phone": phone, "code": code}, timeout=10)
        except Exception as e:
            print(f"[OTP] Falha ao chamar n8n: {e}")
    elif evo_key and evo_url:
        try:
            requests.post(
                f"{evo_url}/message/sendText/{evo_inst}",
                json={
                    "number": phone,
                    "text": f"🔐 Seu código TDS: *{code}*\n\nVálido por 5 minutos. Não compartilhe com ninguém.",
                },
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
    if s:
        s["last_activity_at"] = now_iso()
        s["updated_at"] = now_iso()
        db["students"][phone] = s
        save_db(db)
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


@app.post("/auth/refresh")
def auth_refresh(authorization: Optional[str] = Header(default=None)):
    """Renova sessão existente — retorna novo token com mais 8h de validade."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Token ausente")
    old_token = authorization.split(" ", 1)[1]
    session = _sessions.get(old_token)
    if not session or time.time() > session["expires"]:
        raise HTTPException(401, detail="session_expired")
    new_token = secrets.token_urlsafe(32)
    _sessions[new_token] = {"phone": session["phone"], "expires": time.time() + 28800}
    del _sessions[old_token]
    return {"session_token": new_token}


# Settings (admin only — requires X-Admin-Key header)
def require_admin(x_admin_key: Optional[str] = Header(default=None)):
    if not ADMIN_KEY:
        raise HTTPException(500, "ADMIN_KEY não configurada no servidor")
    if not x_admin_key or x_admin_key != ADMIN_KEY:
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
    chatwoot_website_token: Optional[str] = None
    theme_primary: Optional[str] = None
    theme_secondary: Optional[str] = None
    logo_url: Optional[str] = None
    company_name: Optional[str] = None
    google_sheets_url: Optional[str] = None
    google_sheets_tab: Optional[str] = None
    google_service_account_path: Optional[str] = None


@app.put("/settings")
def put_settings(body: SettingsUpdate, x_admin_key: Optional[str] = Header(default=None)):
    require_admin(x_admin_key)
    current = load_settings()
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    current.update(updates)
    save_settings(current)
    return {"status": "saved"}


# Agents Management

class AgentProvisionRequest(BaseModel):
    name: str
    course_slug: Optional[str] = "geral"

@app.get("/agents")
def list_agents(x_admin_key: Optional[str] = Header(default=None)):
    require_admin(x_admin_key)
    settings = load_settings()
    llm_url = settings.get("anythingllm_url", "http://anythingllm:3001")
    llm_key = settings.get("anythingllm_key")
    
    if not llm_key:
        return []
        
    try:
        resp = requests.get(f"{llm_url}/api/v1/workspaces", headers={"Authorization": f"Bearer {llm_key}"}, timeout=5)
        if resp.status_code == 200:
            return resp.json().get("workspaces", [])
    except Exception as e:
        print(f"Error listing agents: {e}")
    
    return []

@app.post("/agents/provision")
def provision_agent_route(body: AgentProvisionRequest, x_admin_key: Optional[str] = Header(default=None)):
    require_admin(x_admin_key)
    # Import here to avoid circular or early deps issues
    import subprocess
    
    try:
        # Run the script we just created
        cmd = ["python3", "/root/projeto-tds/scripts/agent_factory.py", body.name]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return {"status": "ok", "message": f"Agent {body.name} provisioned successfully.", "output": result.stdout}
        else:
            raise HTTPException(500, f"Factory Error: {result.stderr}")
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/whatsapp/groups")
def list_whatsapp_groups(x_admin_key: Optional[str] = Header(default=None)):
    require_admin(x_admin_key)
    settings = load_settings()
    evo_url = settings.get("evolution_url")
    evo_key = settings.get("evolution_key")
    evo_inst = settings.get("evolution_instance")
    
    if not evo_url or not evo_key:
        return []
        
    try:
        # Fetch all groups for the configured instance (Baileys only)
        url = f"{evo_url}/group/fetchAllGroups/{evo_inst}?getParticipants=false"
        resp = requests.get(url, headers={"apikey": evo_key}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list):
                return data
            # Cloud API returns error dict — not supported
            return []
    except Exception as e:
        print(f"Error fetching WhatsApp groups: {e}")
    
    return []


# --- GOOGLE SHEETS HELPERS ---

def get_gspread_client():
    """Retorna cliente gspread autenticado se a chave de serviço estiver configurada."""
    key_file = GOOGLE_KEY_FILE
    try:
        settings = load_settings()
        settings_path = settings.get("google_service_account_path", "")
        if settings_path and Path(settings_path).exists():
            key_file = settings_path
    except Exception:
        pass

    if not Path(key_file).exists():
        return None

    try:
        import gspread
        from google.oauth2.service_account import Credentials
        creds = Credentials.from_service_account_file(key_file, scopes=GOOGLE_SCOPES)
        return gspread.authorize(creds)
    except Exception as e:
        print(f"[Google Sheets] Erro de autenticação: {e}")
        return None


def _sheet_csv_fallback(url: str, tab: Optional[str] = None) -> dict:
    """Baixa planilha pública via CSV export."""
    export_url = url
    if "/edit" in url or "/view" in url:
        base = url.split("/edit")[0].split("/view")[0]
        export_url = base + "/export?format=csv"
        if "gid=" in url:
            gid = url.split("gid=")[1].split("&")[0]
            export_url += f"&gid={gid}"

    resp = requests.get(export_url, timeout=15)
    if resp.status_code != 200:
        raise HTTPException(
            resp.status_code,
            "Falha ao baixar planilha. Verifique se ela é pública ou configure a Chave Google."
        )
    content = resp.content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))
    rows = [row for row in reader]
    headers = list(reader.fieldnames or [])
    return {"headers": headers, "rows": rows, "method": "public_csv"}


class SheetsImportRequest(BaseModel):
    url: str
    tab: Optional[str] = None
    column_map: dict  # {"whatsapp": "Coluna Planilha", "full_name": "Outra Coluna", ...}
    dry_run: bool = False


@app.post("/settings/google-key")
async def upload_google_key(
    file: UploadFile = File(...),
    x_admin_key: Optional[str] = Header(default=None),
):
    """Faz upload da chave JSON de conta de serviço Google para autenticar Google Sheets."""
    require_admin(x_admin_key)
    content = await file.read()

    try:
        key_data = json.loads(content)
    except Exception:
        raise HTTPException(400, "Arquivo não é um JSON válido")

    required_fields = ["type", "project_id", "private_key", "client_email"]
    missing = [f for f in required_fields if f not in key_data]
    if missing:
        raise HTTPException(400, f"JSON inválido: campos ausentes: {missing}")
    if key_data.get("type") != "service_account":
        raise HTTPException(400, "Deve ser uma chave de conta de serviço (type: service_account)")

    key_path = Path(GOOGLE_KEY_FILE)
    key_path.parent.mkdir(parents=True, exist_ok=True)
    with open(key_path, "wb") as f:
        f.write(content)

    current = load_settings()
    current["google_service_account_path"] = str(key_path)
    save_settings(current)

    return {
        "status": "ok",
        "project_id": key_data.get("project_id"),
        "client_email": key_data.get("client_email"),
    }


@app.get("/settings/google-key/status")
def google_key_status(x_admin_key: Optional[str] = Header(default=None)):
    """Retorna status da chave Google configurada."""
    require_admin(x_admin_key)
    settings = load_settings()
    key_path = settings.get("google_service_account_path") or GOOGLE_KEY_FILE
    if not Path(key_path).exists():
        return {"configured": False}
    try:
        with open(key_path) as f:
            key_data = json.load(f)
        return {
            "configured": True,
            "project_id": key_data.get("project_id"),
            "client_email": key_data.get("client_email"),
        }
    except Exception:
        return {"configured": False, "error": "Arquivo de chave corrompido"}


@app.get("/external/sheets")
def fetch_external_sheet(
    url: str,
    tab: Optional[str] = None,
    x_admin_key: Optional[str] = Header(default=None),
):
    """Lê uma planilha Google. Usa conta de serviço se configurada, caso contrário CSV público."""
    require_admin(x_admin_key)
    if "docs.google.com/spreadsheets/d/" not in url:
        raise HTTPException(400, "URL de planilha inválida")

    client = get_gspread_client()
    if client:
        try:
            sh = client.open_by_url(url)
            worksheet = sh.worksheet(tab) if tab else sh.get_worksheet(0)
            records = worksheet.get_all_records()
            headers = list(records[0].keys()) if records else []
            return {"headers": headers, "rows": records, "method": "authenticated"}
        except Exception as e:
            print(f"[Google Sheets] gspread falhou, usando CSV: {e}")

    try:
        return _sheet_csv_fallback(url, tab)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Erro ao processar planilha: {str(e)}")


@app.post("/admin/import/sheets")
def import_from_sheets(body: SheetsImportRequest, x_admin_key: Optional[str] = Header(default=None)):
    """
    Importa alunos de uma planilha Google para o banco de dados.
    column_map: mapeamento de campo interno → nome da coluna na planilha.
    Ex: {"whatsapp": "Telefone", "full_name": "Nome Completo", "localidade": "Cidade"}
    """
    require_admin(x_admin_key)

    rows = []
    client = get_gspread_client()

    if client:
        try:
            sh = client.open_by_url(body.url)
            worksheet = sh.worksheet(body.tab) if body.tab else sh.get_worksheet(0)
            rows = worksheet.get_all_records()
        except Exception as e:
            raise HTTPException(500, f"Erro ao ler planilha via API Google: {str(e)}")
    else:
        try:
            result = _sheet_csv_fallback(body.url, body.tab)
            rows = result["rows"]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(500, f"Erro ao baixar planilha: {str(e)}")

    mapped = []
    for row in rows:
        student: dict = {}
        for field, col in body.column_map.items():
            student[field] = str(row.get(col, "")).strip()
        if not student.get("whatsapp"):
            continue
        student["whatsapp"] = "".join(filter(str.isdigit, student["whatsapp"]))
        if student["whatsapp"]:
            mapped.append(student)

    if body.dry_run:
        return {
            "dry_run": True,
            "total_rows": len(rows),
            "importable": len(mapped),
            "preview": mapped[:10],
        }

    db = load_db()
    created = 0
    updated = 0
    for student in mapped:
        phone = student["whatsapp"]
        existing = db["students"].get(phone, {})
        for k, v in student.items():
            if v:
                existing[k] = v
        existing.setdefault("created_at", now_iso())
        existing["updated_at"] = now_iso()
        existing["whatsapp"] = phone
        if "name" not in existing and existing.get("full_name"):
            existing["name"] = existing["full_name"]
        if phone in db["students"]:
            updated += 1
        else:
            created += 1
        db["students"][phone] = existing

    save_db(db)
    return {
        "dry_run": False,
        "total_rows": len(rows),
        "importable": len(mapped),
        "created": created,
        "updated": updated,
    }


@app.get("/admin/students/export")
def export_students_csv(x_admin_key: Optional[str] = Header(default=None)):
    require_admin(x_admin_key)
    db = load_db()
    students = db.get("students", {})
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow(["Whatsapp", "Nome", "Nome Completo", "CPF", "Localidade", "Cidade", "Curso Atual", "Progresso"])
    
    for phone, s in students.items():
        writer.writerow([
            phone,
            s.get("name", ""),
            s.get("full_name", ""),
            s.get("cpf", ""),
            s.get("localidade", ""),
            s.get("city", ""),
            s.get("current_course", ""),
            s.get("progress", 0)
        ])
    
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=relatorio_alunos_tds.csv"}
    )


@app.post("/admin/students/bulk")
def bulk_upsert_students(body: BulkStudentsRequest, x_admin_key: Optional[str] = Header(default=None)):
    require_admin(x_admin_key)
    db = load_db()
    created = 0
    updated = 0
    skipped = 0
    errors = []

    for item in body.students:
        phone = item.whatsapp.strip()
        if not phone:
            skipped += 1
            errors.append("Registro sem whatsapp")
            continue

        exists = phone in db["students"]
        student = db["students"].get(phone, {})
        student.update({
            "whatsapp": phone,
            "name": item.full_name,
            "full_name": item.full_name,
            "cpf": item.cpf or student.get("cpf", ""),
            "localidade": item.localidade or student.get("localidade", ""),
            "updated_at": now_iso(),
        })
        student.setdefault("created_at", now_iso())
        student.setdefault("progress", 0)
        db["students"][phone] = student

        if item.course_slug:
            student["current_course"] = item.course_slug
            student.setdefault("progress", 0)

        if exists:
            updated += 1
        else:
            created += 1

    save_db(db)
    return {"created": created, "updated": updated, "skipped": skipped, "errors": errors}


@app.get("/admin/metrics/summary")
def metrics_summary(x_admin_key: Optional[str] = Header(default=None)):
    require_admin(x_admin_key)
    db = load_db()
    students = db.get("students", {})
    courses = {c.get("slug"): c.get("title", c.get("slug")) for c in load_courses()}
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)

    total_students = len(students)
    active_students = 0
    completed_students = 0
    inactive_7d = 0
    by_course_map = {}

    for phone, student in students.items():
        progress = int(student.get("progress", 0) or 0)
        course_slug = student.get("current_course")
        if progress > 0:
            active_students += 1
        if progress >= 100:
            completed_students += 1

        last_activity = (
            parse_iso_date(student.get("last_activity"))
            or parse_iso_date(student.get("updated_at"))
            or parse_iso_date(student.get("created_at"))
        )
        if last_activity and last_activity < cutoff:
            inactive_7d += 1

        if course_slug:
            item = by_course_map.setdefault(course_slug, {
                "slug": course_slug,
                "title": courses.get(course_slug, course_slug),
                "enrolled": 0,
                "progress_sum": 0,
                "completed": 0,
            })
            item["enrolled"] += 1
            item["progress_sum"] += progress
            if progress >= 100:
                item["completed"] += 1

    by_course = []
    for item in by_course_map.values():
        enrolled = item["enrolled"] or 1
        by_course.append({
            "slug": item["slug"],
            "title": item["title"],
            "enrolled": item["enrolled"],
            "avg_progress": round(item["progress_sum"] / enrolled, 2),
            "completed": item["completed"],
        })

    day_counts = {}
    for i in range(30):
        dt = datetime.utcnow() - timedelta(days=i)
        day_counts[dt.strftime("%Y-%m-%d")] = 0

    for event in db.get("tracking", []):
        ts = parse_iso_date(event.get("timestamp"))
        if not ts:
            continue
        key = ts.strftime("%Y-%m-%d")
        if key in day_counts:
            day_counts[key] += 1

    activity_by_day = [{"date": day, "lessons_viewed": day_counts[day]} for day in sorted(day_counts.keys())]
    certificates_issued = len(db.get("certificates", {}))

    return {
        "total_students": total_students,
        "active_students": active_students,
        "completed_students": completed_students,
        "inactive_7d": inactive_7d,
        "by_course": by_course,
        "activity_by_day": activity_by_day,
        "certificates_issued": certificates_issued,
    }


@app.get("/student/{phone}/export")
def export_student_data(phone: str, authorization: Optional[str] = Header(default=None), x_admin_key: Optional[str] = Header(default=None)):
    if x_admin_key != ADMIN_KEY:
        session_phone = get_session(authorization)
        if session_phone != phone:
            raise HTTPException(401, "Não autorizado para exportar este aluno")

    db = load_db()
    student = db.get("students", {}).get(phone)
    if not student:
        raise HTTPException(404, "Aluno não encontrado")

    student_certs = [c for c in db.get("certificates", {}).values() if c.get("whatsapp") == phone]
    tracking = [t for t in db.get("tracking", []) if t.get("whatsapp") == phone]
    return {"student": student, "certificates": student_certs, "tracking": tracking}


@app.delete("/student/{phone}")
def delete_student(phone: str, x_admin_key: Optional[str] = Header(default=None)):
    require_admin(x_admin_key)
    db = load_db()
    if phone not in db.get("students", {}):
        raise HTTPException(404, "Aluno não encontrado")

    del db["students"][phone]
    cert_keys_to_remove = [k for k, c in db.get("certificates", {}).items() if c.get("whatsapp") == phone]
    for key in cert_keys_to_remove:
        del db["certificates"][key]
    db["tracking"] = [t for t in db.get("tracking", []) if t.get("whatsapp") != phone]
    save_db(db)
    return {"deleted": True, "data_removed": ["student", "certificates", "tracking"]}


# --- PROXY: RAG (AnythingLLM) ---

@app.get("/admin/rag/documents")
def proxy_list_rag_docs(x_admin_key: Optional[str] = Header(default=None)):
    require_admin(x_admin_key)
    settings = load_settings()
    llm_url = settings.get("anythingllm_url", "").rstrip('/')
    llm_key = settings.get("anythingllm_key")
    workspace = settings.get("anythingllm_workspace", "tds-lms-knowledge")
    
    if not llm_key: return []
    
    try:
        url = f"{llm_url}/api/v1/workspace/{workspace}"
        resp = requests.get(url, headers={"Authorization": f"Bearer {llm_key}"}, timeout=10)
        if resp.status_code == 200:
            # AnythingLLM returns {"workspace": [{...}]} — workspace is an array
            workspaces = resp.json().get("workspace", [])
            if isinstance(workspaces, list) and workspaces:
                return workspaces[0].get("documents", [])
            elif isinstance(workspaces, dict):
                return workspaces.get("documents", [])
    except Exception as e:
        print(f"RAG List Error: {e}")
    return []

@app.post("/admin/rag/upload")
async def proxy_upload_rag_doc(file: UploadFile = File(...), x_admin_key: Optional[str] = Header(default=None)):
    require_admin(x_admin_key)
    settings = load_settings()
    llm_url = settings.get("anythingllm_url", "").rstrip('/')
    llm_key = settings.get("anythingllm_key")
    workspace = settings.get("anythingllm_workspace", "tds-lms-knowledge")
    
    try:
        # 1. Upload to system
        upload_url = f"{llm_url}/api/v1/document/upload"
        contents = await file.read()
        files = {"file": (file.filename, contents, file.content_type)}
        headers = {"Authorization": f"Bearer {llm_key}"}

        res_upload = requests.post(upload_url, files=files, headers=headers, timeout=30)
        if res_upload.status_code != 200:
            raise HTTPException(res_upload.status_code, f"AnythingLLM Upload Error: {res_upload.text}")

        upload_data = res_upload.json()
        documents = upload_data.get("documents", [])
        if not documents:
            raise HTTPException(500, "AnythingLLM returned no document location after upload")
        doc_path = documents[0].get("location")

        # 2. Add to workspace
        update_url = f"{llm_url}/api/v1/workspace/{workspace}/update-embeddings"
        requests.post(update_url, json={"adds": [doc_path]}, headers=headers, timeout=20)
        
        return {"success": True, "path": doc_path}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.delete("/admin/rag/documents/{path:path}")
def proxy_delete_rag_doc(path: str, x_admin_key: Optional[str] = Header(default=None)):
    require_admin(x_admin_key)
    settings = load_settings()
    llm_url = settings.get("anythingllm_url", "").rstrip('/')
    llm_key = settings.get("anythingllm_key")
    workspace = settings.get("anythingllm_workspace", "tds-lms-knowledge")
    
    try:
        update_url = f"{llm_url}/api/v1/workspace/{workspace}/update-embeddings"
        requests.post(update_url, json={"deletes": [path]}, headers={"Authorization": f"Bearer {llm_key}"}, timeout=10)
        return {"success": True}
    except Exception as e:
        raise HTTPException(500, str(e))


# --- PROXY: Evolution API ---

@app.post("/admin/evolution/instance/create")
def proxy_evo_create(body: dict, x_admin_key: Optional[str] = Header(default=None)):
    require_admin(x_admin_key)
    settings = load_settings()
    url = f"{settings.get('evolution_url')}/instance/create"
    # Ensure integration is set
    body.setdefault("integration", "WHATSAPP-BAILEYS")
    resp = requests.post(url, json=body, headers={"apikey": settings.get("evolution_key")}, timeout=15)
    return JSONResponse(status_code=resp.status_code, content=resp.json())

@app.get("/admin/evolution/instance/fetch")
def proxy_evo_fetch(x_admin_key: Optional[str] = Header(default=None)):
    require_admin(x_admin_key)
    settings = load_settings()
    url = f"{settings.get('evolution_url')}/instance/fetchInstances"
    resp = requests.get(url, headers={"apikey": settings.get("evolution_key")}, timeout=15)
    return JSONResponse(status_code=resp.status_code, content=resp.json())

@app.get("/admin/evolution/instance/connect/{instance}")
def proxy_evo_connect(instance: str, x_admin_key: Optional[str] = Header(default=None)):
    require_admin(x_admin_key)
    settings = load_settings()
    url = f"{settings.get('evolution_url')}/instance/connect/{instance}"
    resp = requests.get(url, headers={"apikey": settings.get("evolution_key")}, timeout=15)
    return JSONResponse(status_code=resp.status_code, content=resp.json())

@app.post("/admin/evolution/chatwoot/set/{instance}")
def proxy_evo_chatwoot(instance: str, body: dict, x_admin_key: Optional[str] = Header(default=None)):
    require_admin(x_admin_key)
    settings = load_settings()
    url = f"{settings.get('evolution_url')}/chatwoot/set/{instance}"
    resp = requests.post(url, json=body, headers={"apikey": settings.get("evolution_key")}, timeout=15)
    return JSONResponse(status_code=resp.status_code, content=resp.json())

@app.delete("/admin/evolution/instance/delete/{instance}")
def proxy_evo_delete(instance: str, x_admin_key: Optional[str] = Header(default=None)):
    require_admin(x_admin_key)
    settings = load_settings()
    url = f"{settings.get('evolution_url')}/instance/delete/{instance}"
    resp = requests.delete(url, headers={"apikey": settings.get("evolution_key")}, timeout=15)
    return JSONResponse(status_code=resp.status_code, content=resp.json())

@app.post("/admin/evolution/message/send/{instance}")
def proxy_evo_send(instance: str, body: dict, x_admin_key: Optional[str] = Header(default=None)):
    require_admin(x_admin_key)
    settings = load_settings()
    url = f"{settings.get('evolution_url')}/message/sendText/{instance}"
    resp = requests.post(url, json=body, headers={"apikey": settings.get("evolution_key")}, timeout=15)
    return JSONResponse(status_code=resp.status_code, content=resp.json())

@app.post("/admin/evolution/group/create/{instance}")
def proxy_evo_group_create(instance: str, body: EvolutionGroupCreate, x_admin_key: Optional[str] = Header(default=None)):
    require_admin(x_admin_key)
    settings = load_settings()
    url = f"{settings.get('evolution_url')}/group/create/{instance}"
    resp = requests.post(url, json=body.model_dump(), headers={"apikey": settings.get("evolution_key")}, timeout=20)
    return JSONResponse(status_code=resp.status_code, content=resp.json())

@app.post("/student/sisec")
def update_sisec(payload: SisecUpdate, x_admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key")):
    require_admin(x_admin_key)
    db = load_db()
    if payload.whatsapp not in db["students"]:
        db["students"][payload.whatsapp] = {
            "whatsapp": payload.whatsapp,
            "name": payload.data.get("campo_6", "Estudante"),
            "role": "student",
            "status_atendimento": "bot"
        }
    db["students"][payload.whatsapp]["sisec_data"] = payload.data
    db["students"][payload.whatsapp]["updated_at"] = now_iso()
    save_db(db)
    return {"status": "ok", "fields": len(payload.data)}


# --- PROXY: Chatwoot Automation ---

@app.get("/admin/chatwoot/contacts/search")
def proxy_chatwoot_search(q: str, x_admin_key: Optional[str] = Header(default=None)):
    require_admin(x_admin_key)
    settings = load_settings()
    account_id = settings.get("chatwoot_account_id", "1")
    url = f"{settings.get('chatwoot_url')}/api/v1/accounts/{account_id}/contacts/search?q={q}"
    resp = requests.get(url, headers={"api_access_token": settings.get("chatwoot_token")}, timeout=10)
    return JSONResponse(status_code=resp.status_code, content=resp.json())

@app.post("/admin/chatwoot/conversations/{conv_id}/toggle_status")
def proxy_chatwoot_toggle(conv_id: str, body: dict, x_admin_key: Optional[str] = Header(default=None)):
    require_admin(x_admin_key)
    settings = load_settings()
    account_id = settings.get("chatwoot_account_id", "1")
    url = f"{settings.get('chatwoot_url')}/api/v1/accounts/{account_id}/conversations/{conv_id}/toggle_status"
    resp = requests.post(url, json=body, headers={"api_access_token": settings.get("chatwoot_token")}, timeout=10)
    return JSONResponse(status_code=resp.status_code, content=resp.json())

@app.get("/admin/chatwoot/contacts/{contact_id}/conversations")
def proxy_chatwoot_contact_convs(contact_id: str, x_admin_key: Optional[str] = Header(default=None)):
    require_admin(x_admin_key)
    settings = load_settings()
    account_id = settings.get("chatwoot_account_id", "1")
    url = f"{settings.get('chatwoot_url')}/api/v1/accounts/{account_id}/contacts/{contact_id}/conversations"
    resp = requests.get(url, headers={"api_access_token": settings.get("chatwoot_token")}, timeout=10)
    return JSONResponse(status_code=resp.status_code, content=resp.json())

@app.post("/admin/chatwoot/conversations/{conv_id}/messages")
def proxy_chatwoot_msg(conv_id: str, body: dict, x_admin_key: Optional[str] = Header(default=None)):
    require_admin(x_admin_key)
    settings = load_settings()
    account_id = settings.get("chatwoot_account_id", "1")
    url = f"{settings.get('chatwoot_url')}/api/v1/accounts/{account_id}/conversations/{conv_id}/messages"
    resp = requests.post(url, json=body, headers={"api_access_token": settings.get("chatwoot_token")}, timeout=10)
    return JSONResponse(status_code=resp.status_code, content=resp.json())

@app.post("/admin/chatwoot/inboxes")
def proxy_chatwoot_inbox(body: dict, x_admin_key: Optional[str] = Header(default=None)):
    require_admin(x_admin_key)
    settings = load_settings()
    account_id = settings.get("chatwoot_account_id", "1")
    url = f"{settings.get('chatwoot_url')}/api/v1/accounts/{account_id}/inboxes"
    resp = requests.post(url, json=body, headers={"api_access_token": settings.get("chatwoot_token")}, timeout=10)
    return JSONResponse(status_code=resp.status_code, content=resp.json())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
