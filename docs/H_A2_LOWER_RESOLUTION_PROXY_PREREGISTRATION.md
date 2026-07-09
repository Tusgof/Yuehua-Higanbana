# H-A2 Lower-Resolution Proxy Preregistration

## Purpose

This artifact pre-registers the next H-A2 test before any new exact 2022 SPY bar-source chase.

The goal is not to prove deployable edge. The goal is to ask whether H-A2 still deserves exact-data work after using the coarsest local data that can answer the current question.

## Hypothesis

H-A2 says the macro-conditioned ORB mechanism is real only if scheduled macro-event and volatility-regime labels explain a stable difference in opening-range follow-through and already-observed implementable option outcomes.

If lower-resolution opening proxies and existing trade outcomes do not show this relationship, H-A2 should be weakened or deprioritized before chasing exact 2022 SPY 1-minute bars.

## Minimum Data Resolution

For the mechanism proxy, 1-minute bars are not required.

Allowed proxy inputs:

- 5-minute bars for the 9:30-9:35 ET opening range.
- 15-minute bars for a coarser opening-momentum proxy.
- Daily macro and VIX/VXV labels.
- Existing exact-quote trade outcome summaries from already-generated artifacts.

For an exact ORB backtest, 1-minute bars are still required. Exact entry timing, breakout ordering, stop/target path, and option fill timing cannot be proven from 15-minute proxy data.

## Planned Proxy Tests

1. `proxy_opening_followthrough_5m`
   - Compare opening-range follow-through, realized intraday range, and directional persistence by macro-event and VIX regime.

2. `proxy_opening_followthrough_15m`
   - Test whether coarser opening momentum preserves the same macro/VIX relationship as the 5-minute proxy.

3. `existing_trade_outcome_by_regime`
   - Reconcile proxy labels with existing implementable PnL, trade count, cost drag, and drawdown by macro/VIX regime.

## Split And Trial Policy

- Design/train period: `2023-03-28` to `2023-12-31`.
- OOS period: `2024-01-01` to `2024-12-31`.
- Chronological split is required.
- Random split is forbidden.
- OOS tuning is forbidden.
- All resolution and regime trials must be logged.
- DSR is required if Sharpe or best-trial selection is reported.

## Statistical Policy

If the future run produces a return or trade series, it must report:

- sample length,
- MinTRL/PSR or a clear not-applicable reason,
- `under-sampled` label when N is below MinTRL,
- `underpowered` label when statistical power is insufficient,
- big-day dependency if strategy returns exist,
- mid versus implementable PnL if option PnL exists.

## Allowed Claims

The future run may say:

- H-A2 is weakened at proxy level.
- H-A2 is falsified at proxy level.
- H-A2 remains worth exact-data prioritization.

## Forbidden Claims

This preregistration and the future proxy run do not allow:

- exact 2022-10 ORB entry/exit claims,
- E2 acceptance-grade edge claims,
- deployable strategy edge claims,
- paper trading,
- operational validation,
- real-money trading,
- IBKR historical-data requests,
- paid data,
- new data providers,
- LLM calls.

## Verification

```powershell
python scripts\validate_h_a2_lower_resolution_proxy_preregistration.py
python -m unittest tests.test_validate_h_a2_lower_resolution_proxy_preregistration
```
