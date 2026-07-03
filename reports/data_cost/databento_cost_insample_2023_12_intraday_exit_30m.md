# Databento Cost Estimate Report

- **Mode**: `live`
- **Total request count**: 280
- **Total estimated cost**: `$6.601407`
- **Decision**: `review`
- **Decision reason**: Estimated cost $6.601407 is at or above review threshold $5.0.

## Scenario Summary

| Scenario | Requests | First Start UTC | Last End UTC | Dataset | Schema | Symbol |
|:--|--:|:--|:--|:--|:--|:--|
| `insample_2023_12` | 280 | `2023-12-01T14:30:00+00:00` | `2023-12-29T20:50:00+00:00` | `OPRA.PILLAR` | `cbbo-1m` | `SPY.OPT` |

## Decision Rule

- Start with `one_day_sample --live` only.
- Move to `one_month_pilot --live` only if the one-day estimate is acceptable.
- Do not run OOS/full live estimates until the smaller estimates are reviewed.
- Do not download data from Databento until cost, coverage, and schema are explicitly accepted.
