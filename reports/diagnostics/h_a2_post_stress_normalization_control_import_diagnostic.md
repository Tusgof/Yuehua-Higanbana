# H-A2 Post-Stress Normalization/Control Import Diagnostic

- Status: `complete`
- Conclusion: `เธขเธฑเธเธชเธฃเธธเธเนเธกเนเนเธ”เน`
- Evidence tier: `E1`
- Decision: `post_stress_normalization_control_candidate_trade_data_ready_for_separate_preregistered_exact_replay`

## Import Summary

- Data quality notes: `Databento reported reduced-quality data for 2025-05-06 during download; the diagnostic must preserve this note and inspect the date explicitly.`
- Raw files: `20`
- Total raw bytes: `1057077119`
- SPY dates: `10`
- SPY bar rows: `3900`
- OPRA dates: `10`
- OPRA quote rows: `36296592`
- 0DTE valid-mid quote rows: `939097`

## Locked Signal And Availability

- Clean macro/VIX dates: `8`
- Locked signal true dates: `1`
- Candidate trade data ready dates: `1`
- Candidate trade data blocked dates: `0`
- No-candidate dates: `9`
- Ready dates: `2025-05-05`

## Per-Date Results

| Date | Clean macro/VIX | Proxy signal | Followthrough | Locked signal | Availability |
|---|---:|---|---:|---:|---|
| 2025-05-05 | `True` | `call` | `0.002238` | `True` | `candidate_trade_data_ready` |
| 2025-05-06 | `True` | `none` | `0.0` | `False` | `no_candidate_trade_signal` |
| 2025-05-07 | `False` | `none` | `0.0` | `False` | `no_candidate_trade_signal` |
| 2025-05-08 | `True` | `none` | `0.0` | `False` | `no_candidate_trade_signal` |
| 2025-05-09 | `True` | `call` | `-0.005306` | `False` | `no_candidate_trade_signal` |
| 2025-05-12 | `True` | `none` | `0.0` | `False` | `no_candidate_trade_signal` |
| 2025-05-13 | `False` | `call` | `0.007499` | `False` | `no_candidate_trade_signal` |
| 2025-05-14 | `True` | `none` | `0.0` | `False` | `no_candidate_trade_signal` |
| 2025-05-15 | `True` | `none` | `0.0` | `False` | `no_candidate_trade_signal` |
| 2025-05-16 | `True` | `none` | `0.0` | `False` | `no_candidate_trade_signal` |

## Guardrails

- No network, additional paid data, IBKR request, LLM call, GDELT retry, exact replay, or strategy PnL was used.
- Threshold `0.001` and the 09:35-only H-A2 rule were preserved.
- This diagnostic does not approve paper trading, operational validation, real-money trading, or E2 evidence.

## Next Safe Action

Pre-register a separate bounded exact-replay diagnostic for the post-stress normalization/control candidate dates only before computing candidate-trade PnL or making any E2 claim.
