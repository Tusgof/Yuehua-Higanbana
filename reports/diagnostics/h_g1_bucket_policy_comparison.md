# H-G1 Bucket Policy Comparison

- Status: `policy_review_complete_h_g1_still_blocked`
- Conclusion: `ยังสรุปไม่ได้`
- Evidence tier: `E1`
- Allowed output status: `policy_review_only`
- Network used: `False`
- Paid data used: `False`
- Strategy PnL used: `False`
- Source rows: `2822` across `10` dates

## Candidate Summary

| Candidate | Gate | Status | Passed dates | Blocked dates | Failures |
|:--|:--|:--|--:|--:|--:|
| `candidate_a_current_v2_moneyness_only` | `moneyness_only` | `policy_candidate_blocked` | 5 | 5 | 5 |
| `candidate_b_side_aware_required_bucket` | `side_aware` | `policy_candidate_passes_coverage_review` | 10 | 0 | 0 |
| `candidate_c_notional_weighted_coverage` | `notional_weighted` | `policy_candidate_blocked` | 9 | 1 | 1 |

## Recommendation

- Recommended candidate for a separate policy-adoption review: `candidate_b_side_aware_required_bucket`
- Policy adopted now: `False`
- Strategy use allowed: `False`
- Reason: Side-aware buckets target the diagnosed mechanism: H-G1.15 found all blocked failed-bucket rows were opposite-right ITM rows caused by moneyness-only buckets. This candidate passes coverage review without using strategy PnL, new dates, or paid data.

## Candidate Details

### candidate_a_current_v2_moneyness_only

- Status: `policy_candidate_blocked`
- Failures: `5`

| Date | Status | Blockers | Warnings |
|:--|:--|:--|:--|
| `2023-08-09` | `blocked` | `otm_call_computed_rate_below_60pct` | `none` |
| `2023-09-13` | `blocked` | `otm_put_computed_rate_below_60pct` | `none` |
| `2023-10-27` | `pass` | `none` | `none` |
| `2023-12-29` | `pass` | `none` | `none` |
| `2024-01-03` | `blocked` | `otm_put_computed_rate_below_60pct` | `none` |
| `2024-05-21` | `blocked` | `otm_call_computed_rate_below_60pct` | `none` |
| `2024-08-05` | `pass` | `none` | `none` |
| `2024-08-07` | `pass` | `none` | `none` |
| `2024-10-31` | `pass` | `none` | `none` |
| `2024-12-18` | `blocked` | `otm_call_computed_rate_below_60pct` | `none` |

### candidate_b_side_aware_required_bucket

- Status: `policy_candidate_passes_coverage_review`
- Failures: `0`

| Date | Status | Blockers | Warnings |
|:--|:--|:--|:--|
| `2023-08-09` | `pass` | `none` | `none` |
| `2023-09-13` | `pass` | `none` | `none` |
| `2023-10-27` | `pass` | `none` | `none` |
| `2023-12-29` | `pass` | `none` | `none` |
| `2024-01-03` | `pass` | `none` | `none` |
| `2024-05-21` | `pass` | `none` | `none` |
| `2024-08-05` | `pass` | `none` | `none` |
| `2024-08-07` | `pass` | `none` | `none` |
| `2024-10-31` | `pass` | `none` | `none` |
| `2024-12-18` | `pass` | `none` | `none` |

### candidate_c_notional_weighted_coverage

- Status: `policy_candidate_blocked`
- Failures: `1`
- Warnings: `5`

| Date | Status | Blockers | Warnings |
|:--|:--|:--|:--|
| `2023-08-09` | `pass` | `none` | `otm_call_row_rate_warning` |
| `2023-09-13` | `pass` | `none` | `otm_put_row_rate_warning` |
| `2023-10-27` | `blocked` | `otm_call_oi_notional_share_below_floor` | `none` |
| `2023-12-29` | `pass` | `none` | `none` |
| `2024-01-03` | `pass` | `none` | `otm_put_row_rate_warning` |
| `2024-05-21` | `pass` | `none` | `otm_call_row_rate_warning` |
| `2024-08-05` | `pass` | `none` | `none` |
| `2024-08-07` | `pass` | `none` | `none` |
| `2024-10-31` | `pass` | `none` | `none` |
| `2024-12-18` | `pass` | `none` | `otm_call_row_rate_warning` |

## Decision

If continuing H-G1, draft an explicit policy adoption artifact for the side-aware required-bucket gate and rerun the gamma diagnostic under that policy. Do not treat this comparison as strategy validation, do not use strategy PnL for policy selection, and do not use NOVI/net-gamma as a strategy filter.
