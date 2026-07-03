# Databento Cost Estimate Report

- **Mode**: `dry_run`
- **Total request count**: 294
- **Total estimated cost**: not available in dry-run mode
- **Warning**: This is a request plan only. Use --live with DATABENTO_API_KEY to call Databento metadata.get_cost. Parent symbol SPY.OPT is an upper-bound request.
- **Decision**: `review`
- **Decision reason**: Dry-run has no dollar estimate. Run one_day_sample --live before any download.

## Scenario Summary

| Scenario | Requests | First Start UTC | Last End UTC | Dataset | Schema | Symbol |
|:--|--:|:--|:--|:--|:--|:--|
| `oos_2024_12_intraday_exit_30m_daily_union` | 294 | `2024-12-02T14:30:00+00:00` | `2024-12-31T20:50:00+00:00` | `OPRA.PILLAR` | `cbbo-1m` | `SPY.OPT` |

## Decision Rule

- Start with `one_day_sample --live` only.
- Move to `one_month_pilot --live` only if the one-day estimate is acceptable.
- Do not run OOS/full live estimates until the smaller estimates are reviewed.
- Do not download data from Databento until cost, coverage, and schema are explicitly accepted.
