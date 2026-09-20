"""OAuth 2.1 authorization server for MCP clients.

The flow mirrors the Financial Datasets experience:

    install -> /authorize -> /login (Anansi account) -> /consent -> redirect back

Login uses Firebase (Google or email) via the public web config; the resulting
refresh token is stored server-side and used to mint ID tokens for /api. The
SDK handles PKCE and redirect-URI validation; we supply client/code/token
storage and the two user-facing pages.
"""

from __future__ import annotations

import hashlib
import hmac
import html
import json
import os
import secrets
import time
from typing import Any
from urllib.parse import urlparse

import httpx
from fastmcp.server.auth import OAuthProvider
from mcp.server.auth.provider import (
    AccessToken,
    AuthorizationCode,
    AuthorizationParams,
    RefreshToken,
)
from mcp.server.auth.settings import ClientRegistrationOptions, RevocationOptions
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse

from . import auth as session_auth
from .config import load_settings

SCOPE = "macro.read"
CODE_TTL_S = 300
ACCESS_TTL_S = 3600
REFRESH_TTL_S = 30 * 24 * 3600
PENDING_TTL_S = 900
SESSION_COOKIE = "anansi_mcp_session"
AUTHZ_COOKIE = "anansi_mcp_authz"


class AnansiOAuthProvider(OAuthProvider):
    def __init__(self, base_url: str, session_secret: str, timeout: float = 15.0):
        super().__init__(
            base_url=base_url,
            required_scopes=[SCOPE],
            client_registration_options=ClientRegistrationOptions(
                enabled=True, valid_scopes=[SCOPE], default_scopes=[SCOPE]
            ),
            revocation_options=RevocationOptions(enabled=True),
        )
        self._secret = session_secret.encode()
        self._http = httpx.AsyncClient(timeout=timeout)
        self._clients: dict[str, OAuthClientInformationFull] = {}
        self._codes: dict[str, AuthorizationCode] = {}
        self._access: dict[str, AccessToken] = {}
        self._refresh: dict[str, RefreshToken] = {}
        self._sessions: dict[str, dict[str, Any]] = {}  # sid -> {uid, expires_at}
        self._pending: dict[str, dict[str, Any]] = {}  # rid -> authorization request

    # --- client registration ---

    async def get_client(self, client_id: str) -> OAuthClientInformationFull | None:
        return self._clients.get(client_id)

    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        self._clients[client_info.client_id] = client_info

    # --- authorization ---

    async def authorize(
        self, client: OAuthClientInformationFull, params: AuthorizationParams
    ) -> str:
        rid = secrets.token_urlsafe(16)
        self._prune()
        self._pending[rid] = {
            "client_id": client.client_id,
            "scopes": params.scopes,
            "code_challenge": params.code_challenge,
            "redirect_uri": str(params.redirect_uri),
            "redirect_uri_provided_explicitly": params.redirect_uri_provided_explicitly,
            "resource": params.resource,
            "state": params.state,
            "expires_at": time.time() + PENDING_TTL_S,
        }
        return f"{str(self.base_url).rstrip('/')}/login?rid={rid}"

    def pending(self, rid: str) -> dict[str, Any] | None:
        """The pending authorization request for `rid`, or None if missing/expired."""
        self._prune()
        entry = self._pending.get(rid)
        if entry and entry["expires_at"] > time.time():
            return entry
        return None

    def _prune(self) -> None:
        """Drop expired entries so the in-memory stores stay bounded."""
        now = time.time()
        self._codes = {k: v for k, v in self._codes.items() if v.expires_at > now}
        self._access = {
            k: v
            for k, v in self._access.items()
            if v.expires_at is None or v.expires_at > now
        }
        self._refresh = {k: v for k, v in self._refresh.items() if v.expires_at > now}
        self._pending = {
            k: v for k, v in self._pending.items() if v["expires_at"] > now
        }
        self._sessions = {
            k: v for k, v in self._sessions.items() if v["expires_at"] > now
        }

    async def load_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: str
    ) -> AuthorizationCode | None:
        code = self._codes.get(authorization_code)
        if code and code.expires_at > time.time():
            return code
        return None

    async def exchange_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: AuthorizationCode
    ) -> OAuthToken:
        self._prune()
        self._codes.pop(authorization_code.code, None)
        access = self._new_access(
            client.client_id, authorization_code.scopes, authorization_code.subject,
            authorization_code.resource,
        )
        refresh = self._new_refresh(
            client.client_id, authorization_code.scopes, authorization_code.subject,
            authorization_code.resource,
        )
        return OAuthToken(
            access_token=access.token,
            token_type="Bearer",
            expires_in=ACCESS_TTL_S,
            scope=" ".join(authorization_code.scopes),
            refresh_token=refresh.token,
        )

    # --- refresh tokens ---

    async def load_refresh_token(
        self, client: OAuthClientInformationFull, refresh_token: str
    ) -> RefreshToken | None:
        token = self._refresh.get(refresh_token)
        if token and token.expires_at > time.time():
            return token
        return None

    async def exchange_refresh_token(
        self,
        client: OAuthClientInformationFull,
        refresh_token: RefreshToken,
        scopes: list[str],
    ) -> OAuthToken:
        self._prune()
        self._refresh.pop(refresh_token.token, None)
        granted = scopes or refresh_token.scopes
        access = self._new_access(
            client.client_id, granted, refresh_token.subject, refresh_token.resource
        )
        refresh = self._new_refresh(
            client.client_id, granted, refresh_token.subject, refresh_token.resource
        )
        return OAuthToken(
            access_token=access.token,
            token_type="Bearer",
            expires_in=ACCESS_TTL_S,
            scope=" ".join(granted),
            refresh_token=refresh.token,
        )

    # --- access tokens ---

    async def load_access_token(self, token: str) -> AccessToken | None:
        access = self._access.get(token)
        if access and (access.expires_at is None or access.expires_at > time.time()):
            return access
        return None

    async def revoke_token(self, token: AccessToken | RefreshToken) -> None:
        self._access.pop(token.token, None)
        self._refresh.pop(token.token, None)

    # --- helpers ---

    def _new_access(self, client_id, scopes, subject, resource) -> AccessToken:
        token = AccessToken(
            token=secrets.token_urlsafe(32),
            client_id=client_id,
            scopes=list(scopes or [SCOPE]),
            expires_at=int(time.time()) + ACCESS_TTL_S,
            resource=resource,
            subject=subject,
            claims={"uid": subject},
        )
        self._access[token.token] = token
        return token

    def _new_refresh(self, client_id, scopes, subject, resource) -> RefreshToken:
        token = RefreshToken(
            token=secrets.token_urlsafe(32),
            client_id=client_id,
            scopes=list(scopes or [SCOPE]),
            expires_at=int(time.time()) + REFRESH_TTL_S,
            resource=resource,
            subject=subject,
        )
        self._refresh[token.token] = token
        return token

    def issue_code(self, rid: str, uid: str) -> str:
        """Create the authorization code and return the client redirect URL."""
        self._prune()
        pending = self._pending.pop(rid)
        code = secrets.token_urlsafe(32)
        self._codes[code] = AuthorizationCode(
            code=code,
            scopes=pending["scopes"],
            expires_at=time.time() + CODE_TTL_S,
            client_id=pending["client_id"],
            code_challenge=pending["code_challenge"],
            redirect_uri=pending["redirect_uri"],
            redirect_uri_provided_explicitly=pending["redirect_uri_provided_explicitly"],
            resource=pending["resource"],
            subject=uid,
        )
        params = {"code": code}
        if pending.get("state"):
            params["state"] = pending["state"]
        sep = "&" if "?" in pending["redirect_uri"] else "?"
        return pending["redirect_uri"] + sep + "&".join(f"{k}={v}" for k, v in params.items())

    def deny(self, rid: str) -> str:
        pending = self._pending.pop(rid, None) or {}
        uri = pending.get("redirect_uri", "")
        params = {"error": "access_denied"}
        if pending.get("state"):
            params["state"] = pending["state"]
        sep = "&" if "?" in uri else "?"
        return uri + sep + "&".join(f"{k}={v}" for k, v in params.items())

    # --- session cookies ---

    def new_session(self, uid: str) -> str:
        self._prune()
        sid = secrets.token_urlsafe(24)
        self._sessions[sid] = {"uid": uid, "expires_at": time.time() + REFRESH_TTL_S}
        return self._signed(sid)

    def session_uid(self, request: Request) -> str | None:
        raw = request.cookies.get(SESSION_COOKIE)
        sid = self._unsign(raw) if raw else None
        entry = self._sessions.get(sid) if sid else None
        return entry["uid"] if entry else None

    def sign_authz(self, rid: str) -> str:
        return self._signed(f"authz:{rid}")

    def verify_authz(self, request: Request, rid: str) -> bool:
        """True only if this browser started the authorization request `rid`."""
        raw = request.cookies.get(AUTHZ_COOKIE)
        return bool(raw) and self._unsign(raw) == f"authz:{rid}"

    def _signed(self, value: str) -> str:
        mac = hmac.new(self._secret, value.encode(), hashlib.sha256).hexdigest()
        return f"{value}.{mac}"

    def _unsign(self, value: str) -> str | None:
        sid, _, mac = value.partition(".")
        expected = hmac.new(self._secret, sid.encode(), hashlib.sha256).hexdigest()
        return sid if sid and hmac.compare_digest(mac, expected) else None

    async def verify_firebase_token(self, id_token: str) -> str | None:
        """Confirm the ID token with Firebase and return the uid."""
        settings = load_settings()
        response = await self._http.post(
            "https://identitytoolkit.googleapis.com/v1/accounts:lookup",
            params={"key": settings.firebase_api_key},
            json={"idToken": id_token},
        )
        if response.status_code >= 400:
            return None
        users = response.json().get("users") or []
        return users[0].get("localId") if users else None


# --- pages -------------------------------------------------------------------

_PAGE_STYLE = """
body{font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
background:#0b0b0c;color:#f5f5f5;display:flex;justify-content:center;min-height:100vh;margin:0}
.card{width:360px;margin-top:12vh;text-align:center}
h1{font-size:20px;font-weight:600;margin:0 0 24px}
.box{border:1px solid #2a2a2e;border-radius:12px;padding:18px;text-align:left;margin-bottom:28px;background:#141416}
.row{display:flex;align-items:center;gap:12px;margin-bottom:14px}
.row:last-child{margin-bottom:0}
.sub{color:#a1a1aa;font-size:13px}
.label{color:#a1a1aa;font-size:12px;text-transform:uppercase;letter-spacing:.04em;margin-bottom:8px}
.btn{display:block;width:100%;box-sizing:border-box;padding:11px 14px;border-radius:8px;border:1px solid #2a2a2e;
background:#1c1c1f;color:#f5f5f5;font-size:14px;cursor:pointer;text-align:center;text-decoration:none;margin-bottom:12px}
.btn.primary{background:#2563eb;border-color:#2563eb}
.btn:hover{filter:brightness(1.1)}
.deny{background:transparent;border:1px solid #3f3f46}
.err{color:#f87171;font-size:13px;min-height:18px;margin-bottom:12px}
.field{width:100%;box-sizing:border-box;padding:11px 12px;border-radius:8px;border:1px solid #2a2a2e;
background:#0f0f11;color:#f5f5f5;font-size:14px;margin-bottom:10px}
.field:focus{outline:none;border-color:#3f3f46}
.back{display:block;text-align:center;color:#71717a;font-size:13px;text-decoration:none;margin-top:2px}
.foot{color:#71717a;font-size:13px;margin-top:8px}
.foot a{color:#93c5fd;text-decoration:none}
"""


def _login_html(rid: str, login_url: str) -> str:
    settings = load_settings()
    config = {
        "apiKey": settings.firebase_api_key or "",
        "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN", ""),
        "projectId": settings.firebase_project_id or "",
    }
    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Authorize Anansi MCP Server</title><style>{_PAGE_STYLE}</style></head>
<body><div class="card">
<h1>Authorize Anansi MCP Server</h1>
<div class="box">
  <div class="row"><div><div>Anansi MCP Server</div>
    <div class="sub">wants to access your Anansi account</div></div></div>
  <div class="row"><div><div>Data Access</div>
    <div class="sub">Macroeconomic data (read-only)</div></div></div>
</div>
<div id="err" class="err"></div>
<button class="btn" id="google">Continue with Google</button>
<button class="btn" id="email">Continue with Email</button>
<form id="emailForm" style="display:none">
  <input class="field" id="emailInput" type="email" placeholder="Email" autocomplete="username" required>
  <input class="field" id="passwordInput" type="password" placeholder="Password" autocomplete="current-password" required>
  <button class="btn primary" type="submit">Sign in</button>
  <a class="back" href="#" id="back">Back</a>
</form>
<div class="foot">Need to create an account? <a href="https://www.anansidata.com/auth" target="_blank" rel="noopener">Sign up</a><br>
<span class="sub" style="font-size:12px">Then return to this tab and sign in.</span></div>
</div>
<script type="module">
import {{ initializeApp }} from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
import {{ getAuth, GoogleAuthProvider, signInWithPopup, signInWithEmailAndPassword }} from "https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js";
const app = initializeApp({json.dumps(config)});
const auth = getAuth(app);
const err = document.getElementById("err");
const googleBtn = document.getElementById("google");
const emailBtn = document.getElementById("email");
const form = document.getElementById("emailForm");
const emailInput = document.getElementById("emailInput");
const passwordInput = document.getElementById("passwordInput");

function messageFor(ex) {{
  const code = (ex && ex.code) || "";
  if (code === "auth/invalid-credential" || code === "auth/wrong-password" || code === "auth/user-not-found")
    return "Incorrect email or password.";
  if (code === "auth/invalid-email") return "That doesn't look like a valid email address.";
  if (code === "auth/too-many-requests") return "Too many attempts — please wait a minute and try again.";
  if (code === "auth/user-disabled") return "This account has been disabled.";
  return "Sign-in failed. Please try again.";
}}
async function submit(user) {{
  const idToken = await user.getIdToken();
  const res = await fetch("{login_url}/login/session", {{
    method: "POST", headers: {{"Content-Type": "application/json"}},
    body: JSON.stringify({{rid: "{rid}", idToken, refreshToken: user.refreshToken}})
  }});
  if (!res.ok) {{ err.textContent = "Sign-in failed. Please try again."; return; }}
  const data = await res.json();
  window.location = data.redirect;
}}
googleBtn.onclick = async () => {{
  err.textContent = "";
  try {{ await submit((await signInWithPopup(auth, new GoogleAuthProvider())).user); }}
  catch (ex) {{ if (ex && ex.code === "auth/popup-closed-by-user") return; err.textContent = messageFor(ex); }}
}};
emailBtn.onclick = () => {{
  googleBtn.style.display = "none";
  emailBtn.style.display = "none";
  form.style.display = "block";
  emailInput.focus();
}};
document.getElementById("back").onclick = (event) => {{
  event.preventDefault();
  form.style.display = "none";
  googleBtn.style.display = "block";
  emailBtn.style.display = "block";
  err.textContent = "";
}};
form.onsubmit = async (event) => {{
  event.preventDefault();
  err.textContent = "";
  try {{
    const user = (await signInWithEmailAndPassword(auth, emailInput.value.trim(), passwordInput.value)).user;
    await submit(user);
  }} catch (ex) {{ err.textContent = messageFor(ex); }}
}};
</script></body></html>"""


def _consent_html(rid: str, login_url: str, client_name: str, redirect_host: str) -> str:
    name = html.escape(client_name)
    host = html.escape(redirect_host)
    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Authorize Anansi MCP Server?</title><style>{_PAGE_STYLE}</style></head>
<body><div class="card">
<h1 style="text-align:left">Authorize Anansi MCP Server?</h1>
<p class="sub" style="text-align:left"><strong>{name}</strong> wants the following permissions</p>
<ul class="sub" style="text-align:left;padding-left:20px"><li>Read access to macroeconomic data</li></ul>
<p class="sub" style="text-align:left">You'll be redirected to {host}.</p>
<form method="post" action="{login_url}/consent">
  <input type="hidden" name="rid" value="{rid}">
  <div style="display:flex;gap:12px">
    <button class="btn deny" name="decision" value="deny" style="flex:1">Cancel</button>
    <button class="btn primary" name="decision" value="approve" style="flex:1">Authorize</button>
  </div>
</form>
</div></body></html>"""


def _expired_html() -> str:
    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Authorization request expired</title><style>{_PAGE_STYLE}</style></head>
<body><div class="card"><h1>Authorization request expired</h1>
<p class="sub">Please start again from your client.</p></div></body></html>"""


def register_routes(mcp, provider: AnansiOAuthProvider) -> None:
    base = str(provider.base_url).rstrip("/")

    @mcp.custom_route("/login", methods=["GET"])
    async def login_page(request: Request) -> Any:
        rid = request.query_params.get("rid", "")
        if provider.pending(rid) is None:
            return HTMLResponse(_expired_html(), status_code=400)
        if provider.session_uid(request):
            response: Any = RedirectResponse(f"{base}/consent?rid={rid}", status_code=302)
        else:
            response = HTMLResponse(_login_html(rid, base))
        # Bind this authorization request to this browser.
        response.set_cookie(
            AUTHZ_COOKIE,
            provider.sign_authz(rid),
            httponly=True,
            samesite="lax",
            secure=base.startswith("https"),
            max_age=PENDING_TTL_S,
            path="/",
        )
        return response

    @mcp.custom_route("/login/session", methods=["POST"])
    async def login_session(request: Request) -> Any:
        body = await request.json()
        rid = body.get("rid", "")
        id_token = body.get("idToken", "")
        refresh_token = body.get("refreshToken", "")
        if provider.pending(rid) is None:
            return JSONResponse({"error": "expired"}, status_code=400)
        uid = await provider.verify_firebase_token(id_token)
        if not uid:
            return JSONResponse({"error": "invalid_token"}, status_code=401)
        if refresh_token:
            session_auth.sessions().set(uid, refresh_token)
        # Mirror the web console: create/backfill the Anansi profile on login.
        await session_auth.provision_user(id_token)
        response = JSONResponse({"redirect": f"{base}/consent?rid={rid}"})
        response.set_cookie(
            SESSION_COOKIE,
            provider.new_session(uid),
            httponly=True,
            samesite="lax",
            secure=str(base).startswith("https"),
            max_age=REFRESH_TTL_S,
            path="/",
        )
        return response

    @mcp.custom_route("/consent", methods=["GET"])
    async def consent_page(request: Request) -> Any:
        rid = request.query_params.get("rid", "")
        pending = provider.pending(rid)
        if pending is None:
            return HTMLResponse(_expired_html(), status_code=400)
        if not provider.session_uid(request) or not provider.verify_authz(request, rid):
            return RedirectResponse(f"{base}/login?rid={rid}", status_code=302)
        client = await provider.get_client(pending["client_id"])
        client_name = (
            client.client_name if client and client.client_name else pending["client_id"]
        )
        redirect_host = urlparse(pending["redirect_uri"]).netloc or pending["redirect_uri"]
        return HTMLResponse(_consent_html(rid, base, client_name, redirect_host))

    @mcp.custom_route("/consent", methods=["POST"])
    async def consent_decision(request: Request) -> Any:
        form = await request.form()
        rid = str(form.get("rid", ""))
        decision = str(form.get("decision", ""))
        if provider.pending(rid) is None:
            return HTMLResponse(_expired_html(), status_code=400)
        uid = provider.session_uid(request)
        if not uid or not provider.verify_authz(request, rid):
            return RedirectResponse(f"{base}/login?rid={rid}", status_code=302)
        if decision != "approve":
            return RedirectResponse(provider.deny(rid), status_code=302)
        return RedirectResponse(provider.issue_code(rid, uid), status_code=302)
