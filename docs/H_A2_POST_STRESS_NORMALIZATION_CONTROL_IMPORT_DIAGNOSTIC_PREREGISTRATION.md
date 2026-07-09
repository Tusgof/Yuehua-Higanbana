# H-A2 Post-Stress Normalization/Control Import Diagnostic Preregistration

## Status
- **Hypothesis**: H-A2
- **Evidence tier**: E0
- **Status**: preregistered
- **Created**: 2026-07-08
- **Controlling JSON**: `experiments/h_a2_post_stress_normalization_control_import_diagnostic_preregistration.json`

## Why This Exists
The post-stress normalization/control pack for `2025-05-05` through `2025-05-16` has already been downloaded. That download is only raw data acquisition. It does not prove that H-A2 has an edge and it does not approve exact replay or PnL.

This preregistration defines the next local-only step: import and normalize the already-downloaded raw files, then diagnose whether the locked H-A2 signal and required quote windows are auditable on this second normal/control validation pack.

## Locked Signal
- Decision and entry time stay at `09:35:00` ET.
- Threshold stays at `0.001`.
- Features stay `clean_macro_vix_condition` and `proxy_5m_followthrough`.
- No threshold search, no OOS tuning, no delayed-entry component, and no 15-minute conflict component.

## Allowed Next Work
- Inventory the 20 downloaded raw files.
- Preserve and inspect the 2025-05-06 reduced-quality note from Databento.
- Parse the downloaded SPY `ohlcv-1m` files.
- Parse the downloaded OPRA `cbbo-1m` grouped windows.
- Normalize UTC/ET timestamps and option quote fields.
- Reconstruct only the locked 09:35 signal for each date.
- Check whether entry and 15:45 forced-close quotes are available on candidate dates.
- Write an E1-or-lower diagnostic report.

## Forbidden
- No new Databento download.
- No resumed high-VIX-first acquisition from this step.
- No new paid provider.
- No IBKR request.
- No exact replay directly from this preregistration.
- No strategy PnL from this preregistration.
- No paper trading, operational validation, real-money trading, or E2 claim.
- No LLM call and no GDELT retry.
- No threshold change and no new OOS-selected filter.

## Verification
Run:

```powershell
python scripts\validate_h_a2_post_stress_normalization_control_import_diagnostic_preregistration.py
python -m unittest tests.test_validate_h_a2_post_stress_normalization_control_import_diagnostic_preregistration
```
