# H-G1 Gamma Strategy-Ablation Pre-Registration

## Status
- **Hypothesis**: `H-G1`
- **Artifact**: `experiments/h_g1_gamma_strategy_ablation_preregistration.json`
- **Evidence tier**: `E0`
- **Conclusion**: `ยังสรุปไม่ได้`
- **Network / paid data**: none
- **Strategy use allowed**: no
- **Paper trading allowed**: no

## Purpose
H-G1.19 passed only a data-validity diagnostic for the `signed-OI gamma proxy`. H-G1.20 then showed that strategy use is still blocked because the project has not tested whether the proxy improves an actual trading rule.

This document locks the next ablation design before any strategy PnL is reviewed.

## Locked Comparison
The next test must compare:

1. `baseline_quant_only`: existing timestamp-clean Sub-System A ORB rule with no gamma filter.
2. `skip_negative_gamma_proxy_days`: skip baseline trades when the decision-time signed-OI gamma proxy is negative.
3. `skip_extreme_negative_gamma_proxy_days`: skip baseline trades in the train-fitted most-negative proxy tercile.
4. `positive_gamma_proxy_only`: allow baseline trades only when the proxy is positive.

No additional variant may be added without a new pre-registration.

## Controls
- Use chronological split only: train `2022-05-11` to `2023-12-31`, OOS from `2024-01-01`.
- Fit thresholds on train only and freeze them before OOS.
- Record every attempted variant in `reports/experiments/search_logs/h_g1_gamma_strategy_ablation_search_log.jsonl`.
- Report DSR or a DSR blocker if any selected-best metric is shown.
- Report Sharpe with MinTRL and PSR; mark results `under-sampled` or `underpowered` when required.
- Report mid PnL and implementable PnL separately, including cost drag and `$0.64` per leg.
- Run the big-day dependency check by removing the most extreme 5% winning and losing trades or close days.
- Use only the term `signed-OI gamma proxy` unless a real dealer/customer inventory source is acquired.

## Next Action
Implement the ablation runner against this pre-registration. The runner must not use new paid data, new gamma dates, or OOS tuning.
