# บันทึกการวิจัย: H-A2 Delayed-Entry Condition

## 1. ข้อมูลพื้นฐาน

- Timestamp UTC: `2026-07-07T07:36:51Z`
- โครงการ: SPY 0DTE - Higanbana
- หัวข้อ: ตรวจความเป็นไปได้ของ H-A2 แบบ delayed entry
- ผู้บันทึก: Codex
- สถานะ: เสร็จสิ้น
- ระดับหลักฐาน: `E1`
- ข้อสรุป: `ยังสรุปไม่ได้`
- Artifact หลัก:
  - `experiments/h_a2_delayed_entry_condition_preregistration.json`
  - `reports/experiments/h_a2_delayed_entry_condition_summary.json`
  - `reports/experiments/h_a2_delayed_entry_condition_report.md`
  - `reports/experiments/search_logs/h_a2_delayed_entry_condition_search_log.jsonl`

## 2. วัตถุประสงค์

### อ่านแบบเร็ว

หลังพบว่าเงื่อนไขเดิมรู้ครบช้ากว่า `09:35 ET` รอบนี้ถามต่อว่า ถ้าเรายอมเปลี่ยนเป็น delayed-entry strategy ที่รู้ข้อมูลครบแถว `09:45 ET` แนวคิดนี้ไปต่อได้ไหม คำตอบคือยังสรุปไม่ได้ เพราะ artifact ปัจจุบันยังไม่มี quote/fill ที่ 09:45 ให้คำนวณ `implementable PnL` จริง

รอบนี้จึงช่วยแยกสองเรื่องออกจากกัน: เงื่อนไขอาจมีเหตุผลเชิงกลไก แต่ยังไม่ใช่ระบบที่เทรดได้ ถ้าไม่มีราคาที่เข้าออกได้จริงตามเวลาใหม่

## 3. วิธีการและขั้นตอน

1. ใช้ locked condition เดิมที่รู้ครบหลัง `09:45 ET`
2. ตรวจจำนวน trade ที่ retained/skipped จากข้อมูลเดิม
3. ไม่ทำ threshold search ใหม่ และไม่ tune OOS
4. ตรวจว่ามี quote/fill `09:45 ET` ที่ใช้คำนวณ `implementable PnL` หรือไม่

คำสั่งตรวจหลัก:

```powershell
python scripts\validate_h_a2_delayed_entry_condition.py
python -m unittest tests.test_h_a2_delayed_entry_condition
```

## 4. ผลการศึกษาและข้อมูลดิบ

| Metric | ค่า |
|---|---:|
| Baseline OOS non-risk trade days | `34` |
| Retained OOS trade days | `13` |
| Skipped OOS trade days | `21` |
| OOS retention rate | `0.382353` |
| Threshold search used | `false` |
| Trial count | `0` |

ผลที่ได้คือ delayed-entry idea ยังน่าสนใจในเชิงกลไก เพราะ retained/skipped pattern ยังคล้ายกับเงื่อนไขที่ดูดี แต่ยังไม่มีราคาที่เวลาเข้าใหม่ จึงยังไม่รู้ว่าเมื่อนำไปคำนวณ option จริงหลัง spread และค่าธรรมเนียม ผลจะยังดีอยู่หรือไม่

## 5. ปัญหา อุปสรรค และการแก้ไข

ปัญหาหลักคือไม่มี auditable `09:45 ET` option quote/fill ใน artifact ปัจจุบัน ถ้าจะทำ delayed-entry จริง ต้อง pre-register การหา quote และ cost model ใหม่ก่อน ไม่ใช่นำ PnL ของ entry เวลาเดิมมาแทน

สิ่งที่ห้ามสรุปจากรอบนี้:

- ห้ามบอกว่า delayed-entry edge ผ่านแล้ว
- ห้ามอ้าง `implementable PnL` ของ delayed entry
- ห้ามซื้อข้อมูลหรือขอ IBKR จากผลนี้โดยไม่มีแผนแยก

## 6. ข้อสรุปและก้าวต่อไป

ข้อสรุป: `ยังสรุปไม่ได้` เพราะยังเป็น proxy-only สำหรับ delayed entry

แนวคิดนี้ยังไม่ตาย แต่ต้องถูกแยกออกจาก original-entry branch อย่างชัดเจน ถ้าจะทำต่อ ต้องวัดราคาที่เข้าออกตามเวลาใหม่จริง

ก้าวต่อไป:

1. แก้ H-A2 ให้เป็น original-entry rule ที่ใช้ข้อมูล `09:35 ET` จริง
2. ถ้าจะทำ delayed entry ต้อง pre-register acquisition plan แยกก่อน
