import hashlib
import json
import os
import random
import secrets
import time
import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import requests
import csv
import io
from fastapi import FastAPI, HTTPException, Header, File, UploadFile, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, Response
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from lms_lite_v2_routes import router as v2_router
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
ADMIN_KEY = os.getenv("ADMIN_KEY", "admin-tds-2026")
VALIDATION_BASE_URL = os.getenv("VALIDATION_BASE_URL", "https://ops.ipexdesenvolvimento.cloud")

# In-memory stores (reset on restart — ok for beta)
_otp_store: dict = {}   # phone -> {"code": "123456", "expires": timestamp, "attempts": 0}
_sessions: dict = {}     # token -> {"phone": "556399...", "expires": timestamp}
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="otp/verify")

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
        return {"students": {}, "certificates": {}, "communities": {}, "webhook_events": [], "quiz_bank": {}, "notification_log": [], "tracking": []}
    with open(DB_FILE) as f:
        db = json.load(f)
    db.setdefault("students", {})
    db.setdefault("certificates", {})
    db.setdefault("communities", {})
    db.setdefault("webhook_events", [])
    db.setdefault("quiz_bank", {})
    db.setdefault("notification_log", [])
    db.setdefault("tracking", [])
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
    "n8n_webhook_url": "",
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

class QuizSubmit(BaseModel):
    phone: str
    course_slug: str
    answers: list[int]


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
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


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
    return {"ok": True, "whatsapp": body.whatsapp, "consent_date": existing["consent_date"]}


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
        s["last_activity"] = now_iso()
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
        # Fetch all groups for the configured instance
        url = f"{evo_url}/group/findAll/{evo_inst}"
        resp = requests.get(url, headers={"apikey": evo_key}, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"Error fetching WhatsApp groups: {e}")
    
    return []


@app.get("/external/sheets")
def fetch_external_sheet(url: str, x_admin_key: Optional[str] = Header(default=None)):
    require_admin(x_admin_key)
    if "docs.google.com/spreadsheets/d/" not in url:
        raise HTTPException(400, "URL de planilha inválida")
    
    # Transform URL to CSV export if not already
    export_url = url
    if "/edit" in url:
        export_url = url.split("/edit")[0] + "/export?format=csv"
        # Preserve GID if present
        if "gid=" in url:
            gid = url.split("gid=")[1].split("&")[0]
            export_url += f"&gid={gid}"
    
    try:
        resp = requests.get(export_url, timeout=15)
        if resp.status_code != 200:
            raise HTTPException(resp.status_code, "Falha ao baixar planilha")
        
        content = resp.content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(content))
        data = [row for row in reader]
        # Get headers for mapping
        headers = reader.fieldnames or []
        
        return {"headers": headers, "rows": data}
    except Exception as e:
        raise HTTPException(500, f"Erro ao processar planilha: {str(e)}")


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
    cutoff = datetime.utcnow() - timedelta(days=7)

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
        url = f"{llm_url}/v1/workspace/{workspace}"
        resp = requests.get(url, headers={"Authorization": f"Bearer {llm_key}"}, timeout=10)
        if resp.status_code == 200:
            return resp.json().get("workspace", {}).get("documents", [])
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
        upload_url = f"{llm_url}/v1/document/upload"
        contents = await file.read()
        files = {"file": (file.filename, contents, file.content_type)}
        headers = {"Authorization": f"Bearer {llm_key}"}
        
        res_upload = requests.post(upload_url, files=files, headers=headers, timeout=30)
        if res_upload.status_code != 200:
            raise HTTPException(res_upload.status_code, f"AnythingLLM Upload Error: {res_upload.text}")
            
        doc_path = res_upload.json().get("documents", [])[0].get("location")
        
        # 2. Add to workspace
        update_url = f"{llm_url}/v1/workspace/{workspace}/update-embeddings"
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
        update_url = f"{llm_url}/v1/workspace/{workspace}/update-embeddings"
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
