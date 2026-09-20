"""Shared helpers for tool modules."""

from __future__ import annotations

import functools
from collections.abc import Awaitable, Callable
from typing import Any

from mcp.types import ToolAnnotations

from ..context import AppContext
from ..errors import AnansiAPIError

READ_ONLY = ToolAnnotations(readOnlyHint=True, openWorldHint=False)


def guarded(fn: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
    """Turn an API failure into a structured result instead of a raised error."""

    @functools.wraps(fn)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await fn(*args, **kwargs)
        except AnansiAPIError as err:
            return from_api_error(err)

    return wrapper


def dataset_name(ctx: AppContext, dataset: str | None) -> str:
    return dataset or ctx.settings.dataset


def parse_codes(value: Any) -> list[str]:
    if value is None:
        return []
    parts = value.split(",") if isinstance(value, str) else list(value)
    return [str(part).strip().upper() for part in parts if str(part).strip()]


def parse_list(value: Any) -> list[str]:
    """Split a csv string or list into trimmed values, preserving case."""
    if value is None:
        return []
    parts = value.split(",") if isinstance(value, str) else list(value)
    return [str(part).strip() for part in parts if str(part).strip()]


def partition_countries(names: list[str]) -> tuple[list[str], list[str]]:
    """Split names into (comma-free, comma-containing).

    The platform API splits the `country` parameter on commas, so names that
    themselves contain a comma cannot be sent as a filter.
    """
    plain = [n for n in names if "," not in n]
    comma = [n for n in names if "," in n]
    return plain, comma


def compact_series(row: dict[str, Any]) -> dict[str, Any]:
    stats = row.get("stats") or {}
    return {
        "series_code": row.get("series_code"),
        "name": row.get("name"),
        "country": row.get("country"),
        "country_code": row.get("country_code"),
        "indicator": row.get("indicator"),
        "frequency": row.get("frequency"),
        "unit": row.get("unit"),
        "coverage": {
            "start": stats.get("start_date"),
            "end": stats.get("end_date"),
            "latest": stats.get("last_value"),
        },
    }


def from_api_error(err: AnansiAPIError) -> dict[str, Any]:
    if err.status == 401:
        return {
            "status": "unauthorized",
            "hint": err.message or "Sign in required to access Anansi data.",
        }
    if err.status == 403:
        # The platform reports a machine-readable `reason`; map the ones the
        # agent can act on, otherwise pass the server's message through.
        reason = err.reason or err.code
        hints = {
            "email-unverified": (
                "Your email is not verified yet. Verify it, then retry — "
                "the next call refreshes automatically."
            ),
            "not-entitled": "Your account is not entitled to this dataset.",
            "export-disabled": "Downloads are disabled on trial access.",
            "addon-required": "This content requires an add-on subscription.",
            "staging-forbidden": "Staging data is restricted to internal users.",
        }
        return {
            "status": reason.replace("-", "_"),
            "code": str(err.code),
            "hint": hints.get(reason, err.message),
        }
    if err.status == 404:
        return {"status": "not_found", "code": str(err.code), "hint": err.message}
    if err.status == 429:
        return {"status": "rate_limited", "hint": "Rate limit reached. Retry shortly."}
    return {"status": "api_error", "code": str(err.code), "message": err.message}
