# H-A2 Delayed-Entry Condition Preregistration

## Status
- **Hypothesis**: H-A2
- **Evidence tier**: E0
- **Status**: preregistered
- **Created**: 2026-07-06
- **Controlling JSON**: `experiments/h_a2_delayed_entry_condition_preregistration.json`

## Why This Exists
H-A2.28 found that the locked condition cannot be used as an original 09:35 ET entry filter because one component is only known around 09:45 ET.

This preregistration keeps the threshold `0.001` fixed and asks the next narrower question: if the decision time moves after the 15-minute conflict window, is there still an economically useful delayed-entry candidate after fill and cost assumptions?

## Locked Rule
- Keep the clean macro/VIX condition from prior H-A2 work.
- Keep opening-followthrough threshold `0.001`.
- Move the candidate decision time to `09:45:00` ET or later.
- Do not reuse original 09:35 PnL as delayed-entry PnL.
- Do not search another threshold or add an OOS-selected filter.

## Planned Checks
1. **Timestamp cleanliness**: prove all features are known by the delayed decision time.
2. **Fill and cost feasibility**: state whether delayed-entry quote data exists, or label the result proxy-only.
3. **Retained sample recount**: report train/OOS retained and skipped counts.
4. **Implementable PnL comparison**: compare delayed-entry candidate against baseline and skipped groups when quote data exists.
5. **Risk and robustness recheck**: preserve MinTRL/PSR, under-sampled, underpowered, DSR/search-log, big-day, and concentration checks.
6. **Hypothesis decision**: continue delayed-entry research, revise toward a timestamp-clean original-entry rule, or park H-A2.

## Allowed Outcome
The future run may only produce E1 diagnostic/prioritization evidence. It may not approve exact replay, paper trading, operational validation, real-money trading, or an E2 claim.

## Verification
Run:

```powershell
python scripts\validate_h_a2_delayed_entry_condition_preregistration.py
python -m unittest tests.test_validate_h_a2_delayed_entry_condition_preregistration
```
