# H-A2 Independent Validation Cost Gate

- **Hypothesis**: `H-A2`
- **Experiment**: `h_a2_post_exact_replay_sample_expansion_decision`
- **Batch**: `post_stress_normalization_control_pack`
- **Selected key env**: `DATABENTO_API_AI`
- **Mode**: `live_metadata_cost_no_download_grouped_conservative`
- **Download performed**: `False`
- **Planned requests**: `150`
- **Total estimated cost**: `5.558642`
- **Cost guard used**: `$120.494368` / `$125.0`
- **Remaining before stop**: `$4.505632`
- **Projected usage if downloaded**: `$126.05301`
- **Projected selected-key usage if downloaded**: `$5.558642`
- **Decision**: `metadata_estimate_pass_next_download_decision_required`
- **Download allowed under current guard**: `False`
- **Reason**: Metadata estimate $5.558642 fits within selected key cap $100.0 and MO/AI pool cap $200.0; a separate download decision artifact is still required before any data pull.

## Planned Requests

| Date | Field | Window | Dataset | Schema | Start | End | Cost |
|:--|:--|:--|:--|:--|:--|:--|--:|
| `2025-05-05` | `option_entry_quote` | `2025-05-05_entry_0935` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-05T13:30:00+00:00` | `2025-05-05T13:40:00+00:00` | `` |
| `2025-05-05` | `option_exit_quotes` | `2025-05-05_entry_check_1000` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-05T13:55:00+00:00` | `2025-05-05T14:05:00+00:00` | `` |
| `2025-05-05` | `option_exit_quotes` | `2025-05-05_exit_check_1030` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-05T14:25:00+00:00` | `2025-05-05T14:35:00+00:00` | `` |
| `2025-05-05` | `option_exit_quotes` | `2025-05-05_exit_check_1100` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-05T14:55:00+00:00` | `2025-05-05T15:05:00+00:00` | `` |
| `2025-05-05` | `option_exit_quotes` | `2025-05-05_exit_check_1130` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-05T15:25:00+00:00` | `2025-05-05T15:35:00+00:00` | `` |
| `2025-05-05` | `option_exit_quotes` | `2025-05-05_exit_check_1200` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-05T15:55:00+00:00` | `2025-05-05T16:05:00+00:00` | `` |
| `2025-05-05` | `option_exit_quotes` | `2025-05-05_exit_check_1230` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-05T16:25:00+00:00` | `2025-05-05T16:35:00+00:00` | `` |
| `2025-05-05` | `option_exit_quotes` | `2025-05-05_exit_check_1300` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-05T16:55:00+00:00` | `2025-05-05T17:05:00+00:00` | `` |
| `2025-05-05` | `option_exit_quotes` | `2025-05-05_exit_check_1330` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-05T17:25:00+00:00` | `2025-05-05T17:35:00+00:00` | `` |
| `2025-05-05` | `option_exit_quotes` | `2025-05-05_exit_check_1400` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-05T17:55:00+00:00` | `2025-05-05T18:05:00+00:00` | `` |
| `2025-05-05` | `option_exit_quotes` | `2025-05-05_exit_check_1430` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-05T18:25:00+00:00` | `2025-05-05T18:35:00+00:00` | `` |
| `2025-05-05` | `option_exit_quotes` | `2025-05-05_exit_check_1500` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-05T18:55:00+00:00` | `2025-05-05T19:05:00+00:00` | `` |
| `2025-05-05` | `option_exit_quotes` | `2025-05-05_exit_check_1530` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-05T19:25:00+00:00` | `2025-05-05T19:35:00+00:00` | `` |
| `2025-05-05` | `option_exit_quotes` | `2025-05-05_forced_close_1545` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-05T19:40:00+00:00` | `2025-05-05T19:50:00+00:00` | `` |
| `2025-05-05` | `spy_underlying_bars` | `2025-05-05_spy_underlying_full_session` | `EQUS.MINI` | `ohlcv-1m` | `2025-05-05T13:30:00+00:00` | `2025-05-05T20:00:00+00:00` | `0.000244` |
| `2025-05-06` | `option_entry_quote` | `2025-05-06_entry_0935` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-06T13:30:00+00:00` | `2025-05-06T13:40:00+00:00` | `` |
| `2025-05-06` | `option_exit_quotes` | `2025-05-06_entry_check_1000` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-06T13:55:00+00:00` | `2025-05-06T14:05:00+00:00` | `` |
| `2025-05-06` | `option_exit_quotes` | `2025-05-06_exit_check_1030` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-06T14:25:00+00:00` | `2025-05-06T14:35:00+00:00` | `` |
| `2025-05-06` | `option_exit_quotes` | `2025-05-06_exit_check_1100` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-06T14:55:00+00:00` | `2025-05-06T15:05:00+00:00` | `` |
| `2025-05-06` | `option_exit_quotes` | `2025-05-06_exit_check_1130` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-06T15:25:00+00:00` | `2025-05-06T15:35:00+00:00` | `` |
| `2025-05-06` | `option_exit_quotes` | `2025-05-06_exit_check_1200` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-06T15:55:00+00:00` | `2025-05-06T16:05:00+00:00` | `` |
| `2025-05-06` | `option_exit_quotes` | `2025-05-06_exit_check_1230` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-06T16:25:00+00:00` | `2025-05-06T16:35:00+00:00` | `` |
| `2025-05-06` | `option_exit_quotes` | `2025-05-06_exit_check_1300` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-06T16:55:00+00:00` | `2025-05-06T17:05:00+00:00` | `` |
| `2025-05-06` | `option_exit_quotes` | `2025-05-06_exit_check_1330` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-06T17:25:00+00:00` | `2025-05-06T17:35:00+00:00` | `` |
| `2025-05-06` | `option_exit_quotes` | `2025-05-06_exit_check_1400` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-06T17:55:00+00:00` | `2025-05-06T18:05:00+00:00` | `` |
| `2025-05-06` | `option_exit_quotes` | `2025-05-06_exit_check_1430` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-06T18:25:00+00:00` | `2025-05-06T18:35:00+00:00` | `` |
| `2025-05-06` | `option_exit_quotes` | `2025-05-06_exit_check_1500` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-06T18:55:00+00:00` | `2025-05-06T19:05:00+00:00` | `` |
| `2025-05-06` | `option_exit_quotes` | `2025-05-06_exit_check_1530` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-06T19:25:00+00:00` | `2025-05-06T19:35:00+00:00` | `` |
| `2025-05-06` | `option_exit_quotes` | `2025-05-06_forced_close_1545` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-06T19:40:00+00:00` | `2025-05-06T19:50:00+00:00` | `` |
| `2025-05-06` | `spy_underlying_bars` | `2025-05-06_spy_underlying_full_session` | `EQUS.MINI` | `ohlcv-1m` | `2025-05-06T13:30:00+00:00` | `2025-05-06T20:00:00+00:00` | `0.000244` |
| `2025-05-07` | `option_entry_quote` | `2025-05-07_entry_0935` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-07T13:30:00+00:00` | `2025-05-07T13:40:00+00:00` | `` |
| `2025-05-07` | `option_exit_quotes` | `2025-05-07_entry_check_1000` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-07T13:55:00+00:00` | `2025-05-07T14:05:00+00:00` | `` |
| `2025-05-07` | `option_exit_quotes` | `2025-05-07_exit_check_1030` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-07T14:25:00+00:00` | `2025-05-07T14:35:00+00:00` | `` |
| `2025-05-07` | `option_exit_quotes` | `2025-05-07_exit_check_1100` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-07T14:55:00+00:00` | `2025-05-07T15:05:00+00:00` | `` |
| `2025-05-07` | `option_exit_quotes` | `2025-05-07_exit_check_1130` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-07T15:25:00+00:00` | `2025-05-07T15:35:00+00:00` | `` |
| `2025-05-07` | `option_exit_quotes` | `2025-05-07_exit_check_1200` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-07T15:55:00+00:00` | `2025-05-07T16:05:00+00:00` | `` |
| `2025-05-07` | `option_exit_quotes` | `2025-05-07_exit_check_1230` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-07T16:25:00+00:00` | `2025-05-07T16:35:00+00:00` | `` |
| `2025-05-07` | `option_exit_quotes` | `2025-05-07_exit_check_1300` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-07T16:55:00+00:00` | `2025-05-07T17:05:00+00:00` | `` |
| `2025-05-07` | `option_exit_quotes` | `2025-05-07_exit_check_1330` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-07T17:25:00+00:00` | `2025-05-07T17:35:00+00:00` | `` |
| `2025-05-07` | `option_exit_quotes` | `2025-05-07_exit_check_1400` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-07T17:55:00+00:00` | `2025-05-07T18:05:00+00:00` | `` |
| `2025-05-07` | `option_exit_quotes` | `2025-05-07_exit_check_1430` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-07T18:25:00+00:00` | `2025-05-07T18:35:00+00:00` | `` |
| `2025-05-07` | `option_exit_quotes` | `2025-05-07_exit_check_1500` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-07T18:55:00+00:00` | `2025-05-07T19:05:00+00:00` | `` |
| `2025-05-07` | `option_exit_quotes` | `2025-05-07_exit_check_1530` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-07T19:25:00+00:00` | `2025-05-07T19:35:00+00:00` | `` |
| `2025-05-07` | `option_exit_quotes` | `2025-05-07_forced_close_1545` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-07T19:40:00+00:00` | `2025-05-07T19:50:00+00:00` | `` |
| `2025-05-07` | `spy_underlying_bars` | `2025-05-07_spy_underlying_full_session` | `EQUS.MINI` | `ohlcv-1m` | `2025-05-07T13:30:00+00:00` | `2025-05-07T20:00:00+00:00` | `0.000244` |
| `2025-05-08` | `option_entry_quote` | `2025-05-08_entry_0935` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-08T13:30:00+00:00` | `2025-05-08T13:40:00+00:00` | `` |
| `2025-05-08` | `option_exit_quotes` | `2025-05-08_entry_check_1000` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-08T13:55:00+00:00` | `2025-05-08T14:05:00+00:00` | `` |
| `2025-05-08` | `option_exit_quotes` | `2025-05-08_exit_check_1030` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-08T14:25:00+00:00` | `2025-05-08T14:35:00+00:00` | `` |
| `2025-05-08` | `option_exit_quotes` | `2025-05-08_exit_check_1100` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-08T14:55:00+00:00` | `2025-05-08T15:05:00+00:00` | `` |
| `2025-05-08` | `option_exit_quotes` | `2025-05-08_exit_check_1130` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-08T15:25:00+00:00` | `2025-05-08T15:35:00+00:00` | `` |
| `2025-05-08` | `option_exit_quotes` | `2025-05-08_exit_check_1200` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-08T15:55:00+00:00` | `2025-05-08T16:05:00+00:00` | `` |
| `2025-05-08` | `option_exit_quotes` | `2025-05-08_exit_check_1230` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-08T16:25:00+00:00` | `2025-05-08T16:35:00+00:00` | `` |
| `2025-05-08` | `option_exit_quotes` | `2025-05-08_exit_check_1300` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-08T16:55:00+00:00` | `2025-05-08T17:05:00+00:00` | `` |
| `2025-05-08` | `option_exit_quotes` | `2025-05-08_exit_check_1330` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-08T17:25:00+00:00` | `2025-05-08T17:35:00+00:00` | `` |
| `2025-05-08` | `option_exit_quotes` | `2025-05-08_exit_check_1400` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-08T17:55:00+00:00` | `2025-05-08T18:05:00+00:00` | `` |
| `2025-05-08` | `option_exit_quotes` | `2025-05-08_exit_check_1430` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-08T18:25:00+00:00` | `2025-05-08T18:35:00+00:00` | `` |
| `2025-05-08` | `option_exit_quotes` | `2025-05-08_exit_check_1500` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-08T18:55:00+00:00` | `2025-05-08T19:05:00+00:00` | `` |
| `2025-05-08` | `option_exit_quotes` | `2025-05-08_exit_check_1530` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-08T19:25:00+00:00` | `2025-05-08T19:35:00+00:00` | `` |
| `2025-05-08` | `option_exit_quotes` | `2025-05-08_forced_close_1545` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-08T19:40:00+00:00` | `2025-05-08T19:50:00+00:00` | `` |
| `2025-05-08` | `spy_underlying_bars` | `2025-05-08_spy_underlying_full_session` | `EQUS.MINI` | `ohlcv-1m` | `2025-05-08T13:30:00+00:00` | `2025-05-08T20:00:00+00:00` | `0.000244` |
| `2025-05-09` | `option_entry_quote` | `2025-05-09_entry_0935` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-09T13:30:00+00:00` | `2025-05-09T13:40:00+00:00` | `` |
| `2025-05-09` | `option_exit_quotes` | `2025-05-09_entry_check_1000` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-09T13:55:00+00:00` | `2025-05-09T14:05:00+00:00` | `` |
| `2025-05-09` | `option_exit_quotes` | `2025-05-09_exit_check_1030` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-09T14:25:00+00:00` | `2025-05-09T14:35:00+00:00` | `` |
| `2025-05-09` | `option_exit_quotes` | `2025-05-09_exit_check_1100` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-09T14:55:00+00:00` | `2025-05-09T15:05:00+00:00` | `` |
| `2025-05-09` | `option_exit_quotes` | `2025-05-09_exit_check_1130` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-09T15:25:00+00:00` | `2025-05-09T15:35:00+00:00` | `` |
| `2025-05-09` | `option_exit_quotes` | `2025-05-09_exit_check_1200` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-09T15:55:00+00:00` | `2025-05-09T16:05:00+00:00` | `` |
| `2025-05-09` | `option_exit_quotes` | `2025-05-09_exit_check_1230` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-09T16:25:00+00:00` | `2025-05-09T16:35:00+00:00` | `` |
| `2025-05-09` | `option_exit_quotes` | `2025-05-09_exit_check_1300` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-09T16:55:00+00:00` | `2025-05-09T17:05:00+00:00` | `` |
| `2025-05-09` | `option_exit_quotes` | `2025-05-09_exit_check_1330` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-09T17:25:00+00:00` | `2025-05-09T17:35:00+00:00` | `` |
| `2025-05-09` | `option_exit_quotes` | `2025-05-09_exit_check_1400` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-09T17:55:00+00:00` | `2025-05-09T18:05:00+00:00` | `` |
| `2025-05-09` | `option_exit_quotes` | `2025-05-09_exit_check_1430` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-09T18:25:00+00:00` | `2025-05-09T18:35:00+00:00` | `` |
| `2025-05-09` | `option_exit_quotes` | `2025-05-09_exit_check_1500` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-09T18:55:00+00:00` | `2025-05-09T19:05:00+00:00` | `` |
| `2025-05-09` | `option_exit_quotes` | `2025-05-09_exit_check_1530` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-09T19:25:00+00:00` | `2025-05-09T19:35:00+00:00` | `` |
| `2025-05-09` | `option_exit_quotes` | `2025-05-09_forced_close_1545` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-09T19:40:00+00:00` | `2025-05-09T19:50:00+00:00` | `` |
| `2025-05-09` | `spy_underlying_bars` | `2025-05-09_spy_underlying_full_session` | `EQUS.MINI` | `ohlcv-1m` | `2025-05-09T13:30:00+00:00` | `2025-05-09T20:00:00+00:00` | `0.000244` |
| `2025-05-12` | `option_entry_quote` | `2025-05-12_entry_0935` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-12T13:30:00+00:00` | `2025-05-12T13:40:00+00:00` | `` |
| `2025-05-12` | `option_exit_quotes` | `2025-05-12_entry_check_1000` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-12T13:55:00+00:00` | `2025-05-12T14:05:00+00:00` | `` |
| `2025-05-12` | `option_exit_quotes` | `2025-05-12_exit_check_1030` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-12T14:25:00+00:00` | `2025-05-12T14:35:00+00:00` | `` |
| `2025-05-12` | `option_exit_quotes` | `2025-05-12_exit_check_1100` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-12T14:55:00+00:00` | `2025-05-12T15:05:00+00:00` | `` |
| `2025-05-12` | `option_exit_quotes` | `2025-05-12_exit_check_1130` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-12T15:25:00+00:00` | `2025-05-12T15:35:00+00:00` | `` |
| `2025-05-12` | `option_exit_quotes` | `2025-05-12_exit_check_1200` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-12T15:55:00+00:00` | `2025-05-12T16:05:00+00:00` | `` |
| `2025-05-12` | `option_exit_quotes` | `2025-05-12_exit_check_1230` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-12T16:25:00+00:00` | `2025-05-12T16:35:00+00:00` | `` |
| `2025-05-12` | `option_exit_quotes` | `2025-05-12_exit_check_1300` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-12T16:55:00+00:00` | `2025-05-12T17:05:00+00:00` | `` |
| `2025-05-12` | `option_exit_quotes` | `2025-05-12_exit_check_1330` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-12T17:25:00+00:00` | `2025-05-12T17:35:00+00:00` | `` |
| `2025-05-12` | `option_exit_quotes` | `2025-05-12_exit_check_1400` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-12T17:55:00+00:00` | `2025-05-12T18:05:00+00:00` | `` |
| `2025-05-12` | `option_exit_quotes` | `2025-05-12_exit_check_1430` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-12T18:25:00+00:00` | `2025-05-12T18:35:00+00:00` | `` |
| `2025-05-12` | `option_exit_quotes` | `2025-05-12_exit_check_1500` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-12T18:55:00+00:00` | `2025-05-12T19:05:00+00:00` | `` |
| `2025-05-12` | `option_exit_quotes` | `2025-05-12_exit_check_1530` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-12T19:25:00+00:00` | `2025-05-12T19:35:00+00:00` | `` |
| `2025-05-12` | `option_exit_quotes` | `2025-05-12_forced_close_1545` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-12T19:40:00+00:00` | `2025-05-12T19:50:00+00:00` | `` |
| `2025-05-12` | `spy_underlying_bars` | `2025-05-12_spy_underlying_full_session` | `EQUS.MINI` | `ohlcv-1m` | `2025-05-12T13:30:00+00:00` | `2025-05-12T20:00:00+00:00` | `0.000244` |
| `2025-05-13` | `option_entry_quote` | `2025-05-13_entry_0935` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-13T13:30:00+00:00` | `2025-05-13T13:40:00+00:00` | `` |
| `2025-05-13` | `option_exit_quotes` | `2025-05-13_entry_check_1000` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-13T13:55:00+00:00` | `2025-05-13T14:05:00+00:00` | `` |
| `2025-05-13` | `option_exit_quotes` | `2025-05-13_exit_check_1030` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-13T14:25:00+00:00` | `2025-05-13T14:35:00+00:00` | `` |
| `2025-05-13` | `option_exit_quotes` | `2025-05-13_exit_check_1100` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-13T14:55:00+00:00` | `2025-05-13T15:05:00+00:00` | `` |
| `2025-05-13` | `option_exit_quotes` | `2025-05-13_exit_check_1130` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-13T15:25:00+00:00` | `2025-05-13T15:35:00+00:00` | `` |
| `2025-05-13` | `option_exit_quotes` | `2025-05-13_exit_check_1200` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-13T15:55:00+00:00` | `2025-05-13T16:05:00+00:00` | `` |
| `2025-05-13` | `option_exit_quotes` | `2025-05-13_exit_check_1230` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-13T16:25:00+00:00` | `2025-05-13T16:35:00+00:00` | `` |
| `2025-05-13` | `option_exit_quotes` | `2025-05-13_exit_check_1300` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-13T16:55:00+00:00` | `2025-05-13T17:05:00+00:00` | `` |
| `2025-05-13` | `option_exit_quotes` | `2025-05-13_exit_check_1330` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-13T17:25:00+00:00` | `2025-05-13T17:35:00+00:00` | `` |
| `2025-05-13` | `option_exit_quotes` | `2025-05-13_exit_check_1400` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-13T17:55:00+00:00` | `2025-05-13T18:05:00+00:00` | `` |
| `2025-05-13` | `option_exit_quotes` | `2025-05-13_exit_check_1430` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-13T18:25:00+00:00` | `2025-05-13T18:35:00+00:00` | `` |
| `2025-05-13` | `option_exit_quotes` | `2025-05-13_exit_check_1500` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-13T18:55:00+00:00` | `2025-05-13T19:05:00+00:00` | `` |
| `2025-05-13` | `option_exit_quotes` | `2025-05-13_exit_check_1530` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-13T19:25:00+00:00` | `2025-05-13T19:35:00+00:00` | `` |
| `2025-05-13` | `option_exit_quotes` | `2025-05-13_forced_close_1545` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-13T19:40:00+00:00` | `2025-05-13T19:50:00+00:00` | `` |
| `2025-05-13` | `spy_underlying_bars` | `2025-05-13_spy_underlying_full_session` | `EQUS.MINI` | `ohlcv-1m` | `2025-05-13T13:30:00+00:00` | `2025-05-13T20:00:00+00:00` | `0.000244` |
| `2025-05-14` | `option_entry_quote` | `2025-05-14_entry_0935` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-14T13:30:00+00:00` | `2025-05-14T13:40:00+00:00` | `` |
| `2025-05-14` | `option_exit_quotes` | `2025-05-14_entry_check_1000` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-14T13:55:00+00:00` | `2025-05-14T14:05:00+00:00` | `` |
| `2025-05-14` | `option_exit_quotes` | `2025-05-14_exit_check_1030` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-14T14:25:00+00:00` | `2025-05-14T14:35:00+00:00` | `` |
| `2025-05-14` | `option_exit_quotes` | `2025-05-14_exit_check_1100` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-14T14:55:00+00:00` | `2025-05-14T15:05:00+00:00` | `` |
| `2025-05-14` | `option_exit_quotes` | `2025-05-14_exit_check_1130` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-14T15:25:00+00:00` | `2025-05-14T15:35:00+00:00` | `` |
| `2025-05-14` | `option_exit_quotes` | `2025-05-14_exit_check_1200` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-14T15:55:00+00:00` | `2025-05-14T16:05:00+00:00` | `` |
| `2025-05-14` | `option_exit_quotes` | `2025-05-14_exit_check_1230` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-14T16:25:00+00:00` | `2025-05-14T16:35:00+00:00` | `` |
| `2025-05-14` | `option_exit_quotes` | `2025-05-14_exit_check_1300` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-14T16:55:00+00:00` | `2025-05-14T17:05:00+00:00` | `` |
| `2025-05-14` | `option_exit_quotes` | `2025-05-14_exit_check_1330` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-14T17:25:00+00:00` | `2025-05-14T17:35:00+00:00` | `` |
| `2025-05-14` | `option_exit_quotes` | `2025-05-14_exit_check_1400` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-14T17:55:00+00:00` | `2025-05-14T18:05:00+00:00` | `` |
| `2025-05-14` | `option_exit_quotes` | `2025-05-14_exit_check_1430` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-14T18:25:00+00:00` | `2025-05-14T18:35:00+00:00` | `` |
| `2025-05-14` | `option_exit_quotes` | `2025-05-14_exit_check_1500` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-14T18:55:00+00:00` | `2025-05-14T19:05:00+00:00` | `` |
| `2025-05-14` | `option_exit_quotes` | `2025-05-14_exit_check_1530` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-14T19:25:00+00:00` | `2025-05-14T19:35:00+00:00` | `` |
| `2025-05-14` | `option_exit_quotes` | `2025-05-14_forced_close_1545` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-14T19:40:00+00:00` | `2025-05-14T19:50:00+00:00` | `` |
| `2025-05-14` | `spy_underlying_bars` | `2025-05-14_spy_underlying_full_session` | `EQUS.MINI` | `ohlcv-1m` | `2025-05-14T13:30:00+00:00` | `2025-05-14T20:00:00+00:00` | `0.000244` |
| `2025-05-15` | `option_entry_quote` | `2025-05-15_entry_0935` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-15T13:30:00+00:00` | `2025-05-15T13:40:00+00:00` | `` |
| `2025-05-15` | `option_exit_quotes` | `2025-05-15_entry_check_1000` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-15T13:55:00+00:00` | `2025-05-15T14:05:00+00:00` | `` |
| `2025-05-15` | `option_exit_quotes` | `2025-05-15_exit_check_1030` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-15T14:25:00+00:00` | `2025-05-15T14:35:00+00:00` | `` |
| `2025-05-15` | `option_exit_quotes` | `2025-05-15_exit_check_1100` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-15T14:55:00+00:00` | `2025-05-15T15:05:00+00:00` | `` |
| `2025-05-15` | `option_exit_quotes` | `2025-05-15_exit_check_1130` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-15T15:25:00+00:00` | `2025-05-15T15:35:00+00:00` | `` |
| `2025-05-15` | `option_exit_quotes` | `2025-05-15_exit_check_1200` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-15T15:55:00+00:00` | `2025-05-15T16:05:00+00:00` | `` |
| `2025-05-15` | `option_exit_quotes` | `2025-05-15_exit_check_1230` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-15T16:25:00+00:00` | `2025-05-15T16:35:00+00:00` | `` |
| `2025-05-15` | `option_exit_quotes` | `2025-05-15_exit_check_1300` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-15T16:55:00+00:00` | `2025-05-15T17:05:00+00:00` | `` |
| `2025-05-15` | `option_exit_quotes` | `2025-05-15_exit_check_1330` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-15T17:25:00+00:00` | `2025-05-15T17:35:00+00:00` | `` |
| `2025-05-15` | `option_exit_quotes` | `2025-05-15_exit_check_1400` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-15T17:55:00+00:00` | `2025-05-15T18:05:00+00:00` | `` |
| `2025-05-15` | `option_exit_quotes` | `2025-05-15_exit_check_1430` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-15T18:25:00+00:00` | `2025-05-15T18:35:00+00:00` | `` |
| `2025-05-15` | `option_exit_quotes` | `2025-05-15_exit_check_1500` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-15T18:55:00+00:00` | `2025-05-15T19:05:00+00:00` | `` |
| `2025-05-15` | `option_exit_quotes` | `2025-05-15_exit_check_1530` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-15T19:25:00+00:00` | `2025-05-15T19:35:00+00:00` | `` |
| `2025-05-15` | `option_exit_quotes` | `2025-05-15_forced_close_1545` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-15T19:40:00+00:00` | `2025-05-15T19:50:00+00:00` | `` |
| `2025-05-15` | `spy_underlying_bars` | `2025-05-15_spy_underlying_full_session` | `EQUS.MINI` | `ohlcv-1m` | `2025-05-15T13:30:00+00:00` | `2025-05-15T20:00:00+00:00` | `0.000244` |
| `2025-05-16` | `option_entry_quote` | `2025-05-16_entry_0935` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-16T13:30:00+00:00` | `2025-05-16T13:40:00+00:00` | `` |
| `2025-05-16` | `option_exit_quotes` | `2025-05-16_entry_check_1000` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-16T13:55:00+00:00` | `2025-05-16T14:05:00+00:00` | `` |
| `2025-05-16` | `option_exit_quotes` | `2025-05-16_exit_check_1030` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-16T14:25:00+00:00` | `2025-05-16T14:35:00+00:00` | `` |
| `2025-05-16` | `option_exit_quotes` | `2025-05-16_exit_check_1100` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-16T14:55:00+00:00` | `2025-05-16T15:05:00+00:00` | `` |
| `2025-05-16` | `option_exit_quotes` | `2025-05-16_exit_check_1130` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-16T15:25:00+00:00` | `2025-05-16T15:35:00+00:00` | `` |
| `2025-05-16` | `option_exit_quotes` | `2025-05-16_exit_check_1200` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-16T15:55:00+00:00` | `2025-05-16T16:05:00+00:00` | `` |
| `2025-05-16` | `option_exit_quotes` | `2025-05-16_exit_check_1230` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-16T16:25:00+00:00` | `2025-05-16T16:35:00+00:00` | `` |
| `2025-05-16` | `option_exit_quotes` | `2025-05-16_exit_check_1300` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-16T16:55:00+00:00` | `2025-05-16T17:05:00+00:00` | `` |
| `2025-05-16` | `option_exit_quotes` | `2025-05-16_exit_check_1330` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-16T17:25:00+00:00` | `2025-05-16T17:35:00+00:00` | `` |
| `2025-05-16` | `option_exit_quotes` | `2025-05-16_exit_check_1400` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-16T17:55:00+00:00` | `2025-05-16T18:05:00+00:00` | `` |
| `2025-05-16` | `option_exit_quotes` | `2025-05-16_exit_check_1430` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-16T18:25:00+00:00` | `2025-05-16T18:35:00+00:00` | `` |
| `2025-05-16` | `option_exit_quotes` | `2025-05-16_exit_check_1500` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-16T18:55:00+00:00` | `2025-05-16T19:05:00+00:00` | `` |
| `2025-05-16` | `option_exit_quotes` | `2025-05-16_exit_check_1530` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-16T19:25:00+00:00` | `2025-05-16T19:35:00+00:00` | `` |
| `2025-05-16` | `option_exit_quotes` | `2025-05-16_forced_close_1545` | `OPRA.PILLAR` | `cbbo-1m` | `2025-05-16T19:40:00+00:00` | `2025-05-16T19:50:00+00:00` | `` |
| `2025-05-16` | `spy_underlying_bars` | `2025-05-16_spy_underlying_full_session` | `EQUS.MINI` | `ohlcv-1m` | `2025-05-16T13:30:00+00:00` | `2025-05-16T20:00:00+00:00` | `0.000244` |

## Guardrail

This is a metadata cost gate only. It does not download Databento data, add validation PnL days, approve exact replay, or approve paper trading.
