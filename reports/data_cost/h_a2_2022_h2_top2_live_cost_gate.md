# H-A2 2022 H2 Top2 Live Cost Gate

## Status
- Mode: `live_metadata_cost_only`
- No new paid data downloaded: `true`
- Gate status: `blocked`
- Cost guard: `$105.0 / $125.0`
- Remaining headroom: `$20.0`

## Live Metadata Estimates
| Month | Rank | Requests | Estimated cost | Errors | Source |
|:--|--:|--:|--:|--:|:--|
| `2022-10` | 1 | 21 | `$10.52248` | 0 | `reports/data_cost/databento_cost_h_a2_2022_10_stress.json` |
| `2022-09` | 2 | 21 | `$10.226392` | 0 | `reports/data_cost/databento_cost_h_a2_2022_09_stress.json` |

## Gate Decision
- Top2 combined estimate: `$20.748872`
- Current headroom: `$20.0`
- Excess over headroom: `$0.748872`
- Download allowed now: `false`

Do not download top2 under the current `$125` guard. The next safe action is either real top-up/scope decision for H-A2, or continuing no-cost work such as H-B2 while H-A2 stress expansion remains cost-blocked.
