# H-G1 Local Cache Overlap Scan

- **Status**: `blocked_no_additional_no_paid_overlap`
- **Evidence tier**: `E0`
- **Conclusion**: ยังสรุปไม่ได้
- **Network used**: `False`
- **Paid data used**: `False`
- **Strategy PnL used**: `False`
- **Strategy use allowed**: `False`

## Counts

- Baseline closed trade dates: `90`
- Current gamma dates: `10`
- Current baseline/gamma intersection: `2`
- Additional no-paid gamma-ready dates: `0`
- Projected no-paid gamma-ready intersection: `2`
- Quote/bar cached baseline dates missing OI: `88`

## Current Covered Trade Dates

2023-10-27, 2024-12-18

## MinTRL / PSR Gate

- **Status**: `blocked_insufficient_observations`
- **Reason**: No additional baseline trade dates have local quote, local SPY bar, and local OI files outside the current H-G1 gamma date set. The no-paid expanded sample remains too small to estimate Sharpe distribution inputs such as skewness, kurtosis, first-order autocorrelation, PSR, or MinTRL.

## Next Safe Action

Keep H-G1 parked. Return to News-Unblock or H-A2 external blockers; do not run a new gamma ablation or paid gamma cost gate from this scan because no additional no-paid gamma-ready baseline trade dates were found.
