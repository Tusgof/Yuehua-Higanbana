# H-A2 Fresh OOS Timestamp-Clean Checkpoint

## คำถามและข้อสรุป

- คำถาม: ภายใต้ prior-close VIX ต่ำกว่า 25 และไม่มีข่าวมหภาคสำคัญ สัญญาณ ORB ที่รู้ได้จริงเวลา 09:35 ทำให้ SPY 0DTE debit vertical spread หลังต้นทุนมีผลตอบแทนเฉลี่ยเป็นบวกในข้อมูล OOS ใหม่ 20 วันหรือไม่
- ข้อสรุป: `ยังสรุปไม่ได้`
- เหตุผล: การทดลองใช้ราคาปิดของแท่งที่ประทับเวลา 09:35 ซึ่งรู้ได้ประมาณ 09:36 แต่ใช้ราคาออปชันเวลา 09:35 เป็นราคาเข้า จึงเกิด entry-before-signal mismatch และ PnL ใช้อ้างอิงสมมติฐานไม่ได้

## การแก้ Lookahead และข้อจำกัดเวลา

กฎเดิมใช้ราคา 15:45 คัดเลือกสถานะย้อนหลัง จึงถูกตัดออกก่อนอ่านผลชุดนี้ อย่างไรก็ตาม ราคาปิดของแท่งที่ประทับเวลา 09:35 จะรู้ได้ประมาณ 09:36 ผลรอบนี้จึงเป็น 09:36 proxy ไม่ใช่ exact 09:35

## ผลรวม

- Candidate ที่พบย้อนหลัง: `6`
- Replay ที่คำนวณได้: `6`
- Mechanical PnL (invalid for inference): `249.64`
- PnL valid for inference: `False`
- Under-sampled: `True`
- Underpowered: `True`

## รายวัน

| Date | VIX bucket | Quality warning | ORB direction | Candidate | Replay | Implementable PnL |
|:--|:--|:--:|:--:|:--:|:--:|--:|
| 2025-08-13 | low_vix_2025 | True | None | False | not_candidate |  |
| 2025-08-14 | low_vix_2025 | False | call | True | complete | 2.44 |
| 2025-08-15 | low_vix_2025 | False | None | False | not_candidate |  |
| 2025-08-19 | low_vix_2025 | True | None | False | not_candidate |  |
| 2025-08-25 | low_vix_2025 | True | None | False | not_candidate |  |
| 2025-08-26 | low_vix_2025 | False | None | False | not_candidate |  |
| 2025-08-27 | low_vix_2025 | False | None | False | not_candidate |  |
| 2025-08-28 | low_vix_2025 | False | None | False | not_candidate |  |
| 2025-09-12 | low_vix_2025 | True | None | False | not_candidate |  |
| 2025-09-15 | low_vix_2025 | False | None | False | not_candidate |  |
| 2026-04-13 | normal_vix_2026 | False | None | False | not_candidate |  |
| 2026-04-14 | normal_vix_2026 | False | call | True | complete | 146.44 |
| 2026-04-15 | normal_vix_2026 | False | None | False | not_candidate |  |
| 2026-04-16 | normal_vix_2026 | False | None | False | not_candidate |  |
| 2026-04-17 | normal_vix_2026 | False | call | True | complete | 72.44 |
| 2026-04-20 | normal_vix_2026 | False | None | False | not_candidate |  |
| 2026-04-21 | normal_vix_2026 | False | put | True | complete | 128.44 |
| 2026-04-22 | normal_vix_2026 | False | put | True | complete | -49.56 |
| 2026-04-23 | normal_vix_2026 | False | None | False | not_candidate |  |
| 2026-04-24 | normal_vix_2026 | False | put | True | complete | -50.56 |

## Checkpoint

- Stop expansion: `True`
- Reasons: `['exact_0935_timestamp_semantics_not_satisfied']`
- Next: Stop expansion. Treat this as a 09:36 proxy only; pre-register an actually observable 09:35 rule or an explicit 09:36 rule on data whose outcomes have not been viewed.
