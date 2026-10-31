from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.config import get_settings

SESSION_COOKIE = "warsaw_admin_session"
CSRF_COOKIE = "warsaw_csrf_token"


def _serializer() -> URLSafeTimedSerializer:
    settings = get_settings()
    return URLSafeTimedSerializer(settings.secret_key, salt="admin-session")


def create_session_token(admin_id: int, username: str) -> str:
    return _serializer().dumps({"admin_id": admin_id, "username": username, "iat": time.time()})


def load_session_token(token: str) -> dict[str, Any] | None:
    settings = get_settings()
    max_age = settings.session_ttl_hours * 3600
    try:
        payload = _serializer().loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None
    if not isinstance(payload, dict) or "admin_id" not in payload:
        return None
    return payload


def create_csrf_token(session_token: str) -> str:
    settings = get_settings()
    digest = hmac.new(
        settings.secret_key.encode("utf-8"),
        session_token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return digest


def verify_csrf_token(session_token: str, csrf_token: str) -> bool:
    expected = create_csrf_token(session_token)
    return hmac.compare_digest(expected, csrf_token or "")


def hash_ip(ip: str) -> str:
    settings = get_settings()
    return hashlib.sha256(f"{settings.secret_key}:{ip}".encode("utf-8")).hexdigest()


def dumps_safe(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, default=str)
