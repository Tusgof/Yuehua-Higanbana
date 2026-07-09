# H-A2 Locked-Condition Signal Attribution Preregistration

## Status
- **Hypothesis**: H-A2
- **Evidence tier**: E0
- **Status**: preregistered
- **Created**: 2026-07-06
- **Controlling JSON**: `experiments/h_a2_locked_condition_signal_attribution_preregistration.json`

## Why This Exists
H-A2.26 kept threshold `0.001` locked and did not tune on OOS. That is good discipline, but it does not answer one important question:

Can this condition be used at the actual trade decision time, or is it using information that only becomes visible after the decision?

If the feature is only known after the intended entry, it cannot be called a deployable entry filter. It may still be useful as a mechanism clue or delayed-entry candidate, but that would require a separate preregistered test.

## Locked Rule
- Keep clean macro/VIX condition from prior H-A2 work.
- Keep opening-followthrough threshold `0.001`.
- Do not search another threshold.
- Do not add a new OOS-selected filter.
- Do not use this audit to approve paper trading, operational validation, real-money trading, or E2 evidence.

## Planned Checks
1. **Decision timestamp availability audit**: identify when the feature becomes knowable relative to the intended decision time.
2. **Entry rule classification**: classify the locked condition as deployable entry filter, delayed-entry candidate, or diagnostic proxy only.
3. **Outcome-proxy leakage audit**: check whether the same-session proxy overlaps too closely with the PnL outcome.
4. **Fixed-threshold reconciliation**: prove threshold `0.001` stays unchanged and no new filter is added.
5. **Hypothesis implication review**: state what H-A2 hypothesis remains valid to test next.

## Allowed Outcome
The future run may only support one of these decisions:
- prioritize exact replay later,
- draft a delayed-entry preregistration,
- park the current revised condition,
- or revise H-A2 again with a new preregistration.

It must not claim the edge is validated.

## Verification
Run:

```powershell
python scripts\validate_h_a2_locked_condition_signal_attribution_preregistration.py
python -m unittest tests.test_validate_h_a2_locked_condition_signal_attribution_preregistration
```
