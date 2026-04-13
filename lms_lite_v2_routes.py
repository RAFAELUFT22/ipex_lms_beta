from datetime import datetime, timezone
import os
from typing import Literal, Optional

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field
import requests

router = APIRouter()


# TODO: replace with shared settings import from lms_lite_api.py
ADMIN_KEY = 'admin-tds-2026'


def send_unified_reply(phone: str, message: str, channel: str = "whatsapp") -> dict:
  """
  Lightweight notifier used by admin broadcast/notification flows.
  Today it proxies through Evolution (WhatsApp). Telegram is best-effort
  and currently uses same transport when channel='both'.
  """
  if channel not in {"whatsapp", "telegram", "both"}:
    raise ValueError("Canal inválido")

  evo_url = os.getenv("EVOLUTION_URL", "https://evolution.ipexdesenvolvimento.cloud").rstrip("/")
  evo_key = os.getenv("EVOLUTION_KEY", "")
  evo_inst = os.getenv("EVOLUTION_INSTANCE", "tds_suporte_audiovisual")
  if not evo_url or not evo_key:
    raise RuntimeError("Integração Evolution não configurada")

  url = f"{evo_url}/message/sendText/{evo_inst}"
  payload = {"number": phone, "text": message}
  resp = requests.post(url, json=payload, headers={"apikey": evo_key}, timeout=12)
  if resp.status_code >= 400:
    raise RuntimeError(f"Falha no envio: {resp.status_code}")
  return {"status": "sent", "channel": "whatsapp", "phone": phone}


class CommunityCreate(BaseModel):
  title: str
  slug: str
  whatsapp_group_id: str
  description: Optional[str] = ''


class BroadcastRequest(BaseModel):
  message: str = Field(min_length=1)


class ChatQueryRequest(BaseModel):
  phone: str
  message: str
  workspace: Optional[str] = None


class SetModeRequest(BaseModel):
  phone: str
  mode: Literal['bot', 'human', 'new']


class WebhookPayload(BaseModel):
  phone: Optional[str] = None
  message: Optional[str] = None
  timestamp: Optional[str] = None
  provider_event: dict = Field(default_factory=dict)


def require_admin_key(x_admin_key: Optional[str]):
  if x_admin_key != ADMIN_KEY:
    raise HTTPException(status_code=401, detail='Invalid X-Admin-Key')


@router.post('/whatsapp/webhook')
def whatsapp_webhook(payload: WebhookPayload):
  """Receive webhook payload from n8n / Evolution API."""
  # TODO: persist event in db['webhook_events'] and route to bot/human flow.
  return {
    'status': 'accepted',
    'received_at': datetime.now(timezone.utc).isoformat(),
    'phone': payload.phone,
  }


@router.get('/communities')
def get_communities(x_admin_key: Optional[str] = Header(default=None, alias='X-Admin-Key')):
  require_admin_key(x_admin_key)
  # TODO: read from db['communities']
  return []


@router.post('/communities')
def create_community(body: CommunityCreate, x_admin_key: Optional[str] = Header(default=None, alias='X-Admin-Key')):
  require_admin_key(x_admin_key)
  # TODO: insert new community into db['communities']
  return {
    'status': 'created',
    'community': body.model_dump(),
  }


@router.post('/communities/{slug}/broadcast')
def broadcast_to_community(slug: str, body: BroadcastRequest, x_admin_key: Optional[str] = Header(default=None, alias='X-Admin-Key')):
  require_admin_key(x_admin_key)
  # TODO: iterate members and send sequentially through Evolution API
  return {
    'status': 'queued',
    'slug': slug,
    'message': body.message,
    'sent_count': 0,
  }


@router.post('/chat/query')
def chat_query(body: ChatQueryRequest):
  # TODO: validate student, check mode, call AnythingLLM, and reply via Evolution API.
  return {
    'status': 'ok',
    'phone': body.phone,
    'workspace': body.workspace,
    'reply': 'TODO: AI reply stub',
  }


@router.post('/chat/set_mode')
def set_mode(body: SetModeRequest, x_admin_key: Optional[str] = Header(default=None, alias='X-Admin-Key')):
  require_admin_key(x_admin_key)
  # TODO: update db['students'][phone]['status_atendimento']
  return {
    'status': 'updated',
    'phone': body.phone,
    'mode': body.mode,
  }


@router.get('/admin/webhook/events')
def list_webhook_events(
  filter: Optional[str] = Query(default=None),
  x_admin_key: Optional[str] = Header(default=None, alias='X-Admin-Key'),
):
  require_admin_key(x_admin_key)
  # TODO: fetch latest 100 events from db['webhook_events'] and apply optional filter.
  return {
    'items': [],
    'filter': filter,
  }


@router.get('/admin/students/{phone}/conversation')
def get_student_conversation(phone: str, x_admin_key: Optional[str] = Header(default=None, alias='X-Admin-Key')):
  require_admin_key(x_admin_key)
  # TODO: return conversation history from persistent db
  return {
    'phone': phone,
    'messages': [],
  }
