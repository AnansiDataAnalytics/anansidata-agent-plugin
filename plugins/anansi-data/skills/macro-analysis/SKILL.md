---
name: macro-analysis
description: Use when answering macroeconomic questions with Anansi data — choosing the right dataset and indicator, interpreting units, and handling forecasts.
---

# Macro analysis with Anansi

## Datasets

Pick one per request with the `dataset` argument on any tool. Default is `wed`.

| Dataset | `dataset` | Coverage | Frequency |
|---|---|---|---|
| World Economic Database | `wed` (default) | Broad economic coverage, many indicators | Annual, quarterly, monthly |
| Global Macro Database (GMD) | `gmd` | Harmonized long-run macro panel, ~240 countries, ~25 indicators | Annual only |

- "GMD" / "Global Macro Database" → set `dataset="gmd"`. GMD is a **dataset, not an indicator** — never pass "GMD" as an indicator name.
- "WED" / "World Economic Database" → `dataset="wed"`.
- GMD is annual-only: do not pass `frequency`, and expect `list_frequencies` to return only Annual.
- Unsure what a dataset contains? Call `list_datasets`, `list_indicators`, or `search_series` with that `dataset`.

## Vocabulary

| User says | Indicator |
|---|---|
| inflation | Inflation rate |
| inflation index, CPI | Consumer price index |
| GDP, economic output | Nominal GDP (current prices) or Real GDP (constant prices) |
| GDP per person | Real GDP per capita |
| growth | derive with `compute_series(operation="growth")` |
| unemployment | Unemployment rate |
| government debt | General government debt (% of GDP) |
| deficit | General government deficit (% of GDP) |
| current account | Current account (% of GDP) |
| interest rate | Central bank policy rate |
| population | Population |
| exchange rate | US dollar exchange rate |

## Workflow

1. Call `list_datasets` if unsure which dataset the account can access; pass `dataset` to the relevant tool.
2. Use `compare_countries` or `get_country_profile` for common asks.
3. If a name is not found, call `list_indicators` or `search_series` (for that dataset). Never invent a series code.
4. State the dataset, frequency, and unit in every answer.
5. Use `compute_series` for growth, CAGR, spread, and correlation instead of calculating from raw numbers.
