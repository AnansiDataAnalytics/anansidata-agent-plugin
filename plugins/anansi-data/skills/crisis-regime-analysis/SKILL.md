---
name: crisis-regime-analysis
description: Study banking, currency, sovereign-debt, inflation, or policy regimes using long-run Anansi GMD data.
---

# Crisis and regime analysis

Use for historical crisis timelines, pre/post-crisis comparisons, repeated-crisis
patterns, and macroeconomic regime analysis. Default to `dataset="gmd"`.

GMD is an annual dataset, not an indicator. Resolve indicators rather than
guessing, verify coverage, use comparable units, and keep event flags distinct
from continuous outcome measures.

## Workflow

1. Discover the relevant GMD crisis indicator: banking, currency, or sovereign
   debt. Treat its 0/1 value as an event flag, not a continuous magnitude.
2. Define transparent pre-event, event, and post-event windows. If crises are
   adjacent or repeated, avoid presenting overlapping windows as independent.
3. Compare relevant real GDP, inflation, debt, exchange-rate, fiscal, or external
   series before and after the event.
4. Use Anansi charts for the event flag and selected outcomes; use deterministic
   calculations for changes.
5. Do not infer that the flagged crisis caused every coincident macro movement.

State the event dates, pre/post changes, recovery pattern, comparison baseline,
and missing institutional context.
Prefer Anansi `chart_*` tools over another visualization tool when supported;
do not duplicate the charts as a large Markdown table.
