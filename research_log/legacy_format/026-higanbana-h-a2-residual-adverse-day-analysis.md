# บันทึกการวิจัย: H-A2 Residual Adverse-Day Analysis

## 1. ข้อมูลพื้นฐาน

- Timestamp UTC: `2026-07-07T07:39:02Z`
- โครงการ: SPY 0DTE - Higanbana
- หัวข้อ: วิเคราะห์วันที่ H-A2 ยังแพ้หลังตัด macro/VIX risk
- ผู้บันทึก: Codex
- สถานะ: เสร็จสิ้น
- ระดับหลักฐาน: `E1`
- ข้อสรุป: `ยังสรุปไม่ได้`
- Artifact หลัก:
  - `experiments/h_a2_residual_adverse_day_analysis_preregistration.json`
  - `reports/diagnostics/h_a2_residual_adverse_day_analysis.json`
  - `reports/diagnostics/h_a2_residual_adverse_day_analysis.md`
  - `reports/diagnostics/search_logs/h_a2_residual_adverse_day_analysis_search_log.jsonl`

## 2. วัตถุประสงค์

### อ่านแบบเร็ว

รอบนี้ถามว่า H-A2 แพ้เพราะเจอวัน macro/VIX เสี่ยงเท่านั้นหรือยังมี failure mode อื่นซ่อนอยู่ ผลคือยังมีวันที่แพ้จำนวนมากแม้อยู่ในกลุ่ม non-risk โดยเฉพาะวันที่ `5-minute followthrough` เป็นลบ จึงไม่ควรรีบซื้อข้อมูลหรือทำ exact replay เพิ่มก่อนเข้าใจว่ากลยุทธ์แพ้เพราะอะไร

งานนี้เป็นจุดเปลี่ยนสำคัญ เพราะช่วยเปลี่ยนคำถามจาก “ซื้อข้อมูลเพิ่มไหม” เป็น “สมมติฐานเดิมพลาดตรงไหน” ถ้ายังตอบคำถามหลังไม่ได้ การซื้อข้อมูลเพิ่มอาจแค่ทำให้เราแพงขึ้นโดยไม่ได้ฉลาดขึ้น

## 3. วิธีการและขั้นตอน

1. ใช้ trade days เดิม 90 วัน และแบ่งกลุ่มด้วย macro/VIX label ที่มีอยู่
2. ตรวจ non-risk losing days และ macro-only losing days
3. ดูว่าวันแพ้เกี่ยวข้องกับ `5-minute followthrough` หรือไม่
4. ไม่สร้าง filter ใหม่จาก OOS และไม่อ้าง acceptance

คำสั่งตรวจหลัก:

```powershell
python scripts\validate_h_a2_residual_adverse_day_analysis.py
python -m unittest tests.test_h_a2_residual_adverse_day_analysis
```

## 4. ผลการศึกษาและข้อมูลดิบ

| Metric | ค่า |
|---|---:|
| Trade days ทั้งหมด | `90` |
| Non-risk trade days | `64` |
| Non-risk losing days | `40` |
| Macro-only trade days | `26` |
| Macro-only losing days | `21` |
| Trial count | `4` |
| Evidence tier | `E1` |

ผลสำคัญคือ “non-risk” ไม่ได้แปลว่าปลอดภัย กลุ่มที่ไม่มี macro/VIX risk ตาม label เดิมยังแพ้ถึง 40 จาก 64 trade days แปลว่า H-A2 ยังมีช่องโหว่ด้านสภาพตลาดช่วงเปิด หรือสัญญาณเข้า trade ยังหยาบเกินไป

## 5. ปัญหา อุปสรรค และการแก้ไข

sample ยังเล็ก และเมื่อแตกเป็น bucket ย่อยก็ยิ่งเล็กลง ผลนี้จึงเป็น diagnostic เพื่อชี้ทางแก้สมมติฐาน ไม่ใช่การยืนยัน edge สิ่งที่แก้ได้แล้วคือเรารู้ว่าการตัด macro/VIX อย่างเดียวไม่พอ สิ่งที่ยังแก้ไม่ได้คือยังไม่มี validation sample ใหญ่พอเพื่อบอกว่าการเพิ่มเงื่อนไขใหม่จะรอดจริงหรือไม่

สิ่งที่ห้ามสรุปจากรอบนี้:

- ห้ามบอกว่า H-A2 ใช้งานได้จริงแล้ว
- ห้ามบอกว่า macro/VIX filter เพียงพอ
- ห้ามเริ่ม exact replay, paid data, IBKR, LLM หรือ `paper trading` จากผลนี้โดยตรง

## 6. ข้อสรุปและก้าวต่อไป

ข้อสรุป: `ยังสรุปไม่ได้` แต่ควร revise H-A2 ก่อนทำ exact replay ต่อ

หลักฐานบอกว่าปัญหาไม่ได้อยู่แค่วันข่าวหรือวัน VIX สูง ยังมี residual losses ในวันที่ดูสะอาดกว่า ดังนั้นสมมติฐาน H-A2 ต้องแคบและชัดขึ้น โดยเฉพาะเรื่องแรงตามต่อหลังเปิดตลาด

ก้าวต่อไป:

1. Pre-register เงื่อนไข H-A2 ที่เพิ่ม opening-followthrough failure-mode checks
2. ทดสอบเงื่อนไขใหม่แบบมี guardrail ก่อน action ที่แพงกว่า
