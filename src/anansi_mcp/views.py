"""Prefab view builders for the chart tools.

The Apps/Prefab extra is optional. When it is not installed these helpers are
unused and the chart tools fall back to structured data plus a text summary.
"""

from __future__ import annotations

from typing import Any

try:  # optional extra: fastmcp[apps]
    from prefab_ui.app import PrefabApp
    from prefab_ui.components import Column, DataTable, DataTableColumn, Heading, Text
    from prefab_ui.components.charts import BarChart, ChartSeries, LineChart

    PREFAB_AVAILABLE = True
except (ImportError, ModuleNotFoundError):  # pragma: no cover - without the extra
    PREFAB_AVAILABLE = False


def timeseries_view(
    title: str, series: list[dict[str, Any]], chart_type: str = "line"
) -> Any:
    """Line or bar chart of one or more series, merged on date."""
    merged: dict[str, dict[str, float]] = {}
    for item in series:
        for observation in item["observations"]:
            if observation.get("value") is None:
                continue
            merged.setdefault(observation["date"], {})[item["key"]] = observation["value"]
    data = [{"date": date, **values} for date, values in sorted(merged.items())]
    components = [
        ChartSeries(data_key=item["key"], label=item["label"]) for item in series
    ]
    chart_cls = BarChart if chart_type == "bar" else LineChart
    with Column(gap=3, css_class="p-4") as view:
        Heading(title)
        chart_cls(
            data=data,
            series=components,
            x_axis="date",
            show_legend=len(series) > 1,
            show_tooltip=True,
        )
    return PrefabApp(view=view)


def table_view(
    title: str,
    columns: list[tuple[str, str]],
    rows: list[dict[str, Any]],
    subtitle: str | None = None,
) -> Any:
    """A simple sortable table."""
    with Column(gap=3, css_class="p-4") as view:
        Heading(title)
        if subtitle:
            Text(subtitle)
        DataTable(
            columns=[
                DataTableColumn(key=key, header=header, sortable=True)
                for key, header in columns
            ],
            rows=rows,
            search=True,
        )
    return PrefabApp(view=view)
