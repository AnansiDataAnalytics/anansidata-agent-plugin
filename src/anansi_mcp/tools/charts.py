"""Chart tools.

Universal posture: the data and a text summary are always returned. When the
Apps/Prefab extra is installed, an interactive view is attached too.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastmcp import FastMCP
from fastmcp.tools import ToolResult

from .. import views
from ..context import AppContext
from . import providers
from ._shared import READ_ONLY, dataset_name, guarded, parse_list


def _range_of(observations: list[dict[str, Any]]) -> tuple[str | None, str | None]:
    dated = [o for o in observations if o.get("value") is not None]
    if not dated:
        return None, None
    return dated[0]["date"], dated[-1]["date"]


def register(mcp: FastMCP, ctx: AppContext) -> None:
    @mcp.tool(
        name="chart_series",
        title="Chart a series",
        annotations=READ_ONLY,
        app=views.PREFAB_AVAILABLE,
    )
    @guarded
    async def chart_series(
        series_code: Annotated[str, "Series code, e.g. 'IND_CPI_A'."],
        start_date: Annotated[str | None, "Start date YYYY-MM-DD."] = None,
        end_date: Annotated[str | None, "End date YYYY-MM-DD."] = None,
        chart_type: Annotated[str, "'line' (default) or 'bar'."] = "line",
        dataset: Annotated[
            str | None, "Dataset id: 'wed' or 'gmd'. Defaults to the configured dataset."
        ] = None,
    ) -> Any:
        """Chart one series over time."""
        ds = dataset_name(ctx, dataset)
        data = await providers.get_series_data(
            ctx, ds, [series_code.upper()], start_date, end_date
        )
        if data.get("status") != "ok" or not data.get("series"):
            return data
        item = data["series"][0]
        start, end = _range_of(item["observations"])
        summary = (
            f"{item.get('name') or item['series_code']} "
            f"({item.get('frequency')}, {item.get('unit')}): "
            f"{item['observation_count']} points, {start} to {end}."
        )
        if not views.PREFAB_AVAILABLE:
            return {**data, "summary": summary}
        view = views.timeseries_view(
            item.get("name") or item["series_code"],
            [
                {
                    "key": item["series_code"],
                    "label": item.get("name") or item["series_code"],
                    "observations": item["observations"],
                }
            ],
            chart_type,
        )
        return ToolResult(content=summary, structured_content=view)

    @mcp.tool(
        name="chart_compare",
        title="Chart country comparison",
        annotations=READ_ONLY,
        app=views.PREFAB_AVAILABLE,
    )
    @guarded
    async def chart_compare(
        indicator: Annotated[str, "Exact indicator name or code."],
        countries: Annotated[list[str] | str, "Country names or ISO3 codes."],
        frequency: Annotated[str, "Annual, Quarterly, or Monthly."] = "Annual",
        start_date: Annotated[str | None, "Start date YYYY-MM-DD."] = None,
        end_date: Annotated[str | None, "End date YYYY-MM-DD."] = None,
        chart_type: Annotated[str, "'line' (default) or 'bar'."] = "line",
        dataset: Annotated[
            str | None, "Dataset id: 'wed' or 'gmd'. Defaults to the configured dataset."
        ] = None,
    ) -> Any:
        """Chart one indicator across several countries."""
        ds = dataset_name(ctx, dataset)
        country_list = parse_list(countries)
        data = await providers.compare_countries(
            ctx, ds, indicator, country_list, frequency, start_date, end_date
        )
        if data.get("status") != "ok":
            return data
        rows = data["rows"]
        chart_series = []
        for code, name in (data.get("countries") or {}).items():
            observations = [
                {"date": row["date"], "value": row[code]}
                for row in rows
                if code in row
            ]
            chart_series.append({"key": code, "label": name, "observations": observations})
        start = rows[0]["date"] if rows else None
        end = rows[-1]["date"] if rows else None
        summary = (
            f"{data['indicator']} ({frequency}, {data.get('unit')}) across "
            f"{len(chart_series)} countries, {start} to {end}."
        )
        if not views.PREFAB_AVAILABLE:
            return {**data, "summary": summary}
        view = views.timeseries_view(
            f"{data['indicator']} — comparison", chart_series, chart_type
        )
        return ToolResult(content=summary, structured_content=view)

    @mcp.tool(
        name="chart_country_profile",
        title="Chart country profile",
        annotations=READ_ONLY,
        app=views.PREFAB_AVAILABLE,
    )
    @guarded
    async def chart_country_profile(
        country: Annotated[str, "Country name or ISO3 code."],
        dataset: Annotated[
            str | None, "Dataset id: 'wed' or 'gmd'. Defaults to the configured dataset."
        ] = None,
    ) -> Any:
        """Dashboard of a country's headline macro indicators."""
        ds = dataset_name(ctx, dataset)
        data = await providers.get_country_profile(ctx, ds, country)
        if data.get("status") != "ok":
            return data
        rows = []
        for metric in data["metrics"]:
            latest = metric.get("latest") or {}
            rows.append(
                {
                    "indicator": metric["indicator"],
                    "latest": latest.get("value"),
                    "unit": metric.get("unit"),
                    "as_of": latest.get("date"),
                    "change_pct": metric.get("change_pct"),
                }
            )
        summary = (
            f"{data.get('country')} — {len(rows)} headline indicators. "
            + "; ".join(
                f"{r['indicator']}: {r['latest']} {r['unit'] or ''}".strip()
                for r in rows[:5]
            )
            + "."
        )
        if not views.PREFAB_AVAILABLE:
            return {**data, "summary": summary}
        view = views.table_view(
            f"{data.get('country')} — macro profile",
            [
                ("indicator", "Indicator"),
                ("latest", "Latest"),
                ("unit", "Unit"),
                ("as_of", "As of"),
                ("change_pct", "Change %"),
            ],
            rows,
            subtitle="Latest actual value and change vs the previous period.",
        )
        return ToolResult(content=summary, structured_content=view)
