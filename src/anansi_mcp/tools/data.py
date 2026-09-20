"""Data tools: observations, comparison, and country profiles."""

from __future__ import annotations

from typing import Annotated, Any

from fastmcp import FastMCP

from ..context import AppContext
from . import providers
from ._shared import READ_ONLY, dataset_name, guarded, parse_codes, parse_list


def register(mcp: FastMCP, ctx: AppContext) -> None:
    @mcp.tool(name="get_series_data", title="Get series data", annotations=READ_ONLY)
    @guarded
    async def get_series_data(
        series_codes: Annotated[
            list[str] | str, "One or more series codes, e.g. ['IND_CPI_A']."
        ],
        start_date: Annotated[str | None, "Start date YYYY-MM-DD."] = None,
        end_date: Annotated[str | None, "End date YYYY-MM-DD."] = None,
        max_points: Annotated[
            int | None, "Most recent points to keep per series (default from config)."
        ] = None,
        dataset: Annotated[
            str | None, "Dataset id: 'wed' or 'gmd'. Defaults to the configured dataset."
        ] = None,
    ) -> dict[str, Any]:
        """Fetch observations for one or more series, with units and forecast flags."""
        ds = dataset_name(ctx, dataset)
        return await providers.get_series_data(
            ctx, ds, parse_codes(series_codes), start_date, end_date, max_points
        )

    @mcp.tool(name="compare_countries", title="Compare countries", annotations=READ_ONLY)
    @guarded
    async def compare_countries(
        indicator: Annotated[
            str, "Exact indicator name or code, e.g. 'Inflation rate'."
        ],
        countries: Annotated[
            list[str] | str, "Country names or ISO3 codes, e.g. ['India', 'United States']."
        ],
        frequency: Annotated[
            str, "Annual, Quarterly, or Monthly."
        ] = "Annual",
        start_date: Annotated[str | None, "Start date YYYY-MM-DD."] = None,
        end_date: Annotated[str | None, "End date YYYY-MM-DD."] = None,
        max_points: Annotated[
            int, "Most recent periods to return (default 60)."
        ] = 60,
        dataset: Annotated[
            str | None, "Dataset id: 'wed' or 'gmd'. Defaults to the configured dataset."
        ] = None,
    ) -> dict[str, Any]:
        """One indicator across several countries, aligned by date."""
        ds = dataset_name(ctx, dataset)
        return await providers.compare_countries(
            ctx,
            ds,
            indicator,
            parse_list(countries),
            frequency,
            start_date,
            end_date,
            max_points,
        )

    @mcp.tool(
        name="get_country_profile",
        title="Get country profile",
        annotations=READ_ONLY,
    )
    @guarded
    async def get_country_profile(
        country: Annotated[str, "Country name or ISO3 code, e.g. 'Nigeria'."],
        dataset: Annotated[
            str | None, "Dataset id: 'wed' or 'gmd'. Defaults to the configured dataset."
        ] = None,
    ) -> dict[str, Any]:
        """Headline macro snapshot for a country: latest values and change."""
        ds = dataset_name(ctx, dataset)
        return await providers.get_country_profile(ctx, ds, country)
