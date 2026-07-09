# H-A2 Revised Condition Robustness Preregistration

## Status
- **Hypothesis**: H-A2
- **Evidence tier**: E0
- **Status**: preregistered
- **Created**: 2026-07-06
- **Controlling JSON**: `experiments/h_a2_revised_condition_robustness_preregistration.json`

## Why This Exists
H-A2.24 improved local OOS residual-loss behavior after locking the opening-followthrough threshold at `0.001` using train data only. The result is interesting, but it keeps only 13 OOS trade days, so it is still under-sampled and cannot validate an edge.

This preregistration prevents the next step from quietly becoming OOS tuning. The robustness audit must keep threshold `0.001` fixed and ask whether the improvement is fragile, concentrated, or dependent on one or two extreme days.

## Locked Rule
- Keep the clean macro/VIX regime condition from prior H-A2 work.
- Keep opening-followthrough threshold `0.001`.
- Do not fit, search, widen, narrow, or replace the threshold in this audit.
- Do not add a new OOS-selected filter.

## Planned Checks
1. **Threshold provenance audit**: prove threshold `0.001` came from train-only selection and was not changed after OOS review.
2. **Big-day dependency check**: test whether the OOS improvement survives removing extreme trade days where sample size allows.
3. **Concentration fragility check**: inspect side, month, weekday, and VIX buckets.
4. **Skip-cost tradeoff check**: report how much opportunity the revised condition removes.
5. **Sample adequacy relabeling**: keep MinTRL/PSR and under-sampled/underpowered labels explicit.

## Allowed Outcome
The future run may support only one of these decisions:
- prioritize exact replay later when the 2022 SPY underlying-bar blocker clears,
- park the revised condition,
- or revise H-A2 again with a new preregistration.

It must not approve paper trading, operational validation, real-money trading, exact 2022 replay, paid data, IBKR requests, live LLM calls, or E2 evidence.

## Verification
Run:

```powershell
python scripts\validate_h_a2_revised_condition_robustness_preregistration.py
python -m unittest tests.test_validate_h_a2_revised_condition_robustness_preregistration
```
