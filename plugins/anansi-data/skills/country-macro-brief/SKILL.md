---
name: country-macro-brief
description: Build an evidence-led macroeconomic brief or outlook for one country using Anansi data.
---

# Country macro brief

Read [analysis and presentation practices](../../references/analysis-presentation.md)
and [dataset selection](../../references/dataset-selection.md) before beginning.

Use this for country snapshots, economic health checks, outlooks, and requests
such as “what is happening in Nigeria's economy?”

Use WED for current, forecast, or higher-frequency analysis; use annual GMD for
long-run, structural, or crisis analysis. Resolve indicators rather than
guessing. Keep units comparable, treat rate and ratio changes as percentage
points, and label forecasts and coverage gaps.

## Workflow

1. Choose WED for a current brief or GMD for a long-run structural profile.
2. Use `get_country_profile` to establish headline indicators. Fetch relevant
   series when the profile needs trend or forecast context.
3. Organize the interpretation around growth, prices, labour, fiscal, external,
   and monetary conditions; omit dimensions without evidence.
4. Distinguish latest actuals from the forecast tail and surface conflicting
   signals rather than forcing a single narrative.
5. Use `chart_country_profile`, then `chart_series` for the one or two trends
   that explain the conclusion. Do not recreate the dashboard elsewhere.

Finish with the central assessment, 3–5 supporting findings, principal risks,
and material data caveats. Do not issue investment advice or claim causal
drivers that the data alone cannot establish.
