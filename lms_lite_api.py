import hashlib
import io
import json
import os
import random
import secrets
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import csv
import requests
from fastapi import FastAPI, HTTPException, Header, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from lms_lite_v2_routes import router as v2_router

# --- CONFIG ---
DB_FILE = os.getenv("DB_FILE", "/app/lms_lite_db.json")
SETTINGS_FILE = os.getenv("SETTINGS_FILE", "/app/settings.json")
COURSES_FILE = os.getenv("COURSES_FILE", "/app/courses/tds/tds-courses-2026.json")
VALIDATION_BASE_URL = os.getenv("VALIDATION_BASE_URL", "https://ops.ipexdesenvolvimento.cloud")

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

app.include_router(v2_router)


# --- DB HELPERS ---
def load_db() -> dict:
    if not Path(DB_FILE).exists():
        return {
            "students": {},
            "certificates": {},
            "communities": {},
            "webhook_events": [],
            "tracking": {"student_courses": {}, "interactions": []},
            "bot_group_links": {},
        }
    with open(DB_FILE) as f:
        db = json.load(f)
    db.setdefault("students", {})
    db.setdefault("certificates", {})
    db.setdefault("communities", {})
    db.setdefault("webhook_events", [])
    db.setdefault("tracking", {"student_courses": {}, "interactions": []})
    db["tracking"].setdefault("student_courses", {})
    db["tracking"].setdefault("interactions", [])
    db.setdefault("bot_group_links", {})
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
    "bot_contexts": {},
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


def api_success(data: Any = None, message: Optional[str] = None) -> dict:
    payload = {"success": True, "data": data}
    if message:
        payload["message"] = message
    return payload


def get_course(slug: str) -> dict:
    for c in load_courses():
        if c.get("slug") == slug:
            return c
    return {}


def get_course_lessons(course_slug: str) -> list[str]:
    course = get_course(course_slug)
    lessons: list[str] = []
    for chapter_idx, chapter in enumerate(course.get("chapters", []), start=1):
        for lesson_idx, lesson in enumerate(chapter.get("lessons", []), start=1):
            title = lesson.get("title", f"Lição {lesson_idx}")
            lessons.append(f"{chapter_idx}.{lesson_idx}::{title}")
    return lessons


def get_student_course_tracking(db: dict, whatsapp: str, course_slug: str) -> dict:
    key = f"{whatsapp}:{course_slug}"
    table = db["tracking"]["student_courses"]
    if key not in table:
        lessons = get_course_lessons(course_slug)
        table[key] = {
            "whatsapp": whatsapp,
            "course_slug": course_slug,
            "lesson_status": {lesson_key: "not_started" for lesson_key in lessons},
            "completed_at": None,
            "total_time_seconds": 0,
            "last_seen_at": None,
        }
    return table[key]


def compute_progress_percent(tracking: dict) -> int:
    statuses = list(tracking.get("lesson_status", {}).values())
    if not statuses:
        return 0
    done = len([s for s in statuses if s == "completed"])
    return int(round((done / len(statuses)) * 100))


def get_bot_context(course_slug: Optional[str] = None) -> dict:
    settings = load_settings()
    default_context = {
        "anythingllm_url": settings.get("anythingllm_url"),
        "anythingllm_key": settings.get("anythingllm_key"),
        "anythingllm_workspace": settings.get("anythingllm_workspace"),
        "evolution_url": settings.get("evolution_url"),
        "evolution_key": settings.get("evolution_key"),
        "evolution_instance": settings.get("evolution_instance"),
        "allowed_groups": [],
    }
    contexts = settings.get("bot_contexts", {}) or {}
    if course_slug and course_slug in contexts:
        merged = dict(default_context)
        merged.update(contexts[course_slug] or {})
        return merged
    return default_context


def track_interaction(db: dict, event: dict):
    event["timestamp"] = datetime.utcnow().isoformat() + "Z"
    db["tracking"]["interactions"].append(event)


def generate_cert_hash(whatsapp: str, course_slug: str) -> str:
    raw = f"{whatsapp}:{course_slug}:{TDS_SECRET}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def build_student_response(whatsapp: str, s: dict, db: Optional[dict] = None) -> dict:
    """Return student object with normalized enrollments list."""
    db = db or load_db()
    course_slug = s.get("current_course", "")
    progress = s.get("progress", 0)
    status = "completed" if progress >= 100 else "active"
    lesson_status = {}

    if course_slug:
        tracking = get_student_course_tracking(db, whatsapp, course_slug)
        lesson_status = tracking.get("lesson_status", {})
        progress = compute_progress_percent(tracking)
        s["progress"] = progress
        if progress >= 100:
            tracking["completed_at"] = tracking.get("completed_at") or (datetime.utcnow().isoformat() + "Z")
            status = "completed"
        else:
            status = "active"

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
            "lesson_status": lesson_status,
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
    lesson_key: Optional[str] = None
    status: Optional[str] = "completed"
    time_spent_seconds: Optional[int] = 0

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
        build_student_response(phone, s, db)
        for phone, s in db["students"].items()
    ]


@app.get("/student/{phone}")
def get_student(phone: str):
    db = load_db()
    s = db["students"].get(phone)
    if not s:
        raise HTTPException(404, "Aluno não encontrado")
    return build_student_response(phone, s, db)


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
    s["current_course"] = body.course_slug
    tracking = get_student_course_tracking(db, body.whatsapp, body.course_slug)
    if body.lesson_key:
        if body.lesson_key not in tracking["lesson_status"]:
            tracking["lesson_status"][body.lesson_key] = "not_started"
        tracking["lesson_status"][body.lesson_key] = body.status or "completed"
    tracking["total_time_seconds"] = tracking.get("total_time_seconds", 0) + max(body.time_spent_seconds or 0, 0)
    tracking["last_seen_at"] = datetime.utcnow().isoformat() + "Z"
    progress = compute_progress_percent(tracking)
    s["progress"] = progress
    db["students"][body.whatsapp] = s
    track_interaction(db, {
        "event": "progress_update",
        "whatsapp": body.whatsapp,
        "course_slug": body.course_slug,
        "lesson_key": body.lesson_key,
        "status": body.status,
        "time_spent_seconds": body.time_spent_seconds or 0,
    })
    save_db(db)
    return {"new_progress": progress, "lesson_status": tracking["lesson_status"]}


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
    if s.get("current_course") != body.course_slug:
        raise HTTPException(400, "Aluno não está matriculado no curso informado.")
    tracking = get_student_course_tracking(db, body.whatsapp, body.course_slug)
    progress = compute_progress_percent(tracking)
    if progress < 100:
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
    track_interaction(db, {"event": "certificate_issued", "whatsapp": body.whatsapp, "course_slug": body.course_slug})
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
    return build_student_response(phone, s, db)


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
    bot_contexts: Optional[dict] = None


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


def fetch_whatsapp_groups_for_context(course_slug: Optional[str] = None) -> list:
    context = get_bot_context(course_slug)
    evo_url = (context.get("evolution_url") or "").rstrip("/")
    evo_key = context.get("evolution_key")
    evo_inst = context.get("evolution_instance")
    if not evo_url or not evo_key or not evo_inst:
        return []
    try:
        url = f"{evo_url}/group/findAll/{evo_inst}"
        resp = requests.get(url, headers={"apikey": evo_key}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data if isinstance(data, list) else data.get("groups", [])
    except Exception as e:
        print(f"Error fetching WhatsApp groups: {e}")
    return []


@app.get("/admin/whatsapp/groups")
def list_admin_whatsapp_groups(course_slug: Optional[str] = None, x_admin_key: Optional[str] = Header(default=None)):
    require_admin(x_admin_key)
    return api_success(fetch_whatsapp_groups_for_context(course_slug))


@app.post("/admin/whatsapp/groups/link")
def link_whatsapp_groups(body: dict, x_admin_key: Optional[str] = Header(default=None)):
    require_admin(x_admin_key)
    course_slug = body.get("course_slug")
    group_ids = body.get("group_ids", [])
    if not course_slug:
        raise HTTPException(400, "course_slug é obrigatório.")
    if not isinstance(group_ids, list):
        raise HTTPException(400, "group_ids deve ser uma lista.")
    db = load_db()
    db["bot_group_links"][course_slug] = group_ids
    save_db(db)
    return api_success({"course_slug": course_slug, "group_ids": group_ids}, "Grupos vinculados.")


@app.get("/whatsapp/groups")
def list_whatsapp_groups_legacy(x_admin_key: Optional[str] = Header(default=None)):
    require_admin(x_admin_key)
    return fetch_whatsapp_groups_for_context(None)


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


@app.get("/admin/students")
def admin_list_students(
    course_slug: Optional[str] = None,
    group_id: Optional[str] = None,
    status: Optional[str] = None,
    x_admin_key: Optional[str] = Header(default=None),
):
    require_admin(x_admin_key)
    db = load_db()
    out = []
    for phone, student in db.get("students", {}).items():
        normalized = build_student_response(phone, student, db)
        enrollment = normalized.get("enrollments", [{}])[0] if normalized.get("enrollments") else {}
        if course_slug and enrollment.get("course", {}).get("slug") != course_slug:
            continue
        if status and enrollment.get("status") != status:
            continue
        if group_id:
            linked_groups = db.get("bot_group_links", {}).get(enrollment.get("course", {}).get("slug", ""), [])
            if group_id not in linked_groups:
                continue
        out.append(normalized)
    return api_success(out)


@app.get("/admin/students/export")
def export_students_csv(course_slug: Optional[str] = None, x_admin_key: Optional[str] = Header(default=None)):
    require_admin(x_admin_key)
    db = load_db()
    students = db.get("students", {})
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow([
        "Whatsapp", "Nome", "Nome Completo", "CPF", "Localidade", "Cidade", "Curso Atual",
        "Progresso", "Status", "Interesse", "TempoTotalSegundos", "ConcluidoEm"
    ])
    
    for phone, s in students.items():
        tracking = get_student_course_tracking(db, phone, s.get("current_course", "")) if s.get("current_course") else {}
        progress = compute_progress_percent(tracking) if tracking else s.get("progress", 0)
        if course_slug and s.get("current_course") != course_slug:
            continue
        writer.writerow([
            phone,
            s.get("name", ""),
            s.get("full_name", ""),
            s.get("cpf", ""),
            s.get("localidade", "") or s.get("sisec_data", {}).get("localidade", ""),
            s.get("city", "") or s.get("sisec_data", {}).get("localidade", ""),
            s.get("current_course", ""),
            progress,
            "completed" if progress >= 100 else "active",
            s.get("sisec_data", {}).get("interesse", ""),
            tracking.get("total_time_seconds", 0) if tracking else 0,
            tracking.get("completed_at", "") if tracking else "",
        ])
    
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=relatorio_alunos_tds.csv"}
    )


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


def get_ai_response(query: str, context: dict) -> str:
    llm_url = (context.get("anythingllm_url") or "").rstrip("/")
    llm_key = context.get("anythingllm_key")
    workspace = context.get("anythingllm_workspace")
    if not llm_url or not llm_key or not workspace:
        return "Configuração do assistente indisponível para este curso."
    try:
        endpoint = f"{llm_url}/api/v1/workspace/{workspace}/chat"
        resp = requests.post(
            endpoint,
            headers={"Authorization": f"Bearer {llm_key}", "Content-Type": "application/json"},
            json={"message": query, "mode": "query"},
            timeout=20,
        )
        if resp.status_code == 200:
            payload = resp.json()
            return payload.get("textResponse") or payload.get("response") or "Sem resposta do motor RAG."
        return f"Falha no RAG ({resp.status_code})."
    except Exception as e:
        return f"Erro ao consultar RAG: {e}"


@app.post("/admin/chat/proxy")
def admin_chat_proxy(body: dict, x_admin_key: Optional[str] = Header(default=None)):
    require_admin(x_admin_key)
    query = body.get("query", "")
    course_slug = body.get("course_slug")
    context = get_bot_context(course_slug)
    answer = get_ai_response(query, context)
    return api_success({"answer": answer, "course_slug": course_slug})


@app.post("/webhook/evolution")
def evolution_webhook(payload: dict):
    db = load_db()
    event_data = payload.get("data", {}) if isinstance(payload, dict) else {}
    text = ((event_data.get("message") or {}).get("conversation") or "").strip()
    remote_jid = event_data.get("key", {}).get("remoteJid", "")
    from_me = event_data.get("key", {}).get("fromMe", False)
    if from_me or not remote_jid or not text:
        return api_success({"ignored": True})

    is_group = remote_jid.endswith("@g.us")
    whatsapp = (event_data.get("key", {}).get("participant") or remote_jid).split("@")[0]
    student = db.get("students", {}).get(whatsapp, {})
    course_slug = student.get("current_course")
    if is_group and not course_slug:
        return api_success({"ignored": True, "reason": "student_without_course"})
    if is_group and course_slug:
        allowed = db.get("bot_group_links", {}).get(course_slug, [])
        if allowed and remote_jid not in allowed:
            return api_success({"ignored": True, "reason": "group_not_linked"})

    cmd = None
    query = text
    if text.startswith("/duvida"):
        cmd = "duvida"
        query = text.replace("/duvida", "", 1).strip() or "Explique o conteúdo do módulo atual."
    elif text.startswith("/resumo"):
        cmd = "resumo"
        query = "Gere um resumo prático dos pontos principais do módulo atual."
    else:
        return api_success({"ignored": True, "reason": "command_not_supported"})

    context = get_bot_context(course_slug)
    answer = get_ai_response(query, context)
    evo_url = (context.get("evolution_url") or "").rstrip("/")
    evo_key = context.get("evolution_key")
    evo_inst = context.get("evolution_instance")
    if evo_url and evo_key and evo_inst:
        try:
            requests.post(
                f"{evo_url}/message/sendText/{evo_inst}",
                json={"number": remote_jid, "text": answer},
                headers={"apikey": evo_key},
                timeout=10,
            )
        except Exception as e:
            print(f"Erro enviando resposta WhatsApp: {e}")

    track_interaction(db, {
        "event": "whatsapp_command",
        "command": cmd,
        "whatsapp": whatsapp,
        "group_jid": remote_jid if is_group else None,
        "course_slug": course_slug,
        "query": query,
    })
    db["webhook_events"].append(payload)
    save_db(db)
    return api_success({"processed": True, "command": cmd})


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
