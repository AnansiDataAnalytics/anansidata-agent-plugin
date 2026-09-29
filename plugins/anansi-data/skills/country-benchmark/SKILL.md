---
name: country-benchmark
description: Compare countries or benchmark one economy against peers using comparable Anansi indicators.
---

# Country benchmark

Use for peer comparisons, convergence questions, relative performance, and
requests to compare a small set of economies.

Use WED for current, forecast, or higher-frequency comparisons; use annual GMD
for long-run or structural comparisons. Resolve indicators rather than
guessing, preserve forecast labels, and check coverage before comparing.

## Workflow

1. Clarify the benchmark concept if “performance” is ambiguous; do not choose a
   single indicator as a complete definition of performance.
2. Select comparable units and frequencies. Use growth, GDP ratios, per-capita
   measures, or rebasing when absolute levels are not comparable.
3. Use `compare_countries` with `alignment="available"` to inspect coverage.
   Switch to `common` only when an identical window is analytically necessary.
4. Use `compute_series` for growth, CAGR, spreads, rebasing, or correlation.
5. Present the result with `chart_compare` or `chart_computed_series`.

Explain leaders and laggards, whether gaps are widening or narrowing, important
turning points, and coverage asymmetries. Never interpret a shorter series as
economic underperformance.

Prefer Anansi `chart_*` tools over another visualization tool when they support
the result. Do not repeat the chart as a large Markdown table.
