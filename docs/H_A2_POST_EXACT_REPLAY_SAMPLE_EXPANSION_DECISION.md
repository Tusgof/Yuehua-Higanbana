# H-A2 Post Exact-Replay Sample-Expansion Decision

## Status
- **Hypothesis**: H-A2
- **Evidence tier**: E0
- **Status**: preregistered
- **Created**: 2026-07-07
- **Controlling JSON**: `experiments/h_a2_post_exact_replay_sample_expansion_decision.json`

## Why This Exists
H-A2.49 replayed only one normal/control candidate date: `2025-02-11`.

That trade lost money:

- `mid_pnl = -22.00`
- `implementable_pnl = -26.56`
- `cost_drag_vs_mid = 4.56`

This does not validate H-A2. It also does not falsify H-A2, because one trade is under-sampled and underpowered. The right next step is not to change the threshold or claim failure. The right next step is to add a second pre-selected validation window through a cost gate.

## Decision
The next H-A2 step is a metadata-only Databento cost estimate for:

- `post_stress_normalization_control_pack`
- Date range: `2025-05-05` to `2025-05-16`
- Trading days: 10
- VIX range from local labels: `17.24` to `24.76`
- High-importance macro days from local calendar: 0

The selected key env for this estimate is `DATABENTO_API_AI`. The key value must never be stored.

## Locked Signal
- Decision and entry time stay at `09:35:00` ET.
- Threshold stays at `0.001`.
- Features stay `clean_macro_vix_condition` and `proxy_5m_followthrough`.
- No threshold search.
- No OOS tuning.
- No delayed-entry component.
- No 15-minute conflict component.

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
python scripts\validate_h_a2_post_exact_replay_sample_expansion_decision.py
python -m unittest tests.test_validate_h_a2_post_exact_replay_sample_expansion_decision
```
