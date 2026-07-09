# H-A2 Independent Validation Cost Gate

- **Hypothesis**: `H-A2`
- **Experiment**: `h_a2_normal_control_sample_decision`
- **Batch**: `low_normal_vix_control_pack`
- **Selected key env**: `DATABENTO_API_MO`
- **Mode**: `live_metadata_cost_no_download_grouped_conservative`
- **Download performed**: `False`
- **Planned requests**: `150`
- **Total estimated cost**: `5.398913`
- **Cost guard used**: `$120.494368` / `$125.0`
- **Remaining before stop**: `$4.505632`
- **Projected usage if downloaded**: `$125.893281`
- **Projected selected-key usage if downloaded**: `$5.398913`
- **Decision**: `metadata_estimate_pass_next_download_decision_required`
- **Download allowed under current guard**: `False`
- **Reason**: Metadata estimate $5.398913 fits within selected key cap $100.0 and MO/AI pool cap $200.0; a separate download decision artifact is still required before any data pull.

## Planned Requests

| Date | Field | Window | Dataset | Schema | Start | End | Cost |
|:--|:--|:--|:--|:--|:--|:--|--:|
| `2025-02-03` | `option_entry_quote` | `2025-02-03_entry_0935` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-03T14:30:00+00:00` | `2025-02-03T14:40:00+00:00` | `` |
| `2025-02-03` | `option_exit_quotes` | `2025-02-03_entry_check_1000` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-03T14:55:00+00:00` | `2025-02-03T15:05:00+00:00` | `` |
| `2025-02-03` | `option_exit_quotes` | `2025-02-03_exit_check_1030` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-03T15:25:00+00:00` | `2025-02-03T15:35:00+00:00` | `` |
| `2025-02-03` | `option_exit_quotes` | `2025-02-03_exit_check_1100` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-03T15:55:00+00:00` | `2025-02-03T16:05:00+00:00` | `` |
| `2025-02-03` | `option_exit_quotes` | `2025-02-03_exit_check_1130` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-03T16:25:00+00:00` | `2025-02-03T16:35:00+00:00` | `` |
| `2025-02-03` | `option_exit_quotes` | `2025-02-03_exit_check_1200` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-03T16:55:00+00:00` | `2025-02-03T17:05:00+00:00` | `` |
| `2025-02-03` | `option_exit_quotes` | `2025-02-03_exit_check_1230` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-03T17:25:00+00:00` | `2025-02-03T17:35:00+00:00` | `` |
| `2025-02-03` | `option_exit_quotes` | `2025-02-03_exit_check_1300` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-03T17:55:00+00:00` | `2025-02-03T18:05:00+00:00` | `` |
| `2025-02-03` | `option_exit_quotes` | `2025-02-03_exit_check_1330` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-03T18:25:00+00:00` | `2025-02-03T18:35:00+00:00` | `` |
| `2025-02-03` | `option_exit_quotes` | `2025-02-03_exit_check_1400` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-03T18:55:00+00:00` | `2025-02-03T19:05:00+00:00` | `` |
| `2025-02-03` | `option_exit_quotes` | `2025-02-03_exit_check_1430` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-03T19:25:00+00:00` | `2025-02-03T19:35:00+00:00` | `` |
| `2025-02-03` | `option_exit_quotes` | `2025-02-03_exit_check_1500` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-03T19:55:00+00:00` | `2025-02-03T20:05:00+00:00` | `` |
| `2025-02-03` | `option_exit_quotes` | `2025-02-03_exit_check_1530` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-03T20:25:00+00:00` | `2025-02-03T20:35:00+00:00` | `` |
| `2025-02-03` | `option_exit_quotes` | `2025-02-03_forced_close_1545` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-03T20:40:00+00:00` | `2025-02-03T20:50:00+00:00` | `` |
| `2025-02-03` | `spy_underlying_bars` | `2025-02-03_spy_underlying_full_session` | `EQUS.MINI` | `ohlcv-1m` | `2025-02-03T14:30:00+00:00` | `2025-02-03T21:00:00+00:00` | `0.000244` |
| `2025-02-04` | `option_entry_quote` | `2025-02-04_entry_0935` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-04T14:30:00+00:00` | `2025-02-04T14:40:00+00:00` | `` |
| `2025-02-04` | `option_exit_quotes` | `2025-02-04_entry_check_1000` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-04T14:55:00+00:00` | `2025-02-04T15:05:00+00:00` | `` |
| `2025-02-04` | `option_exit_quotes` | `2025-02-04_exit_check_1030` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-04T15:25:00+00:00` | `2025-02-04T15:35:00+00:00` | `` |
| `2025-02-04` | `option_exit_quotes` | `2025-02-04_exit_check_1100` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-04T15:55:00+00:00` | `2025-02-04T16:05:00+00:00` | `` |
| `2025-02-04` | `option_exit_quotes` | `2025-02-04_exit_check_1130` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-04T16:25:00+00:00` | `2025-02-04T16:35:00+00:00` | `` |
| `2025-02-04` | `option_exit_quotes` | `2025-02-04_exit_check_1200` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-04T16:55:00+00:00` | `2025-02-04T17:05:00+00:00` | `` |
| `2025-02-04` | `option_exit_quotes` | `2025-02-04_exit_check_1230` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-04T17:25:00+00:00` | `2025-02-04T17:35:00+00:00` | `` |
| `2025-02-04` | `option_exit_quotes` | `2025-02-04_exit_check_1300` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-04T17:55:00+00:00` | `2025-02-04T18:05:00+00:00` | `` |
| `2025-02-04` | `option_exit_quotes` | `2025-02-04_exit_check_1330` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-04T18:25:00+00:00` | `2025-02-04T18:35:00+00:00` | `` |
| `2025-02-04` | `option_exit_quotes` | `2025-02-04_exit_check_1400` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-04T18:55:00+00:00` | `2025-02-04T19:05:00+00:00` | `` |
| `2025-02-04` | `option_exit_quotes` | `2025-02-04_exit_check_1430` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-04T19:25:00+00:00` | `2025-02-04T19:35:00+00:00` | `` |
| `2025-02-04` | `option_exit_quotes` | `2025-02-04_exit_check_1500` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-04T19:55:00+00:00` | `2025-02-04T20:05:00+00:00` | `` |
| `2025-02-04` | `option_exit_quotes` | `2025-02-04_exit_check_1530` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-04T20:25:00+00:00` | `2025-02-04T20:35:00+00:00` | `` |
| `2025-02-04` | `option_exit_quotes` | `2025-02-04_forced_close_1545` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-04T20:40:00+00:00` | `2025-02-04T20:50:00+00:00` | `` |
| `2025-02-04` | `spy_underlying_bars` | `2025-02-04_spy_underlying_full_session` | `EQUS.MINI` | `ohlcv-1m` | `2025-02-04T14:30:00+00:00` | `2025-02-04T21:00:00+00:00` | `0.000244` |
| `2025-02-05` | `option_entry_quote` | `2025-02-05_entry_0935` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-05T14:30:00+00:00` | `2025-02-05T14:40:00+00:00` | `` |
| `2025-02-05` | `option_exit_quotes` | `2025-02-05_entry_check_1000` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-05T14:55:00+00:00` | `2025-02-05T15:05:00+00:00` | `` |
| `2025-02-05` | `option_exit_quotes` | `2025-02-05_exit_check_1030` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-05T15:25:00+00:00` | `2025-02-05T15:35:00+00:00` | `` |
| `2025-02-05` | `option_exit_quotes` | `2025-02-05_exit_check_1100` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-05T15:55:00+00:00` | `2025-02-05T16:05:00+00:00` | `` |
| `2025-02-05` | `option_exit_quotes` | `2025-02-05_exit_check_1130` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-05T16:25:00+00:00` | `2025-02-05T16:35:00+00:00` | `` |
| `2025-02-05` | `option_exit_quotes` | `2025-02-05_exit_check_1200` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-05T16:55:00+00:00` | `2025-02-05T17:05:00+00:00` | `` |
| `2025-02-05` | `option_exit_quotes` | `2025-02-05_exit_check_1230` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-05T17:25:00+00:00` | `2025-02-05T17:35:00+00:00` | `` |
| `2025-02-05` | `option_exit_quotes` | `2025-02-05_exit_check_1300` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-05T17:55:00+00:00` | `2025-02-05T18:05:00+00:00` | `` |
| `2025-02-05` | `option_exit_quotes` | `2025-02-05_exit_check_1330` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-05T18:25:00+00:00` | `2025-02-05T18:35:00+00:00` | `` |
| `2025-02-05` | `option_exit_quotes` | `2025-02-05_exit_check_1400` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-05T18:55:00+00:00` | `2025-02-05T19:05:00+00:00` | `` |
| `2025-02-05` | `option_exit_quotes` | `2025-02-05_exit_check_1430` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-05T19:25:00+00:00` | `2025-02-05T19:35:00+00:00` | `` |
| `2025-02-05` | `option_exit_quotes` | `2025-02-05_exit_check_1500` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-05T19:55:00+00:00` | `2025-02-05T20:05:00+00:00` | `` |
| `2025-02-05` | `option_exit_quotes` | `2025-02-05_exit_check_1530` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-05T20:25:00+00:00` | `2025-02-05T20:35:00+00:00` | `` |
| `2025-02-05` | `option_exit_quotes` | `2025-02-05_forced_close_1545` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-05T20:40:00+00:00` | `2025-02-05T20:50:00+00:00` | `` |
| `2025-02-05` | `spy_underlying_bars` | `2025-02-05_spy_underlying_full_session` | `EQUS.MINI` | `ohlcv-1m` | `2025-02-05T14:30:00+00:00` | `2025-02-05T21:00:00+00:00` | `0.000244` |
| `2025-02-06` | `option_entry_quote` | `2025-02-06_entry_0935` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-06T14:30:00+00:00` | `2025-02-06T14:40:00+00:00` | `` |
| `2025-02-06` | `option_exit_quotes` | `2025-02-06_entry_check_1000` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-06T14:55:00+00:00` | `2025-02-06T15:05:00+00:00` | `` |
| `2025-02-06` | `option_exit_quotes` | `2025-02-06_exit_check_1030` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-06T15:25:00+00:00` | `2025-02-06T15:35:00+00:00` | `` |
| `2025-02-06` | `option_exit_quotes` | `2025-02-06_exit_check_1100` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-06T15:55:00+00:00` | `2025-02-06T16:05:00+00:00` | `` |
| `2025-02-06` | `option_exit_quotes` | `2025-02-06_exit_check_1130` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-06T16:25:00+00:00` | `2025-02-06T16:35:00+00:00` | `` |
| `2025-02-06` | `option_exit_quotes` | `2025-02-06_exit_check_1200` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-06T16:55:00+00:00` | `2025-02-06T17:05:00+00:00` | `` |
| `2025-02-06` | `option_exit_quotes` | `2025-02-06_exit_check_1230` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-06T17:25:00+00:00` | `2025-02-06T17:35:00+00:00` | `` |
| `2025-02-06` | `option_exit_quotes` | `2025-02-06_exit_check_1300` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-06T17:55:00+00:00` | `2025-02-06T18:05:00+00:00` | `` |
| `2025-02-06` | `option_exit_quotes` | `2025-02-06_exit_check_1330` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-06T18:25:00+00:00` | `2025-02-06T18:35:00+00:00` | `` |
| `2025-02-06` | `option_exit_quotes` | `2025-02-06_exit_check_1400` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-06T18:55:00+00:00` | `2025-02-06T19:05:00+00:00` | `` |
| `2025-02-06` | `option_exit_quotes` | `2025-02-06_exit_check_1430` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-06T19:25:00+00:00` | `2025-02-06T19:35:00+00:00` | `` |
| `2025-02-06` | `option_exit_quotes` | `2025-02-06_exit_check_1500` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-06T19:55:00+00:00` | `2025-02-06T20:05:00+00:00` | `` |
| `2025-02-06` | `option_exit_quotes` | `2025-02-06_exit_check_1530` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-06T20:25:00+00:00` | `2025-02-06T20:35:00+00:00` | `` |
| `2025-02-06` | `option_exit_quotes` | `2025-02-06_forced_close_1545` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-06T20:40:00+00:00` | `2025-02-06T20:50:00+00:00` | `` |
| `2025-02-06` | `spy_underlying_bars` | `2025-02-06_spy_underlying_full_session` | `EQUS.MINI` | `ohlcv-1m` | `2025-02-06T14:30:00+00:00` | `2025-02-06T21:00:00+00:00` | `0.000244` |
| `2025-02-07` | `option_entry_quote` | `2025-02-07_entry_0935` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-07T14:30:00+00:00` | `2025-02-07T14:40:00+00:00` | `` |
| `2025-02-07` | `option_exit_quotes` | `2025-02-07_entry_check_1000` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-07T14:55:00+00:00` | `2025-02-07T15:05:00+00:00` | `` |
| `2025-02-07` | `option_exit_quotes` | `2025-02-07_exit_check_1030` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-07T15:25:00+00:00` | `2025-02-07T15:35:00+00:00` | `` |
| `2025-02-07` | `option_exit_quotes` | `2025-02-07_exit_check_1100` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-07T15:55:00+00:00` | `2025-02-07T16:05:00+00:00` | `` |
| `2025-02-07` | `option_exit_quotes` | `2025-02-07_exit_check_1130` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-07T16:25:00+00:00` | `2025-02-07T16:35:00+00:00` | `` |
| `2025-02-07` | `option_exit_quotes` | `2025-02-07_exit_check_1200` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-07T16:55:00+00:00` | `2025-02-07T17:05:00+00:00` | `` |
| `2025-02-07` | `option_exit_quotes` | `2025-02-07_exit_check_1230` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-07T17:25:00+00:00` | `2025-02-07T17:35:00+00:00` | `` |
| `2025-02-07` | `option_exit_quotes` | `2025-02-07_exit_check_1300` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-07T17:55:00+00:00` | `2025-02-07T18:05:00+00:00` | `` |
| `2025-02-07` | `option_exit_quotes` | `2025-02-07_exit_check_1330` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-07T18:25:00+00:00` | `2025-02-07T18:35:00+00:00` | `` |
| `2025-02-07` | `option_exit_quotes` | `2025-02-07_exit_check_1400` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-07T18:55:00+00:00` | `2025-02-07T19:05:00+00:00` | `` |
| `2025-02-07` | `option_exit_quotes` | `2025-02-07_exit_check_1430` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-07T19:25:00+00:00` | `2025-02-07T19:35:00+00:00` | `` |
| `2025-02-07` | `option_exit_quotes` | `2025-02-07_exit_check_1500` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-07T19:55:00+00:00` | `2025-02-07T20:05:00+00:00` | `` |
| `2025-02-07` | `option_exit_quotes` | `2025-02-07_exit_check_1530` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-07T20:25:00+00:00` | `2025-02-07T20:35:00+00:00` | `` |
| `2025-02-07` | `option_exit_quotes` | `2025-02-07_forced_close_1545` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-07T20:40:00+00:00` | `2025-02-07T20:50:00+00:00` | `` |
| `2025-02-07` | `spy_underlying_bars` | `2025-02-07_spy_underlying_full_session` | `EQUS.MINI` | `ohlcv-1m` | `2025-02-07T14:30:00+00:00` | `2025-02-07T21:00:00+00:00` | `0.000244` |
| `2025-02-10` | `option_entry_quote` | `2025-02-10_entry_0935` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-10T14:30:00+00:00` | `2025-02-10T14:40:00+00:00` | `` |
| `2025-02-10` | `option_exit_quotes` | `2025-02-10_entry_check_1000` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-10T14:55:00+00:00` | `2025-02-10T15:05:00+00:00` | `` |
| `2025-02-10` | `option_exit_quotes` | `2025-02-10_exit_check_1030` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-10T15:25:00+00:00` | `2025-02-10T15:35:00+00:00` | `` |
| `2025-02-10` | `option_exit_quotes` | `2025-02-10_exit_check_1100` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-10T15:55:00+00:00` | `2025-02-10T16:05:00+00:00` | `` |
| `2025-02-10` | `option_exit_quotes` | `2025-02-10_exit_check_1130` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-10T16:25:00+00:00` | `2025-02-10T16:35:00+00:00` | `` |
| `2025-02-10` | `option_exit_quotes` | `2025-02-10_exit_check_1200` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-10T16:55:00+00:00` | `2025-02-10T17:05:00+00:00` | `` |
| `2025-02-10` | `option_exit_quotes` | `2025-02-10_exit_check_1230` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-10T17:25:00+00:00` | `2025-02-10T17:35:00+00:00` | `` |
| `2025-02-10` | `option_exit_quotes` | `2025-02-10_exit_check_1300` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-10T17:55:00+00:00` | `2025-02-10T18:05:00+00:00` | `` |
| `2025-02-10` | `option_exit_quotes` | `2025-02-10_exit_check_1330` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-10T18:25:00+00:00` | `2025-02-10T18:35:00+00:00` | `` |
| `2025-02-10` | `option_exit_quotes` | `2025-02-10_exit_check_1400` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-10T18:55:00+00:00` | `2025-02-10T19:05:00+00:00` | `` |
| `2025-02-10` | `option_exit_quotes` | `2025-02-10_exit_check_1430` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-10T19:25:00+00:00` | `2025-02-10T19:35:00+00:00` | `` |
| `2025-02-10` | `option_exit_quotes` | `2025-02-10_exit_check_1500` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-10T19:55:00+00:00` | `2025-02-10T20:05:00+00:00` | `` |
| `2025-02-10` | `option_exit_quotes` | `2025-02-10_exit_check_1530` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-10T20:25:00+00:00` | `2025-02-10T20:35:00+00:00` | `` |
| `2025-02-10` | `option_exit_quotes` | `2025-02-10_forced_close_1545` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-10T20:40:00+00:00` | `2025-02-10T20:50:00+00:00` | `` |
| `2025-02-10` | `spy_underlying_bars` | `2025-02-10_spy_underlying_full_session` | `EQUS.MINI` | `ohlcv-1m` | `2025-02-10T14:30:00+00:00` | `2025-02-10T21:00:00+00:00` | `0.000244` |
| `2025-02-11` | `option_entry_quote` | `2025-02-11_entry_0935` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-11T14:30:00+00:00` | `2025-02-11T14:40:00+00:00` | `` |
| `2025-02-11` | `option_exit_quotes` | `2025-02-11_entry_check_1000` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-11T14:55:00+00:00` | `2025-02-11T15:05:00+00:00` | `` |
| `2025-02-11` | `option_exit_quotes` | `2025-02-11_exit_check_1030` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-11T15:25:00+00:00` | `2025-02-11T15:35:00+00:00` | `` |
| `2025-02-11` | `option_exit_quotes` | `2025-02-11_exit_check_1100` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-11T15:55:00+00:00` | `2025-02-11T16:05:00+00:00` | `` |
| `2025-02-11` | `option_exit_quotes` | `2025-02-11_exit_check_1130` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-11T16:25:00+00:00` | `2025-02-11T16:35:00+00:00` | `` |
| `2025-02-11` | `option_exit_quotes` | `2025-02-11_exit_check_1200` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-11T16:55:00+00:00` | `2025-02-11T17:05:00+00:00` | `` |
| `2025-02-11` | `option_exit_quotes` | `2025-02-11_exit_check_1230` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-11T17:25:00+00:00` | `2025-02-11T17:35:00+00:00` | `` |
| `2025-02-11` | `option_exit_quotes` | `2025-02-11_exit_check_1300` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-11T17:55:00+00:00` | `2025-02-11T18:05:00+00:00` | `` |
| `2025-02-11` | `option_exit_quotes` | `2025-02-11_exit_check_1330` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-11T18:25:00+00:00` | `2025-02-11T18:35:00+00:00` | `` |
| `2025-02-11` | `option_exit_quotes` | `2025-02-11_exit_check_1400` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-11T18:55:00+00:00` | `2025-02-11T19:05:00+00:00` | `` |
| `2025-02-11` | `option_exit_quotes` | `2025-02-11_exit_check_1430` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-11T19:25:00+00:00` | `2025-02-11T19:35:00+00:00` | `` |
| `2025-02-11` | `option_exit_quotes` | `2025-02-11_exit_check_1500` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-11T19:55:00+00:00` | `2025-02-11T20:05:00+00:00` | `` |
| `2025-02-11` | `option_exit_quotes` | `2025-02-11_exit_check_1530` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-11T20:25:00+00:00` | `2025-02-11T20:35:00+00:00` | `` |
| `2025-02-11` | `option_exit_quotes` | `2025-02-11_forced_close_1545` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-11T20:40:00+00:00` | `2025-02-11T20:50:00+00:00` | `` |
| `2025-02-11` | `spy_underlying_bars` | `2025-02-11_spy_underlying_full_session` | `EQUS.MINI` | `ohlcv-1m` | `2025-02-11T14:30:00+00:00` | `2025-02-11T21:00:00+00:00` | `0.000244` |
| `2025-02-12` | `option_entry_quote` | `2025-02-12_entry_0935` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-12T14:30:00+00:00` | `2025-02-12T14:40:00+00:00` | `` |
| `2025-02-12` | `option_exit_quotes` | `2025-02-12_entry_check_1000` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-12T14:55:00+00:00` | `2025-02-12T15:05:00+00:00` | `` |
| `2025-02-12` | `option_exit_quotes` | `2025-02-12_exit_check_1030` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-12T15:25:00+00:00` | `2025-02-12T15:35:00+00:00` | `` |
| `2025-02-12` | `option_exit_quotes` | `2025-02-12_exit_check_1100` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-12T15:55:00+00:00` | `2025-02-12T16:05:00+00:00` | `` |
| `2025-02-12` | `option_exit_quotes` | `2025-02-12_exit_check_1130` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-12T16:25:00+00:00` | `2025-02-12T16:35:00+00:00` | `` |
| `2025-02-12` | `option_exit_quotes` | `2025-02-12_exit_check_1200` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-12T16:55:00+00:00` | `2025-02-12T17:05:00+00:00` | `` |
| `2025-02-12` | `option_exit_quotes` | `2025-02-12_exit_check_1230` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-12T17:25:00+00:00` | `2025-02-12T17:35:00+00:00` | `` |
| `2025-02-12` | `option_exit_quotes` | `2025-02-12_exit_check_1300` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-12T17:55:00+00:00` | `2025-02-12T18:05:00+00:00` | `` |
| `2025-02-12` | `option_exit_quotes` | `2025-02-12_exit_check_1330` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-12T18:25:00+00:00` | `2025-02-12T18:35:00+00:00` | `` |
| `2025-02-12` | `option_exit_quotes` | `2025-02-12_exit_check_1400` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-12T18:55:00+00:00` | `2025-02-12T19:05:00+00:00` | `` |
| `2025-02-12` | `option_exit_quotes` | `2025-02-12_exit_check_1430` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-12T19:25:00+00:00` | `2025-02-12T19:35:00+00:00` | `` |
| `2025-02-12` | `option_exit_quotes` | `2025-02-12_exit_check_1500` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-12T19:55:00+00:00` | `2025-02-12T20:05:00+00:00` | `` |
| `2025-02-12` | `option_exit_quotes` | `2025-02-12_exit_check_1530` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-12T20:25:00+00:00` | `2025-02-12T20:35:00+00:00` | `` |
| `2025-02-12` | `option_exit_quotes` | `2025-02-12_forced_close_1545` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-12T20:40:00+00:00` | `2025-02-12T20:50:00+00:00` | `` |
| `2025-02-12` | `spy_underlying_bars` | `2025-02-12_spy_underlying_full_session` | `EQUS.MINI` | `ohlcv-1m` | `2025-02-12T14:30:00+00:00` | `2025-02-12T21:00:00+00:00` | `0.000244` |
| `2025-02-13` | `option_entry_quote` | `2025-02-13_entry_0935` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-13T14:30:00+00:00` | `2025-02-13T14:40:00+00:00` | `` |
| `2025-02-13` | `option_exit_quotes` | `2025-02-13_entry_check_1000` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-13T14:55:00+00:00` | `2025-02-13T15:05:00+00:00` | `` |
| `2025-02-13` | `option_exit_quotes` | `2025-02-13_exit_check_1030` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-13T15:25:00+00:00` | `2025-02-13T15:35:00+00:00` | `` |
| `2025-02-13` | `option_exit_quotes` | `2025-02-13_exit_check_1100` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-13T15:55:00+00:00` | `2025-02-13T16:05:00+00:00` | `` |
| `2025-02-13` | `option_exit_quotes` | `2025-02-13_exit_check_1130` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-13T16:25:00+00:00` | `2025-02-13T16:35:00+00:00` | `` |
| `2025-02-13` | `option_exit_quotes` | `2025-02-13_exit_check_1200` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-13T16:55:00+00:00` | `2025-02-13T17:05:00+00:00` | `` |
| `2025-02-13` | `option_exit_quotes` | `2025-02-13_exit_check_1230` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-13T17:25:00+00:00` | `2025-02-13T17:35:00+00:00` | `` |
| `2025-02-13` | `option_exit_quotes` | `2025-02-13_exit_check_1300` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-13T17:55:00+00:00` | `2025-02-13T18:05:00+00:00` | `` |
| `2025-02-13` | `option_exit_quotes` | `2025-02-13_exit_check_1330` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-13T18:25:00+00:00` | `2025-02-13T18:35:00+00:00` | `` |
| `2025-02-13` | `option_exit_quotes` | `2025-02-13_exit_check_1400` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-13T18:55:00+00:00` | `2025-02-13T19:05:00+00:00` | `` |
| `2025-02-13` | `option_exit_quotes` | `2025-02-13_exit_check_1430` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-13T19:25:00+00:00` | `2025-02-13T19:35:00+00:00` | `` |
| `2025-02-13` | `option_exit_quotes` | `2025-02-13_exit_check_1500` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-13T19:55:00+00:00` | `2025-02-13T20:05:00+00:00` | `` |
| `2025-02-13` | `option_exit_quotes` | `2025-02-13_exit_check_1530` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-13T20:25:00+00:00` | `2025-02-13T20:35:00+00:00` | `` |
| `2025-02-13` | `option_exit_quotes` | `2025-02-13_forced_close_1545` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-13T20:40:00+00:00` | `2025-02-13T20:50:00+00:00` | `` |
| `2025-02-13` | `spy_underlying_bars` | `2025-02-13_spy_underlying_full_session` | `EQUS.MINI` | `ohlcv-1m` | `2025-02-13T14:30:00+00:00` | `2025-02-13T21:00:00+00:00` | `0.000244` |
| `2025-02-14` | `option_entry_quote` | `2025-02-14_entry_0935` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-14T14:30:00+00:00` | `2025-02-14T14:40:00+00:00` | `` |
| `2025-02-14` | `option_exit_quotes` | `2025-02-14_entry_check_1000` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-14T14:55:00+00:00` | `2025-02-14T15:05:00+00:00` | `` |
| `2025-02-14` | `option_exit_quotes` | `2025-02-14_exit_check_1030` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-14T15:25:00+00:00` | `2025-02-14T15:35:00+00:00` | `` |
| `2025-02-14` | `option_exit_quotes` | `2025-02-14_exit_check_1100` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-14T15:55:00+00:00` | `2025-02-14T16:05:00+00:00` | `` |
| `2025-02-14` | `option_exit_quotes` | `2025-02-14_exit_check_1130` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-14T16:25:00+00:00` | `2025-02-14T16:35:00+00:00` | `` |
| `2025-02-14` | `option_exit_quotes` | `2025-02-14_exit_check_1200` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-14T16:55:00+00:00` | `2025-02-14T17:05:00+00:00` | `` |
| `2025-02-14` | `option_exit_quotes` | `2025-02-14_exit_check_1230` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-14T17:25:00+00:00` | `2025-02-14T17:35:00+00:00` | `` |
| `2025-02-14` | `option_exit_quotes` | `2025-02-14_exit_check_1300` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-14T17:55:00+00:00` | `2025-02-14T18:05:00+00:00` | `` |
| `2025-02-14` | `option_exit_quotes` | `2025-02-14_exit_check_1330` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-14T18:25:00+00:00` | `2025-02-14T18:35:00+00:00` | `` |
| `2025-02-14` | `option_exit_quotes` | `2025-02-14_exit_check_1400` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-14T18:55:00+00:00` | `2025-02-14T19:05:00+00:00` | `` |
| `2025-02-14` | `option_exit_quotes` | `2025-02-14_exit_check_1430` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-14T19:25:00+00:00` | `2025-02-14T19:35:00+00:00` | `` |
| `2025-02-14` | `option_exit_quotes` | `2025-02-14_exit_check_1500` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-14T19:55:00+00:00` | `2025-02-14T20:05:00+00:00` | `` |
| `2025-02-14` | `option_exit_quotes` | `2025-02-14_exit_check_1530` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-14T20:25:00+00:00` | `2025-02-14T20:35:00+00:00` | `` |
| `2025-02-14` | `option_exit_quotes` | `2025-02-14_forced_close_1545` | `OPRA.PILLAR` | `cbbo-1m` | `2025-02-14T20:40:00+00:00` | `2025-02-14T20:50:00+00:00` | `` |
| `2025-02-14` | `spy_underlying_bars` | `2025-02-14_spy_underlying_full_session` | `EQUS.MINI` | `ohlcv-1m` | `2025-02-14T14:30:00+00:00` | `2025-02-14T21:00:00+00:00` | `0.000244` |

## Guardrail

This is a metadata cost gate only. It does not download Databento data, add validation PnL days, approve exact replay, or approve paper trading.
