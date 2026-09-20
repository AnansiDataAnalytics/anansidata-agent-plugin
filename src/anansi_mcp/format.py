"""Numeric formatting — the single place values are cleaned for output.

The data layer applies these to derived/display fields so the model (and the
UI) sees readable numbers. Raw observations in `get_series_data` are left at
full precision.
"""

from __future__ import annotations

from typing import Any


def clean(value: Any) -> Any:
    """Round a number to a readable precision, keeping it numeric."""
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return value
    magnitude = abs(number)
    if magnitude >= 1000:
        return round(number)
    if magnitude >= 1:
        return round(number, 2)
    if number == 0:
        return 0.0
    return round(number, 4)


def display(value: Any) -> str | None:
    """Format a number for display (thousands separators)."""
    cleaned = clean(value)
    if cleaned is None:
        return None
    if isinstance(cleaned, int):
        return f"{cleaned:,}"
    if isinstance(cleaned, float):
        return f"{int(cleaned):,}" if cleaned.is_integer() else f"{cleaned:,.2f}"
    return str(cleaned)


def display_pct(value: Any) -> str | None:
    """Format a percentage for display (signed, two decimals)."""
    if value is None:
        return None
    try:
        return f"{float(value):+.2f}%"
    except (TypeError, ValueError):
        return str(value)
