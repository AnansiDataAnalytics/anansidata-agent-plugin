"""Name resolution.

The platform API filters by the **canonical country name** (not ISO3), so
country resolution returns that name. `alphacodes.csv` (the backend's own
reference, vendored unchanged) supplies the names, alpha codes, and short
names; the region map mirrors `config/country-reference.js`. Indicators resolve
against the live catalog.

Resolution is exact — no fuzzy matching, no suggestions.
"""

from __future__ import annotations

import csv
import re
import time
from functools import lru_cache
from pathlib import Path
from typing import Any

from .client import AnansiClient

_CSV = Path(__file__).parent / "data" / "alphacodes.csv"

# Mirrors server/config/country-reference.js (ISO3 -> continent).
_REGIONS: dict[str, list[str]] = {
    "Africa": [
        "DZA", "AGO", "BEN", "BWA", "BFA", "BDI", "CPV", "CMR", "CAF", "TCD",
        "COM", "COG", "COD", "CIV", "DJI", "EGY", "GNQ", "ERI", "SWZ", "ETH",
        "GAB", "GMB", "GHA", "GIN", "GNB", "KEN", "LSO", "LBR", "LBY", "MDG",
        "MWI", "MLI", "MRT", "MUS", "MAR", "MOZ", "NAM", "NER", "NGA", "RWA",
        "STP", "SEN", "SYC", "SLE", "SOM", "ZAF", "SSD", "SDN", "TZA", "TGO",
        "TUN", "UGA", "ZMB", "ZWE",
    ],
    "Americas": [
        "ATG", "ARG", "ABW", "BHS", "BRB", "BLZ", "BMU", "BOL", "BRA", "CAN",
        "CYM", "CHL", "COL", "CRI", "CUB", "CUW", "DMA", "DOM", "ECU", "SLV",
        "GRD", "GRL", "GTM", "GUY", "HTI", "HND", "JAM", "MEX", "NIC", "PAN",
        "PRY", "PER", "PRI", "KNA", "LCA", "VCT", "SUR", "TTO", "USA", "URY",
        "VEN",
    ],
    "Asia": [
        "AFG", "ARM", "AZE", "BHR", "BGD", "BTN", "BRN", "KHM", "CHN", "CYP",
        "GEO", "HKG", "IND", "IDN", "IRN", "IRQ", "ISR", "JPN", "JOR", "KAZ",
        "KWT", "KGZ", "LAO", "LBN", "MAC", "MYS", "MDV", "MNG", "MMR", "NPL",
        "PRK", "OMN", "PAK", "PSE", "PHL", "QAT", "SAU", "SGP", "KOR", "LKA",
        "SYR", "TWN", "TJK", "THA", "TLS", "TUR", "TKM", "ARE", "UZB", "VNM",
        "YEM",
    ],
    "Europe": [
        "ALB", "AND", "AUT", "BLR", "BEL", "BIH", "BGR", "HRV", "CZE", "DNK",
        "EST", "FIN", "FRA", "DEU", "GRC", "HUN", "ISL", "IRL", "ITA", "XKX",
        "LVA", "LIE", "LTU", "LUX", "MLT", "MDA", "MCO", "MNE", "NLD", "MKD",
        "NOR", "POL", "PRT", "ROU", "RUS", "SMR", "SRB", "SVK", "SVN", "ESP",
        "SWE", "CHE", "UKR", "GBR", "VAT",
    ],
    "Oceania": [
        "AUS", "FJI", "KIR", "MHL", "FSM", "NRU", "NCL", "NZL", "PLW", "PNG",
        "PYF", "WSM", "SLB", "TON", "TUV", "VUT",
    ],
}

_REGION_BY_ISO3 = {code: region for region, codes in _REGIONS.items() for code in codes}

# Common names the reference file spells formally.
_ALIASES = {
    "united states": "USA",
    "us": "USA",
    "usa": "USA",
    "america": "USA",
    "united kingdom": "GBR",
    "uk": "GBR",
    "britain": "GBR",
    "great britain": "GBR",
    "south korea": "KOR",
    "korea": "KOR",
    "north korea": "PRK",
    "russia": "RUS",
    "vietnam": "VNM",
    "uae": "ARE",
    "emirates": "ARE",
    "ivory coast": "CIV",
    "czech republic": "CZE",
    "burma": "MMR",
    "holland": "NLD",
    "turkey": "TUR",
}


def _norm(value: Any) -> str:
    text = str(value or "").lower().strip()
    text = text.replace("&", " and ")
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


@lru_cache(maxsize=1)
def _tables() -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    """Return (name_by_norm, iso3_by_norm, canonical_by_iso3)."""
    name_by_norm: dict[str, str] = {}
    iso3_by_norm: dict[str, str] = {}
    canonical_by_iso3: dict[str, str] = {}
    with _CSV.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            iso3 = (row.get("Alpha-3 code") or "").strip().upper()
            country = (row.get("Country") or "").strip()
            if not iso3 or not country:
                continue
            canonical_by_iso3[iso3] = country
            for key, target in (
                (row.get("Country"), name_by_norm),
                (row.get("Country_short"), name_by_norm),
                (row.get("Country"), iso3_by_norm),
                (row.get("Country_short"), iso3_by_norm),
                (row.get("Alpha-2 code"), iso3_by_norm),
                (iso3, iso3_by_norm),
            ):
                normalized = _norm(key)
                if normalized:
                    target.setdefault(normalized, country if target is name_by_norm else iso3)
    for alias, iso3 in _ALIASES.items():
        normalized = _norm(alias)
        name = canonical_by_iso3.get(iso3)
        if name:
            name_by_norm.setdefault(normalized, name)
        iso3_by_norm.setdefault(normalized, iso3)
    return name_by_norm, iso3_by_norm, canonical_by_iso3


def resolve_country(value: str) -> str | None:
    """Return the canonical country name for a name or code, or None."""
    if not value:
        return None
    text = value.strip()
    name_by_norm, iso3_by_norm, _ = _tables()
    if re.fullmatch(r"[A-Za-z]{2,3}", text):
        iso3 = iso3_by_norm.get(text.lower())
        if iso3:
            return _tables()[2].get(iso3)
    return name_by_norm.get(_norm(text))


def resolve_countries(values: list[str]) -> tuple[list[str], list[str]]:
    resolved, missing = [], []
    for value in values:
        name = resolve_country(value)
        if name:
            resolved.append(name)
        else:
            missing.append(value)
    return resolved, missing


def iso3_for_country(value: str) -> str | None:
    if not value:
        return None
    _, iso3_by_norm, _ = _tables()
    return iso3_by_norm.get(_norm(value))


def region_for_country(value: str) -> str | None:
    iso3 = iso3_for_country(value)
    return _REGION_BY_ISO3.get(iso3) if iso3 else None


def list_regions() -> list[str]:
    return list(_REGIONS.keys())


def region_country_names(region: str) -> list[str]:
    """Canonical country names for a region (empty if the region is unknown)."""
    key = next((r for r in _REGIONS if r.lower() == str(region or "").lower()), None)
    if not key:
        return []
    canonical = _tables()[2]
    return [canonical[code] for code in _REGIONS[key] if code in canonical]


def _norm_indicator(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().casefold())


_indicator_cache: dict[str, tuple[float, list[str]]] = {}
_INDICATOR_TTL_S = 600


async def resolve_indicator(client: AnansiClient, dataset: str, value: str) -> str | None:
    """Return the canonical indicator name for a name, or None."""
    if not value:
        return None
    now = time.monotonic()
    cached = _indicator_cache.get(dataset)
    if not cached or now - cached[0] > _INDICATOR_TTL_S:
        names = await client.indicators(dataset)
        _indicator_cache[dataset] = (now, names)
    else:
        names = cached[1]
    target = _norm_indicator(value)
    for name in names:
        if _norm_indicator(name) == target:
            return name
    return None
