# H-G1 Gamma/OI Regime Diagnostic

- Status: `blocked`
- Conclusion: ยังสรุปไม่ได้
- Evidence tier: `E1`
- Strategy use: `diagnostic_only_blocked_by_policy_gates`
- Decision time ET: `09:35:00`
- Dates: 10
- Quote rows: 2822
- Computed Greeks rows: 2089

## Gates

| Gate | Status | Notes |
|:--|:--|:--|
| `coverage` | `blocked` | bucket_weighted_coverage_gate_failed |
| `timestamp_discipline` | `pass` |  |
| `stability` | `pass` |  |
| `economic_sign` | `pass` |  |
| `search_log` | `pass` | No gamma threshold, quartile, or best bucket was selected in this diagnostic. |

## Per-Date Summary

| Date | Quotes | Greeks | Underlying | OI | Required bucket blockers |
|:--|--:|--:|--:|--:|:--|
| 2023-08-09 | 254 | 199 | 254 | 254 | otm_call_computed_rate_below_60pct |
| 2023-09-13 | 250 | 184 | 250 | 250 | otm_put_computed_rate_below_60pct |
| 2023-10-27 | 330 | 235 | 330 | 330 | None |
| 2023-12-29 | 394 | 341 | 394 | 394 | None |
| 2024-01-03 | 124 | 59 | 124 | 124 | otm_put_computed_rate_below_60pct |
| 2024-05-21 | 218 | 197 | 218 | 218 | otm_call_computed_rate_below_60pct |
| 2024-08-05 | 272 | 209 | 272 | 242 | None |
| 2024-08-07 | 370 | 256 | 370 | 370 | None |
| 2024-10-31 | 394 | 238 | 394 | 394 | None |
| 2024-12-18 | 216 | 171 | 216 | 216 | otm_call_computed_rate_below_60pct |

## Decision

ยังสรุปไม่ได้: H-G1 ยังไม่ผ่าน policy v2 จึงห้ามใช้ signed-OI gamma proxy เป็น NOVI/net-gamma strategy filter
