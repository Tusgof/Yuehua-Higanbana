# H-A2 Proxy-First Robustness Preregistration

## Purpose

This artifact pre-registers the next H-A2 step before chasing SPY 2022 1-minute bars again.

The core point is simple: 1-minute bars are a method for exact ORB replay, not the hypothesis itself. If the ORB mechanism is real, lower-resolution local evidence should still help falsify, weaken, or prioritize the hypothesis before more exact data work.

## Hypothesis

H-A2 says the macro-conditioned ORB mechanism should show a stable relationship between opening-session behavior, volatility or macro-event regime, and existing option-trade outcomes.

If that relationship disappears outside exact 1-minute replay, H-A2 is too fragile to justify more exact-data effort without revision.

## Resolution Position

1-minute bars are required for:

- exact 2022-10 ORB entry and exit replay,
- breakout ordering,
- stop/target path,
- exact option fill timing.

1-minute bars are not required for:

- daily macro-event and VIX/VXV regime checks,
- 15-minute opening-session proxy checks,
- 5-minute opening-range proxy checks where local data exists,
- reconciliation against existing exact-quote trade outcomes.

Any future pass from this proxy path remains E1 at most. It cannot approve paper trading, operational validation, or real-money trading.

## Planned Tests

1. `resolution_monotonicity_check`
   - Check whether the H-A2 signal direction remains coherent across daily-regime, 15-minute, 5-minute, and existing trade-outcome views.

2. `macro_vix_separation_check`
   - Separate macro-event labels, VIX regime labels, combined risk labels, and non-risk labels.

3. `existing_trade_reconciliation_check`
   - Compare proxy labels with already-observed implementable option outcomes without re-tuning on OOS.

4. `fragility_and_big_day_check`
   - Check whether the evidence collapses under extreme-observation removal, low sample counts, or MinTRL/PSR weakness.

## Split And Statistical Policy

- Use chronological split only.
- Random split is forbidden.
- OOS tuning is forbidden.
- Report sample count for every bucket.
- Report MinTRL/PSR when a trade or return series exists.
- Mark results as `under-sampled` when N is below MinTRL.
- Mark results as `underpowered` when statistical power is insufficient.
- Keep a search log and DSR blocker or adjustment if a best trial is reported.
- Run big-day dependency checks when strategy returns exist.
- Separate mid PnL from implementable PnL when option PnL exists.

## Allowed Claims

The future run may say:

- H-A2 is weakened at proxy level.
- H-A2 remains worth exact-data prioritization at E1 only.
- H-A2 should be revised before further exact-data source work.
- 1-minute bars are still required only for exact replay, not for mechanism-level proxy testing.

## Forbidden Claims

This preregistration does not allow:

- exact 2022-10 ORB entry or exit claims,
- E2 acceptance-grade evidence claims,
- paper trading,
- operational validation,
- real-money trading,
- IBKR historical-data requests,
- paid data,
- new data providers,
- live LLM calls.

## Verification

```powershell
python -m json.tool experiments\h_a2_proxy_first_robustness_preregistration.json
```
