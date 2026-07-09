# H-A2 Independent Validation Feasibility Preregistration

## Status
- **Hypothesis**: H-A2
- **Evidence tier**: E0
- **Status**: preregistered
- **Created**: 2026-07-06
- **Controlling JSON**: `experiments/h_a2_independent_validation_feasibility_preregistration.json`

## Why This Exists
H-A2.34 kept the timestamp-clean `09:35:00` ET original-entry rule intact and found directionally useful leave-one-out and skip-cost results. The blocker is still evidence strength: retained OOS has only 14 trade days and no high-VIX retained bucket.

This preregistration defines the next no-paid planning step before any paid data, IBKR request, exact replay, paper trading, or E2 claim.

## Locked Signal
- Candidate decision time remains `09:35:00` ET.
- Threshold remains `0.001`.
- Allowed features remain `clean_macro_vix_condition` and `proxy_5m_followthrough`.
- No new filter, no OOS tuning, no 15-minute conflict component, and no delayed-entry PnL reuse.

## Planned Checks
1. **Current gap inventory**: identify the exact sample, regime, high-VIX, and MinTRL/PSR blockers.
2. **Validation target definition**: define what independent data would fairly test the locked H-A2 signal.
3. **No-paid source inventory**: check whether local or free sources can add validation coverage before spending money.
4. **Paid data decision tree**: if no-paid coverage is insufficient, define the later cost-estimate decision tree without approving spending.
5. **Next action selection**: choose no-paid validation scan, paid-cost estimate plan, exact-replay plan, or park H-A2.

## Allowed Outcome
This artifact is planning evidence only. It may justify a future diagnostic run, but it does not validate an edge and does not approve paid data, IBKR requests, exact replay, paper trading, operational validation, real-money trading, or E2 claims.

## Verification
Run:

```powershell
python scripts\validate_h_a2_independent_validation_feasibility_preregistration.py
python -m unittest tests.test_validate_h_a2_independent_validation_feasibility_preregistration
```
