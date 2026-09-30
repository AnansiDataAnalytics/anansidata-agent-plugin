---
name: macro-ranking-screening
description: Rank or screen countries by macroeconomic indicators and interpret the distribution, outliers, and comparability.
---

# Macro ranking and screening

Use for country rankings, top/bottom lists, regional screens, and identifying
outliers. A leaderboard is evidence to interpret, not the final analysis.

Use WED for current or forecast screens and GMD for long-run structural screens.
Resolve indicators rather than guessing, keep units comparable, and inspect
coverage before interpreting the ranking.

## Workflow

1. Choose a comparable measure: ratios, rates, growth, or per-capita indicators
   are generally more meaningful than raw LCU levels across countries.
2. Use `rank_countries` or `chart_rank_countries`. Keep
   `include_forecasts=false` unless the user explicitly asks for an outlook.
3. Verify dates. “Latest” may differ across countries, so disclose material
   as-of differences and use a fixed period when strict comparability matters.
4. Exclude or clearly label aggregates and historical entities when the user
   asked for countries.
5. Prefer the Anansi ranking UI over a Markdown table.

Interpret clusters, outliers, regional patterns, and coverage bias. State the
unit, period, actual/forecast policy, population of ranked economies, and why
the indicator is or is not a sufficient screen.
Keep follow-ups on the ranked metric unless the user explicitly changes scope.
