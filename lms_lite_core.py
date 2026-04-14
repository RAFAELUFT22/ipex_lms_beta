import os
import json
import shutil
import threading
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse

# --- SEGURANÇA: MIDDLEWARE ---

class AdminMiddleware(BaseHTTPMiddleware):
    """Protege automaticamente todas as rotas /admin/* e /settings/*."""
    async def dispatch(self, request, call_next):
        is_admin_route = request.url.path.startswith(("/admin", "/settings"))
        if is_admin_route:
            key = request.headers.get("X-Admin-Key", "")
            expected = os.getenv("ADMIN_KEY")
            if not expected:
                print("[CRITICAL] ADMIN_KEY não configurada no ambiente!")
                return JSONResponse({"detail": "server_misconfigured"}, status_code=500)
            if key != expected:
                return JSONResponse({"detail": "unauthorized"}, status_code=401)
        return await call_next(request)

# --- ROBUSTEZ: DATABASE MANAGER ---

class DatabaseManager:
    MAX_BACKUPS = 10
    MAX_WEBHOOK_EVENTS = 100

    def __init__(self, db_path: str = "lms_lite_db.json", backup_dir: str = "backups"):
        self.db_path = Path(db_path)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._defaults = {
            "students": {}, 
            "certificates": {}, 
            "communities": {},
            "webhook_events": [], 
            "bot_group_links": {},
            "course_workspace_links": {},
            "tracking": [],
            "enrollment_requests": []
        }

    def _load(self) -> dict:
        if not self.db_path.exists():
            return dict(self._defaults)
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            return dict(self._defaults)
        for key, val in self._defaults.items():
            data.setdefault(key, val)
        return data

    def _save(self, data: dict) -> None:
        if self.db_path.exists():
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            shutil.copy2(self.db_path, self.backup_dir / f"lms_lite_db_{ts}.json")
            backups = sorted(self.backup_dir.glob("lms_lite_db_*.json"))
            if len(backups) > self.MAX_BACKUPS:
                for old in backups[:-self.MAX_BACKUPS]: old.unlink()
        tmp_path = self.db_path.with_suffix(".tmp")
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
                f.flush(); os.fsync(f.fileno())
            tmp_path.replace(self.db_path)
        except:
            if tmp_path.exists(): tmp_path.unlink()

    # --- API PÚBLICA ---

    def append_enrollment_request(self, payload: dict) -> None:
        with self._lock:
            data = self._load()
            reqs = data.setdefault("enrollment_requests", [])
            payload["requested_at"] = datetime.now(timezone.utc).isoformat()
            reqs.append(payload)
            self._save(data)

    def get_student_by_telegram(self, telegram_id: str) -> Optional[dict]:
        with self._lock:
            for s in self._load()["students"].values():
                if s.get("telegram_id") == telegram_id: return s
            return None

    def link_telegram(self, phone: str, telegram_id: str) -> None:
        with self._lock:
            data = self._load()
            if phone in data["students"]:
                data["students"][phone]["telegram_id"] = telegram_id
                self._save(data)

    def get_student(self, phone: str) -> Optional[dict]:
        with self._lock: return self._load()["students"].get(phone)

    def save_student(self, phone: str, student_data: dict) -> None:
        with self._lock:
            data = self._load(); data["students"][phone] = student_data; self._save(data)

    def get_all_students(self) -> dict:
        with self._lock: return self._load()["students"]

    def get_communities(self) -> dict:
        with self._lock: return self._load().get("communities", {})

    def save_community(self, slug: str, community_data: dict) -> None:
        with self._lock:
            data = self._load(); data.setdefault("communities", {})[slug] = community_data; self._save(data)

    def delete_community(self, slug: str) -> None:
        with self._lock:
            data = self._load()
            if slug in data.get("communities", {}): del data["communities"][slug]; self._save(data)

    def get_certificates(self) -> dict:
        with self._lock: return self._load()["certificates"]

    def save_certificate(self, cert_hash: str, cert_data: dict) -> None:
        with self._lock:
            data = self._load(); data["certificates"][cert_hash] = cert_data; self._save(data)

    def append_webhook_event(self, payload: dict) -> None:
        with self._lock:
            data = self._load()
            events = data.get("webhook_events", [])
            events.append({"received_at": datetime.now(timezone.utc).isoformat(), "payload": payload})
            data["webhook_events"] = events[-self.MAX_WEBHOOK_EVENTS:]
            self._save(data)

    def get_bot_group_links(self) -> dict:
        with self._lock: return self._load().get("bot_group_links", {})

    def save_bot_group_link(self, group_id: str, course_slug: str) -> None:
        with self._lock:
            data = self._load(); data.setdefault("bot_group_links", {})[group_id] = course_slug; self._save(data)

    def get_course_workspace_links(self) -> dict:
        with self._lock: return self._load().get("course_workspace_links", {})

    def save_course_workspace_link(self, course_slug: str, workspace_slug: str) -> None:
        with self._lock:
            data = self._load(); data.setdefault("course_workspace_links", {})[course_slug] = workspace_slug; self._save(data)

# --- INSTANCIA SINGLETON ---
DB_PATH = os.getenv("DB_FILE", "lms_lite_db.json")
BACKUP_PATH = os.path.join(os.path.dirname(DB_PATH), "backups")
db = DatabaseManager(db_path=DB_PATH, backup_dir=BACKUP_PATH)
