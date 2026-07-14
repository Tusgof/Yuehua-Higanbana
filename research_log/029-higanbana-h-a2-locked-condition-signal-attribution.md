# บันทึกการวิจัย: H-A2 Locked Condition Signal Attribution

## 1. ข้อมูลพื้นฐาน

- Timestamp UTC: `2026-07-07T07:38:53Z`
- โครงการ: SPY 0DTE - Higanbana
- หัวข้อ: ตรวจว่า locked condition ของ H-A2 รู้ทันเวลา entry จริงหรือไม่
- ผู้บันทึก: Codex
- สถานะ: เสร็จสิ้น
- ระดับหลักฐาน: `E1`
- ข้อสรุป: `ยังสรุปไม่ได้`
- Artifact หลัก:
  - `experiments/h_a2_locked_condition_signal_attribution_preregistration.json`
  - `reports/experiments/h_a2_locked_condition_signal_attribution_summary.json`
  - `reports/experiments/h_a2_locked_condition_signal_attribution_report.md`
  - `reports/experiments/search_logs/h_a2_locked_condition_signal_attribution_search_log.jsonl`

## 2. วัตถุประสงค์

### อ่านแบบเร็ว

รอบนี้เจอปัญหาสำคัญ: เงื่อนไข H-A2 ที่ดูดีไม่ได้รู้ครบตอน `09:35 ET` เพราะมี feature บางส่วนที่ต้องรอหน้าต่าง 15 นาทีจบก่อน ดังนั้นห้ามใช้ full condition นี้เป็น original-entry filter ที่ 09:35 ต้องถือเป็น delayed-entry candidate หรือ diagnostic proxy เท่านั้น

นี่ไม่ใช่เรื่องเล็ก เพราะถ้าเราเผลอใช้ข้อมูลที่รู้หลังเวลา entry มาตัดสิน trade ที่เวลา 09:35 ผล backtest จะสวยเกินจริงจาก lookahead leakage

## 3. วิธีการและขั้นตอน

1. ตรวจว่าแต่ละ feature ใน locked condition รู้ได้ตอนเวลาใด
2. เทียบเวลารู้ข้อมูลกับ baseline entry time `09:35:00 ET`
3. ตรวจ threshold provenance ว่าไม่ได้ search ค่าใหม่
4. แยก allowed claim ระหว่าง delayed-entry candidate กับ original-entry rule

คำสั่งตรวจหลัก:

```powershell
python scripts\validate_h_a2_locked_condition_signal_attribution.py
python -m unittest tests.test_h_a2_locked_condition_signal_attribution
```

## 4. ผลการศึกษาและข้อมูลดิบ

| Metric | ค่า |
|---|---:|
| Baseline entry time | `09:35:00 ET` |
| Earliest full-feature completion | `09:45:00 ET` |
| Locked threshold | `0.001` |
| Retained OOS trade days | `13` |
| Skipped OOS trade days | `21` |
| Classification | `delayed_entry_candidate_and_diagnostic_proxy_only` |

ผลนี้บอกว่า threshold อาจล็อกสะอาด แต่ feature set ไม่สะอาดด้านเวลา ถ้าใช้กับ entry เดิมที่ 09:35 เงื่อนไขนี้รู้ข้อมูลไม่ทัน จึงใช้เป็นกฎเข้า trade เดิมไม่ได้

## 5. ปัญหา อุปสรรค และการแก้ไข

ข้อจำกัดนี้เป็น timestamp leakage risk โดยตรง การแก้คือห้ามเอา full condition ไปปะบน original entry ต้องเลือกทางใดทางหนึ่ง: แยกเป็น delayed-entry branch ที่ต้องมีราคาที่เวลาใหม่ หรือถอยกลับไปสร้าง original-entry rule ที่ใช้เฉพาะข้อมูลที่รู้ทัน 09:35

สิ่งที่ห้ามสรุปจากรอบนี้:

- ห้ามบอกว่า locked condition ใช้เปิด trade ที่ `09:35 ET` ได้
- ห้ามบอกว่า H-A2 edge validated
- ห้ามทำ exact replay หรือ `paper trading` จากผลนี้โดยตรง

## 6. ข้อสรุปและก้าวต่อไป

ข้อสรุป: `ยังสรุปไม่ได้` สำหรับ edge แต่สรุปด้าน methodology ได้ว่า full condition ไม่ใช่ original-entry rule

ผลนี้ทำให้เราต้องระวังมากขึ้นกับทุกสัญญาณที่ใช้ข้อมูลหลังเวลา entry ต่อให้ตัวเลขดูดี ก็ใช้ไม่ได้ถ้ามันรู้ข้อมูลช้าเกินเวลาตัดสินใจจริง

ก้าวต่อไป:

1. ทดสอบ delayed entry แบบ pre-registered ถ้าจะเดินสายนั้น
2. หรือแก้ H-A2 ให้เป็น timestamp-clean original-entry rule
