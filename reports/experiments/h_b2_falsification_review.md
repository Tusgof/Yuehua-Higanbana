# H-B2 Falsification Review

- Status: `review_complete`
- Conclusion: `ไม่ผ่าน`
- Decision: `keep_h_b2_parked_current_grid_not_resurrected`
- Evidence tier: `E1`
- Source summary: `reports/experiments/h_b2_subsystem_b_scale_summary.json`
- Current grid failed keep-active rule: `True`
- Acceptance-grade falsified: `False`
- Network used: `False`
- Paid data used: `False`
- LLM called: `False`
- Paper trading allowed: `False`

## Scenario Review

| Scenario | Trades | Total impl PnL | OOS impl PnL | Sharpe proxy | PSR(SR>0) | Labels | Big-day |
|---|---:|---:|---:|---:|---:|---|---|
| account_10000_wing_5 | 413 | -5604.56 | -3332.88 | -0.082674 | 0.057628 | under-sampled, underpowered | pass |
| account_25000_wing_5 | 413 | -5604.56 | -3332.88 | -0.102007 | 0.026729 | under-sampled, underpowered | pass |
| account_10000_wing_10 | 90 | -784.80 | -686.68 | -0.058111 | 0.296930 | under-sampled, underpowered | pass |
| account_25000_wing_10 | 412 | -5973.44 | -3866.76 | -0.108110 | 0.019990 | under-sampled, underpowered | pass |
| account_10000_wing_15 | 0 | 0.00 | 0.00 | - | - | under-sampled, underpowered | insufficient_trades |
| account_25000_wing_15 | 406 | -5729.72 | -3641.04 | -0.103341 | 0.024275 | under-sampled, underpowered | pass |
| account_10000_wing_20 | 0 | 0.00 | 0.00 | - | - | under-sampled, underpowered | insufficient_trades |
| account_25000_wing_20 | 0 | 0.00 | 0.00 | - | - | under-sampled, underpowered | insufficient_trades |

## Decision

The current H-B2 grid fails the pre-registered keep-active rule because no scenario has both positive total implementable PnL and positive OOS implementable PnL.
This review keeps H-B2 parked rather than deleting Sub-System B from scope: the current grid/mechanism failed, but other Sub-System B mechanisms require a separate revised hypothesis.

## Forbidden Actions

- Do not use H-B2 current grid for paper trading.
- Do not claim Sub-System B is deployable from this review.
- Do not buy new data for H-B2 from this review alone.
- Do not delete Sub-System B from project scope solely because this grid failed.

## Tier Blockers

- E1 falsification review only
- No E2 acceptance-grade validation
- Some scenarios remain under-sampled or underpowered
- Grid search remains diagnostic and cannot support deployment selection
- Current grid failure does not falsify all possible Sub-System B mechanisms
