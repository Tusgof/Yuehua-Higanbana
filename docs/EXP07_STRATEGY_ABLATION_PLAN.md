# Exp07 Strategy Ablation Plan

## Purpose

This document defines how the guarded Exp07 policy must be tested before it can affect strategy research or live decisions.

The machine-readable plan is `tests/fixtures/exp07_strategy_ablation_plan_v1.json`. The validator is `scripts/validate_exp07_strategy_ablation_plan.py`.

The status runner is `scripts/run_exp07_strategy_ablation.py`. It emits a blocked readiness artifact only; it is not a completed strategy ablation result.

## Required Variants

| Variant | Role | Can Block Trades |
|:--|:--|:--|
| `baseline_quant_only` | Quantitative filters and execution rules only | No |
| `guarded_policy_gate` | Deterministic guarded Exp07 policy as a trade gate | Yes |
| `raw_llm_observation_only` | Raw LLM output logged for diagnostics only | No |

Raw LLM decisions must not be used as a gate. The controlled v12 prompt matrix failed the raw LLM gate, so raw LLM output can only be diagnostic evidence.

## Required Data

- Wider SPY 0DTE bid/ask data with enough trades for `N >= 500`.
- Real news archive, not only fixture headlines.
- Real macro calendar archive from official source snapshots, not only fixture rows. This requirement is currently satisfied by the 2022-2026 official-source canonical macro archive.
- Bid/ask quotes for implementable PnL.

## Required Metrics

- `trade_count`
- `skip_rate`
- `total_net_pnl`
- `sharpe`
- `sortino`
- `max_drawdown`
- `es95`
- `es99`
- `worst_day_loss`
- `win_rate`
- `payoff_ratio`
- `cost_drag`
- `benchmark_return`

## Acceptance Logic

The guarded policy can only advance if:

- it does not reduce trade count below the minimum sample threshold,
- it improves `es99` or `worst_day_loss`,
- it does not reduce OOS Sharpe below the baseline,
- parameters are locked before OOS,
- OOS results are not used for tuning.

## Verification

```powershell
python scripts\validate_exp07_strategy_ablation_plan.py
python scripts\run_exp07_strategy_ablation.py
python -m unittest tests.test_validate_exp07_strategy_ablation_plan
```
