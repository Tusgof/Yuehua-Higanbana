# Databento Pilot Sensitivity Report

## สถานะ
- ข้อสรุป: ยังสรุปไม่ได้
- Pilot decision: `needs_design_review_before_wider_data`
- รายงานนี้ใช้เพื่อดูความไวของ pilot เท่านั้น ไม่ใช่หลักฐานว่า strategy มี edge

## Decision Reasons
- worst full-spread stress total_net_pnl=-117.0
- strict close skipped_trades=0
- trade_count is far below N >= 500
- pilot is fragile under stress or close data coverage is weak

## Scenario Summary
| Scenario | Fill | Fee/Contract | Close | Closed | Skipped | Net PnL | Worst | MDD |
|:--|:--|--:|:--|--:|--:|--:|--:|--:|
| `mid_fee_0_0_strict` | `mid` | 0.0 | `strict_1545` | 3 | 0 | -96.0 | -33.0 | -0.096 |
| `mid_fee_0_65_strict` | `mid` | 0.65 | `strict_1545` | 3 | 0 | -103.8 | -35.6 | -0.1038 |
| `mid_fee_1_0_strict` | `mid` | 1.0 | `strict_1545` | 3 | 0 | -108.0 | -37.0 | -0.108 |
| `half_spread_fee_0_0_strict` | `half_spread` | 0.0 | `strict_1545` | 3 | 0 | -99.0 | -34.0 | -0.099 |
| `half_spread_fee_0_65_strict` | `half_spread` | 0.65 | `strict_1545` | 3 | 0 | -106.8 | -36.6 | -0.1068 |
| `half_spread_fee_1_0_strict` | `half_spread` | 1.0 | `strict_1545` | 3 | 0 | -111.0 | -38.0 | -0.111 |
| `full_spread_stress_fee_0_0_strict` | `full_spread_stress` | 0.0 | `strict_1545` | 3 | 0 | -105.0 | -36.0 | -0.105 |
| `full_spread_stress_fee_0_65_strict` | `full_spread_stress` | 0.65 | `strict_1545` | 3 | 0 | -112.8 | -38.6 | -0.1128 |
| `full_spread_stress_fee_1_0_strict` | `full_spread_stress` | 1.0 | `strict_1545` | 3 | 0 | -117.0 | -40.0 | -0.117 |
| `mid_fee_0_nearest_close` | `mid` | 0.0 | `nearest_1545_window` | 3 | 0 | -96.0 | -33.0 | -0.096 |

## ข้อจำกัด
- ใช้เฉพาะ pilot window และมี closed trades น้อยมาก
- ยังไม่รวม VIX/VXV, macro, LLM gate, target/stop intraday, fill retry และ Sub-System B
- `nearest_1545_window` เป็น diagnostic เท่านั้น ไม่ควรใช้แทน forced-close exact quote โดยไม่ทดสอบเพิ่ม
