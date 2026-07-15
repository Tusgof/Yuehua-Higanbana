# บันทึกการวิจัย: H-A2 Revised Opening-Followthrough Condition

## 1. ข้อมูลพื้นฐาน

- Timestamp UTC: `2026-07-07T07:39:03Z`
- โครงการ: SPY 0DTE - Higanbana
- หัวข้อ: ทดสอบ H-A2 ที่เพิ่มเงื่อนไข opening followthrough
- ผู้บันทึก: Codex
- สถานะ: เสร็จสิ้น
- ระดับหลักฐาน: `E1`
- ข้อสรุป: `ยังสรุปไม่ได้`
- Artifact หลัก:
  - `experiments/h_a2_revised_opening_followthrough_condition_preregistration.json`
  - `reports/experiments/h_a2_revised_opening_followthrough_condition_summary.json`
  - `reports/experiments/h_a2_revised_opening_followthrough_condition_report.md`
  - `reports/experiments/search_logs/h_a2_revised_opening_followthrough_condition_search_log.jsonl`

## 2. วัตถุประสงค์

### อ่านแบบเร็ว

รอบนี้ลองแก้ H-A2 จากบทเรียนก่อนหน้า: ถ้าวันที่แพ้จำนวนมากเกี่ยวกับแรงตามต่อหลังเปิดตลาด เราควรตรวจว่า opening followthrough ช่วยคัดวันที่ควรเทรดได้ไหม ผลดูดีมากใน OOS เพราะ loss count ลดจาก 21 เหลือ 1 วัน และค่าเฉลี่ย PnL ดีขึ้น แต่ trade ที่เหลือมีแค่ 13 วัน จึงยังไม่พอสำหรับ acceptance

ผลนี้น่าสนใจ แต่ต้องอ่านอย่างระวัง ตัวเลขที่สวยจาก sample เล็กอาจเป็น edge จริงก็ได้ หรืออาจเป็นการเลือกช่วงที่โชคดีก็ได้ งานนี้จึงเป็นการตั้ง candidate condition ไม่ใช่คำตอบสุดท้าย

## 3. วิธีการและขั้นตอน

1. ใช้ threshold grid ที่ล็อกจาก train เท่านั้น ไม่ใช้ OOS เลือกค่า
2. เงื่อนไขที่เลือกคือ `train_threshold_0.001`
3. เทียบ baseline non-risk กับ revised condition ทั้ง train และ OOS
4. ตรวจ search log, sample adequacy, และห้ามอ้าง `E2`

คำสั่งตรวจหลัก:

```powershell
python scripts\validate_h_a2_revised_opening_followthrough_condition.py
python -m unittest tests.test_h_a2_revised_opening_followthrough_condition
```

## 4. ผลการศึกษาและข้อมูลดิบ

| Metric | ค่า |
|---|---:|
| Baseline OOS non-risk trade days | `34` |
| Revised OOS trade days | `13` |
| Skipped OOS trade days | `21` |
| Baseline OOS loss count | `21` |
| Revised OOS loss count | `1` |
| OOS avg PnL change | `65.814479` |
| Locked threshold | `0.001` |
| Trial count | `7` |

ตัวเลขบอกว่าเงื่อนไขใหม่ช่วยตัดวันที่แย่ออกได้มากในข้อมูลที่มีอยู่ แต่ก็แลกด้วยการทำให้จำนวน trade ลดลงแรงมาก จาก 34 วันเหลือ 13 วัน นี่คือสัญญาณว่าเงื่อนไขอาจจับกลไกจริงได้ แต่ก็เพิ่มความเสี่ยงเรื่อง sample เล็กและ selection bias

## 5. ปัญหา อุปสรรค และการแก้ไข

ข้อจำกัดหลักคือ retained OOS เหลือแค่ 13 วัน ทำให้ `MinTRL` / `PSR` ยังยืนยันไม่ได้ แม้ตัวเลขจะดูดีมากก็ตาม อีกจุดที่ต้องระวังคือการทดลองมี 7 trial จึงต้องรักษา search log และห้ามเลือกผลที่ดูดีที่สุดไปเล่าเหมือนเป็น edge ที่พิสูจน์แล้ว

สิ่งที่ห้ามสรุปจากรอบนี้:

- ห้ามบอกว่า H-A2 ผ่านแล้ว
- ห้ามบอกว่า threshold `0.001` เป็น deployable filter โดยไม่มี exact replay
- ห้ามใช้ผลนี้เปิด `paper trading`

## 6. ข้อสรุปและก้าวต่อไป

ข้อสรุป: `ยังสรุปไม่ได้` แต่เงื่อนไข opening followthrough เป็นกลไกที่ควรตรวจต่อ

ผล OOS ดีขึ้นชัด แต่จำนวนตัวอย่างยังต่ำเกินกว่าจะยืนยัน edge รอบต่อไปต้องตรวจความทนทานและ timestamp discipline ให้ชัด ไม่ใช่รีบเพิ่ม filter ใหม่ทับผลที่ยังไม่แน่น

ก้าวต่อไป:

1. เก็บเงื่อนไขนี้เป็น `E1 prioritization evidence`
2. ทำ robustness check และ exact replay เมื่อข้อมูลพร้อม
