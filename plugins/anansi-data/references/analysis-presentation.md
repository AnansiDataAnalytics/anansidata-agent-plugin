# Analysis and presentation practices

Apply these practices whenever an Anansi skill retrieves or presents data.

## Lead with analysis

- Answer the economic question first. Treat retrieval as supporting work, not the result.
- State the main finding, quantify it, then explain the important turning points,
  comparisons, or outliers.
- Keep follow-up analysis and suggested questions on the metric or relationship the
  user selected. Add another variable only when the user asks or it is necessary to
  answer the original question; explain that dependency when it occurs.
- Surface material limitations—forecast status, incomparable units, uneven dates,
  sparse coverage, or methodological breaks—without adding generic disclaimers.

## Use the host's native visualization capability

- Use Anansi tools for retrieval, comparison, ranking, coverage checks, and
  deterministic calculations. They return the analysis-ready data; they do not
  render charts.
- When a visual materially improves the answer and the host has a native
  visualization capability, use it. In ChatGPT or Codex, prefer Visualize when it is
  available. In Claude, prefer its native custom visual or chart capability.
- Treat an explicit request to chart, plot, show, or visualize the result as sufficient
  reason to use the native capability when it is available. Do not answer such a
  request with only a Markdown table.
- Choose the visual from the analytical question: a line chart for change over time,
  a bar or dot plot for a country comparison or ranking, and small multiples when
  unlike units or scales would make a combined axis misleading.
- Build the visual only after resolving indicators, aligning dates, checking units,
  and identifying actual and forecast observations. Pass human-readable labels and
  the returned values to the host visualization; never ask it to retrieve or invent
  Anansi data.
- Keep actuals and forecasts visually distinct, label axes and units, show the data
  period, and disclose material coverage differences. Do not combine incompatible
  units on one axis merely to fit everything into one chart.
- Treat the visual and prose as one answer. Lead with the economic conclusion,
  include one decision-relevant visual by default, and interpret it without repeating
  the full dataset as a Markdown table.
- If the native visualization capability is unavailable or a visual would add little,
  answer in prose. Use a compact Markdown table only when exact lookup values or a
  small ranking are genuinely clearer in rows.

## Preserve meaning

- Use human-readable series labels as the primary names; keep series codes secondary
  for reproducibility.
- Separate actual observations from forecasts and identify material as-of-date or
  coverage differences.
- Describe rate and ratio changes in percentage points when appropriate. Preserve
  the returned unit and frequency.
- Mention raw-source inspection or additional WED coverage only when it helps answer
  the question. Do not turn either into a routine promotion.
