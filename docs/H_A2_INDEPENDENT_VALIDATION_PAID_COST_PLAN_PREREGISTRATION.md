# H-A2 Independent Validation Paid-Cost Plan Preregistration

## Status
- **Hypothesis**: H-A2
- **Evidence tier**: E0
- **Status**: preregistered
- **Created**: 2026-07-06
- **Controlling JSON**: `experiments/h_a2_independent_validation_paid_cost_plan_preregistration.json`

## Why This Exists
H-A2.36 found that no-paid sources can define the validation gap but cannot add independent implementable SPY 0DTE PnL days. The current retained OOS evidence has only 14 trade days, no retained high-VIX bucket, and no MinTRL/PSR acceptance path.

This artifact defines the exact narrow cost-estimate scope before any provider call. It is not a download decision and it is not edge evidence.

## Locked Signal
- Decision and entry time stay at `09:35:00` ET.
- Threshold stays at `0.001`.
- Features stay `clean_macro_vix_condition` and `proxy_5m_followthrough`.
- No new OOS-selected filter, no threshold search, no delayed-entry component, and no 15-minute conflict component.

## Candidate Estimate Windows
1. `sample_cost_probe_high_vix_one_day`: `2025-04-08`, VIX close `52.33`.
2. `high_vix_validation_pack`: `2025-04-04`, `2025-04-07`, `2025-04-08`, `2025-04-09`, `2025-04-10`, `2025-04-11`.
3. `low_normal_vix_control_pack`: `2025-02-03` to `2025-02-14`.
4. `post_stress_normalization_control_pack`: `2025-05-05` to `2025-05-16`.

The first future action, if this plan remains valid, is only a metadata cost estimate for the one-day high-VIX sample. Broader estimates must be sequential and must stop if the cost guard would be breached.

## Required Fields
- OPRA `cbbo-1m` SPY option quotes around `09:35` ET.
- OPRA `cbbo-1m` SPY option quotes for intraday checks and `15:45` forced close.
- SPY `ohlcv-1m` underlying bars for signal reconstruction.
- Existing local VIX/VXV and macro labels.

## Cost Guard
Current cost guard basis is `$119.989706` used against the `$125` stop threshold, leaving `$5.010294`. This preregistration does not call Databento and does not approve download. A later metadata estimate may start only after this validator and the latest paid-cost audit pass.

## Forbidden
- No paid download.
- No live Databento estimate from this preregistration.
- No IBKR request.
- No exact replay.
- No LLM call.
- No GDELT retry.
- No paper trading, operational validation, real-money trading, or E2 claim.

## Verification
Run:

```powershell
python scripts\validate_h_a2_independent_validation_paid_cost_plan_preregistration.py
python -m unittest tests.test_validate_h_a2_independent_validation_paid_cost_plan_preregistration
```
