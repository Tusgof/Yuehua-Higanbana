# บันทึกการวิจัย: H-A2 Original-Entry Revision

## 1. ข้อมูลพื้นฐาน

- Timestamp UTC: `2026-07-07T07:39:02Z`
- โครงการ: SPY 0DTE - Higanbana
- หัวข้อ: แก้ H-A2 ให้ใช้เฉพาะข้อมูลที่รู้ได้ตอน original entry
- ผู้บันทึก: Codex
- สถานะ: เสร็จสิ้น
- ระดับหลักฐาน: `E1`
- ข้อสรุป: `ยังสรุปไม่ได้`
- Artifact หลัก:
  - `experiments/h_a2_original_entry_revision_preregistration.json`
  - `reports/experiments/h_a2_original_entry_revision_summary.json`
  - `reports/experiments/h_a2_original_entry_revision_report.md`
  - `reports/experiments/search_logs/h_a2_original_entry_revision_search_log.jsonl`

## 2. วัตถุประสงค์

### อ่านแบบเร็ว

หลังพบว่า full condition เดิมรู้ช้าเกิน `09:35 ET` รอบนี้จึงกลับมาแก้ H-A2 ให้ใช้เฉพาะข้อมูลที่รู้ทัน original entry เท่านั้น ผลคือ rule ใหม่สะอาดด้านเวลา และยัง retain OOS ได้ 14 วัน แต่ sample ยังเล็กมาก จึงยังเป็น `E1` diagnostic เท่านั้น

ความสำคัญของรอบนี้คือยอมเสียความสวยของตัวเลขบางส่วนเพื่อรักษาความถูกต้องของเวลา เพราะระบบที่ใช้ข้อมูลอนาคตแม้เพียงเล็กน้อยจะให้ผล backtest ที่ไม่น่าเชื่อถือ

## 3. วิธีการและขั้นตอน

1. ใช้เฉพาะ feature ที่รู้ได้ตอน `09:35 ET`
2. ไม่ใช้ 15-minute conflict component ที่รู้หลังเวลา entry
3. ไม่ทำ threshold search ใหม่ และไม่ tune OOS
4. ตรวจ retained/skipped trade days และ sample adequacy

คำสั่งตรวจหลัก:

```powershell
python scripts\validate_h_a2_original_entry_revision.py
python -m unittest tests.test_h_a2_original_entry_revision
```

## 4. ผลการศึกษาและข้อมูลดิบ

| Metric | ค่า |
|---|---:|
| Baseline OOS non-risk trade days | `34` |
| Retained OOS trade days | `14` |
| Skipped OOS trade days | `20` |
| OOS retention rate | `0.411765` |
| Retained train trade days | `16` |
| Threshold search used | `false` |
| Trial count | `0` |

ผลนี้บอกว่าเมื่อถอด feature ที่รู้ช้าออก H-A2 ไม่ได้พังทันที rule ที่เหลือยังคัด trade ได้บางส่วนและยังมีทิศทางให้ศึกษา แต่จำนวน retained OOS 14 วันยังต่ำเกินไปที่จะบอกว่า edge มีจริง

## 5. ปัญหา อุปสรรค และการแก้ไข

การทดลองนี้แก้ปัญหา timestamp leakage ได้ แต่ยังไม่แก้ปัญหา sample size และ regime coverage ดังนั้นผลจึงยัง `under-sampled` และ `underpowered`

สิ่งที่ห้ามสรุปจากรอบนี้:

- ห้ามบอกว่า original-entry rule ผ่านแล้ว
- ห้ามอ้าง `E2` หรือ `paper trading`
- ห้าม exact replay โดยไม่มีแผน validation ต่อ

## 6. ข้อสรุปและก้าวต่อไป

ข้อสรุป: `ยังสรุปไม่ได้` แต่ H-A2 แบบ original-entry ยังควรตรวจต่อ

จุดที่ดีคือ rule นี้สะอาดด้านเวลา จุดที่ยังอ่อนคือจำนวนตัวอย่างยังน้อยมาก งานถัดไปจึงควรถามว่า rule นี้ทนพอไหม และต้องใช้ validation เพิ่มแบบไหน ไม่ใช่รีบ deploy

ก้าวต่อไป:

1. ทำ robustness/prioritization review
2. วางแผน independent validation ก่อนซื้อข้อมูลหรือ replay ต่อ
