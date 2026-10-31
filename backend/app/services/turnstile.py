from __future__ import annotations

import httpx

from app.config import get_settings


async def verify_turnstile(token: str, remote_ip: str | None = None) -> bool:
    settings = get_settings()
    # Demo / local mode: skip verification when explicitly bypassed,
    # in tests, or when Turnstile keys are not configured.
    if (
        settings.turnstile_bypass
        or settings.environment in {"test", "development", "demo"}
        or not settings.turnstile_secret_key
        or not settings.turnstile_site_key
    ):
        return True

    data = {
        "secret": settings.turnstile_secret_key,
        "response": token,
    }
    if remote_ip:
        data["remoteip"] = remote_ip

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(settings.turnstile_verify_url, data=data)
        response.raise_for_status()
        payload = response.json()
        return bool(payload.get("success"))
