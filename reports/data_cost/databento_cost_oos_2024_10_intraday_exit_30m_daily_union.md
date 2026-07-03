# Databento Cost Estimate Report

- **Mode**: `live`
- **Total request count**: 23
- **Planned research windows**: 322
- **Live cost request count**: 23
- **Cost granularity**: `daily_union`
- **Total estimated cost**: `$12.671726`
- **Decision**: `review`
- **Decision reason**: Estimated cost $12.671726 is at or above review threshold $5.0.

## Scenario Summary

| Scenario | Requests | First Start UTC | Last End UTC | Dataset | Schema | Symbol |
|:--|--:|:--|:--|:--|:--|:--|
| `oos_2024_10_intraday_exit_30m_daily_union` | 23 | `2024-10-01T13:30:00+00:00` | `2024-10-31T19:50:00+00:00` | `OPRA.PILLAR` | `cbbo-1m` | `SPY.OPT` |

## Decision Rule

- Start with `one_day_sample --live` only.
- Move to `one_month_pilot --live` only if the one-day estimate is acceptable.
- Do not run OOS/full live estimates until the smaller estimates are reviewed.
- Do not download data from Databento until cost, coverage, and schema are explicitly accepted.
