# H-A2 Normal/Control Sample Decision

## Status
- **Hypothesis**: H-A2
- **Evidence tier**: E0
- **Status**: preregistered
- **Created**: 2026-07-06
- **Controlling JSON**: `experiments/h_a2_normal_control_sample_decision.json`

## Why This Exists
The first independent-validation sample, `2025-04-08`, was useful high-VIX availability evidence but produced no candidate H-A2 trade because the clean macro/VIX condition failed.

The user decision on 2026-07-06 changed the next priority: test normal/control regimes before collecting more stress samples. This prevents the research from over-focusing on high-VIX days when the live hypothesis may be conditional on calmer regimes.

## Decision
The prior high-VIX-first sequence is paused. The next H-A2 data-planning step is a metadata-only Databento estimate for:

1. `low_normal_vix_control_pack`: `2025-02-03` to `2025-02-14`, 10 trading days, local VIX range `14.77` to `18.62`, no high-importance macro days in the local macro calendar.
2. `post_stress_normalization_control_pack`: `2025-05-05` to `2025-05-16`, 10 trading days, local VIX range `17.24` to `24.76`, no high-importance macro days in the local macro calendar.

The next selected key env for a future metadata-only estimate is `DATABENTO_API_MO`. The key value must never be stored.

## Locked Signal
- Decision and entry time stay at `09:35:00` ET.
- Threshold stays at `0.001`.
- Features stay `clean_macro_vix_condition` and `proxy_5m_followthrough`.
- No threshold search, no OOS tuning, no delayed-entry component, and no 15-minute conflict component.

## What This Does Not Permit
- No paid download.
- No exact replay.
- No IBKR request.
- No LLM call.
- No GDELT retry.
- No paper trading, operational validation, real-money trading, or E2 claim.

## Verification
Run:

```powershell
python scripts\validate_h_a2_normal_control_sample_decision.py
python -m unittest tests.test_validate_h_a2_normal_control_sample_decision
```
