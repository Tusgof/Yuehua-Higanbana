# H-A2 Independent Validation Paid Download Decision

## Status
- **Hypothesis**: H-A2
- **Evidence tier**: E0
- **Status**: decision complete
- **Created**: 2026-07-06
- **Controlling JSON**: `experiments/h_a2_independent_validation_paid_download_decision.json`

## Why This Exists
H-A2.38 estimated the first independent-validation high-VIX sample day, `2025-04-08`, at `$0.504662` for 15 Databento requests. That estimate did not download data and explicitly required a separate download decision.

This artifact is that decision. It approves only the one-day `sample_cost_probe_high_vix_one_day` download after `python scripts/audit_paid_costs.py` passes. It is not a research result and does not validate H-A2 edge.

## Approved Scope
- Date: `2025-04-08`
- Provider: Databento
- Symbol scope: SPY only
- Request count: 15
- Option data: OPRA `cbbo-1m` for `SPY.OPT`
- Underlying data: `EQUS.MINI` `ohlcv-1m` for `SPY`
- Estimated cost: `$0.504662`
- Projected usage after download: `$120.494368` against the `$125` guard

## Locked Signal
- Decision time and entry time stay at `09:35:00` ET.
- Threshold stays at `0.001`.
- Features stay `clean_macro_vix_condition` and `proxy_5m_followthrough`.
- No threshold search, no OOS tuning, no new OOS-selected filter, no delayed-entry component, and no 15-minute conflict component.

## Required Before Download
Run:

```powershell
python scripts\audit_paid_costs.py
```

Proceed only if the audit still reports `status=pass` and projected usage remains below `$125`.

## Forbidden
- No date beyond `2025-04-08`.
- No broad 2025 calendar estimate or download.
- No high-VIX pack/control-pack download under this decision.
- No new paid provider.
- No IBKR request.
- No exact replay directly from this decision.
- No LLM call.
- No GDELT retry.
- No paper trading, operational validation, real-money trading, or E2 claim.

## Verification
Run:

```powershell
python scripts\validate_h_a2_independent_validation_paid_download_decision.py
python -m unittest tests.test_validate_h_a2_independent_validation_paid_download_decision
```
