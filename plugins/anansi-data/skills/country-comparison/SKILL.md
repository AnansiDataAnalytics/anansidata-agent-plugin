---
name: country-comparison
description: Use when comparing a metric across countries or ranking countries with Anansi data.
---

# Country comparison

- Every tool takes an optional `dataset` (`"wed"` default, or `"gmd"` = Global Macro Database, annual-only). Pass it through when the user names a database.
- Use `compare_countries` for a few countries. Pass names; the tools resolve ISO3 internally.
- `rank_countries` with the default `period="latest"` returns the most recent actual value per country. Passing a year (e.g. `"2023"`) selects that year.
- Use `get_country_profile` for a single country overview.
- Report the unit, frequency, and date of each value.
- A country missing from the result has no data for that indicator and frequency. Say so rather than omitting it silently.
