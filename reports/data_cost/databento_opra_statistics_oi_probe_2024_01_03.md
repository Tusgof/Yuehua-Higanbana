# Databento Cost Estimate Report

- **Mode**: `live`
- **Total request count**: 1
- **Planned research windows**: 3
- **Live cost request count**: 1
- **Cost granularity**: `daily_union`
- **Total estimated cost**: `$0.0`
- **Decision**: `pass`
- **Decision reason**: Estimated cost $0.0 is below review threshold $1.0.

## Scenario Summary

| Scenario | Requests | First Start UTC | Last End UTC | Dataset | Schema | Symbol |
|:--|--:|:--|:--|:--|:--|:--|
| `opra_statistics_oi_probe_2024_01_03` | 1 | `2024-01-03T14:30:00+00:00` | `2024-01-03T20:50:00+00:00` | `OPRA.PILLAR` | `statistics` | `SPY.OPT` |

## Decision Rule

- Start with `one_day_sample --live` only.
- Move to `one_month_pilot --live` only if the one-day estimate is acceptable.
- Do not run OOS/full live estimates until the smaller estimates are reviewed.
- Do not download data from Databento until cost, coverage, and schema are explicitly accepted.
