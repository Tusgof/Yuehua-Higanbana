# บันทึกการวิจัย: H-A2 Post-Stress Normalization/Control Import Diagnostic

## 1. ข้อมูลพื้นฐาน

- Timestamp UTC: `2026-07-08T07:36:45Z`
- โครงการ: SPY 0DTE - Higanbana
- หัวข้อ: ตรวจข้อมูล post-stress normalization/control pack ก่อน exact replay
- ผู้บันทึก: Codex
- สถานะ: เสร็จสิ้น
- ระดับหลักฐาน: `E1`
- ข้อสรุป: `ยังสรุปไม่ได้`
- Artifact หลัก:
  - `experiments/h_a2_post_stress_normalization_control_import_diagnostic_preregistration.json`
  - `reports/diagnostics/h_a2_post_stress_normalization_control_import_diagnostic.json`
  - `reports/diagnostics/h_a2_post_stress_normalization_control_import_diagnostic.md`
  - `reports/diagnostics/search_logs/h_a2_post_stress_normalization_control_import_diagnostic_search_log.jsonl`

## 2. วัตถุประสงค์

### อ่านแบบเร็ว

รอบนี้ตรวจว่า data pack ชุด `2025-05-05` ถึง `2025-05-16` ที่โหลดจาก Databento แล้ว สามารถใช้เป็นฐานสำหรับ H-A2 ต่อได้หรือไม่ ผลคือ parse ได้ครบ 10 วัน และพบ candidate-ready date 1 วัน คือ `2025-05-05`

ผลนี้ยังไม่ใช่กำไรขาดทุน ยังไม่ใช่ exact replay และยังไม่ใช่หลักฐานว่า H-A2 มี edge จริง สิ่งที่สรุปได้คือข้อมูลชุดนี้พร้อมสำหรับการทำ exact replay แบบแยก preregistration เฉพาะ candidate date ที่พบ

คำถามของรอบนี้คือ: ข้อมูล raw DBN ที่ซื้อมาแล้วมี SPY bar, OPRA quote, timestamp และ quote availability พอสำหรับ reconstruct สัญญาณ H-A2 ตามกฎเดิมหรือไม่ ไม่ใช่คำถามว่ากลยุทธ์ทำกำไรหรือยัง

## 3. วิธีการและขั้นตอน

1. ตรวจ preregistration ด้วย `scripts\validate_h_a2_post_stress_normalization_control_import_diagnostic_preregistration.py`
2. ใช้เฉพาะไฟล์ DBN ใน `post_stress_normalization_control_pack` ที่ดาวน์โหลดไว้แล้ว ไม่มีการเรียก API เพิ่ม
3. ตรวจ raw-file inventory, SPY `ohlcv-1m`, OPRA `cbbo-1m`, timestamp alignment และ quote availability
4. reconstruct เฉพาะสัญญาณเดิมของ H-A2: decision time `09:35 ET`, threshold `0.001`, feature `clean_macro_vix_condition` และ `proxy_5m_followthrough`
5. แยกสถานะรายวันเป็น candidate-ready, data-blocked หรือ no-candidate-signal โดยยังไม่คำนวณ PnL

คำสั่งตรวจหลัก:

```powershell
python scripts\validate_h_a2_post_stress_normalization_control_import_diagnostic_preregistration.py
python scripts\run_h_a2_post_stress_normalization_control_import_diagnostic.py
python scripts\validate_h_a2_post_stress_normalization_control_import_diagnostic.py
python -m unittest tests.test_h_a2_post_stress_normalization_control_import_diagnostic
```

## 4. ผลการศึกษาและข้อมูลดิบ

| Metric | ค่า |
|---|---:|
| ช่วงวันที่ | `2025-05-05` ถึง `2025-05-16` |
| จำนวนวัน | `10` |
| Raw DBN files | `20` |
| Raw bytes | `1,057,077,119` |
| SPY bar rows | `3,900` |
| OPRA quote rows | `36,296,592` |
| 0DTE valid-mid quote rows | `939,097` |
| Timestamp alignment | `pass` |
| Clean macro/VIX dates | `8` |
| Locked signal true dates | `1` |
| Candidate-ready dates | `1` |
| Candidate-ready date | `2025-05-05` |

ข้อมูลสำคัญคือ SPY bar และ OPRA quote ผ่านการตรวจ timestamp ครบทั้ง 10 วัน และมี quote ที่ใช้ตรวจ entry/forced close ได้ ข้อมูลจึงไม่ได้ติด blocker แบบขาดไฟล์หรือ timestamp ผิดวัน

วันที่ `2025-05-05` เป็นวันเดียวในชุดนี้ที่สัญญาณ H-A2 ผ่านตามกฎเดิม และมีข้อมูล quote เพียงพอสำหรับทำ exact replay ต่อได้ ส่วนวันที่อื่นไม่ได้เป็น candidate trade ตามกฎล็อกเดิม ไม่ใช่เพราะข้อมูลหาย

มีข้อควรระวังเรื่องคุณภาพข้อมูล: ตอนดาวน์โหลด Databento แจ้ง reduced-quality data สำหรับ `2025-05-06` รอบนี้บันทึก note นี้ไว้แล้ว และควรระวังเมื่อใช้วันนั้นในงาน diagnostic อื่น แม้วันดังกล่าวไม่ได้เป็น candidate-ready date ในรอบนี้

## 5. ปัญหา อุปสรรค และการแก้ไข

ข้อจำกัดใหญ่ที่สุดคือรอบนี้เป็น import/availability diagnostic เท่านั้น ยังไม่มี `mid_pnl`, `implementable_pnl`, Sharpe, MinTRL หรือ PSR เพราะยังไม่ได้ทำ exact replay

สิ่งที่ห้ามสรุปจากรอบนี้:

- ห้ามบอกว่า H-A2 ผ่านหรือมี edge แล้ว
- ห้ามอ้าง `E2` หรือ acceptance-grade evidence
- ห้ามอนุมัติ `paper trading`, operational validation หรือ real-money trading
- ห้ามคำนวณหรือพูดถึง PnL ของ `2025-05-05` ก่อนมี bounded exact replay preregistration
- ห้ามเปลี่ยน threshold `0.001` หรือเพิ่ม filter ใหม่จากผลย้อนหลังนี้
- ห้ามใช้ข้อมูลชุดนี้เป็นเหตุผลในการซื้อข้อมูลเพิ่มแบบกว้างโดยไม่ตั้งคำถามวิจัยใหม่

## 6. ข้อสรุปและก้าวต่อไป

ข้อสรุป: `ยังสรุปไม่ได้` เพราะรอบนี้พิสูจน์ได้แค่ว่าข้อมูลชุด post-stress normalization/control พร้อมสำหรับ exact replay เฉพาะบางวัน แต่ยังไม่ได้วัดผลการเทรด

สิ่งที่รอบนี้ช่วยตอบได้คือ sample-expansion path เริ่มมี candidate เพิ่มอีก 1 วันจากชุดข้อมูลใหม่ ทำให้ H-A2 ไม่ได้หยุดอยู่แค่ candidate เดิมจาก normal/control pack แต่หลักฐานยังอยู่ระดับ `E1` และยังเล็กมาก

ก้าวต่อไป:

1. Pre-register bounded exact replay สำหรับ candidate-ready date `2025-05-05`
2. ใน exact replay ต้องแยก `mid_pnl` และ `implementable_pnl` พร้อมค่าธรรมเนียมและ bid/ask
3. หลัง exact replay ค่อยรวมผลกับ candidate เดิมเพื่อประเมิน sample size, MinTRL/PSR และทิศทางของสมมติฐาน H-A2 ต่อไป
