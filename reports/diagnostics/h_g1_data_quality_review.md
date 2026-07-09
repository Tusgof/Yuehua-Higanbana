# H-G1 Data Quality Review

- Status: `complete_no_purchase_review`
- Paid cost: `$0.0`
- Network calls: `0`
- Conclusion: ยังสรุปไม่ได้

## Summary

- Dates reviewed: 12
- Missing underlying dates: 2
- Manifest/cache mismatches: 2
- Bucket failures after underlying join exists: 5
- Original computed Greeks rate: `0.622771`
- Computed Greeks rate excluding missing-underlying dates: `0.739238`

## Missing Underlying Dates

| Date | Manifest bar status | Baseline bar rows | Quote snapshot rows | Issue |
|:--|:--|--:|--:|:--|
| 2023-03-13 | `present` | 0 | 260 | `manifest_cache_mismatch_missing_spy_bars` |
| 2023-03-22 | `present` | 0 | 270 | `manifest_cache_mismatch_missing_spy_bars` |

## Remaining Bucket Failures

| Date | Bucket blockers | Computed rate |
|:--|:--|--:|
| 2023-07-12 | `otm_put_computed_rate_below_60pct` | 0.725191 |
| 2023-08-09 | `otm_call_computed_rate_below_60pct` | 0.783465 |
| 2024-01-03 | `otm_put_computed_rate_below_60pct` | 0.475806 |
| 2024-05-21 | `otm_call_computed_rate_below_60pct` | 0.90367 |
| 2024-12-18 | `otm_call_computed_rate_below_60pct` | 0.791667 |

## Decision

H-G1 ยังเป็น data-quality blocker ไม่ใช่ strategy blocker; สองวัน March 2023 ไม่มี SPY bars จริงใน cache แม้ manifest ระบุ present และยังมี bucket-level IV/Greeks coverage failures หลังตัดวันดังกล่าวออก

## Next Safe Action

ทำ H-G1 manifest v2 หรือ repair cache เฉพาะ 2023-03-13 และ 2023-03-22 ก่อน rerun; จากนั้นตรวจ bucket failures ที่เหลือโดยไม่ใช้ signed-OI gamma proxy เป็น trading filter จนกว่า policy gate จะผ่าน
