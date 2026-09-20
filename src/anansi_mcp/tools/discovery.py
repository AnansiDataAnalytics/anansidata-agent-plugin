"""Discovery tools: what exists, and how to find a series."""

from __future__ import annotations

from typing import Annotated, Any

from fastmcp import FastMCP

from ..context import AppContext
from ..errors import COUNTRY_HINT, REGION_HINT, SERIES_HINT, not_found, ok
from ..resolve import (
    iso3_for_country,
    region_country_names,
    region_for_country,
    resolve_countries,
    resolve_indicator,
)
from ._shared import (
    READ_ONLY,
    compact_series,
    dataset_name,
    guarded,
    parse_list,
    partition_countries,
)

Dataset = Annotated[
    str | None, "Dataset id: 'wed' or 'gmd'. Defaults to the configured dataset."
]


def register(mcp: FastMCP, ctx: AppContext) -> None:
    @mcp.tool(name="list_datasets", title="List datasets", annotations=READ_ONLY)
    @guarded
    async def list_datasets() -> dict[str, Any]:
        """List the Anansi datasets available to this account."""
        return ok(**await ctx.client.entitlements())

    @mcp.tool(name="list_countries", title="List countries", annotations=READ_ONLY)
    @guarded
    async def list_countries(dataset: Dataset = None) -> dict[str, Any]:
        """List countries present in the dataset, with ISO3 codes and region."""
        ds = dataset_name(ctx, dataset)
        names = await ctx.client.countries(ds)
        return ok(
            dataset=ds,
            data=[
                {
                    "name": name,
                    "code": iso3_for_country(name),
                    "region": region_for_country(name),
                }
                for name in names
            ],
        )

    @mcp.tool(name="list_indicators", title="List indicators", annotations=READ_ONLY)
    @guarded
    async def list_indicators(dataset: Dataset = None) -> dict[str, Any]:
        """List indicator names present in the dataset."""
        ds = dataset_name(ctx, dataset)
        return ok(dataset=ds, data=await ctx.client.indicators(ds))

    @mcp.tool(name="list_frequencies", title="List frequencies", annotations=READ_ONLY)
    @guarded
    async def list_frequencies(dataset: Dataset = None) -> dict[str, Any]:
        """List the frequencies present in the dataset."""
        ds = dataset_name(ctx, dataset)
        return ok(dataset=ds, data=await ctx.client.frequencies(ds))

    @mcp.tool(name="list_sources", title="List sources", annotations=READ_ONLY)
    @guarded
    async def list_sources(dataset: Dataset = None) -> dict[str, Any]:
        """List the data sources behind the dataset, with coverage statistics."""
        ds = dataset_name(ctx, dataset)
        hierarchy = await ctx.client.sources(ds)
        available = await ctx.client.sources_available(ds)
        return ok(
            dataset=ds,
            sources=hierarchy.get("sources", []),
            coverage=available.get("sources", []),
        )

    @mcp.tool(name="search_series", title="Search series", annotations=READ_ONLY)
    @guarded
    async def search_series(
        query: Annotated[str | None, "Free-text search over names and descriptions."] = None,
        country: Annotated[str | None, "Country name (e.g. 'India')."] = None,
        country_code: Annotated[
            str | None, "Comma-separated ISO3 codes (e.g. 'IND,USA')."
        ] = None,
        indicator: Annotated[
            str | None, "Exact indicator name (e.g. 'Inflation rate')."
        ] = None,
        region: Annotated[
            str | None, "Continent (Africa, Americas, Asia, Europe, Oceania)."
        ] = None,
        frequency: Annotated[str | None, "Annual, Quarterly, or Monthly."] = None,
        start_date: Annotated[str | None, "Only series covering at least this date."] = None,
        end_date: Annotated[str | None, "Only series covering at most this date."] = None,
        limit: Annotated[int, "Max rows (default 25)."] = 25,
        dataset: Dataset = None,
    ) -> dict[str, Any]:
        """Find series by country, indicator, region, frequency, or coverage."""
        ds = dataset_name(ctx, dataset)
        names: list[str] = []
        if country or country_code:
            raw = ([country] if country else []) + parse_list(country_code)
            names, missing = resolve_countries(raw)
            if missing:
                return not_found(", ".join(missing), COUNTRY_HINT)
        if region:
            members = region_country_names(region)
            if not members:
                return not_found(region, REGION_HINT)
            member_set = set(members)
            names = [n for n in names if n in member_set] if names else members
        name = indicator
        if indicator:
            name = await resolve_indicator(ctx.client, ds, indicator)
            if not name:
                return not_found(indicator, "No indicator matched '{value}'. Call list_indicators for valid indicator names.")
        plain, comma = partition_countries(names)
        page_limit = max(1, min(limit, 100))
        if comma:
            # Names with commas can't be filtered server-side; fetch and match
            # locally, then apply the caller's limit.
            all_rows = await ctx.client.search_all_series(
                ds,
                indicator=name,
                frequency=frequency,
                search=query,
                startDate=start_date,
                endDate=end_date,
            )
            wanted = set(names)
            raw = [row for row in all_rows if row.get("country") in wanted][:page_limit]
            total = len(raw)
        else:
            body = await ctx.client.series_search(
                ds,
                country=",".join(plain) if plain else None,
                indicator=name,
                frequency=frequency,
                search=query,
                startDate=start_date,
                endDate=end_date,
                limit=page_limit,
                page=1,
            )
            raw = body.get("data", [])
            total = (body.get("pagination") or {}).get("total")
        rows = [compact_series(row) for row in raw]
        return ok(dataset=ds, count=len(rows), total=total, data=rows)

    @mcp.tool(name="get_series", title="Get series metadata", annotations=READ_ONLY)
    @guarded
    async def get_series(
        series_code: Annotated[str, "Series code, e.g. 'IND_CPI_A'."],
        dataset: Dataset = None,
    ) -> dict[str, Any]:
        """Get metadata and provenance for one series."""
        ds = dataset_name(ctx, dataset)
        meta = await ctx.client.series(ds, series_code.upper())
        if not meta:
            return {"status": "not_found", "input": series_code, "hint": SERIES_HINT}
        return ok(
            **compact_series(meta),
            description=meta.get("description"),
            unit_metadata=meta.get("unit_metadata"),
            sources=[
                {
                    "name": source.get("name"),
                    "display_name": source.get("display_name"),
                    "is_contributing": source.get("is_contributing"),
                    "coverage": source.get("coverage"),
                }
                for source in meta.get("available_sources", [])
            ],
        )
