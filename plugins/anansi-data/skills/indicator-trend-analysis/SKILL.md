---
name: indicator-trend-analysis
description: Analyze the trajectory, turning points, forecasts, and anomalies of a macroeconomic indicator.
---

# Indicator trend analysis

Read [analysis and presentation practices](../../references/analysis-presentation.md)
and [dataset selection](../../references/dataset-selection.md) before beginning.

Use when the user asks how inflation, GDP, debt, unemployment, an exchange rate,
or another macro indicator has evolved.

Use WED for current, forecast, or higher-frequency trends; use annual GMD for
long-run regimes. Resolve indicators rather than guessing, preserve units and
forecast labels, and check coverage before interpreting a path.

## Workflow

1. Resolve the exact indicator and frequency with discovery tools.
2. Inspect coverage and retrieve enough history to distinguish noise from a
   meaningful turn. Respect the user's requested window.
3. Use deterministic growth, moving average, CAGR, z-score, or rebasing only
   when it answers the stated question.
4. When a visual adds value, use the host-native visualization capability for
   the original or transformed path. Preserve the actual/forecast boundary.
5. Identify peaks, troughs, acceleration, deceleration, persistence, and breaks
   only from returned data.

Report the latest actual, any forecast separately, the main turning points, the
magnitude of change, and the relevant caveats. Do not dump the full time series.
