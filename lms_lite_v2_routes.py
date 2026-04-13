from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Literal, Optional

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field
import requests

router = APIRouter()

ADMIN_KEY = os.getenv("ADMIN_KEY", "admin-tds-2026")
DB_FILE = os.getenv("DB_FILE", "/app/lms_lite_db.json")

ANYTHINGLLM_URL = os.getenv("ANYTHINGLLM_URL", "")
ANYTHINGLLM_KEY = os.getenv("ANYTHINGLLM_KEY", "")
ANYTHINGLLM_WORKSPACE = os.getenv("ANYTHINGLLM_WORKSPACE", "tds")

EVOLUTION_URL = os.getenv("EVOLUTION_URL", "").rstrip("/")
EVOLUTION_KEY = os.getenv("EVOLUTION_KEY", "")
EVOLUTION_INSTANCE = os.getenv("EVOLUTION_INSTANCE", "tds_suporte_audiovisual")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")


# --- DB helpers (local copies to avoid circular import with lms_lite_api) ---

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


# --- AnythingLLM helper ---

def _call_anythingllm(workspace: str, message: str, session_id: str) -> str:
    if not ANYTHINGLLM_URL or not ANYTHINGLLM_KEY:
        return "Tutor IA não configurado. Configure ANYTHINGLLM_URL e ANYTHINGLLM_KEY."
    try:
        resp = requests.post(
            f"{ANYTHINGLLM_URL}/api/v1/workspace/{workspace}/chat",
            headers={
                "Authorization": f"Bearer {ANYTHINGLLM_KEY}",
                "Content-Type": "application/json",
            },
            json={"message": message, "mode": "chat", "sessionId": session_id},
            timeout=30,
        )
        if resp.status_code >= 400:
            return f"Erro do tutor IA: {resp.status_code}"
        data = resp.json()
        return data.get("textResponse") or data.get("text") or "Sem resposta do tutor IA."
    except Exception as exc:
        return f"Erro de conexão com o tutor IA: {exc}"


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
    phone: str
    message: str
    workspace: Optional[str] = None
    course_slug: Optional[str] = None


class SetModeRequest(BaseModel):
    phone: str
    mode: Literal["bot", "human", "new"]


class WebhookPayload(BaseModel):
    phone: Optional[str] = None
    message: Optional[str] = None
    timestamp: Optional[str] = None
    provider_event: dict = Field(default_factory=dict)


# --- Routes ---

@router.post("/whatsapp/webhook")
def whatsapp_webhook(payload: WebhookPayload):
    """Receive webhook payload from n8n / Evolution API and persist to DB."""
    db = load_db()
    event = {
        "phone": payload.phone,
        "message": payload.message,
        "timestamp": payload.timestamp or now_iso(),
        "provider_event": payload.provider_event,
        "received_at": now_iso(),
    }
    events = db.setdefault("webhook_events", [])
    events.insert(0, event)
    # Keep last 500 events
    db["webhook_events"] = events[:500]

    # If student exists, update last_activity_at
    if payload.phone and payload.phone in db.get("students", {}):
        db["students"][payload.phone]["last_activity_at"] = now_iso()

    save_db(db)
    return {
        "status": "accepted",
        "received_at": event["received_at"],
        "phone": payload.phone,
    }


@router.get("/communities")
def get_communities(x_admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key")):
    require_admin_key(x_admin_key)
    db = load_db()
    communities = db.get("communities", {})
    return list(communities.values())


@router.post("/communities")
def create_community(body: CommunityCreate, x_admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key")):
    require_admin_key(x_admin_key)
    db = load_db()
    community = {
        **body.model_dump(),
        "members": [],
        "created_at": now_iso(),
    }
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
    sent = 0
    failed = 0
    for phone in members:
        ok = _send_whatsapp(phone, body.message)
        if ok:
            sent += 1
        else:
            failed += 1

    return {"status": "done", "slug": slug, "sent": sent, "failed": failed, "total": len(members)}


@router.post("/chat/query")
def chat_query(body: ChatQueryRequest):
    """Forward message to AnythingLLM and return AI reply."""
    db = load_db()
    student = db.get("students", {}).get(body.phone, {})

    # Determine workspace: explicit > course_workspace_links > student current_course > default
    workspace = body.workspace
    if not workspace and body.course_slug:
        links = db.get("course_workspace_links", {})
        workspace = links.get(body.course_slug)
    if not workspace and student.get("current_course"):
        links = db.get("course_workspace_links", {})
        workspace = links.get(student["current_course"])
    if not workspace:
        workspace = ANYTHINGLLM_WORKSPACE or "tds"

    reply = _call_anythingllm(workspace, body.message, session_id=body.phone)

    # Append to student conversation log
    if body.phone in db.get("students", {}):
        conversation = db["students"][body.phone].setdefault("conversation", [])
        conversation.append({"role": "student", "text": body.message, "ts": now_iso()})
        conversation.append({"role": "ai", "text": reply, "ts": now_iso()})
        # Keep last 100 messages
        db["students"][body.phone]["conversation"] = conversation[-100:]
        db["students"][body.phone]["last_activity_at"] = now_iso()
        save_db(db)

    return {
        "status": "ok",
        "phone": body.phone,
        "workspace": workspace,
        "reply": reply,
    }


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
        filter_lower = filter.lower()
        events = [
            e for e in events
            if filter_lower in (e.get("phone") or "").lower()
            or filter_lower in (e.get("message") or "").lower()
        ]

    return {"items": events[:limit], "total": len(events), "filter": filter}


@router.get("/admin/students/{phone}/conversation")
def get_student_conversation(phone: str, x_admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key")):
    require_admin_key(x_admin_key)
    db = load_db()
    student = db.get("students", {}).get(phone)
    if not student:
        raise HTTPException(404, "Aluno não encontrado")
    return {
        "phone": phone,
        "messages": student.get("conversation", []),
    }
