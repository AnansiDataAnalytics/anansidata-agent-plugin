import asyncio

from fastmcp import Client

from anansi_mcp.server import build_server

EXPECTED = {
    "list_datasets",
    "list_countries",
    "list_indicators",
    "list_frequencies",
    "list_sources",
    "search_series",
    "get_series",
    "get_series_data",
    "compare_countries",
    "get_country_profile",
    "rank_countries",
    "compute_series",
    "check_coverage",
    "chart_series",
    "chart_compare",
    "chart_country_profile",
}


def test_all_tools_register():
    mcp = build_server()

    async def names():
        async with Client(mcp) as client:
            return {tool.name for tool in await client.list_tools()}

    assert EXPECTED <= asyncio.run(names())
