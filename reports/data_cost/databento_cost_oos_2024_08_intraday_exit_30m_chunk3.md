# Databento Cost Estimate Report

- **Mode**: `live`
- **Total request count**: 70
- **Total estimated cost**: `$2.178158`
- **Decision**: `pass`
- **Decision reason**: Estimated cost $2.178158 is below review threshold $5.0.

## Scenario Summary

| Scenario | Requests | First Start UTC | Last End UTC | Dataset | Schema | Symbol |
|:--|--:|:--|:--|:--|:--|:--|
| `oos_2024_08_intraday_exit_30m_chunk3` | 70 | `2024-08-12T13:30:00+00:00` | `2024-08-16T19:50:00+00:00` | `OPRA.PILLAR` | `cbbo-1m` | `SPY.OPT` |

## Decision Rule

- Start with `one_day_sample --live` only.
- Move to `one_month_pilot --live` only if the one-day estimate is acceptable.
- Do not run OOS/full live estimates until the smaller estimates are reviewed.
- Do not download data from Databento until cost, coverage, and schema are explicitly accepted.
