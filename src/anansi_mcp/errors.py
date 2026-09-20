"""Structured, agent-actionable outcomes.

Failures are returned as data, never raised, so the agent can self-correct.
Every hint names the discovery tool to call next.
"""

from __future__ import annotations

from typing import Any

COUNTRY_HINT = (
    "No country matched '{value}'. Call list_countries for valid countries, "
    "or pass the ISO3 code (e.g. IND)."
)
INDICATOR_HINT = (
    "No indicator matched '{value}'. Call list_indicators for valid indicator names."
)
SERIES_HINT = (
    "No series found. Call search_series to see which country, indicator, "
    "and frequency combinations exist."
)
REGION_HINT = (
    "No region matched '{value}'. Valid regions: Africa, Americas, Asia, "
    "Europe, Oceania."
)


class AnansiAPIError(Exception):
    """A non-2xx response from the Anansi API."""

    def __init__(
        self,
        status: int,
        code: str,
        message: str,
        request_id: str | None = None,
        reason: str | None = None,
    ):
        super().__init__(f"{code} ({status}): {message}")
        self.status = status
        self.code = code
        self.message = message
        self.request_id = request_id
        self.reason = reason


def ok(**payload: Any) -> dict[str, Any]:
    return {"status": "ok", **payload}


def not_found(value: str, hint: str) -> dict[str, Any]:
    return {"status": "not_found", "input": value, "hint": hint.format(value=value)}


def no_data(series_code: str, hint: str = SERIES_HINT, **extra: Any) -> dict[str, Any]:
    return {"status": "no_data", "series_code": series_code, "hint": hint, **extra}


def not_entitled(dataset: str) -> dict[str, Any]:
    return {
        "status": "not_entitled",
        "dataset": dataset,
        "hint": f"Your account does not have access to the '{dataset}' dataset.",
    }


def ambiguous(value: str, options: list[str]) -> dict[str, Any]:
    return {
        "status": "ambiguous",
        "input": value,
        "options": options,
        "hint": "Multiple matches. Retry with one of the options.",
    }
