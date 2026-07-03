# Databento Cost Estimate Report

- **Mode**: `live`
- **Total request count**: 21
- **Planned research windows**: 294
- **Live cost request count**: 21
- **Cost granularity**: `daily_union`
- **Total estimated cost**: `$10.52248`
- **Decision**: `pass`
- **Decision reason**: Estimated cost $10.52248 is below review threshold $20.0.

## Scenario Summary

| Scenario | Requests | First Start UTC | Last End UTC | Dataset | Schema | Symbol |
|:--|--:|:--|:--|:--|:--|:--|
| `h_a2_2022_10_stress` | 21 | `2022-10-03T13:30:00+00:00` | `2022-10-31T19:50:00+00:00` | `OPRA.PILLAR` | `cbbo-1m` | `SPY.OPT` |

## Decision Rule

- Start with `one_day_sample --live` only.
- Move to `one_month_pilot --live` only if the one-day estimate is acceptable.
- Do not run OOS/full live estimates until the smaller estimates are reviewed.
- Do not download data from Databento until cost, coverage, and schema are explicitly accepted.
