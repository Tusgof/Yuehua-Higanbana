# Databento Cost Estimate Report

- **Mode**: `live`
- **Total request count**: 14
- **Total estimated cost**: `$0.312721`
- **Decision**: `pass`
- **Decision reason**: Estimated cost $0.312721 is below review threshold $5.0.

## Scenario Summary

| Scenario | Requests | First Start UTC | Last End UTC | Dataset | Schema | Symbol |
|:--|--:|:--|:--|:--|:--|:--|
| `insample_2023_09` | 14 | `2023-09-25T13:30:00+00:00` | `2023-09-25T19:50:00+00:00` | `OPRA.PILLAR` | `cbbo-1m` | `SPY.OPT` |

## Decision Rule

- Start with `one_day_sample --live` only.
- Move to `one_month_pilot --live` only if the one-day estimate is acceptable.
- Do not run OOS/full live estimates until the smaller estimates are reviewed.
- Do not download data from Databento until cost, coverage, and schema are explicitly accepted.
