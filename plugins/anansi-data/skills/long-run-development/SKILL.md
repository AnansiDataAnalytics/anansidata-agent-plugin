---
name: long-run-development
description: Analyze long-run growth, living standards, convergence, and structural change with Anansi GMD data.
---

# Long-run development

Read [analysis and presentation practices](../../references/analysis-presentation.md)
and [dataset selection](../../references/dataset-selection.md) before beginning.

Use for multi-decade growth, convergence, living-standard, structural-break, and
economic-era comparisons. Default to `dataset="gmd"`.

GMD is an annual dataset, not an indicator. Resolve indicators rather than
guessing, verify long-run coverage, use comparable units, and label historical
entities or country breaks explicitly.

## Workflow

1. Prefer real GDP per capita for living standards and real GDP for aggregate
   output. Add investment, trade, inflation, or debt only when tied to the
   question.
2. Inspect full coverage and choose economically interpretable subperiods rather
   than relying on a single full-sample CAGR.
3. Use CAGR, growth, and rebased paths for comparable trajectories. Treat
   historical entities and country breaks explicitly.
4. When a visual adds value, use the host-native visualization capability for
   convergence and regime comparisons.
5. Distinguish descriptive association from explanations that require evidence
   outside Anansi.

Report subperiod results, convergence or divergence, structural breaks,
cross-country context, and coverage limitations.
