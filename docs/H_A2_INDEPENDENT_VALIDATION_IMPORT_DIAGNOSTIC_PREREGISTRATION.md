# H-A2 Independent Validation Import Diagnostic Preregistration

## Status
- **Hypothesis**: H-A2
- **Evidence tier**: E0
- **Status**: preregistered
- **Created**: 2026-07-06
- **Controlling JSON**: `experiments/h_a2_independent_validation_import_diagnostic_preregistration.json`

## Why This Exists
H-A2.40 downloaded the one-day high-VIX independent-validation sample for `2025-04-08`. That download is only raw data acquisition. The project still must not jump directly to exact replay or edge claims.

This preregistration defines the next local-only step: import and normalize the already-downloaded raw files, then diagnose whether the locked H-A2 signal and required quote windows are auditable.

## Locked Signal
- Decision and entry time stay at `09:35:00` ET.
- Threshold stays at `0.001`.
- Features stay `clean_macro_vix_condition` and `proxy_5m_followthrough`.
- No threshold search, no OOS tuning, no delayed-entry component, and no 15-minute conflict component.

## Allowed Next Work
- Inventory the 15 downloaded raw files.
- Parse the downloaded SPY `ohlcv-1m` file.
- Parse the downloaded OPRA `cbbo-1m` windows.
- Normalize UTC/ET timestamps and option quote fields.
- Reconstruct only the locked 09:35 signal.
- Check whether entry, intraday, and 15:45 forced-close quotes are available.
- Write an E1-or-lower diagnostic report.

## Forbidden
- No new Databento download.
- No new paid provider.
- No IBKR request.
- No exact replay directly from this preregistration.
- No paper trading, operational validation, real-money trading, or E2 claim.
- No LLM call and no GDELT retry.
- No threshold change and no new OOS-selected filter.

## Verification
Run:

```powershell
python scripts\validate_h_a2_independent_validation_import_diagnostic_preregistration.py
python -m unittest tests.test_validate_h_a2_independent_validation_import_diagnostic_preregistration
```
