# H-A2 Original-Entry Revision Preregistration

## Status
- **Hypothesis**: H-A2
- **Evidence tier**: E0
- **Status**: preregistered
- **Created**: 2026-07-06
- **Controlling JSON**: `experiments/h_a2_original_entry_revision_preregistration.json`

## Why This Exists
H-A2.30 showed that the delayed-entry condition is timestamp-clean at 09:45 ET, but current artifacts do not contain auditable 09:45 option quotes/fills. That means delayed-entry implementable PnL is not computable yet.

This preregistration creates the safer no-paid branch: revise H-A2 back to an original-entry rule that uses only information known by `09:35:00` ET.

## Locked Rule
- Candidate decision time remains `09:35:00` ET.
- Use only deterministic macro/VIX labels known by the decision time.
- Use only the 09:30-09:35 opening-followthrough feature.
- Keep threshold `0.001` locked.
- Exclude the 15-minute conflict component because it is only known around 09:45 ET.
- Do not search a new threshold or add an OOS-selected filter.

## Planned Checks
1. **Timestamp cleanliness**: prove all used features are known by 09:35 ET.
2. **Sample recount**: report train/OOS retained and skipped counts.
3. **Implementable PnL**: use existing original-entry 09:35 trade outcomes only as original-entry PnL, never as delayed-entry PnL.
4. **Risk and sample adequacy**: preserve MinTRL/PSR, under-sampled, underpowered, DSR/search-log, big-day, and concentration checks.
5. **Hypothesis decision**: continue original-entry research, return to delayed-entry quote acquisition, or park H-A2.

## Allowed Outcome
The future run may only produce E1 diagnostic/prioritization evidence. It may not approve exact replay, paper trading, operational validation, real-money trading, or an E2 claim.

## Verification
Run:

```powershell
python scripts\validate_h_a2_original_entry_revision_preregistration.py
python -m unittest tests.test_validate_h_a2_original_entry_revision_preregistration
```
