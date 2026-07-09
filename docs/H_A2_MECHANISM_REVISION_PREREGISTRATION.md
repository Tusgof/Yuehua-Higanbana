# H-A2 Mechanism Revision Preregistration

## Status
- **Hypothesis**: H-A2
- **Evidence tier**: E0
- **Status**: preregistered
- **Created**: 2026-07-08
- **Controlling JSON**: `experiments/h_a2_mechanism_revision_preregistration.json`

## Why This Exists
The current locked H-A2 condition has two exact-replayed candidates:

- `2025-02-11`: `implementable_pnl = -26.56`
- `2025-05-05`: `implementable_pnl = -32.56`

Two trades are not enough to reject H-A2 as a broad strategy family. But both losing after implementable costs is enough to stop expanding the same condition blindly.

## Revised Question
Does a SPY 0DTE ORB debit vertical spread have positive implementable expectancy only when early directional continuation is strong enough, scheduled risk is clean, option spread cost is low enough, and the market regime supports follow-through rather than opening-range mean reversion?

## Mechanism
The old condition may have identified direction, but not enough post-entry movement to beat debit, bid/ask spread, and per-leg fees. H-A2 is therefore reframed as a conditional continuation hypothesis, not an always-on clean-day ORB hypothesis.

## Next Diagnostic
The next diagnostic is `h_a2_mechanism_revision_audit`.

It must use local artifacts only and report:

- why the two exact-replayed candidates lost;
- whether direction signal and post-entry magnitude are different problems;
- whether cost drag is too large relative to expected movement;
- which regime or rule dimensions are logically justified before any parameter search;
- whether to park the current locked condition, preregister a train-only revised rule, or write a targeted sample/regime expansion plan.

## What This Does Not Permit
- No paid data.
- No exact replay expansion.
- No threshold search.
- No OOS-selected filter.
- No IBKR request.
- No LLM call.
- No GDELT retry.
- No paper trading, operational validation, real-money trading, or E2 claim.

## Verification
Run:

```powershell
python scripts\validate_h_a2_mechanism_revision_preregistration.py
python -m unittest tests.test_validate_h_a2_mechanism_revision_preregistration
```
