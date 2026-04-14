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

WA_CLOUD_TOKEN = os.getenv("WA_CLOUD_TOKEN", "")
WA_PHONE_NUMBER_ID = os.getenv("WA_PHONE_NUMBER_ID", "")

def _send_whatsapp(number_or_jid: str, message: str) -> bool:
    """Send WhatsApp message via Evolution API (Baileys) or WhatsApp Cloud API (Official).

    Accepts either a plain phone number ("5563999991111") or a full JID
    ("556399999111@s.whatsapp.net" or "12345678901@g.us" for groups).
    """
    # 1. Tenta via WhatsApp Cloud API se for número individual e estiver configurado
    if WA_CLOUD_TOKEN and WA_PHONE_NUMBER_ID and "@" not in number_or_jid:
        try:
            url = f"https://graph.facebook.com/v18.0/{WA_PHONE_NUMBER_ID}/messages"
            headers = {"Authorization": f"Bearer {WA_CLOUD_TOKEN}", "Content-Type": "application/json"}
            payload = {
                "messaging_product": "whatsapp",
                "to": number_or_jid,
                "type": "text",
                "text": {"body": message}
            }
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            if resp.status_code < 300:
                return True
        except Exception as exc:
            logger.error("Cloud API failed, falling back to Evolution: %s", exc)

    # 2. Fallback para Evolution API (obrigatório para grupos @g.us)
    if not EVOLUTION_URL or not EVOLUTION_KEY:
        return False
    try:
        resp = requests.post(
            f"{EVOLUTION_URL}/message/sendText/{EVOLUTION_INSTANCE}",
            json={"number": number_or_jid, "text": message},
            headers={"apikey": EVOLUTION_KEY},
            timeout=30,
        )
        return resp.status_code < 400
    except Exception:
        return False

def evo_create_group(group_name: str, participants: list[str]) -> Optional[str]:
    """Create a group in Evolution API and return its JID."""
    if not EVOLUTION_URL or not EVOLUTION_KEY:
        return None
    try:
        resp = requests.post(
            f"{EVOLUTION_URL}/group/create/{EVOLUTION_INSTANCE}",
            json={"groupName": group_name, "participants": participants},
            headers={"apikey": EVOLUTION_KEY},
            timeout=20,
        )
        if resp.status_code < 300:
            return resp.json().get("groupJid") or resp.json().get("id")
    except Exception as exc:
        logger.error("Failed to create group: %s", exc)
    return None


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

def _llm_api(method: str, path: str, payload: dict | None = None, settings: dict | None = None) -> dict | None:
    """Generic AnythingLLM API call using admin key. Returns parsed JSON or None on error."""
    s = settings or load_settings()
    llm_url = s.get("anythingllm_url", "").rstrip("/")
    llm_key = s.get("anythingllm_key", "")
    if not llm_url or not llm_key:
        logger.error("AnythingLLM not configured")
        return None
    try:
        headers = {"Authorization": f"Bearer {llm_key}", "Content-Type": "application/json"}
        url = f"{llm_url}/api/v1{path}"
        resp = requests.request(method, url, headers=headers, json=payload, timeout=10)
        if resp.status_code >= 400:
            logger.error("AnythingLLM %s %s → %s: %s", method, path, resp.status_code, resp.text[:200])
            return None
        return resp.json()
    except Exception as exc:
        logger.exception("AnythingLLM request failed: %s", exc)
        return None


def _provision_llm_account(phone: str, name: str, workspace_slug: str, settings: dict | None = None) -> dict:
    """Create an AnythingLLM account for a student and assign to the given workspace.

    Returns dict with keys: ok, username, password, workspace_slug, llm_url, error.
    Idempotent: if the username already exists, returns existing credentials stored in db.
    """
    s = settings or load_settings()
    llm_url = s.get("anythingllm_url", "").rstrip("/")

    # Deterministic username: tds_ + last 8 digits of phone
    digits = "".join(c for c in phone if c.isdigit())
    username = f"tds_{digits[-8:]}" if len(digits) >= 8 else f"tds_{digits}"
    # Simple password: TDS@ + last 4 phone digits (easy to remember/share)
    password = f"TDS@{digits[-4:]}"

    # Check if user already exists
    data = _llm_api("GET", "/admin/users", settings=s)
    if data:
        for u in data.get("users", []):
            if u.get("username") == username:
                logger.info("LLM account %s already exists (id=%s)", username, u["id"])
                _llm_assign_workspace(u["id"], workspace_slug, s)
                return {"ok": True, "username": username, "password": password,
                        "workspace_slug": workspace_slug, "llm_url": llm_url, "error": None}

    # Create user
    result = _llm_api("POST", "/admin/users/new",
                      {"username": username, "password": password, "role": "default"}, s)
    if not result or not result.get("user"):
        return {"ok": False, "username": username, "password": password,
                "workspace_slug": workspace_slug, "llm_url": llm_url,
                "error": result.get("error", "Failed to create LLM user") if result else "API error"}

    user_id = result["user"]["id"]
    logger.info("Created LLM account %s (id=%s)", username, user_id)

    # Assign to workspace
    _llm_assign_workspace(user_id, workspace_slug, s)

    return {"ok": True, "username": username, "password": password,
            "workspace_slug": workspace_slug, "llm_url": llm_url, "error": None}


def _llm_assign_workspace(user_id: int, workspace_slug: str, settings: dict | None = None) -> bool:
    """Add a user to an AnythingLLM workspace by slug."""
    result = _llm_api("POST", f"/admin/workspaces/{workspace_slug}/manage-users",
                      {"userIds": [user_id], "reset": False}, settings)
    if result and result.get("success"):
        logger.info("Assigned user %s to workspace %s", user_id, workspace_slug)
        return True
    logger.error("Failed to assign user %s to workspace %s: %s", user_id, workspace_slug, result)
    return False


def get_ai_response(message: str, workspace: str, session_id: str) -> str:
    settings = load_settings()
    llm_url = settings.get("anythingllm_url", "").rstrip("/")
    llm_key = settings.get("anythingllm_key", "")

    if not llm_url or not llm_key:
        logger.error("AnythingLLM is not configured (url/key missing).")
        return FRIENDLY_AI_ERROR

    # Tenta obter contexto do aluno para personalizar a resposta
    db = load_db()
    # session_id costuma ser o whatsapp do aluno nestes fluxos
    student = db.get("students", {}).get(session_id, {})
    sisec = student.get("sisec_data", {})
    
    # Constrói prefixo de personalidade baseado no SISEC
    persona_prefix = "Você é o Tutor IA do TDS. Responda de forma acolhedora."
    if sisec:
        persona_prefix += f"\nContexto do Aluno: Nome {student.get('name')}, Localidade {student.get('localidade')}."
        if sisec.get("campo_40") == "Sim": persona_prefix += " O aluno é trabalhador rural."
        if sisec.get("campo_15") == "Sim": persona_prefix += " O aluno se identifica como Quilombola."
        if sisec.get("campo_63"): persona_prefix += f" Atividades: {sisec.get('campo_63')}."

    full_message = f"{persona_prefix}\n\nPergunta do Aluno: {message}"

    try:
        resp = requests.post(
            f"{llm_url}/api/v1/workspace/{workspace}/chat",
            headers={"Authorization": f"Bearer {llm_key}", "Content-Type": "application/json"},
            json={"message": full_message, "mode": "chat", "sessionId": session_id},
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


def _parse_jid(jid: str) -> tuple[str, bool]:
    """Return (phone_number, is_group). Group JIDs end in @g.us, DM JIDs in @s.whatsapp.net."""
    if not jid:
        return "", False
    number = jid.split("@")[0]
    is_group = jid.endswith("@g.us")
    return number, is_group


def extract_phone(payload: "WebhookPayload") -> Optional[str]:
    """Return the *sender* phone number (individual), not the group JID."""
    if payload.phone:
        return payload.phone
    event = payload.provider_event or {}
    data = event.get("data", {})

    # Evolution v2: for group messages the real sender is in data.participant
    participant = data.get("participant") or data.get("senderParticipant")
    if participant:
        phone, _ = _parse_jid(participant)
        if phone:
            return phone

    remote_jid = data.get("key", {}).get("remoteJid", "")
    if remote_jid:
        phone, is_group = _parse_jid(remote_jid)
        # For DM: remoteJid IS the sender. For groups: already handled above; fallback to number part.
        if phone:
            return phone

    for candidate in [
        event.get("phone"),
        event.get("from"),
        event.get("sender"),
        event.get("senderNumber"),
    ]:
        if candidate:
            return str(candidate)
    return None


def extract_reply_jid(payload: "WebhookPayload") -> Optional[str]:
    """Return the JID to reply to: the group JID for group messages, or sender JID for DMs."""
    event = payload.provider_event or {}
    data = event.get("data", {})
    remote_jid = data.get("key", {}).get("remoteJid", "")
    if remote_jid:
        return remote_jid
    return None


def is_group_message(payload: "WebhookPayload") -> bool:
    """Return True if this webhook event came from a WhatsApp group."""
    event = payload.provider_event or {}
    remote_jid = event.get("data", {}).get("key", {}).get("remoteJid", "")
    return remote_jid.endswith("@g.us")


def extract_message(payload: "WebhookPayload") -> str:
    if payload.message:
        return payload.message
    event = payload.provider_event or {}
    data = event.get("data", {})
    msg = data.get("message", {})
    for candidate in [
        msg.get("conversation"),
        msg.get("extendedTextMessage", {}).get("text"),
        msg.get("imageMessage", {}).get("caption"),
        event.get("message"),
        event.get("text"),
        event.get("body"),
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


@router.post("/admin/students/{phone}/provision-llm")
def provision_student_llm(
    phone: str,
    x_admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key"),
):
    """Provision an AnythingLLM account for a specific student.

    Creates the account (idempotent) and assigns to the workspace mapped to
    the student's current course. Stores credentials in the student record.
    """
    require_admin_key(x_admin_key)
    db = load_db()
    student = db.get("students", {}).get(phone)
    if not student:
        raise HTTPException(404, f"Student {phone} not found")

    settings = load_settings()
    course_slug = student.get("current_course") or "geral"
    workspace_slug = resolve_workspace(db, course_slug, fallback=settings.get("anythingllm_workspace", "tds"))

    result = _provision_llm_account(phone, student.get("name", ""), workspace_slug, settings)
    if not result["ok"]:
        raise HTTPException(500, f"LLM provisioning failed: {result['error']}")

    # Store in student record (password hint only — not the real password for security)
    student.setdefault("llm_account", {})
    student["llm_account"].update({
        "username": result["username"],
        "workspace_slug": workspace_slug,
        "llm_url": result["llm_url"],
        "provisioned_at": now_iso(),
    })
    db["students"][phone] = student
    save_db(db)

    return {
        "ok": True,
        "phone": phone,
        "username": result["username"],
        "password": result["password"],
        "workspace_slug": workspace_slug,
        "llm_url": result["llm_url"],
    }


@router.post("/admin/courses/{course_slug}/provision-llm")
def provision_course_llm(
    course_slug: str,
    notify: bool = Query(False, description="Send credentials to student via WhatsApp"),
    x_admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key"),
):
    """Provision AnythingLLM accounts for all students enrolled in a course.

    Pass ?notify=true to send login credentials via WhatsApp after provisioning.
    """
    require_admin_key(x_admin_key)
    db = load_db()
    settings = load_settings()

    workspace_slug = resolve_workspace(db, course_slug, fallback=settings.get("anythingllm_workspace", "tds"))

    students = db.get("students", {})
    targets = {
        phone: s for phone, s in students.items()
        if course_slug in s.get("enrollments", {}) or s.get("current_course") == course_slug
    }

    if not targets:
        return {"ok": True, "provisioned": 0, "failed": 0, "skipped": 0, "details": [],
                "message": f"No students found for course '{course_slug}'"}

    provisioned, failed, skipped = 0, 0, 0
    details = []

    for phone, student in targets.items():
        existing = student.get("llm_account", {})
        if existing.get("username") and existing.get("workspace_slug") == workspace_slug:
            skipped += 1
            details.append({"phone": phone, "status": "skipped", "username": existing["username"]})
            continue

        result = _provision_llm_account(phone, student.get("name", ""), workspace_slug, settings)
        if result["ok"]:
            provisioned += 1
            student.setdefault("llm_account", {}).update({
                "username": result["username"],
                "workspace_slug": workspace_slug,
                "llm_url": result["llm_url"],
                "provisioned_at": now_iso(),
            })
            db["students"][phone] = student

            if notify:
                msg = (
                    f"🤖 *TDS — Tutor IA*\n\n"
                    f"Olá, {student.get('name', 'aluno(a)')}! Seu acesso ao Tutor IA foi criado:\n\n"
                    f"🔗 {result['llm_url']}\n"
                    f"👤 Usuário: `{result['username']}`\n"
                    f"🔑 Senha: `{result['password']}`\n\n"
                    f"Entre e converse com o Tutor sobre o conteúdo do seu curso!"
                )
                _send_whatsapp(phone, msg)

            details.append({"phone": phone, "status": "provisioned",
                            "username": result["username"], "workspace_slug": workspace_slug})
        else:
            failed += 1
            details.append({"phone": phone, "status": "failed", "error": result["error"]})

    save_db(db)
    return {"ok": True, "provisioned": provisioned, "failed": failed, "skipped": skipped, "details": details}


@router.post("/whatsapp/webhook")
def whatsapp_webhook(payload: WebhookPayload):
    """Receive webhook from n8n / Evolution, persist event and auto-reply via AI.

    Supports both direct messages and group messages.
    Group messages: remoteJid ends in @g.us — bot replies to the group JID.
    DM messages: remoteJid ends in @s.whatsapp.net — bot replies to sender.
    """
    db = load_db()
    phone = extract_phone(payload)       # individual sender phone
    message = extract_message(payload)
    reply_jid = extract_reply_jid(payload) or phone  # group JID or sender JID
    from_group = is_group_message(payload)

    # Skip messages sent by the bot itself (fromMe=True)
    from_me = payload.provider_event.get("data", {}).get("key", {}).get("fromMe", False)
    if from_me:
        return {"status": "ignored", "reason": "own_message"}

    course_slug = None
    workspace = "tds"
    ai_reply = None

    if phone and message:
        student = db.get("students", {}).get(phone, {})
        course_slug = student.get("current_course")
        workspace = resolve_workspace(db, course_slug, fallback="tds")

        # Only auto-reply for bot-mode students (default: bot)
        mode = student.get("status_atendimento", "bot")
        if mode == "bot":
            ai_reply = get_ai_response(message, workspace, session_id=phone)
            if ai_reply:
                # For groups, reply to group JID. For DMs, reply to sender number.
                _send_whatsapp(reply_jid, ai_reply)

        # Update student activity timestamp
        if phone in db.get("students", {}):
            db["students"][phone]["last_activity_at"] = now_iso()

    event_record = {
        "received_at": now_iso(),
        "phone": phone,
        "reply_jid": reply_jid,
        "from_group": from_group,
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
        "reply_jid": reply_jid,
        "from_group": from_group,
        "workspace": workspace,
        "reply": ai_reply,
    }


@router.get("/communities")
def get_communities(x_admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key")):
    require_admin_key(x_admin_key)
    db = load_db()
    communities = []
    for c in db.get("communities", {}).values():
        c_copy = dict(c)
        c_copy["member_count"] = len(c.get("members", []))
        communities.append(c_copy)
    return communities


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
    
    group_jid = community.get("whatsapp_group_id")
    members = community.get("members", [])
    
    # Se existe um group_id (JID), envia direto pro grupo (1 única chamada)
    if group_jid:
        ok = _send_whatsapp(group_jid, body.message)
        return {
            "status": "done", 
            "slug": slug, 
            "sent": 1 if ok else 0, 
            "failed": 0 if ok else 1, 
            "total": 1, 
            "method": "group_broadcast"
        }

    # Fallback: envia para cada membro individualmente
    sent, failed = 0, 0
    for phone in members:
        if _send_whatsapp(phone, body.message):
            sent += 1
        else:
            failed += 1
    return {"status": "done", "slug": slug, "sent": sent, "failed": failed, "total": len(members), "method": "individual_broadcast"}


@router.post("/communities/{slug}/members")
def add_community_member(slug: str, phone: str, x_admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key")):
    require_admin_key(x_admin_key)
    db = load_db()
    if slug not in db.get("communities", {}):
        raise HTTPException(404, "Comunidade não encontrada")
    
    members = db["communities"][slug].get("members", [])
    if phone not in members:
        members.append(phone)
        db["communities"][slug]["members"] = members
        save_db(db)
    return {"status": "added", "slug": slug, "phone": phone, "total": len(members)}


@router.delete("/communities/{slug}/members/{phone}")
def remove_community_member(slug: str, phone: str, x_admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key")):
    require_admin_key(x_admin_key)
    db = load_db()
    if slug not in db.get("communities", {}):
        raise HTTPException(404, "Comunidade não encontrada")
    
    members = db["communities"][slug].get("members", [])
    if phone in members:
        members.remove(phone)
        db["communities"][slug]["members"] = members
        save_db(db)
    return {"status": "removed", "slug": slug, "phone": phone, "total": len(members)}


@router.post("/admin/communities/setup_cartilha_groups")
def setup_cartilha_groups(x_admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key")):
    """Cria grupos de WhatsApp para todas as cartilhas/cursos e registra como comunidades."""
    require_admin_key(x_admin_key)
    db = load_db()
    
    # Lista de cursos/cartilhas reais
    cartilhas = [
        {"slug": "agricultura-sustentavel", "title": "TDS — Agricultura Sustentável"},
        {"slug": "audiovisual", "title": "TDS — Audiovisual"},
        {"slug": "financas-empreendedorismo", "title": "TDS — Finanças e Empreendedorismo"},
        {"slug": "financas-melhor-idade", "title": "TDS — Finanças Melhor Idade"},
        {"slug": "associativismo-cooperativismo", "title": "TDS — Associativismo"},
        {"slug": "ia-dia-a-dia", "title": "TDS — IA no dia a dia"},
        {"slug": "sim-pequenos-produtores", "title": "TDS — Inspeção Municipal (SIM)"},
    ]
    
    created = []
    errors = []
    
    for c in cartilhas:
        # Se já existe comunidade com esse slug, pula criação de grupo (ou podemos forçar)
        if c["slug"] in db.get("communities", {}):
            continue
            
        # Tenta criar grupo na Evolution (participantes vazios inicialmente ou admin)
        group_jid = evo_create_group(c["title"], ["5563993010823"])
        
        if group_jid:
            community = {
                "title": c["title"],
                "slug": c["slug"],
                "whatsapp_group_id": group_jid,
                "description": f"Grupo de estudos da cartilha: {c['title']}",
                "members": [],
                "created_at": now_iso()
            }
            db.setdefault("communities", {})[c["slug"]] = community
            created.append(c["slug"])
        else:
            errors.append({"slug": c["slug"], "error": "Failed to create group in Evolution"})
            
    if created:
        save_db(db)
        
    return {"status": "finished", "created": created, "errors": errors}


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
