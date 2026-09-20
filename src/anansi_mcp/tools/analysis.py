"""Analysis tools: ranking, derived metrics, and coverage checks."""

from __future__ import annotations

from typing import Annotated, Any

from fastmcp import FastMCP

from ..context import AppContext
from . import providers
from ._shared import READ_ONLY, dataset_name, guarded, parse_codes


def register(mcp: FastMCP, ctx: AppContext) -> None:
    @mcp.tool(name="rank_countries", title="Rank countries", annotations=READ_ONLY)
    @guarded
    async def rank_countries(
        indicator: Annotated[str, "Exact indicator name or code."],
        frequency: Annotated[str, "Annual, Quarterly, or Monthly."] = "Annual",
        period: Annotated[
            str, "A year (e.g. '2023') or 'latest' (default)."
        ] = "latest",
        limit: Annotated[int, "How many countries to return."] = 20,
        dataset: Annotated[
            str | None, "Dataset id: 'wed' or 'gmd'. Defaults to the configured dataset."
        ] = None,
    ) -> dict[str, Any]:
        """Rank countries by an indicator for the latest period or a given year."""
        ds = dataset_name(ctx, dataset)
        return await providers.rank_countries(ctx, ds, indicator, frequency, period, limit)

    @mcp.tool(name="compute_series", title="Compute from series", annotations=READ_ONLY)
    @guarded
    async def compute_series(
        series_codes: Annotated[
            list[str] | str, "Series codes to compute over."
        ],
        operation: Annotated[
            str,
            "growth, cagr, rebase, moving_average, zscore, spread, or correlation.",
        ],
        start_date: Annotated[str | None, "Start date YYYY-MM-DD."] = None,
        end_date: Annotated[str | None, "End date YYYY-MM-DD."] = None,
        window: Annotated[int, "Window for moving_average."] = 5,
        max_points: Annotated[
            int, "Most recent derived points to return (default 60)."
        ] = 60,
        dataset: Annotated[
            str | None, "Dataset id: 'wed' or 'gmd'. Defaults to the configured dataset."
        ] = None,
    ) -> dict[str, Any]:
        """Derived metrics computed in the tool: growth, CAGR, spread, correlation, and more."""
        ds = dataset_name(ctx, dataset)
        return await providers.compute_series(
            ctx, ds, parse_codes(series_codes), operation, start_date, end_date, window, max_points
        )

    @mcp.tool(name="check_coverage", title="Check coverage", annotations=READ_ONLY)
    @guarded
    async def check_coverage(
        series_code: Annotated[str, "Series code, e.g. 'IND_CPI_A'."],
        dataset: Annotated[
            str | None, "Dataset id: 'wed' or 'gmd'. Defaults to the configured dataset."
        ] = None,
    ) -> dict[str, Any]:
        """Coverage, forecast tail, and contributing sources for a series."""
        ds = dataset_name(ctx, dataset)
        return await providers.check_coverage(ctx, ds, series_code)
