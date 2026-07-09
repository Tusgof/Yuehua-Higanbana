# H-A2 Post-Stress Normalization/Control Exact Replay Preregistration

## Status
- **Hypothesis**: H-A2
- **Evidence tier**: E0
- **Status**: preregistered
- **Created**: 2026-07-08
- **Controlling JSON**: `experiments/h_a2_post_stress_normalization_control_exact_replay_preregistration.json`

## Why This Exists
H-A2.55 showed that the post-stress normalization/control data pack can be read locally and that the locked H-A2 signal has exactly one candidate-ready date: `2025-05-05`.

That result is still not edge evidence. It only says the data exists and the candidate signal can be reconstructed. This preregistration defines the next bounded exact-replay diagnostic before any candidate-trade PnL is computed.

## Scope
- Candidate date: `2025-05-05`
- Candidate direction: `call`
- Entry decision time: `09:35:00` ET
- Forced close time: `15:45:00` ET
- Threshold: `0.001`

No other dates are in scope. If the future runner cannot select the required option legs from the pre-registered rules, it must mark the replay blocked instead of choosing a new rule after seeing results.

## Replay Rules
- Strategy family: Sub-System A ORB directional debit vertical spread.
- Entry uses the candidate-date `09:35` bid/ask quote context.
- Forced close uses the `15:45` bid/ask quote context.
- Report `mid_pnl` and `implementable_pnl` separately.
- Include `$0.64` per leg fees.
- Use nearest discrete strike rounding.
- Do not use interpolation.
- Do not select strikes after seeing PnL.

## Forbidden
- No new data download.
- No threshold change.
- No new OOS-selected filter.
- No replay beyond `2025-05-05`.
- No IBKR request.
- No GDELT retry.
- No LLM call.
- No E2 claim.
- No paper trading, operational validation, or real-money approval.

## Verification
Run:

```powershell
python scripts\validate_h_a2_post_stress_normalization_control_exact_replay_preregistration.py
python -m unittest tests.test_validate_h_a2_post_stress_normalization_control_exact_replay_preregistration
```
