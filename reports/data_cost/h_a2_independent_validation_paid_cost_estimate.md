# H-A2 Independent Validation Cost Gate

- **Hypothesis**: `H-A2`
- **Experiment**: `h_a2_independent_validation_paid_cost_plan`
- **Batch**: `sample_cost_probe_high_vix_one_day`
- **Mode**: `live_metadata_cost_no_download`
- **Download performed**: `False`
- **Planned requests**: `15`
- **Total estimated cost**: `0.504662`
- **Cost guard used**: `$119.989706` / `$125.0`
- **Remaining before stop**: `$5.010294`
- **Projected usage if downloaded**: `$120.494368`
- **Decision**: `metadata_estimate_pass_next_download_decision_required`
- **Download allowed under current guard**: `False`
- **Reason**: Metadata estimate $0.504662 fits within remaining headroom $5.010294; a separate download decision artifact is still required before any data pull.

## Planned Requests

| Date | Field | Window | Dataset | Schema | Start | End | Cost |
|:--|:--|:--|:--|:--|:--|:--|--:|
| `2025-04-08` | `option_entry_quote` | `2025-04-08_entry_0935` | `OPRA.PILLAR` | `cbbo-1m` | `2025-04-08T13:30:00+00:00` | `2025-04-08T13:40:00+00:00` | `0.034448` |
| `2025-04-08` | `option_exit_quotes` | `2025-04-08_entry_check_1000` | `OPRA.PILLAR` | `cbbo-1m` | `2025-04-08T13:55:00+00:00` | `2025-04-08T14:05:00+00:00` | `0.036213` |
| `2025-04-08` | `option_exit_quotes` | `2025-04-08_exit_check_1030` | `OPRA.PILLAR` | `cbbo-1m` | `2025-04-08T14:25:00+00:00` | `2025-04-08T14:35:00+00:00` | `0.036044` |
| `2025-04-08` | `option_exit_quotes` | `2025-04-08_exit_check_1100` | `OPRA.PILLAR` | `cbbo-1m` | `2025-04-08T14:55:00+00:00` | `2025-04-08T15:05:00+00:00` | `0.036078` |
| `2025-04-08` | `option_exit_quotes` | `2025-04-08_exit_check_1130` | `OPRA.PILLAR` | `cbbo-1m` | `2025-04-08T15:25:00+00:00` | `2025-04-08T15:35:00+00:00` | `0.03619` |
| `2025-04-08` | `option_exit_quotes` | `2025-04-08_exit_check_1200` | `OPRA.PILLAR` | `cbbo-1m` | `2025-04-08T15:55:00+00:00` | `2025-04-08T16:05:00+00:00` | `0.036194` |
| `2025-04-08` | `option_exit_quotes` | `2025-04-08_exit_check_1230` | `OPRA.PILLAR` | `cbbo-1m` | `2025-04-08T16:25:00+00:00` | `2025-04-08T16:35:00+00:00` | `0.036266` |
| `2025-04-08` | `option_exit_quotes` | `2025-04-08_exit_check_1300` | `OPRA.PILLAR` | `cbbo-1m` | `2025-04-08T16:55:00+00:00` | `2025-04-08T17:05:00+00:00` | `0.036228` |
| `2025-04-08` | `option_exit_quotes` | `2025-04-08_exit_check_1330` | `OPRA.PILLAR` | `cbbo-1m` | `2025-04-08T17:25:00+00:00` | `2025-04-08T17:35:00+00:00` | `0.036229` |
| `2025-04-08` | `option_exit_quotes` | `2025-04-08_exit_check_1400` | `OPRA.PILLAR` | `cbbo-1m` | `2025-04-08T17:55:00+00:00` | `2025-04-08T18:05:00+00:00` | `0.036116` |
| `2025-04-08` | `option_exit_quotes` | `2025-04-08_exit_check_1430` | `OPRA.PILLAR` | `cbbo-1m` | `2025-04-08T18:25:00+00:00` | `2025-04-08T18:35:00+00:00` | `0.036139` |
| `2025-04-08` | `option_exit_quotes` | `2025-04-08_exit_check_1500` | `OPRA.PILLAR` | `cbbo-1m` | `2025-04-08T18:55:00+00:00` | `2025-04-08T19:05:00+00:00` | `0.036057` |
| `2025-04-08` | `option_exit_quotes` | `2025-04-08_exit_check_1530` | `OPRA.PILLAR` | `cbbo-1m` | `2025-04-08T19:25:00+00:00` | `2025-04-08T19:35:00+00:00` | `0.036103` |
| `2025-04-08` | `option_exit_quotes` | `2025-04-08_forced_close_1545` | `OPRA.PILLAR` | `cbbo-1m` | `2025-04-08T19:40:00+00:00` | `2025-04-08T19:50:00+00:00` | `0.036113` |
| `2025-04-08` | `spy_underlying_bars` | `2025-04-08_spy_underlying_full_session` | `EQUS.MINI` | `ohlcv-1m` | `2025-04-08T13:30:00+00:00` | `2025-04-08T20:00:00+00:00` | `0.000244` |

## Guardrail

This is a metadata cost gate only. It does not download Databento data, add validation PnL days, approve exact replay, or approve paper trading.
