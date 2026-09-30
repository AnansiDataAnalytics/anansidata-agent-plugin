# WED series codes and units

Authoritative dictionary: https://www.anansidata.com/guides/wed-data-dictionary

## Code grammar

`{ISO3}_{VARIABLE}_{FREQUENCY}`

- `ISO3` is the three-letter country or territory code.
- `VARIABLE` is the WED variable code. Confirm it using Anansi discovery or
  series metadata rather than inferring an unfamiliar code.
- `FREQUENCY` is `A` annual, `Q` quarterly, or `M` monthly.

Example: `ARG_RGDP_USD_A` is **Argentina — Real GDP (in USD) (Annual)**.
The dictionary defines `rGDP_USD` as real GDP in USD with the unit
`2015 = 2015 nominal GDP in million USD`; it is not a generic current-dollar
nominal-GDP measure.

## Common affixes

- Leading `r`: real/inflation-adjusted, such as `rGDP` or `rHPI`.
- `_USD`: denominated in US dollars rather than local currency.
- `_GDP`: expressed as a share of nominal GDP.
- `_pc`: per capita.
- `_TR`: total return, including price change and income.
- `cgov`: central government; `gen_gov`: general government. These perimeters
  are distinct and must not be treated as interchangeable.

## Interpretation safeguards

- Monetary values labeled `Million LCU` or `Million USD` are stored in
  millions. Preserve that source unit in calculations and exports.
- LCU series use each country's own currency and are not directly comparable
  across countries. Prefer ratios, per-capita measures, or an available USD
  variant for cross-country work.
- A real series and a nominal series answer different questions. Do not switch
  between them silently.
- Read the returned metadata for the exact variable name, unit, country, and
  frequency. Codes are identifiers, not suitable primary chart or prose labels.
