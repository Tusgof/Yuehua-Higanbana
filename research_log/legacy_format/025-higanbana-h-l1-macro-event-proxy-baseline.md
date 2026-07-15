# บันทึกการวิจัย: H-L1 Macro Event Proxy Baseline

## 1. ข้อมูลพื้นฐาน

- Timestamp UTC: `2026-07-07T07:39:03Z`
- โครงการ: SPY 0DTE - Higanbana
- หัวข้อ: สร้าง baseline จาก macro/VIX ก่อนทดสอบ LLM หรือข่าวจริง
- ผู้บันทึก: Codex
- สถานะ: เสร็จสิ้น
- ระดับหลักฐาน: `E1`
- ข้อสรุป: `ยังสรุปไม่ได้`
- Artifact หลัก:
  - `experiments/h_l1_macro_event_proxy_preregistration.json`
  - `reports/experiments/h_l1_macro_event_proxy_baseline_summary.json`
  - `reports/experiments/h_l1_macro_event_proxy_baseline_report.md`
  - `reports/experiments/search_logs/h_l1_macro_event_proxy_baseline_search_log.jsonl`

## 2. วัตถุประสงค์

### อ่านแบบเร็ว

รอบนี้ยังไม่ได้ทดสอบ LLM และยังไม่ได้ทดสอบข่าวจริง เราสร้าง baseline จาก macro calendar และ VIX/VXV เพื่อใช้เป็นคู่เทียบก่อน ถ้าในอนาคต LLM จะมีประโยชน์จริง มันต้องให้ข้อมูลเพิ่มกว่ากฎพื้นฐานพวกนี้ ไม่ใช่แค่บอกซ้ำว่าวัน macro หรือวัน VIX สูงน่ากลัว

งานนี้ช่วยกันความเข้าใจผิดแบบสำคัญ: ระบบที่ใส่ LLM แล้วดูดี อาจไม่ได้ดีเพราะ LLM เข้าใจตลาด แต่อาจดีเพราะมันเลียนแบบ label macro/VIX ที่เรามีอยู่แล้ว

## 3. วิธีการและขั้นตอน

1. ใช้ macro calendar และ VIX/VXV ที่มี timestamp ชัดเจน
2. แบ่ง trade outcome เดิมตามกลุ่ม macro event, VIX regime, และกลุ่มที่สะอาดกว่า
3. ไม่เรียก GDELT ไม่เรียก LLM และไม่ซื้อข้อมูลข่าว
4. บันทึกผลนี้เป็น deterministic baseline ไม่ใช่ prompt experiment

คำสั่งตรวจหลัก:

```powershell
python scripts\validate_h_l1_macro_event_proxy_baseline_summary.py
python -m unittest tests.test_h_l1_macro_event_proxy_baseline
```

## 4. ผลการศึกษาและข้อมูลดิบ

| Metric | ค่า |
|---|---:|
| Evidence tier | `E1` |
| LLM call | `false` |
| Real news tested | `false` |
| GDELT retry | `false` |
| Trial count | `4` |
| DSR status | `diagnostic_not_acceptance` |

ผลคือ baseline จาก macro/VIX มีข้อมูลพอเป็นจุดเทียบในอนาคต แต่ยังไม่มีข่าวจริงหรือ LLM เข้ามาเกี่ยวข้อง ดังนั้นรอบนี้ยังตอบไม่ได้ว่า LLM ช่วยกัน tail risk ได้จริงไหม หรือแค่ทำซ้ำสิ่งที่ deterministic rule ทำได้อยู่แล้ว

## 5. ปัญหา อุปสรรค และการแก้ไข

ข้อจำกัดคือข้อมูลนี้เป็น label เชิงเหตุการณ์ ไม่ใช่ข่าวที่ `timestamp-clean` และไม่ใช่ sentiment จาก LLM จึงใช้แทนการทดลอง H-L1 จริงไม่ได้

สิ่งที่ห้ามสรุปจากรอบนี้:

- ห้ามบอกว่า LLM gate ถูกทดสอบแล้ว
- ห้ามบอกว่าข่าวจริงถูกทดสอบแล้ว
- ห้ามใช้ผลนี้เป็นเหตุผลเปิด `paper trading`

## 6. ข้อสรุปและก้าวต่อไป

ข้อสรุป: `ยังสรุปไม่ได้` สำหรับ H-L1 แต่เราได้ baseline ที่ LLM ต้องเอาชนะในอนาคต

บทเรียนของรอบนี้คือ ก่อนจะใช้ LLM เราต้องรู้ก่อนว่ากฎง่าย ๆ จาก macro/VIX ทำได้แค่ไหน มิฉะนั้นเราจะไม่รู้ว่า LLM เพิ่มคุณค่าจริงหรือเพิ่มแค่ความซับซ้อน

ก้าวต่อไป:

1. ปลดล็อกข่าวจริงที่ `timestamp-clean` ก่อน
2. ออกแบบ prompt/LLM measurement ให้เทียบกับ baseline นี้อย่างยุติธรรม
