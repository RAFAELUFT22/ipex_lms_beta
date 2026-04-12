import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Optional

import requests
from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter()
logger = logging.getLogger(__name__)

ADMIN_KEY = os.getenv("ADMIN_KEY", "admin-tds-2026")
DB_FILE = os.getenv("DB_FILE", "/app/lms_lite_db.json")
SETTINGS_FILE = os.getenv("SETTINGS_FILE", "/app/settings.json")

if not Path(DB_FILE).parent.exists() and Path("./lms_lite_db.json").exists():
    DB_FILE = "./lms_lite_db.json"
if not Path(SETTINGS_FILE).parent.exists() and Path("./settings.json").exists():
    SETTINGS_FILE = "./settings.json"

EVOLUTION_URL = os.getenv("EVOLUTION_URL", "").rstrip("/")
EVOLUTION_KEY = os.getenv("EVOLUTION_KEY", "")
EVOLUTION_INSTANCE = os.getenv("EVOLUTION_INSTANCE", "tds_suporte_audiovisual")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
FRIENDLY_AI_ERROR = "O Tutor está revisando os manuais, tente novamente em instantes."


# --- DB helpers (local copies to avoid circular import with lms_lite_api) ---

def load_db() -> dict:
    if not Path(DB_FILE).exists():
        return {
            "students": {}, "certificates": {}, "communities": {},
            "webhook_events": [], "quiz_bank": {}, "notification_log": [],
            "tracking": [], "course_workspace_links": {},
        }
    with open(DB_FILE, encoding="utf-8") as f:
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
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)


def load_settings() -> dict:
    defaults = {
        "anythingllm_url": os.getenv("ANYTHINGLLM_URL", "https://llm.ipexdesenvolvimento.cloud"),
        "anythingllm_key": os.getenv("ANYTHINGLLM_KEY", ""),
        "anythingllm_workspace": os.getenv("ANYTHINGLLM_WORKSPACE", "tds"),
    }
    if not Path(SETTINGS_FILE).exists():
        return defaults
    try:
        with open(SETTINGS_FILE, encoding="utf-8") as f:
            saved = json.load(f)
        defaults.update(saved)
    except Exception as exc:
        logger.error("Failed to load settings: %s", exc)
    return defaults


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


# --- Messaging helpers ---

def _send_whatsapp(phone: str, message: str) -> bool:
    if not EVOLUTION_URL or not EVOLUTION_KEY:
        return False
    try:
        resp = requests.post(
            f"{EVOLUTION_URL}/message/sendText/{EVOLUTION_INSTANCE}",
            json={"number": phone, "text": message},
            headers={"apikey": EVOLUTION_KEY},
            timeout=12,
        )
        return resp.status_code < 400
    except Exception:
        return False


def _send_telegram(chat_id: str, message: str) -> bool:
    if not TELEGRAM_BOT_TOKEN:
        return False
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": message},
            timeout=12,
        )
        return resp.status_code < 400
    except Exception:
        return False


def send_unified_reply(phone: str, message: str, channel: str = "whatsapp") -> dict:
    """Send message via WhatsApp, Telegram, or both."""
    if channel not in {"whatsapp", "telegram", "both"}:
        raise ValueError("Canal inválido")

    wa_ok = False
    tg_ok = False

    if channel in ("whatsapp", "both"):
        wa_ok = _send_whatsapp(phone, message)
        if not wa_ok and channel == "whatsapp":
            raise RuntimeError("Falha no envio via WhatsApp")

    if channel in ("telegram", "both"):
        tg_ok = _send_telegram(phone, message)

    return {"status": "sent", "channel": channel, "whatsapp": wa_ok, "telegram": tg_ok, "phone": phone}


# --- AnythingLLM helpers ---

def get_ai_response(message: str, workspace: str, session_id: str) -> str:
    settings = load_settings()
    llm_url = settings.get("anythingllm_url", "").rstrip("/")
    llm_key = settings.get("anythingllm_key", "")

    if not llm_url or not llm_key:
        logger.error("AnythingLLM is not configured (url/key missing).")
        return FRIENDLY_AI_ERROR

    try:
        resp = requests.post(
            f"{llm_url}/api/v1/workspace/{workspace}/chat",
            headers={"Authorization": f"Bearer {llm_key}", "Content-Type": "application/json"},
            json={"message": message, "mode": "chat", "sessionId": session_id},
            timeout=30,
        )
        if resp.status_code >= 400:
            logger.error("AnythingLLM error (%s): %s", resp.status_code, resp.text)
            return FRIENDLY_AI_ERROR
        data = resp.json()
        return data.get("textResponse") or data.get("response") or data.get("text") or FRIENDLY_AI_ERROR
    except Exception as exc:
        logger.exception("AnythingLLM request failed: %s", exc)
        return FRIENDLY_AI_ERROR


def resolve_workspace(db: dict, course_slug: Optional[str], fallback: str = "tds") -> str:
    links = db.get("course_workspace_links", {})
    if course_slug and links.get(course_slug):
        return links[course_slug]
    settings = load_settings()
    return settings.get("anythingllm_workspace") or fallback


def resolve_phone_from_session(authorization: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    if not authorization or not authorization.startswith("Bearer "):
        return None, None
    token = authorization.split(" ", 1)[1]
    try:
        import lms_lite_api  # local import to avoid module import cycle
        session = lms_lite_api._sessions.get(token)
        if not session:
            return None, token
        if datetime.now().timestamp() > session.get("expires", 0):
            lms_lite_api._sessions.pop(token, None)
            return None, token
        return session.get("phone"), token
    except Exception as exc:
        logger.error("Failed to resolve session token: %s", exc)
        return None, token


def extract_phone(payload: "WebhookPayload") -> Optional[str]:
    if payload.phone:
        return payload.phone
    event = payload.provider_event or {}
    for candidate in [
        event.get("phone"),
        event.get("from"),
        event.get("sender"),
        event.get("senderNumber"),
        event.get("data", {}).get("key", {}).get("remoteJid", "").split("@")[0],
    ]:
        if candidate:
            return str(candidate)
    return None


def extract_message(payload: "WebhookPayload") -> str:
    if payload.message:
        return payload.message
    event = payload.provider_event or {}
    for candidate in [
        event.get("message"),
        event.get("text"),
        event.get("body"),
        event.get("data", {}).get("message", {}).get("conversation"),
        event.get("data", {}).get("message", {}).get("extendedTextMessage", {}).get("text"),
    ]:
        if candidate:
            return str(candidate)
    return ""


# --- Auth helper ---

def require_admin_key(x_admin_key: Optional[str]):
    if x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Invalid X-Admin-Key")


# --- Models ---

class CommunityCreate(BaseModel):
    title: str
    slug: str
    whatsapp_group_id: str
    description: Optional[str] = ""


class BroadcastRequest(BaseModel):
    message: str = Field(min_length=1)


class ChatQueryRequest(BaseModel):
    phone: Optional[str] = None
    message: str
    workspace: Optional[str] = None
    course_slug: Optional[str] = None


class SetModeRequest(BaseModel):
    phone: str
    mode: Literal["bot", "human", "new"]


class CourseWorkspaceLinkRequest(BaseModel):
    course_slug: str
    workspace_slug: str


class WebhookPayload(BaseModel):
    phone: Optional[str] = None
    message: Optional[str] = None
    timestamp: Optional[str] = None
    provider_event: dict = Field(default_factory=dict)


# --- Routes ---

@router.post("/admin/courses/link_workspace")
def link_course_workspace(
    body: CourseWorkspaceLinkRequest,
    x_admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key"),
):
    """Link a course slug to a specific AnythingLLM workspace."""
    require_admin_key(x_admin_key)
    db = load_db()
    db.setdefault("course_workspace_links", {})[body.course_slug] = body.workspace_slug
    save_db(db)
    return {"status": "linked", "course_slug": body.course_slug, "workspace_slug": body.workspace_slug}


@router.get("/admin/courses/link_workspace")
def list_course_workspace_links(
    x_admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key"),
):
    require_admin_key(x_admin_key)
    db = load_db()
    return {"links": db.get("course_workspace_links", {})}


@router.post("/whatsapp/webhook")
def whatsapp_webhook(payload: WebhookPayload):
    """Receive webhook from n8n / Evolution, persist event and auto-reply via AI."""
    db = load_db()
    phone = extract_phone(payload)
    message = extract_message(payload)

    course_slug = None
    workspace = "tds"
    ai_reply = None

    if phone and message:
        student = db.get("students", {}).get(phone, {})
        course_slug = student.get("current_course")
        workspace = resolve_workspace(db, course_slug, fallback="tds")
        # Only call AI for bot-mode students
        mode = student.get("status_atendimento", "bot")
        if mode == "bot":
            ai_reply = get_ai_response(message, workspace, session_id=phone)
        # Update student activity
        if phone in db.get("students", {}):
            db["students"][phone]["last_activity_at"] = now_iso()

    event_record = {
        "received_at": now_iso(),
        "phone": phone,
        "message": message,
        "course_slug": course_slug,
        "workspace": workspace,
        "reply": ai_reply,
        "provider_event": payload.provider_event,
    }
    events = db.setdefault("webhook_events", [])
    events.insert(0, event_record)
    db["webhook_events"] = events[:500]
    save_db(db)

    return {
        "status": "accepted",
        "received_at": event_record["received_at"],
        "phone": phone,
        "workspace": workspace,
        "reply": ai_reply,
    }


@router.get("/communities")
def get_communities(x_admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key")):
    require_admin_key(x_admin_key)
    db = load_db()
    return list(db.get("communities", {}).values())


@router.post("/communities")
def create_community(body: CommunityCreate, x_admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key")):
    require_admin_key(x_admin_key)
    db = load_db()
    community = {**body.model_dump(), "members": [], "created_at": now_iso()}
    db["communities"][body.slug] = community
    save_db(db)
    return {"status": "created", "community": community}


@router.delete("/communities/{slug}")
def delete_community(slug: str, x_admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key")):
    require_admin_key(x_admin_key)
    db = load_db()
    if slug not in db.get("communities", {}):
        raise HTTPException(404, "Comunidade não encontrada")
    del db["communities"][slug]
    save_db(db)
    return {"status": "deleted", "slug": slug}


@router.post("/communities/{slug}/broadcast")
def broadcast_to_community(slug: str, body: BroadcastRequest, x_admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key")):
    require_admin_key(x_admin_key)
    db = load_db()
    community = db.get("communities", {}).get(slug)
    if not community:
        raise HTTPException(404, "Comunidade não encontrada")
    members = community.get("members", [])
    sent, failed = 0, 0
    for phone in members:
        if _send_whatsapp(phone, body.message):
            sent += 1
        else:
            failed += 1
    return {"status": "done", "slug": slug, "sent": sent, "failed": failed, "total": len(members)}


@router.post("/chat/query")
def chat_query(body: ChatQueryRequest, authorization: Optional[str] = Header(default=None)):
    """Send message to AnythingLLM with course-aware workspace routing and session memory."""
    db = load_db()
    session_phone, token = resolve_phone_from_session(authorization)
    phone = session_phone or body.phone

    if not phone:
        raise HTTPException(status_code=400, detail="phone é obrigatório quando não há Authorization token")

    student = db.get("students", {}).get(phone, {})
    course_slug = body.course_slug or student.get("current_course")
    workspace = body.workspace or resolve_workspace(db, course_slug, fallback="tds")
    session_id = token or phone

    reply = get_ai_response(body.message, workspace, session_id=session_id)

    # Persist conversation history on student record
    if phone in db.get("students", {}):
        conversation = db["students"][phone].setdefault("conversation", [])
        conversation.append({"role": "student", "text": body.message, "ts": now_iso()})
        conversation.append({"role": "ai", "text": reply, "ts": now_iso()})
        db["students"][phone]["conversation"] = conversation[-100:]
        db["students"][phone]["last_activity_at"] = now_iso()
        save_db(db)

    return {"status": "ok", "phone": phone, "course_slug": course_slug, "workspace": workspace, "reply": reply}


@router.post("/chat/set_mode")
def set_mode(body: SetModeRequest, x_admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key")):
    require_admin_key(x_admin_key)
    db = load_db()
    if body.phone not in db.get("students", {}):
        raise HTTPException(404, "Aluno não encontrado")
    db["students"][body.phone]["status_atendimento"] = body.mode
    db["students"][body.phone]["updated_at"] = now_iso()
    save_db(db)
    return {"status": "updated", "phone": body.phone, "mode": body.mode}


@router.get("/admin/webhook/events")
def list_webhook_events(
    filter: Optional[str] = Query(default=None),
    limit: int = Query(default=50, le=200),
    x_admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key"),
):
    require_admin_key(x_admin_key)
    db = load_db()
    events = db.get("webhook_events", [])

    if filter:
        lowered = filter.lower()
        events = [
            e for e in events
            if lowered in (e.get("phone") or "").lower()
            or lowered in (e.get("message") or "").lower()
        ]

    return {"items": events[:limit], "total": len(events), "filter": filter}


@router.get("/admin/students/{phone}/conversation")
def get_student_conversation(phone: str, x_admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key")):
    require_admin_key(x_admin_key)
    db = load_db()
    student = db.get("students", {}).get(phone)
    if not student:
        raise HTTPException(404, "Aluno não encontrado")
    # Return from student conversation log (typed messages) + webhook events for this phone
    typed = student.get("conversation", [])
    webhook_msgs = [
        {"role": "student", "text": e.get("message", ""), "ts": e.get("received_at", ""), "via": "webhook"}
        for e in db.get("webhook_events", [])
        if e.get("phone") == phone and e.get("message")
    ]
    return {"phone": phone, "messages": typed, "webhook_messages": webhook_msgs[:50]}
