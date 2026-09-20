"""Firebase Authentication REST client.

Signs a user in and mints ID tokens using the public Firebase web API key —
the same identity the website and Excel add-in use. No backend involvement.
"""

from __future__ import annotations

import httpx

IDENTITY_BASE = "https://identitytoolkit.googleapis.com/v1"
TOKEN_ENDPOINT = "https://securetoken.googleapis.com/v1/token"


class FirebaseAuthError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


class FirebaseAuth:
    def __init__(self, api_key: str, timeout: float = 15.0):
        if not api_key:
            raise ValueError("FirebaseAuth: FIREBASE_API_KEY is required")
        self._api_key = api_key
        self._http = httpx.AsyncClient(timeout=timeout)

    async def aclose(self) -> None:
        await self._http.aclose()

    async def refresh(self, refresh_token: str) -> dict:
        """Exchange a refresh token for a fresh ID token."""
        return await self._post(
            TOKEN_ENDPOINT,
            {"grant_type": "refresh_token", "refresh_token": refresh_token},
        )

    async def _post(self, url: str, body: dict) -> dict:
        response = await self._http.post(url, params={"key": self._api_key}, json=body)
        data = response.json()
        if response.status_code >= 400 or "error" in data:
            error = data.get("error") or {}
            message = error.get("message") if isinstance(error, dict) else str(error)
            raise FirebaseAuthError(_normalize(str(message or "unknown")), message or "")
        return data


def _normalize(message: str) -> str:
    return {
        "EMAIL_NOT_FOUND": "invalid_credential",
        "INVALID_PASSWORD": "invalid_credential",
        "INVALID_LOGIN_CREDENTIALS": "invalid_credential",
        "USER_DISABLED": "user_disabled",
        "TOO_MANY_ATTEMPTS_TRY_LATER": "too_many_attempts",
        "INVALID_REFRESH_TOKEN": "invalid_refresh_token",
        "TOKEN_EXPIRED": "invalid_refresh_token",
        "USER_NOT_FOUND": "invalid_refresh_token",
    }.get(message, message.lower() or "auth_error")
