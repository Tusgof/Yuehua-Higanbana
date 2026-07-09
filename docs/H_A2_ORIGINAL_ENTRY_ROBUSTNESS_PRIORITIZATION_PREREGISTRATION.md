# H-A2 Original-Entry Robustness And Prioritization Preregistration

## Status
- **Hypothesis**: H-A2
- **Evidence tier**: E0
- **Status**: preregistered
- **Created**: 2026-07-06
- **Controlling JSON**: `experiments/h_a2_original_entry_robustness_prioritization_preregistration.json`

## Why This Exists
H-A2.32 found a timestamp-clean original-entry version of the rule: use only information known by `09:35:00` ET, keep threshold `0.001`, and exclude the 15-minute conflict component.

The issue is sample strength. The retained OOS sample has only 14 trade days, so the result is still under-sampled and underpowered. This preregistration defines the next local review before any claim upgrade, exact replay, paid data, IBKR request, LLM call, or paper-trading step.

## Locked Rule Under Review
- Candidate decision time remains `09:35:00` ET.
- Threshold remains `0.001`.
- Use the H-A2.32 09:35-only rule as-is.
- Do not add a new filter.
- Do not tune on OOS.
- Do not reintroduce the 15-minute conflict component.
- Do not treat this as delayed-entry evidence.

## Planned Checks
1. **Rule integrity**: prove the review keeps the exact H-A2.32 rule.
2. **Leave-one and big-day dependency**: check whether retained OOS performance depends on one or two extreme days.
3. **Regime and calendar concentration**: check whether the signal is concentrated in one month, weekday, volatility bucket, or macro/VIX regime.
4. **Skip-cost tradeoff**: compare retained trades against skipped trades so the rule does not merely hide losses by collapsing the sample.
5. **Validation priority decision**: decide whether to prioritize independent validation-data planning, run another local diagnostic, return to delayed-entry quote acquisition, or park this original-entry branch.

## Allowed Outcome
The future run may only produce E1 diagnostic/prioritization evidence. It may recommend a next research path, but it may not validate an edge or approve exact replay, paper trading, operational validation, real-money trading, or an E2 claim.

## Verification
Run:

```powershell
python scripts\validate_h_a2_original_entry_robustness_prioritization_preregistration.py
python -m unittest tests.test_validate_h_a2_original_entry_robustness_prioritization_preregistration
```
