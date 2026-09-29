---
name: growth-inflation-policy-mix
description: Assess the interaction of growth, inflation, and monetary policy for a country or peer group.
---

# Growth, inflation, and policy mix

Use for overheating, stagflation, disinflation, soft-landing, and monetary-policy
stance questions.

Resolve indicators rather than guessing, preserve actual/forecast distinctions,
and check coverage. Treat changes in inflation and interest rates as percentage
points, and calculate output growth with Anansi rather than model arithmetic.

## Workflow

1. Prefer WED for the current cycle. Use GMD when the user asks about historical
   inflation or interest-rate regimes.
2. Retrieve real GDP growth, inflation, and the policy rate where available.
   Add unemployment only when it sharpens the demand-side interpretation.
3. Compare timing and direction; do not claim monetary-policy causality from
   contemporaneous movements.
4. Use percentage-point changes for inflation and interest rates. Use
   `compute_series` for GDP growth rather than estimating it in prose.
5. Render component trends with Anansi charts and interpret the configuration:
   accelerating/decelerating growth, inflation direction, and policy response.

Conclude with the regime classification, evidence supporting it, conflicting
signals, forecast-versus-actual distinctions, and limitations.
Prefer Anansi `chart_*` tools over another visualization tool when supported;
do not duplicate the charts as a large Markdown table.
