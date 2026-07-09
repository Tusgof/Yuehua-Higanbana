# H-A2 Normal/Control Import Diagnostic

- Status: `complete`
- Conclusion: `ยังสรุปไม่ได้`
- Evidence tier: `E1`
- Decision: `normal_control_candidate_trade_data_ready_for_separate_preregistered_exact_replay`

## Import Summary

- Raw files: `20`
- Total raw bytes: `741157996`
- SPY dates: `10`
- SPY bar rows: `3900`
- OPRA dates: `10`
- OPRA quote rows: `35284142`
- 0DTE valid-mid quote rows: `557254`

## Locked Signal And Availability

- Clean macro/VIX dates: `7`
- Locked signal true dates: `1`
- Candidate trade data ready dates: `1`
- Candidate trade data blocked dates: `0`
- No-candidate dates: `9`
- Ready dates: `2025-02-11`

## Per-Date Results

| Date | Clean macro/VIX | Proxy signal | Followthrough | Locked signal | Availability |
|---|---:|---|---:|---:|---|
| 2025-02-03 | `True` | `none` | `0.0` | `False` | `no_candidate_trade_signal` |
| 2025-02-04 | `False` | `none` | `0.0` | `False` | `no_candidate_trade_signal` |
| 2025-02-05 | `True` | `none` | `0.0` | `False` | `no_candidate_trade_signal` |
| 2025-02-06 | `True` | `none` | `0.0` | `False` | `no_candidate_trade_signal` |
| 2025-02-07 | `False` | `none` | `0.0` | `False` | `no_candidate_trade_signal` |
| 2025-02-10 | `True` | `put` | `-0.002536` | `False` | `no_candidate_trade_signal` |
| 2025-02-11 | `True` | `call` | `0.002336` | `True` | `candidate_trade_data_ready` |
| 2025-02-12 | `False` | `none` | `0.0` | `False` | `no_candidate_trade_signal` |
| 2025-02-13 | `True` | `none` | `0.0` | `False` | `no_candidate_trade_signal` |
| 2025-02-14 | `True` | `put` | `6.6e-05` | `False` | `no_candidate_trade_signal` |

## Guardrails

- No network, additional paid data, IBKR request, LLM call, GDELT retry, exact replay, or strategy PnL was used.
- Threshold `0.001` and the 09:35-only H-A2 rule were preserved.
- This diagnostic does not approve paper trading, operational validation, real-money trading, or E2 evidence.

## Next Safe Action

Pre-register a separate bounded exact-replay diagnostic for the normal/control candidate dates only before computing candidate-trade PnL or making any E2 claim.
