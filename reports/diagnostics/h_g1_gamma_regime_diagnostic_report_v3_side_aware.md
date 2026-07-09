# H-G1 Gamma/OI Regime Diagnostic

- Status: `pass_diagnostic_only`
- Conclusion: ผ่าน
- Evidence tier: `E1`
- Required bucket policy: `h_g1_required_bucket_policy_v3_side_aware`
- Strategy use: `diagnostic_only_not_strategy_ready`
- Network used: `False`
- Paid data used: `False`
- Strategy PnL used: `False`
- Decision time ET: `09:35:00`
- Dates: 10
- Quote rows: 2822
- Computed Greeks rows: 2089

## Gates

| Gate | Status | Notes |
|:--|:--|:--|
| `coverage` | `pass` |  |
| `timestamp_discipline` | `pass` |  |
| `stability` | `pass` |  |
| `economic_sign` | `pass` |  |
| `search_log` | `pass` | No gamma threshold, quartile, or best bucket was selected in this diagnostic. |

## Per-Date Summary

| Date | Quotes | Greeks | Underlying | OI | Required bucket blockers |
|:--|--:|--:|--:|--:|:--|
| 2023-08-09 | 254 | 199 | 254 | 254 | None |
| 2023-09-13 | 250 | 184 | 250 | 250 | None |
| 2023-10-27 | 330 | 235 | 330 | 330 | None |
| 2023-12-29 | 394 | 341 | 394 | 394 | None |
| 2024-01-03 | 124 | 59 | 124 | 124 | None |
| 2024-05-21 | 218 | 197 | 218 | 218 | None |
| 2024-08-05 | 272 | 209 | 272 | 242 | None |
| 2024-08-07 | 370 | 256 | 370 | 370 | None |
| 2024-10-31 | 394 | 238 | 394 | 394 | None |
| 2024-12-18 | 216 | 171 | 216 | 216 | None |

## Decision

ผ่านเฉพาะ data-validity diagnostic: ยังไม่ใช่ strategy acceptance และยังต้องมี backtest/MinTRL/PSR ก่อนใช้เป็น trading gate
