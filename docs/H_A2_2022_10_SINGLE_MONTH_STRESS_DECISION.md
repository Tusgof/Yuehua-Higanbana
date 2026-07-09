# H-A2 2022-10 Single-Month Stress Decision

## Decision
Approve a narrow H-A2 stress-data scope revision for **2022-10 only**.

This is not an evidence pass. It is an E0 cost/scope decision that lets the project buy one high-VIX month because the original top2 purchase is currently blocked by the active cost guard.

## Why 2022-10
- 2022-10 is the rank 1 2022 H2 stress month.
- Average VIX: `30.0057`.
- Max VIX: `33.63`.
- High-VIX days: `21`.
- Stress-VIX days: `11`.
- Trading days: `21`.

The month directly targets H-A2's missing high-volatility/regime evidence instead of buying broad calendar data.

## Cost Guard
- Current working Databento usage: `$109.467226`.
- Stop threshold: `$125.0`.
- Remaining before stop: `$15.532774`.
- 2022-10 live metadata estimate: `$10.52248`.
- Projected usage after download: `$119.989706`.
- Projected remaining after download: `$5.010294`.

The original 2022 H2 top2 bundle remains blocked because `2022-10 + 2022-09 = $20.748872`, which exceeds the current headroom.

## Allowed
- Download only the approved 2022-10 OPRA `cbbo-1m` daily-union requests from `reports/data_cost/databento_cost_h_a2_2022_10_stress.json`.
- Reuse cached files if present.
- Rerun paid-cost audit after download.
- Import/normalize the 2022-10 stress data if the required option quotes and SPY bars are present.

## Forbidden
- Do not download 2022-09 under this decision.
- Do not download top2 or top3 under this decision.
- Do not buy broad 2022 H2 calendar data.
- Do not introduce a new paid provider.
- Do not claim E2 acceptance, paper-trading readiness, or live-trading readiness from this decision.
- Do not run live LLM research from this decision.

## Verification
Run:

```powershell
& 'D:\Fogust\Workspace\Investment\Project\Yuehua Investment Lab\.venv\Scripts\python.exe' scripts\validate_h_a2_2022_10_single_month_decision.py
```

Expected result: `status=pass`.
