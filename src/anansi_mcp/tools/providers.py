"""Task logic shared by the plain tools and the chart tools."""

from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime
from typing import Any

from ..compute import cagr, correlation, growth, moving_average, rebase, spread, zscore
from ..context import AppContext
from ..errors import COUNTRY_HINT, SERIES_HINT, AnansiAPIError, no_data, not_found, ok
from ..format import clean, display, display_pct
from ..resolve import resolve_countries, resolve_country, resolve_indicator
from ._shared import compact_series, from_api_error, partition_countries

HEADLINE_INDICATORS = [
    "Nominal GDP",
    "Real GDP",
    "Real GDP per capita",
    "Inflation rate",
    "Unemployment rate",
    "Current account (% of GDP)",
    "General government debt (% of GDP)",
    "Central bank policy rate",
    "Population",
    "Exports (% of GDP)",
    "Imports (% of GDP)",
]

INDICATOR_HINT = (
    "No indicator matched '{value}'. Call list_indicators for valid indicator names."
)


def today() -> str:
    return datetime.now(UTC).date().isoformat()


def years_ago(years: int) -> str:
    current = datetime.now(UTC).date()
    return date(current.year - years, 1, 1).isoformat()


def _latest_actual(observations: list[dict[str, Any]]) -> dict[str, Any] | None:
    actual = [
        o for o in observations if o.get("value") is not None and not o.get("is_forecast")
    ]
    return actual[-1] if actual else None


def _trim(observations: list[dict[str, Any]], max_points: int) -> tuple[list, bool]:
    if len(observations) <= max_points:
        return observations, False
    return observations[-max_points:], True


def _cap(rows: list[dict[str, Any]], max_points: int) -> tuple[list[dict[str, Any]], bool]:
    if max_points and len(rows) > max_points:
        return rows[-max_points:], True
    return rows, False


def _clean_points(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"date": row["date"], "value": clean(row["value"])} for row in rows]


async def _series_meta(
    ctx: AppContext, dataset: str, codes: list[str]
) -> dict[str, dict[str, Any]]:
    semaphore = asyncio.Semaphore(10)

    async def fetch(code: str):
        async with semaphore:
            return code, await ctx.client.series(dataset, code)

    pairs = await asyncio.gather(*(fetch(c) for c in codes))
    return {code: meta for code, meta in pairs if meta}


async def _fetch_series(
    ctx: AppContext,
    dataset: str,
    names: list[str] | None = None,
    indicator: str | None = None,
    frequency: str | None = None,
    search: str | None = None,
) -> list[dict[str, Any]]:
    """Search series by country names, working around the comma-splitting of
    the platform's `country` parameter."""
    names = names or []
    plain, comma = partition_countries(names)
    if comma:
        # Cannot filter by these names server-side; fetch and match locally.
        rows = await ctx.client.search_all_series(
            dataset, indicator=indicator, frequency=frequency, search=search
        )
        wanted = set(names)
        return [row for row in rows if row.get("country") in wanted]
    return await ctx.client.search_all_series(
        dataset,
        country=",".join(plain) if plain else None,
        indicator=indicator,
        frequency=frequency,
        search=search,
    )


async def get_series_data(
    ctx: AppContext,
    dataset: str,
    codes: list[str],
    start_date: str | None = None,
    end_date: str | None = None,
    max_points: int | None = None,
) -> dict[str, Any]:
    if not codes:
        return not_found("", SERIES_HINT)
    limit = max_points or ctx.settings.max_observations
    try:
        meta = await _series_meta(ctx, dataset, codes)
        found = [c for c in codes if c in meta]
        missing = [c for c in codes if c not in meta]
        if not found:
            return {"status": "not_found", "input": codes, "hint": SERIES_HINT}
        if len(found) == 1:
            code = found[0]
            observations = await ctx.client.series_data(
                dataset, code, start_date, end_date, limit
            )
            by_code = {code: observations}
        else:
            by_code = await ctx.client.series_data_many(
                dataset, found, start_date, end_date, limit
            )
        series = []
        for code in found:
            observations = by_code.get(code, [])
            trimmed, truncated = _trim(observations, limit)
            series.append(
                {
                    "series_code": code,
                    "name": meta[code].get("name"),
                    "country": meta[code].get("country"),
                    "unit": meta[code].get("unit"),
                    "frequency": meta[code].get("frequency"),
                    "observation_count": len(observations),
                    "truncated": truncated,
                    "observations": trimmed,
                }
            )
        return ok(series=series, missing=missing)
    except AnansiAPIError as err:
        return from_api_error(err)


async def compare_countries(
    ctx: AppContext,
    dataset: str,
    indicator: str,
    countries: list[str],
    frequency: str = "Annual",
    start_date: str | None = None,
    end_date: str | None = None,
    max_points: int = 60,
) -> dict[str, Any]:
    names, missing = resolve_countries(countries)
    if missing:
        return {
            "status": "not_found",
            "input": missing,
            "hint": COUNTRY_HINT.format(value=", ".join(missing)),
        }
    try:
        name = await resolve_indicator(ctx.client, dataset, indicator)
        if not name:
            return not_found(indicator, INDICATOR_HINT)
        rows = await _fetch_series(
            ctx, dataset, names, indicator=name, frequency=frequency
        )
        if not rows:
            return no_data(f"{name} / {frequency}")
        by_country = {
            row.get("country_code"): row for row in rows if row.get("country_code")
        }
        codes = [row["series_code"] for row in by_country.values()]
        by_code = await ctx.client.series_data_many(dataset, codes, start_date, end_date)

        dates: dict[str, dict[str, Any]] = {}
        forecasts: dict[str, bool] = {}
        for code, row in by_country.items():
            for observation in by_code.get(row["series_code"], []):
                if observation.get("value") is None:
                    continue
                dates.setdefault(observation["date"], {})[code] = clean(observation["value"])
                if observation.get("is_forecast"):
                    forecasts[observation["date"]] = True
        complete = [d for d in sorted(dates) if len(dates[d]) == len(by_country)]
        table = [
            {"date": d, "is_forecast": forecasts.get(d, False), **dates[d]}
            for d in complete
        ]
        truncated = False
        if max_points and len(table) > max_points:
            table = table[-max_points:]
            truncated = True

        first = next(iter(by_country.values()))
        resolved = {row.get("country") for row in by_country.values()}
        return ok(
            indicator=name,
            frequency=frequency,
            unit=first.get("unit"),
            countries={code: row.get("country") for code, row in by_country.items()},
            observation_count=len(complete),
            truncated=truncated,
            rows=table,
            missing_countries=[n for n in names if n not in resolved],
        )
    except AnansiAPIError as err:
        return from_api_error(err)


async def get_country_profile(
    ctx: AppContext, dataset: str, country: str
) -> dict[str, Any]:
    name = resolve_country(country)
    if not name:
        return not_found(country, COUNTRY_HINT)
    try:
        search = name.split(",")[0].strip() if "," in name else None
        rows = await _fetch_series(
            ctx, dataset, [name], indicator=None, frequency="Annual", search=search
        )
        if not rows:
            return no_data(name)
        by_indicator = {row.get("indicator"): row for row in rows}
        selected = [
            (title, by_indicator[title])
            for title in HEADLINE_INDICATORS
            if title in by_indicator
        ]
        if not selected:
            return no_data(name)
        codes = [row["series_code"] for _, row in selected]
        by_code = await ctx.client.series_data_many(
            dataset, codes, start_date=years_ago(6), end_date=today()
        )
        metrics = []
        for title, row in selected:
            observations = by_code.get(row["series_code"], [])
            actuals = [
                o
                for o in observations
                if o.get("value") is not None and not o.get("is_forecast")
            ]
            change = None
            if len(actuals) >= 2 and actuals[-2]["value"]:
                change = round((actuals[-1]["value"] / actuals[-2]["value"] - 1) * 100, 4)
            latest = actuals[-1] if actuals else None
            metrics.append(
                {
                    "indicator": title,
                    "series_code": row["series_code"],
                    "unit": row.get("unit"),
                    "latest": (
                        {"date": latest["date"], "value": display(latest["value"])}
                        if latest
                        else None
                    ),
                    "change_pct": display_pct(change),
                }
            )
        return ok(
            country=selected[0][1].get("country") or name,
            metrics=metrics,
            missing_indicators=[
                title for title in HEADLINE_INDICATORS if title not in by_indicator
            ],
        )
    except AnansiAPIError as err:
        return from_api_error(err)


async def rank_countries(
    ctx: AppContext,
    dataset: str,
    indicator: str,
    frequency: str = "Annual",
    period: str = "latest",
    limit: int = 20,
) -> dict[str, Any]:
    try:
        name = await resolve_indicator(ctx.client, dataset, indicator)
        if not name:
            return not_found(indicator, INDICATOR_HINT)
        rows = await _fetch_series(
            ctx, dataset, None, indicator=name, frequency=frequency
        )
        if not rows:
            return no_data(f"{name} / {frequency}")
        if str(period).lower() in ("latest", "current", ""):
            start, end = years_ago(3), today()
        else:
            start = f"{int(period)}-01-01"
            end = f"{int(period)}-12-31"
        codes = [row["series_code"] for row in rows]
        by_code = await ctx.client.series_data_many(dataset, codes, start, end, limit=1)
        ranked = []
        for row in rows:
            observations = [
                o for o in by_code.get(row["series_code"], []) if o.get("value") is not None
            ]
            if not observations:
                continue
            point = observations[-1]
            ranked.append(
                {
                    "country": row.get("country"),
                    "country_code": row.get("country_code"),
                    "series_code": row["series_code"],
                    "value": clean(point["value"]),
                    "date": point["date"],
                }
            )
        ranked.sort(key=lambda r: r["value"], reverse=True)
        top = ranked[: max(1, limit)]
        for index, item in enumerate(top, start=1):
            item["rank"] = index
        return ok(
            indicator=name,
            frequency=frequency,
            period=period,
            unit=rows[0].get("unit"),
            country_count=len(ranked),
            rows=top,
        )
    except AnansiAPIError as err:
        return from_api_error(err)


async def compute_series(
    ctx: AppContext,
    dataset: str,
    codes: list[str],
    operation: str,
    start_date: str | None = None,
    end_date: str | None = None,
    window: int = 5,
    max_points: int = 60,
) -> dict[str, Any]:
    data = await get_series_data(ctx, dataset, codes, start_date, end_date)
    if data.get("status") != "ok":
        return data
    observations = {s["series_code"]: s["observations"] for s in data["series"]}
    op = operation.strip().lower()

    if op in ("growth", "yoy", "pct_change"):
        if len(observations) != 1:
            return {"status": "invalid_operation", "hint": "growth takes exactly one series_code."}
        code = next(iter(observations))
        rows, truncated = _cap(_clean_points(growth(observations[code])), max_points)
        return ok(operation="growth", series_code=code, truncated=truncated, result=rows)
    if op in ("cagr", "compound_growth"):
        if len(observations) != 1:
            return {"status": "invalid_operation", "hint": "cagr takes exactly one series_code."}
        code = next(iter(observations))
        result = cagr(observations[code])
        if result:
            result["cagr_pct"] = clean(result["cagr_pct"])
        payload = ok(operation="cagr", series_code=code, result=result)
        if result is None:
            payload["note"] = (
                "CAGR is undefined for this series because it contains "
                "non-positive values. Use operation='growth' instead."
            )
        return payload
    if op in ("rebase", "index"):
        truncated = False
        result = {}
        for code, obs in observations.items():
            rows, trimmed = _cap(_clean_points(rebase(obs)), max_points)
            result[code] = rows
            truncated = truncated or trimmed
        return ok(operation="rebase", truncated=truncated, result=result)
    if op == "moving_average":
        truncated = False
        result = {}
        for code, obs in observations.items():
            rows, trimmed = _cap(_clean_points(moving_average(obs, window)), max_points)
            result[code] = rows
            truncated = truncated or trimmed
        return ok(
            operation="moving_average", window=window, truncated=truncated, result=result
        )
    if op == "zscore":
        truncated = False
        result = {}
        for code, obs in observations.items():
            rows, trimmed = _cap(_clean_points(zscore(obs)), max_points)
            result[code] = rows
            truncated = truncated or trimmed
        return ok(operation="zscore", truncated=truncated, result=result)
    if op == "spread":
        if len(observations) != 2:
            return {"status": "invalid_operation", "hint": "spread takes exactly two series_codes."}
        (a, obs_a), (b, obs_b) = list(observations.items())
        rows, truncated = _cap(_clean_points(spread(obs_a, obs_b)), max_points)
        return ok(operation="spread", a=a, b=b, truncated=truncated, result=rows)
    if op == "correlation":
        if len(observations) != 2:
            return {"status": "invalid_operation", "hint": "correlation takes exactly two series_codes."}
        (a, obs_a), (b, obs_b) = list(observations.items())
        result = correlation(obs_a, obs_b)
        if result:
            result["correlation"] = clean(result["correlation"])
        return ok(operation="correlation", a=a, b=b, result=result)
    return {
        "status": "invalid_operation",
        "operation": operation,
        "supported": [
            "growth",
            "cagr",
            "rebase",
            "moving_average",
            "zscore",
            "spread",
            "correlation",
        ],
    }


async def check_coverage(
    ctx: AppContext, dataset: str, series_code: str
) -> dict[str, Any]:
    try:
        meta = await ctx.client.series(dataset, series_code.upper())
        if not meta:
            return {"status": "not_found", "input": series_code, "hint": SERIES_HINT}
        stats = meta.get("stats") or {}
        sources = [
            {
                "name": source.get("name"),
                "display_name": source.get("display_name"),
                "is_contributing": source.get("is_contributing"),
                "coverage": source.get("coverage"),
            }
            for source in meta.get("available_sources", [])
        ]
        end = stats.get("end_date")
        return ok(
            series=compact_series(meta),
            description=meta.get("description"),
            unit_metadata=meta.get("unit_metadata"),
            observation_count=stats.get("observation_count"),
            forecast_tail=bool(end and str(end)[:10] > today()),
            sources=sources,
        )
    except AnansiAPIError as err:
        return from_api_error(err)
