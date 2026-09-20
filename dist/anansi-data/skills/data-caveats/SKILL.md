---
name: data-caveats
description: Caveats when using Anansi macroeconomic data — forecasts, harmonization, coverage, and units.
---

# Data caveats

- Values include forecasts. Each observation carries `is_forecast`. Never present a forecast as an actual.
- Series are harmonized across sources. Per-source values are not exposed; use the source metadata for provenance.
- Coverage differs by country and indicator. Check with `check_coverage` or `search_series` before promising a range.
- Units vary: percent, percent of GDP, million LCU, USD, index (2015=100), per capita. Never compare values with different units without normalizing.
- Aggregates such as World or regions are not countries.
