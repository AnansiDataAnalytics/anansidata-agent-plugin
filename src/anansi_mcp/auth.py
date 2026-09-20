"""Authentication: session storage and the per-request ID token provider.

The MCP's OAuth login populates the session store with the user's Firebase
refresh token. Every backend call mints (and caches) a fresh Firebase ID token
for the authenticated subject. There is no anonymous or shared-credential path.
"""

from __future__ import annotations

import time
from threading import Lock

import httpx
from fastmcp.server.dependencies import get_access_token

from .config import load_settings
from .firebase import FirebaseAuth


class SessionStore:
    """uid -> Firebase refresh token. In-memory for now; must be encrypted and
    persistent for multi-instance production (tracked in spec §9)."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._refresh: dict[str, str] = {}

    def set(self, uid: str, refresh_token: str) -> None:
        with self._lock:
            self._refresh[uid] = refresh_token

    def get(self, uid: str) -> str | None:
        with self._lock:
            return self._refresh.get(uid)

    def clear(self, uid: str) -> None:
        with self._lock:
            self._refresh.pop(uid, None)


_store = SessionStore()
_firebase: FirebaseAuth | None = None
_id_tokens: dict[str, tuple[str, float]] = {}


def sessions() -> SessionStore:
    return _store


def _client() -> FirebaseAuth:
    global _firebase
    if _firebase is None:
        settings = load_settings()
        if not settings.firebase_api_key:
            raise RuntimeError("FIREBASE_API_KEY is not configured")
        _firebase = FirebaseAuth(settings.firebase_api_key, settings.timeout)
    return _firebase


async def current_id_token(force: bool = False) -> str | None:
    """The Firebase ID token for the authenticated request, or None.

    Pass force=True to bypass the cache and mint a fresh token — used when the
    backend rejects a cached token (e.g. after the user verifies their email).
    """
    try:
        access = get_access_token()
    except (LookupError, RuntimeError):
        return None
    uid = getattr(access, "subject", None) if access else None
    if not uid:
        return None
    now = time.time()
    if force:
        _id_tokens.pop(uid, None)
    cached = _id_tokens.get(uid)
    if cached and cached[1] > now + 30:
        return cached[0]
    refresh_token = _store.get(uid)
    if not refresh_token:
        return None
    data = await _client().refresh(refresh_token)
    token = data.get("id_token") or data.get("idToken")
    expires_in = int(data.get("expires_in") or data.get("expiresIn") or 3600)
    if token:
        _id_tokens[uid] = (token, now + expires_in)
    return token


async def provision_user(id_token: str) -> bool:
    """Create/backfill the Anansi profile for this user.

    This is the same call the web console makes on login: it creates the
    Firestore users/{uid} document (and custom claims) if missing, so a
    Firebase-only account can resolve entitlements. Idempotent and never
    blocks login.
    """
    settings = load_settings()
    try:
        async with httpx.AsyncClient(
            base_url=f"{settings.base_url}/api", timeout=settings.timeout
        ) as http:
            response = await http.post(
                "/auth/provision",
                headers={"Authorization": f"Bearer {id_token}"},
                json={},
            )
            return response.status_code < 400
    except httpx.HTTPError:
        return False
