# บันทึกการวิจัย: H-A2 Original-Entry Robustness Prioritization

## 1. ข้อมูลพื้นฐาน

- Timestamp UTC: `2026-07-07T07:39:02Z`
- โครงการ: SPY 0DTE - Higanbana
- หัวข้อ: ตรวจความทนทานและลำดับงานของ H-A2 original-entry revision
- ผู้บันทึก: Codex
- สถานะ: เสร็จสิ้น
- ระดับหลักฐาน: `E1`
- ข้อสรุป: `ยังสรุปไม่ได้`
- Artifact หลัก:
  - `experiments/h_a2_original_entry_robustness_prioritization_preregistration.json`
  - `reports/experiments/h_a2_original_entry_robustness_prioritization_summary.json`
  - `reports/experiments/h_a2_original_entry_robustness_prioritization_report.md`
  - `reports/experiments/search_logs/h_a2_original_entry_robustness_prioritization_search_log.jsonl`

## 2. วัตถุประสงค์

### อ่านแบบเร็ว

รอบนี้ตรวจว่า original-entry rule ที่สะอาดด้านเวลา ยังพอทนต่อการตรวจพื้นฐานหรือไม่ ผลคือ rule ยัง directionally useful แต่ retained OOS มีแค่ 14 trade days และยังขาด high-VIX bucket ที่พอใช้ จึงยังไม่ควร exact replay แบบใหญ่หรืออ้าง `E2`

นี่เป็นขั้นจัดลำดับงาน ไม่ใช่ขั้นพิสูจน์ edge คำตอบที่ได้คือควรหา independent validation ก่อนเพิ่มความซับซ้อนให้ระบบ

## 3. วิธีการและขั้นตอน

1. ใช้ rule จาก H-A2 original-entry revision โดยไม่เปลี่ยน threshold
2. ตรวจ robustness และ skip-cost tradeoff จากข้อมูลในเครื่อง
3. ไม่ทำ parameter search ใหม่ และไม่ tune OOS
4. เลือก next action จาก blocker จริง เช่น sample size และ regime coverage

คำสั่งตรวจหลัก:

```powershell
python scripts\validate_h_a2_original_entry_robustness_prioritization.py
python -m unittest tests.test_h_a2_original_entry_robustness_prioritization
```

## 4. ผลการศึกษาและข้อมูลดิบ

| Metric | ค่า |
|---|---:|
| Baseline OOS non-risk trade days | `34` |
| Retained OOS trade days | `14` |
| Skipped OOS trade days | `20` |
| OOS retention rate | `0.411765` |
| Retained train trade days | `16` |
| Parameter search used | `false` |
| Trial count | `0` |

ผลคือ rule ไม่พังทันทีเมื่อถูกตรวจแบบ timestamp-clean แต่ยังมีข้อจำกัดหนัก: trade ที่เหลือมีน้อย และ regime coverage ยังไม่พอ โดยเฉพาะช่วง high-VIX ที่ควรมีไว้ทดสอบว่ากลยุทธ์รอดในสภาพตลาดต่างกันหรือไม่

## 5. ปัญหา อุปสรรค และการแก้ไข

retained OOS 14 วันยังไม่พอสำหรับ acceptance และยังไม่มี high-VIX retained bucket ที่ช่วยทดสอบข้าม regime ได้ดีพอ ผลนี้จึงยังไม่ตอบว่าระบบมี edge จริงหรือแค่เลือก sample ถูกช่วง

สิ่งที่ห้ามสรุปจากรอบนี้:

- ห้ามบอกว่า H-A2 ผ่าน `E2`
- ห้ามเริ่ม `paper trading`
- ห้ามซื้อข้อมูลหรือทำ exact replay โดยไม่ pre-register validation plan

## 6. ข้อสรุปและก้าวต่อไป

ข้อสรุป: `ยังสรุปไม่ได้` แต่ original-entry rule ควรถูกใช้เป็น candidate สำหรับ independent validation

หลักฐานยังคงมีทิศทางบวก แต่ blocker ด้าน sample และ regime ยังหนัก งานถัดไปต้องเพิ่มความน่าเชื่อถือของหลักฐาน ไม่ใช่เพิ่มจำนวนตัวแปร

ก้าวต่อไป:

1. Pre-register independent validation-data plan
2. หรือทำ no-paid validation feasibility plan ก่อน action ที่แพงหรือเสี่ยงกว่า
