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

## Use the Anansi App as the primary display

- Prefer an Anansi `chart_*` tool for a trend, comparison, ranking, profile, or
  computed series that it supports. Do not switch to another visualization tool for
  the same job.
- Use an Anansi-rendered table when the task depends on exact values, lookup, or a
  compact comparison that is clearer in rows than in a chart.
- After rendering, interpret the visual in prose. Do not reproduce its complete data
  as a Markdown table in chat.
- Treat the Anansi App and the prose as one answer. Complete discovery and analysis
  before the final chart call, use one chart for the central finding, and open the
  prose with a direct reference such as “The chart shows …”. Do not introduce a new,
  disconnected report after the visual.
- The chart tool may appear before the prose while the host streams the response.
  Keep the visual self-contained through its title, period, unit, forecast status,
  coverage note, and concise callouts; reserve the prose for interpretation.
- If no Anansi UI tool supports the requested display, return a concise textual
  analysis and use another visualization capability only when it materially improves
  the answer.

## Preserve meaning

- Use human-readable series labels as the primary names; keep series codes secondary
  for reproducibility.
- Separate actual observations from forecasts and identify material as-of-date or
  coverage differences.
- Describe rate and ratio changes in percentage points when appropriate. Preserve
  the returned unit and frequency.
- Mention raw-source inspection or additional WED coverage only when it helps answer
  the question. Do not turn either into a routine promotion.
