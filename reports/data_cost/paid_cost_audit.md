# Paid Cost Audit

- Status: `pass`
- Stop threshold: `$125.0`
- Known committed estimated cost: `$169.90613`
- Cost guard basis: `user_reported_actual_usage`
- Cost guard used: `$105.0`
- Remaining before stop: `$20.0`

## Cost Guard Reconciliation

- Actual-usage basis status: `pass`; used `$105.0`; remaining `$20.0`
- Conservative known-estimate basis status: `blocked`; used `$169.90613`; remaining `$-44.90613`
- Estimated-only total not yet committed: `$27.899065`
- Single estimated-only items that would reach stop if committed: `15`

| Item | Cost | Projected Conservative Total | Source |
|:--|--:|--:|:--|
| `databento_cost_h_a2_2022_10_stress` | `$10.52248` | `$180.42861` | `reports\data_cost\databento_cost_h_a2_2022_10_stress.json` |
| `databento_cost_h_a2_2022_09_stress` | `$10.226392` | `$180.132522` | `reports\data_cost\databento_cost_h_a2_2022_09_stress.json` |
| `databento_cost_insample_2023_09_intraday_exit_30m_chunk2` | `$1.543901` | `$171.450031` | `reports\data_cost\databento_cost_insample_2023_09_intraday_exit_30m_chunk2.json` |
| `databento_cost_insample_2023_09_intraday_exit_30m_chunk3` | `$1.526606` | `$171.432736` | `reports\data_cost\databento_cost_insample_2023_09_intraday_exit_30m_chunk3.json` |
| `databento_cost_insample_2023_09_intraday_exit_30m_chunk1` | `$1.460004` | `$171.366134` | `reports\data_cost\databento_cost_insample_2023_09_intraday_exit_30m_chunk1.json` |
| `databento_cost_2024_02_13_intraday_exit_30m` | `$0.358536` | `$170.264666` | `reports\data_cost\databento_cost_2024_02_13_intraday_exit_30m.json` |
| `databento_cost_insample_2023_09_intraday_exit_30m_2023_09_29` | `$0.338082` | `$170.244212` | `reports\data_cost\databento_cost_insample_2023_09_intraday_exit_30m_2023_09_29.json` |
| `databento_cost_insample_2023_12_intraday_exit_30m_sample` | `$0.337333` | `$170.243463` | `reports\data_cost\databento_cost_insample_2023_12_intraday_exit_30m_sample.json` |
| `databento_cost_insample_2023_09_intraday_exit_30m_2023_09_28` | `$0.32245` | `$170.22858` | `reports\data_cost\databento_cost_insample_2023_09_intraday_exit_30m_2023_09_28.json` |
| `databento_cost_insample_2023_09_intraday_exit_30m_2023_09_27` | `$0.316463` | `$170.222593` | `reports\data_cost\databento_cost_insample_2023_09_intraday_exit_30m_2023_09_27.json` |
| `databento_cost_insample_2023_09_intraday_exit_30m_2023_09_25` | `$0.312721` | `$170.218851` | `reports\data_cost\databento_cost_insample_2023_09_intraday_exit_30m_2023_09_25.json` |
| `databento_cost_insample_2023_09_intraday_exit_30m_2023_09_26` | `$0.307899` | `$170.214029` | `reports\data_cost\databento_cost_insample_2023_09_intraday_exit_30m_2023_09_26.json` |
| `databento_cost_insample_2023_09_intraday_exit_30m_sample` | `$0.301829` | `$170.207959` | `reports\data_cost\databento_cost_insample_2023_09_intraday_exit_30m_sample.json` |
| `spy_bars:oos_2024_q4_completion` | `$0.022813` | `$169.928943` | `reports\data_cost\databento_spy_bars_plan_oos_2024_q4_completion.json` |
| `spy_bars:2024_09_chunk4` | `$0.001556` | `$169.907686` | `reports\data_cost\databento_spy_bars_plan_2024_09_chunk4.json` |

## Budget Policy

- Cap extension method: `real_payment_on_existing_databento_account_only`
- Prohibited: `multi_account_signup_credit_harvesting`
- Notes: The user may extend the active cap only by real payment on the existing Databento account. Opening extra accounts or using other identities to harvest duplicate signup credits is prohibited.

## User-Reported Actual Usage

- Actual usage: `$105.0`
- Reported at UTC: `2026-07-03T01:43:53Z`
- Source: `user_reported_databento_account_usage`
- Notes: User reported current total Databento usage in the provider account. Stop threshold remains $125 until topped up by real payment on the existing Databento account only. Multi-account signup-credit harvesting is prohibited. Keep estimated committed cost separately for audit traceability, but use user-reported actual usage as the controlling guard for already-scoped SPY-only work.

## Committed Databento Items

| Item | Cost | Source |
|:--|--:|:--|
| `insample_2023_03:insample_2023_03_intraday_exit_30m_chunk1` | `$0.995454` | `reports\data_cost\databento_download_result_insample_2023_03_intraday_exit_30m_chunk1.json` |
| `insample_2023_03:insample_2023_03_intraday_exit_30m_chunk2` | `$1.658646` | `reports\data_cost\databento_download_result_insample_2023_03_intraday_exit_30m_chunk2.json` |
| `insample_2023_03:insample_2023_03_intraday_exit_30m_chunk3` | `$1.691406` | `reports\data_cost\databento_download_result_insample_2023_03_intraday_exit_30m_chunk3.json` |
| `insample_2023_03:insample_2023_03_intraday_exit_30m_chunk4` | `$1.637277` | `reports\data_cost\databento_download_result_insample_2023_03_intraday_exit_30m_chunk4.json` |
| `insample_2023_03:insample_2023_03_intraday_exit_30m_chunk5` | `$1.603435` | `reports\data_cost\databento_download_result_insample_2023_03_intraday_exit_30m_chunk5.json` |
| `insample_2023_04:insample_2023_04_intraday_exit_30m_chunk1` | `$1.262776` | `reports\data_cost\databento_download_result_insample_2023_04_intraday_exit_30m_chunk1.json` |
| `insample_2023_04:insample_2023_04_intraday_exit_30m_chunk2` | `$1.625636` | `reports\data_cost\databento_download_result_insample_2023_04_intraday_exit_30m_chunk2.json` |
| `insample_2023_04:insample_2023_04_intraday_exit_30m_chunk3` | `$1.648335` | `reports\data_cost\databento_download_result_insample_2023_04_intraday_exit_30m_chunk3.json` |
| `insample_2023_04:insample_2023_04_intraday_exit_30m_chunk4` | `$1.646423` | `reports\data_cost\databento_download_result_insample_2023_04_intraday_exit_30m_chunk4.json` |
| `insample_2023_05:insample_2023_05_intraday_exit_30m_chunk1` | `$1.664383` | `reports\data_cost\databento_download_result_insample_2023_05_intraday_exit_30m_chunk1.json` |
| `insample_2023_05:insample_2023_05_intraday_exit_30m_chunk2` | `$1.566684` | `reports\data_cost\databento_download_result_insample_2023_05_intraday_exit_30m_chunk2.json` |
| `insample_2023_05:insample_2023_05_intraday_exit_30m_chunk3` | `$1.568097` | `reports\data_cost\databento_download_result_insample_2023_05_intraday_exit_30m_chunk3.json` |
| `insample_2023_05:insample_2023_05_intraday_exit_30m_chunk4` | `$1.559283` | `reports\data_cost\databento_download_result_insample_2023_05_intraday_exit_30m_chunk4.json` |
| `insample_2023_05:insample_2023_05_intraday_exit_30m_chunk5` | `$0.629692` | `reports\data_cost\databento_download_result_insample_2023_05_intraday_exit_30m_chunk5.json` |
| `insample_2023_06:insample_2023_06_intraday_exit_30m_chunk1` | `$0.660116` | `reports\data_cost\databento_download_result_insample_2023_06_intraday_exit_30m_chunk1.json` |
| `insample_2023_06:insample_2023_06_intraday_exit_30m_chunk2` | `$1.636944` | `reports\data_cost\databento_download_result_insample_2023_06_intraday_exit_30m_chunk2.json` |
| `insample_2023_06:insample_2023_06_intraday_exit_30m_chunk3` | `$1.618402` | `reports\data_cost\databento_download_result_insample_2023_06_intraday_exit_30m_chunk3.json` |
| `insample_2023_06:insample_2023_06_intraday_exit_30m_chunk4` | `$1.131983` | `reports\data_cost\databento_download_result_insample_2023_06_intraday_exit_30m_chunk4.json` |
| `insample_2023_06:insample_2023_06_intraday_exit_30m_chunk5` | `$1.440132` | `reports\data_cost\databento_download_result_insample_2023_06_intraday_exit_30m_chunk5.json` |
| `insample_2023_07:insample_2023_07_intraday_exit_30m_chunk1` | `$1.172644` | `reports\data_cost\databento_download_result_insample_2023_07_intraday_exit_30m_chunk1.json` |
| `insample_2023_07:insample_2023_07_intraday_exit_30m_chunk2` | `$1.639439` | `reports\data_cost\databento_download_result_insample_2023_07_intraday_exit_30m_chunk2.json` |
| `insample_2023_07:insample_2023_07_intraday_exit_30m_chunk3` | `$1.668873` | `reports\data_cost\databento_download_result_insample_2023_07_intraday_exit_30m_chunk3.json` |
| `insample_2023_07:insample_2023_07_intraday_exit_30m_chunk4` | `$1.56236` | `reports\data_cost\databento_download_result_insample_2023_07_intraday_exit_30m_chunk4.json` |
| `insample_2023_07:insample_2023_07_intraday_exit_30m_chunk5` | `$0.320454` | `reports\data_cost\databento_download_result_insample_2023_07_intraday_exit_30m_chunk5.json` |
| `insample_2023_08:insample_2023_08_intraday_exit_30m_chunk1` | `$1.318652` | `reports\data_cost\databento_download_result_insample_2023_08_intraday_exit_30m_chunk1.json` |
| `insample_2023_08:insample_2023_08_intraday_exit_30m_chunk2` | `$1.652659` | `reports\data_cost\databento_download_result_insample_2023_08_intraday_exit_30m_chunk2.json` |
| `insample_2023_08:insample_2023_08_intraday_exit_30m_chunk3` | `$1.610752` | `reports\data_cost\databento_download_result_insample_2023_08_intraday_exit_30m_chunk3.json` |
| `insample_2023_08:insample_2023_08_intraday_exit_30m_chunk4` | `$1.579655` | `reports\data_cost\databento_download_result_insample_2023_08_intraday_exit_30m_chunk4.json` |
| `insample_2023_08:insample_2023_08_intraday_exit_30m_chunk5` | `$1.22669` | `reports\data_cost\databento_download_result_insample_2023_08_intraday_exit_30m_chunk5.json` |
| `insample_2023_09:insample_2023_09_intraday_exit_30m` | `$6.128126` | `reports\data_cost\databento_download_result_insample_2023_09_intraday_exit_30m.json` |
| `insample_2023_10:insample_2023_10_intraday_exit_30m` | `$7.271917` | `reports\data_cost\databento_download_result_insample_2023_10_intraday_exit_30m.json` |
| `insample_2023_11:insample_2023_11_intraday_exit_30m` | `$6.722094` | `reports\data_cost\databento_download_result_insample_2023_11_intraday_exit_30m.json` |
| `insample_2023_12:insample_2023_12_intraday_exit_30m` | `$6.601407` | `reports\data_cost\databento_download_result_insample_2023_12_intraday_exit_30m.json` |
| `one_month_pilot:databento_download_result` | `$1.483808` | `reports\data_cost\databento_download_result.json` |
| `oos_2024_03_intraday_exit_30m_chunk1:oos_2024_03_intraday_exit_30m_chunk1` | `$0.379074` | `reports\data_cost\databento_download_result_oos_2024_03_intraday_exit_30m_chunk1.json` |
| `oos_2024_03_intraday_exit_30m_chunk2:oos_2024_03_intraday_exit_30m_chunk2` | `$1.817626` | `reports\data_cost\databento_download_result_oos_2024_03_intraday_exit_30m_chunk2.json` |
| `oos_2024_03_intraday_exit_30m_chunk3:oos_2024_03_intraday_exit_30m_chunk3` | `$1.794427` | `reports\data_cost\databento_download_result_oos_2024_03_intraday_exit_30m_chunk3.json` |
| `oos_2024_03_intraday_exit_30m_chunk4:oos_2024_03_intraday_exit_30m_chunk4` | `$1.710115` | `reports\data_cost\databento_download_result_oos_2024_03_intraday_exit_30m_chunk4.json` |
| `oos_2024_03_intraday_exit_30m_chunk5:oos_2024_03_intraday_exit_30m_chunk5` | `$1.400054` | `reports\data_cost\databento_download_result_oos_2024_03_intraday_exit_30m_chunk5.json` |
| `oos_2024_04_intraday_exit_30m_chunk1:oos_2024_04_intraday_exit_30m_chunk1` | `$1.786029` | `reports\data_cost\databento_download_result_oos_2024_04_intraday_exit_30m_chunk1.json` |
| `oos_2024_04_intraday_exit_30m_chunk2:oos_2024_04_intraday_exit_30m_chunk2` | `$1.807738` | `reports\data_cost\databento_download_result_oos_2024_04_intraday_exit_30m_chunk2.json` |
| `oos_2024_04_intraday_exit_30m_chunk3:oos_2024_04_intraday_exit_30m_chunk3` | `$1.680015` | `reports\data_cost\databento_download_result_oos_2024_04_intraday_exit_30m_chunk3.json` |
| `oos_2024_04_intraday_exit_30m_chunk4:oos_2024_04_intraday_exit_30m_chunk4` | `$1.563148` | `reports\data_cost\databento_download_result_oos_2024_04_intraday_exit_30m_chunk4.json` |
| `oos_2024_04_intraday_exit_30m_chunk5:oos_2024_04_intraday_exit_30m_chunk5` | `$0.643736` | `reports\data_cost\databento_download_result_oos_2024_04_intraday_exit_30m_chunk5.json` |
| `oos_2024_05_intraday_exit_30m_chunk1:oos_2024_05_intraday_exit_30m_chunk1` | `$0.943735` | `reports\data_cost\databento_download_result_oos_2024_05_intraday_exit_30m_chunk1.json` |
| `oos_2024_05_intraday_exit_30m_chunk2:oos_2024_05_intraday_exit_30m_chunk2` | `$1.707288` | `reports\data_cost\databento_download_result_oos_2024_05_intraday_exit_30m_chunk2.json` |
| `oos_2024_05_intraday_exit_30m_chunk3:oos_2024_05_intraday_exit_30m_chunk3` | `$1.870508` | `reports\data_cost\databento_download_result_oos_2024_05_intraday_exit_30m_chunk3.json` |
| `oos_2024_05_intraday_exit_30m_chunk4:oos_2024_05_intraday_exit_30m_chunk4` | `$1.825525` | `reports\data_cost\databento_download_result_oos_2024_05_intraday_exit_30m_chunk4.json` |
| `oos_2024_05_intraday_exit_30m_chunk5:oos_2024_05_intraday_exit_30m_chunk5` | `$1.501495` | `reports\data_cost\databento_download_result_oos_2024_05_intraday_exit_30m_chunk5.json` |
| `oos_2024_06_intraday_exit_30m_chunk1:oos_2024_06_intraday_exit_30m_chunk1` | `$1.901772` | `reports\data_cost\databento_download_result_oos_2024_06_intraday_exit_30m_chunk1.json` |
| `oos_2024_06_intraday_exit_30m_chunk2:oos_2024_06_intraday_exit_30m_chunk2` | `$1.864348` | `reports\data_cost\databento_download_result_oos_2024_06_intraday_exit_30m_chunk2.json` |
| `oos_2024_06_intraday_exit_30m_chunk3:oos_2024_06_intraday_exit_30m_chunk3` | `$1.450525` | `reports\data_cost\databento_download_result_oos_2024_06_intraday_exit_30m_chunk3.json` |
| `oos_2024_06_intraday_exit_30m_chunk4:oos_2024_06_intraday_exit_30m_chunk4` | `$1.875331` | `reports\data_cost\databento_download_result_oos_2024_06_intraday_exit_30m_chunk4.json` |
| `oos_2024_07_intraday_exit_30m_chunk1:oos_2024_07_intraday_exit_30m_chunk1` | `$1.302408` | `reports\data_cost\databento_download_result_oos_2024_07_intraday_exit_30m_chunk1.json` |
| `oos_2024_07_intraday_exit_30m_chunk2:oos_2024_07_intraday_exit_30m_chunk2` | `$1.946922` | `reports\data_cost\databento_download_result_oos_2024_07_intraday_exit_30m_chunk2.json` |
| `oos_2024_07_intraday_exit_30m_chunk3:oos_2024_07_intraday_exit_30m_chunk3` | `$2.00895` | `reports\data_cost\databento_download_result_oos_2024_07_intraday_exit_30m_chunk3.json` |
| `oos_2024_07_intraday_exit_30m_chunk4:oos_2024_07_intraday_exit_30m_chunk4` | `$1.916323` | `reports\data_cost\databento_download_result_oos_2024_07_intraday_exit_30m_chunk4.json` |
| `oos_2024_07_intraday_exit_30m_chunk5:oos_2024_07_intraday_exit_30m_chunk5` | `$1.187776` | `reports\data_cost\databento_download_result_oos_2024_07_intraday_exit_30m_chunk5.json` |
| `oos_2024_08_intraday_exit_30m_chunk1:oos_2024_08_intraday_exit_30m_chunk1` | `$0.819428` | `reports\data_cost\databento_download_result_oos_2024_08_intraday_exit_30m_chunk1.json` |
| `oos_2024_08_intraday_exit_30m_chunk2:oos_2024_08_intraday_exit_30m_chunk2` | `$2.269455` | `reports\data_cost\databento_download_result_oos_2024_08_intraday_exit_30m_chunk2.json` |
| `oos_2024_08_intraday_exit_30m_chunk3:oos_2024_08_intraday_exit_30m_chunk3` | `$2.178158` | `reports\data_cost\databento_download_result_oos_2024_08_intraday_exit_30m_chunk3.json` |
| `oos_2024_08_intraday_exit_30m_chunk4:oos_2024_08_intraday_exit_30m_chunk4` | `$2.023917` | `reports\data_cost\databento_download_result_oos_2024_08_intraday_exit_30m_chunk4.json` |
| `oos_2024_08_intraday_exit_30m_chunk5:oos_2024_08_intraday_exit_30m_chunk5` | `$1.994316` | `reports\data_cost\databento_download_result_oos_2024_08_intraday_exit_30m_chunk5.json` |
| `oos_2024_09_intraday_exit_30m_chunk1:oos_2024_09_intraday_exit_30m_chunk1` | `$1.637443` | `reports\data_cost\databento_download_result_oos_2024_09_intraday_exit_30m_chunk1.json` |
| `oos_2024_09_intraday_exit_30m_chunk2:oos_2024_09_intraday_exit_30m_chunk2` | `$2.091257` | `reports\data_cost\databento_download_result_oos_2024_09_intraday_exit_30m_chunk2.json` |
| `oos_2024_09_intraday_exit_30m_chunk3:oos_2024_09_intraday_exit_30m_chunk3` | `$2.038967` | `reports\data_cost\databento_download_result_oos_2024_09_intraday_exit_30m_chunk3.json` |
| `oos_2024_10_intraday_exit_30m_daily_union:oos_2024_10_daily_union` | `$12.671726` | `reports\data_cost\databento_download_result_oos_2024_10_daily_union.json` |
| `oos_2024_11_intraday_exit_30m_daily_union:oos_2024_11_daily_union` | `$11.060765` | `reports\data_cost\databento_download_result_oos_2024_11_daily_union.json` |
| `oos_2024_12_intraday_exit_30m_daily_union:oos_2024_12_daily_union` | `$11.504703` | `reports\data_cost\databento_download_result_oos_2024_12_daily_union.json` |
| `oos_2024_2025:oos_2024_02` | `$1.502165` | `reports\data_cost\databento_download_result_oos_2024_02.json` |
| `oos_2024_2025:oos_2024_02_intraday_exit_30m` | `$7.103458` | `reports\data_cost\databento_download_result_oos_2024_02_intraday_exit_30m.json` |
| `oos_2024_sep_remainder_intraday_exit_30m_daily_union:oos_2024_09_remainder_daily_union` | `$3.419502` | `reports\data_cost\databento_download_result_oos_2024_09_remainder_daily_union.json` |
| `opra_statistics_oi_probe:2024-01-03_full_utc_day_statistics` | `$0.354911` | `reports\data_cost\databento_opra_statistics_oi_download_probe_2024_01_03.json` |
| `spy_bars:2023_03_partial` | `$0.00123` | `reports\data_cost\databento_spy_bars_download_result_2023_03_partial.json` |
| `spy_bars:2023_04` | `$0.006509` | `reports\data_cost\databento_spy_bars_download_result_2023_04.json` |
| `spy_bars:2023_05` | `$0.007579` | `reports\data_cost\databento_spy_bars_download_result_2023_05.json` |
| `spy_bars:2023_06` | `$0.007038` | `reports\data_cost\databento_spy_bars_download_result_2023_06.json` |
| `spy_bars:2023_07` | `$0.006463` | `reports\data_cost\databento_spy_bars_download_result_2023_07.json` |
| `spy_bars:2023_08` | `$0.007457` | `reports\data_cost\databento_spy_bars_download_result_2023_08.json` |
| `spy_bars:2023_09` | `$0.006397` | `reports\data_cost\databento_spy_bars_download_result_2023_09.json` |
| `spy_bars:2023_10` | `$0.007344` | `reports\data_cost\databento_spy_bars_download_result_2023_10.json` |
| `spy_bars:2023_11` | `$0.006615` | `reports\data_cost\databento_spy_bars_download_result_2023_11.json` |
| `spy_bars:2023_12` | `$0.006181` | `reports\data_cost\databento_spy_bars_download_result_2023_12.json` |
| `spy_bars:2024_02` | `$0.006416` | `reports\data_cost\databento_spy_bars_download_result_2024_02.json` |
| `spy_bars:2024_03` | `$0.006722` | `reports\data_cost\databento_spy_bars_download_result_2024_03.json` |
| `spy_bars:2024_04` | `$0.007934` | `reports\data_cost\databento_spy_bars_download_result_2024_04.json` |
| `spy_bars:2024_05` | `$0.007283` | `reports\data_cost\databento_spy_bars_download_result_2024_05.json` |
| `spy_bars:2024_06` | `$0.006182` | `reports\data_cost\databento_spy_bars_download_result_2024_06.json` |
| `spy_bars:2024_07_chunk3` | `$0.00159` | `reports\data_cost\databento_spy_bars_download_result_2024_07_chunk3.json` |
| `spy_bars:2024_07_chunk4` | `$0.001643` | `reports\data_cost\databento_spy_bars_download_result_2024_07_chunk4.json` |
| `spy_bars:2024_07_chunk5` | `$0.000964` | `reports\data_cost\databento_spy_bars_download_result_2024_07_chunk5.json` |
| `spy_bars:2024_07_partial` | `$0.002614` | `reports\data_cost\databento_spy_bars_download_result_2024_07_partial.json` |
| `spy_bars:2024_08_chunk1` | `$0.000666` | `reports\data_cost\databento_spy_bars_download_result_2024_08_chunk1.json` |
| `spy_bars:2024_08_chunk2` | `$0.001802` | `reports\data_cost\databento_spy_bars_download_result_2024_08_chunk2.json` |
| `spy_bars:2024_08_chunk3` | `$0.001691` | `reports\data_cost\databento_spy_bars_download_result_2024_08_chunk3.json` |
| `spy_bars:2024_08_chunk4` | `$0.001545` | `reports\data_cost\databento_spy_bars_download_result_2024_08_chunk4.json` |
| `spy_bars:2024_08_chunk5` | `$0.001631` | `reports\data_cost\databento_spy_bars_download_result_2024_08_chunk5.json` |
| `spy_bars:2024_09_chunk1` | `$0.001372` | `reports\data_cost\databento_spy_bars_download_result_2024_09_chunk1.json` |
| `spy_bars:2024_09_chunk2` | `$0.001653` | `reports\data_cost\databento_spy_bars_download_result_2024_09_chunk2.json` |
| `spy_bars:2024_09_chunk3` | `$0.001638` | `reports\data_cost\databento_spy_bars_download_result_2024_09_chunk3.json` |
| `spy_bars:2024_09_remainder` | `$0.001899` | `reports\data_cost\databento_spy_bars_download_result_2024_09_remainder.json` |
| `spy_bars:2024_10` | `$0.007643` | `reports\data_cost\databento_spy_bars_download_result_2024_10.json` |
| `spy_bars:2024_11` | `$0.006313` | `reports\data_cost\databento_spy_bars_download_result_2024_11.json` |
| `spy_bars:2024_12` | `$0.006782` | `reports\data_cost\databento_spy_bars_download_result_2024_12.json` |
| `spy_bars:default` | `$0.00672` | `reports\data_cost\databento_spy_bars_download_result.json` |
| `exp07_prompt_v13_smoke_summary` | `$0.000164` | `reports\experiments\exp07_prompt_v13_smoke_summary.json` |
| `exp07_prompt_v14_smoke_summary` | `$0.000777` | `reports\experiments\exp07_prompt_v14_smoke_summary.json` |

## Live Estimates Without Completed Download

| Item | Cost | Source |
|:--|--:|:--|
| `databento_cost_2024_02_13_intraday_exit_30m` | `$0.358536` | `reports\data_cost\databento_cost_2024_02_13_intraday_exit_30m.json` |
| `databento_cost_h_a2_2022_09_stress` | `$10.226392` | `reports\data_cost\databento_cost_h_a2_2022_09_stress.json` |
| `databento_cost_h_a2_2022_10_stress` | `$10.52248` | `reports\data_cost\databento_cost_h_a2_2022_10_stress.json` |
| `databento_cost_insample_2023_09_intraday_exit_30m_2023_09_25` | `$0.312721` | `reports\data_cost\databento_cost_insample_2023_09_intraday_exit_30m_2023_09_25.json` |
| `databento_cost_insample_2023_09_intraday_exit_30m_2023_09_26` | `$0.307899` | `reports\data_cost\databento_cost_insample_2023_09_intraday_exit_30m_2023_09_26.json` |
| `databento_cost_insample_2023_09_intraday_exit_30m_2023_09_27` | `$0.316463` | `reports\data_cost\databento_cost_insample_2023_09_intraday_exit_30m_2023_09_27.json` |
| `databento_cost_insample_2023_09_intraday_exit_30m_2023_09_28` | `$0.32245` | `reports\data_cost\databento_cost_insample_2023_09_intraday_exit_30m_2023_09_28.json` |
| `databento_cost_insample_2023_09_intraday_exit_30m_2023_09_29` | `$0.338082` | `reports\data_cost\databento_cost_insample_2023_09_intraday_exit_30m_2023_09_29.json` |
| `databento_cost_insample_2023_09_intraday_exit_30m_chunk1` | `$1.460004` | `reports\data_cost\databento_cost_insample_2023_09_intraday_exit_30m_chunk1.json` |
| `databento_cost_insample_2023_09_intraday_exit_30m_chunk2` | `$1.543901` | `reports\data_cost\databento_cost_insample_2023_09_intraday_exit_30m_chunk2.json` |
| `databento_cost_insample_2023_09_intraday_exit_30m_chunk3` | `$1.526606` | `reports\data_cost\databento_cost_insample_2023_09_intraday_exit_30m_chunk3.json` |
| `databento_cost_insample_2023_09_intraday_exit_30m_sample` | `$0.301829` | `reports\data_cost\databento_cost_insample_2023_09_intraday_exit_30m_sample.json` |
| `databento_cost_insample_2023_12_intraday_exit_30m_sample` | `$0.337333` | `reports\data_cost\databento_cost_insample_2023_12_intraday_exit_30m_sample.json` |
| `spy_bars:2024_09_chunk4` | `$0.001556` | `reports\data_cost\databento_spy_bars_plan_2024_09_chunk4.json` |
| `spy_bars:oos_2024_q4_completion` | `$0.022813` | `reports\data_cost\databento_spy_bars_plan_oos_2024_q4_completion.json` |

## Unpriced Items

- OpenRouter/DeepSeek: Live prompt summary does not record `openrouter_actual_cost_usd`; do not include guessed costs in the committed total. Source: `reports\experiments\exp07_prompt_summary.json`.
- OpenRouter/DeepSeek: Live prompt summary does not record `openrouter_actual_cost_usd`; do not include guessed costs in the committed total. Source: `reports\experiments\exp07_prompt_v10_summary.json`.
- OpenRouter/DeepSeek: Live prompt summary does not record `openrouter_actual_cost_usd`; do not include guessed costs in the committed total. Source: `reports\experiments\exp07_prompt_v11_summary.json`.
- OpenRouter/DeepSeek: Live prompt summary does not record `openrouter_actual_cost_usd`; do not include guessed costs in the committed total. Source: `reports\experiments\exp07_prompt_v12_summary.json`.
- OpenRouter/DeepSeek: Live prompt summary does not record `openrouter_actual_cost_usd`; do not include guessed costs in the committed total. Source: `reports\experiments\exp07_prompt_v2_summary.json`.
- OpenRouter/DeepSeek: Live prompt summary does not record `openrouter_actual_cost_usd`; do not include guessed costs in the committed total. Source: `reports\experiments\exp07_prompt_v3_summary.json`.
- OpenRouter/DeepSeek: Live prompt summary does not record `openrouter_actual_cost_usd`; do not include guessed costs in the committed total. Source: `reports\experiments\exp07_prompt_v4_summary.json`.
- OpenRouter/DeepSeek: Live prompt summary does not record `openrouter_actual_cost_usd`; do not include guessed costs in the committed total. Source: `reports\experiments\exp07_prompt_v5_summary.json`.
- OpenRouter/DeepSeek: Live prompt summary does not record `openrouter_actual_cost_usd`; do not include guessed costs in the committed total. Source: `reports\experiments\exp07_prompt_v6_summary.json`.
- OpenRouter/DeepSeek: Live prompt summary does not record `openrouter_actual_cost_usd`; do not include guessed costs in the committed total. Source: `reports\experiments\exp07_prompt_v7_summary.json`.
- OpenRouter/DeepSeek: Live prompt summary does not record `openrouter_actual_cost_usd`; do not include guessed costs in the committed total. Source: `reports\experiments\exp07_prompt_v8_summary.json`.
- OpenRouter/DeepSeek: Live prompt summary does not record `openrouter_actual_cost_usd`; do not include guessed costs in the committed total. Source: `reports\experiments\exp07_prompt_v9_summary.json`.
