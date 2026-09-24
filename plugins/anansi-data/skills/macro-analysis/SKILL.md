---
name: macro-analysis
description: Use when answering macroeconomic questions with Anansi data — choosing the right indicator, interpreting units, and handling forecasts.
---

# Macro analysis with Anansi

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

1. Use `compare_countries` or `get_country_profile` for common asks.
2. If a name is not found, call `list_indicators` or `search_series`. Never invent a series code.
3. State the frequency and the unit in every answer.
4. Use `compute_series` for growth, CAGR, spread, and correlation instead of calculating from raw numbers.
