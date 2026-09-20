"""FastMCP server assembly."""

from __future__ import annotations

from fastmcp import FastMCP

from .auth import current_id_token
from .client import AnansiClient
from .config import load_settings
from .context import AppContext
from .oauth import AnansiOAuthProvider, register_routes
from .tools import analysis, charts, data, discovery

INSTRUCTIONS = (
    "Anansi provides harmonized macroeconomic data by country. "
    "Resolve names to codes with list_countries and list_indicators, then use "
    "compare_countries, get_country_profile, rank_countries, or get_series_data. "
    "If a name is not found, use the discovery tools rather than guessing."
)


def build_server() -> FastMCP:
    settings = load_settings()
    auth = None
    if settings.mcp_base_url and settings.session_secret:
        auth = AnansiOAuthProvider(
            settings.mcp_base_url, settings.session_secret, settings.timeout
        )
    ctx = AppContext(settings=settings, client=AnansiClient(settings, current_id_token))
    mcp = FastMCP(name="Anansi", instructions=INSTRUCTIONS, auth=auth)
    if auth is not None:
        register_routes(mcp, auth)
    discovery.register(mcp, ctx)
    data.register(mcp, ctx)
    analysis.register(mcp, ctx)
    charts.register(mcp, ctx)
    return mcp


mcp = build_server()
