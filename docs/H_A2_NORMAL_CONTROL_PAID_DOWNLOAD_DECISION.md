# H-A2 Normal/Control Paid Download Decision

## Status
- **Hypothesis**: H-A2
- **Evidence tier**: E0
- **Status**: decision complete
- **Created**: 2026-07-07
- **Controlling JSON**: `experiments/h_a2_normal_control_paid_download_decision.json`

## Why This Exists
H-A2.44 estimated `low_normal_vix_control_pack` at `$5.398913` using selected key env `DATABENTO_API_MO`. That estimate did not download data and explicitly required a separate decision before any pull.

This artifact approves only the tightly scoped normal/control pack download after `python scripts\audit_paid_costs.py` passes. It is not a research result and does not validate H-A2 edge.

## Approved Scope
- Dates: `2025-02-03` to `2025-02-14`
- Provider: Databento
- Selected key env: `DATABENTO_API_MO`
- Symbol scope: SPY only
- Planned required windows: `150`
- Metadata grouped estimate calls: `20`
- Option data: OPRA `cbbo-1m` for `SPY.OPT`
- Underlying data: `EQUS.MINI` `ohlcv-1m` for `SPY`
- Estimated cost: `$5.398913`
- Projected selected-key usage: `$5.398913` / `$100`
- Projected MO/AI pool usage: `$5.398913` / `$200`
- Legacy projected usage: `$125.893281` / `$125`

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

Proceed only if the paid-cost audit still reports `status=pass`, then use `DATABENTO_API_MO` and stay below the selected-key `$100` cap and the MO/AI `$200` pool cap.

## Forbidden
- No date outside `2025-02-03` to `2025-02-14`.
- No `post_stress_normalization_control_pack` download.
- No high-VIX-first acquisition resume.
- No broad 2025 calendar estimate or download.
- No new paid provider.
- No IBKR request.
- No exact replay directly from this decision.
- No LLM call.
- No GDELT retry.
- No paper trading, operational validation, real-money trading, or E2 claim.

## Verification
Run:

```powershell
python scripts\validate_h_a2_normal_control_paid_download_decision.py
python -m unittest tests.test_validate_h_a2_normal_control_paid_download_decision
```
