"""Environment-driven settings."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    # Base host of the Anansi platform (the client appends /api).
    base_url: str
    # Default dataset id sent as the X-Database header.
    dataset: str
    timeout: float
    page_size: int
    max_observations: int
    # Firebase web config (public, same as the website and add-in). Used by the
    # MCP's OAuth login to sign the user in and mint ID tokens for /api.
    firebase_api_key: str | None
    firebase_project_id: str | None
    # Public base URL of this MCP server (used for OAuth redirects), and the
    # secret used to sign the session cookie. Both are required for auth.
    mcp_base_url: str | None
    session_secret: str


def load_settings() -> Settings:
    return Settings(
        base_url=os.getenv("ANANSI_API_BASE_URL", "http://localhost:5001").rstrip("/"),
        dataset=(os.getenv("ANANSI_DATASET") or "wed").strip(),
        timeout=float(os.getenv("ANANSI_TIMEOUT", "30")),
        page_size=int(os.getenv("ANANSI_PAGE_SIZE", "100")),
        max_observations=int(os.getenv("ANANSI_MAX_OBSERVATIONS", "2000")),
        firebase_api_key=(os.getenv("FIREBASE_API_KEY") or "").strip() or None,
        firebase_project_id=(os.getenv("FIREBASE_PROJECT_ID") or "").strip() or None,
        mcp_base_url=(os.getenv("ANANSI_MCP_BASE_URL") or "").strip().rstrip("/") or None,
        session_secret=(os.getenv("MCP_SESSION_SECRET") or "").strip(),
    )
