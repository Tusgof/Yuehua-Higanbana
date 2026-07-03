# Databento Pilot Sensitivity Report

## สถานะ
- ข้อสรุป: ยังสรุปไม่ได้
- Pilot decision: `healthy_enough_for_wider_data_pilot`
- รายงานนี้ใช้เพื่อดูความไวของ pilot เท่านั้น ไม่ใช่หลักฐานว่า strategy มี edge

## Decision Reasons
- worst full-spread stress total_net_pnl=242.0
- strict close skipped_trades=2
- trade_count is far below N >= 500
- pilot remains positive under stress, but this is not strategy acceptance

## Search Log And DSR
- Search log: `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\reports\experiments\search_logs\jan_2024_pilot_sensitivity_search_log.jsonl`
- Trial count: 10
- Selected metric: `total_net_pnl`
- DSR status: `blocked`
- DSR reason: DSR is not computed for this pilot sensitivity output because it is under-sampled, uses a one-month diagnostic window, and does not provide a full acceptance-grade return distribution.

## Scenario Summary
| Scenario | Fill | Fee/Contract | Close | Closed | Skipped | Net PnL | Worst | MDD |
|:--|:--|--:|:--|--:|--:|--:|--:|--:|
| `mid_fee_0_0_strict` | `mid` | 0.0 | `strict_1545` | 4 | 2 | 270.0 | -25.0 | -0.019305 |
| `mid_fee_0_65_strict` | `mid` | 0.65 | `strict_1545` | 4 | 2 | 259.6 | -27.6 | -0.021442 |
| `mid_fee_1_0_strict` | `mid` | 1.0 | `strict_1545` | 4 | 2 | 254.0 | -29.0 | -0.022603 |
| `half_spread_fee_0_0_strict` | `half_spread` | 0.0 | `strict_1545` | 4 | 2 | 266.0 | -26.0 | -0.020124 |
| `half_spread_fee_0_65_strict` | `half_spread` | 0.65 | `strict_1545` | 4 | 2 | 255.6 | -28.6 | -0.022271 |
| `half_spread_fee_1_0_strict` | `half_spread` | 1.0 | `strict_1545` | 4 | 2 | 250.0 | -30.0 | -0.023438 |
| `full_spread_stress_fee_0_0_strict` | `full_spread_stress` | 0.0 | `strict_1545` | 4 | 2 | 258.0 | -28.0 | -0.021773 |
| `full_spread_stress_fee_0_65_strict` | `full_spread_stress` | 0.65 | `strict_1545` | 4 | 2 | 247.6 | -30.6 | -0.02394 |
| `full_spread_stress_fee_1_0_strict` | `full_spread_stress` | 1.0 | `strict_1545` | 4 | 2 | 242.0 | -32.0 | -0.025118 |
| `mid_fee_0_nearest_close` | `mid` | 0.0 | `nearest_1545_window` | 4 | 2 | 270.0 | -25.0 | -0.019305 |

## ข้อจำกัด
- ใช้เฉพาะ pilot window และมี closed trades น้อยมาก
- ยังไม่รวม VIX/VXV, macro, LLM gate, target/stop intraday, fill retry และ Sub-System B
- `nearest_1545_window` เป็น diagnostic เท่านั้น ไม่ควรใช้แทน forced-close exact quote โดยไม่ทดสอบเพิ่ม
