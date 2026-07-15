# บันทึกการวิจัย: H-A2 Revised Condition Robustness

## 1. ข้อมูลพื้นฐาน

- Timestamp UTC: `2026-07-07T07:39:03Z`
- โครงการ: SPY 0DTE - Higanbana
- หัวข้อ: ตรวจความทนทานของ H-A2 revised condition ที่ล็อก threshold แล้ว
- ผู้บันทึก: Codex
- สถานะ: เสร็จสิ้น
- ระดับหลักฐาน: `E1`
- ข้อสรุป: `ยังสรุปไม่ได้`
- Artifact หลัก:
  - `experiments/h_a2_revised_condition_robustness_preregistration.json`
  - `reports/experiments/h_a2_revised_condition_robustness_summary.json`
  - `reports/experiments/h_a2_revised_condition_robustness_report.md`
  - `reports/experiments/search_logs/h_a2_revised_condition_robustness_search_log.jsonl`

## 2. วัตถุประสงค์

### อ่านแบบเร็ว

รอบนี้ไม่ได้หา threshold ใหม่ แต่ตรวจว่าเงื่อนไข `0.001` ที่ล็อกไว้ก่อนหน้านี้ยังดูทนพอหรือไม่ ผลคือ retained OOS 13 วันทำกำไรรวมได้ดีและแพ้เพียง 1 วัน แต่ sample ยังเล็กมาก จึงเป็นหลักฐานให้ “ตรวจต่อ” ไม่ใช่หลักฐานให้ “เชื่อแล้วเทรด”

คำถามของรอบนี้คือแยก “ผลดูดี” ออกจาก “ผลน่าเชื่อถือพอ” ตัวเลขดีขึ้นจริงในชุดข้อมูลนี้ แต่ถ้า trade เหลือน้อยเกินไป เราต้องถือว่าหลักฐานยังเปราะ

## 3. วิธีการและขั้นตอน

1. ใช้ locked threshold `0.001` จากรอบก่อนหน้า
2. ไม่ทำ threshold search ใหม่ และไม่เลือกค่าจาก OOS
3. เทียบ retained OOS, skipped OOS, และ baseline OOS
4. ตรวจ sample adequacy และ big-day dependency ในระดับ diagnostic

คำสั่งตรวจหลัก:

```powershell
python scripts\validate_h_a2_revised_condition_robustness.py
python -m unittest tests.test_h_a2_revised_condition_robustness
```

## 4. ผลการศึกษาและข้อมูลดิบ

| Metric | Baseline / Retained / Skipped |
|---|---:|
| Trade days | `34 / 13 / 21` |
| Avg implementable PnL | `7.087059 / 72.901538 / -33.655238` |
| Total implementable PnL | `240.96 / 947.72 / -706.76` |
| Loss count | `21 / 1 / 20` |
| Worst day PnL | `-55.56 / -11.56 / -55.56` |

ภาพที่ได้คือเงื่อนไขนี้แยกวันที่ดีและวันที่แย่ออกจากกันได้ในข้อมูลชุดนี้ วันที่ถูกเก็บไว้ทำกำไรเฉลี่ยสูงกว่าและมี loss count ต่ำกว่าอย่างชัดเจน แต่จำนวน retained trades แค่ 13 วันทำให้ผลยังอ่อนไหวมากต่อความบังเอิญหรือวันใหญ่ไม่กี่วัน

## 5. ปัญหา อุปสรรค และการแก้ไข

ระบบต้องติดป้าย `under-sampled` และ `underpowered` เพราะ retained OOS trade days ยังไม่พอสำหรับ `MinTRL` / `PSR` รอบนี้จึงเป็น robustness diagnostic เพื่อจัดลำดับงาน ไม่ใช่ deployment gate

สิ่งที่ห้ามสรุปจากรอบนี้:

- ห้ามบอกว่า revised condition ผ่าน acceptance
- ห้ามอ้าง `E2` หรือ `paper trading`
- ห้ามเปลี่ยน threshold ต่อโดยไม่มี preregistration ใหม่

## 6. ข้อสรุปและก้าวต่อไป

ข้อสรุป: `ยังสรุปไม่ได้` แต่ H-A2 revised condition ยังน่าศึกษาต่อในระดับ `E1`

เงื่อนไขนี้ยังไม่ถูกหักล้างจาก robustness เบื้องต้น แต่ก็ยังไม่พ้นข้อจำกัด sample เล็ก ก้าวต่อไปควรเน้น validation ที่เพิ่มข้อมูลจริงหรือ exact replay มากกว่าการปรับแต่งเงื่อนไขต่อ

ก้าวต่อไป:

1. ทำ exact replay เมื่อข้อมูลพร้อม
2. ถ้าจะทำ follow-up ต้อง pre-register และไม่เปลี่ยน threshold `0.001` โดยพลการ
