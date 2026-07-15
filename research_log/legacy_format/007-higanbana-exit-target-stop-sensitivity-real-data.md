# บันทึกการวิจัย: M5.4 Exit Target/Stop Sensitivity

## 1. ข้อมูลพื้นฐาน

- Timestamp UTC: `2026-07-02T06:15:50Z`
- โครงการ: SPY 0DTE - Higanbana
- หัวข้อ: ทดสอบความไวของผลลัพธ์ต่อ profit target และ stop loss ของ Sub-System A
- ผู้บันทึก: Codex
- สถานะ: เสร็จสิ้นแบบ diagnostic
- เครื่องมือ:
  - Python local scripts
  - Databento normalized local artifacts เท่านั้น
- Artifact หลัก:
  - `scripts/run_m5_exit_target_stop_sensitivity.py`
  - `reports/experiments/m5_exit_target_stop_sensitivity_summary.json`
  - `reports/experiments/m5_exit_target_stop_sensitivity_report.md`
  - `reports/experiments/search_logs/m5_exit_target_stop_sensitivity_search_log.jsonl`
  - `reports/experiments/m5_exit_target_stop_components/`

## 2. วัตถุประสงค์

### อ่านแบบเร็ว

บันทึกนี้ตรวจความไวของ Sub-System A ต่อ target/stop หลายแบบ เพื่อดูว่า exit rule ทำให้ผลลัพธ์เปลี่ยนอย่างไร
ผลสำคัญคือเป็นการวัดความเปราะของ exit design และต้องนับ trial/search log ไม่ใช่รายงานเฉพาะค่าที่ดีที่สุด
ข้อห้ามสรุป: ห้ามเลือก target/stop ที่ดูดีที่สุดเป็นระบบจริงโดยไม่มี DSR, MinTRL/PSR และ validation แยก


การทดลองนี้ต้องการตอบว่า Sub-System A แบบ ORB directional debit vertical ควรใช้ forced close อย่างเดียว หรือควรมี profit target และ stop loss ระหว่างวันหรือไม่ เมื่อใช้ข้อมูล option quote จริงที่มีอยู่แล้วและไม่ซื้อข้อมูลเพิ่ม

รอบ M4.3 เคยเปรียบเทียบเพียง `forced_close_only` กับ `target_stop_25_50` แล้วพบว่า target/stop ช่วยบาง metric แต่ยังห้ามใช้ OOS เป็นตัวเลือก parameter รอบนี้จึงขยายเป็น grid ที่ชัดเจนขึ้น บันทึกทุก trial ลง search log และตั้ง DSR เป็น blocker จนกว่า sample จะพอ

ความสำเร็จของรอบนี้ไม่ใช่การเลือก TP/SL สำหรับใช้งานจริง แต่คือการได้หลักฐาน diagnostic ว่า exit rule มีผลต่อ PnL, drawdown, ES95/ES99, worst-day loss และ OOS อย่างไร โดยยังรักษาวินัย no-OOS-tuning

## 3. วิธีการและขั้นตอน

1. อ่านสถานะจาก `PROJECT_BRAIN.md`, `IMPLEMENT_PLAN.md`, และ `AGENTS.md`
2. ใช้ pattern จาก M4.3 และ M5.1-M5.3 เพื่อสร้าง runner ใหม่ `scripts/run_m5_exit_target_stop_sensitivity.py`
3. ใช้ Sub-System A ORB directional debit vertical บนข้อมูลจริงเดิม:
   - in-sample: 2023-03-01 ถึง 2023-12-29
   - OOS: 2024-01-02 ถึง 2024-12-31
4. ใช้ entry model เดิม:
   - ไม่มี entry market order
   - fill model: `half_spread`
   - fee: `$0.64` ต่อ contract ต่อขา
   - close fallback: `nearest_1545_window`
5. ทดสอบ 7 scenarios:
   - `forced_close_only_control`
   - `tp_10_stop_25`
   - `tp_25_stop_50_baseline`
   - `tp_50_stop_50`
   - `tp_50_stop_75`
   - `tp_100_stop_50`
   - `tp_100_stop_100`
6. บันทึกทุก trial ลง search log เพื่อป้องกัน cherry-picking
7. ระบุ DSR เป็น `blocked_under_sampled` เพราะเป็น parameter grid และยังไม่มี sample เพียงพอสำหรับ acceptance-grade conclusion

คำสั่งที่ใช้:

```powershell
python -m unittest tests.test_m5_exit_target_stop_sensitivity
python scripts\run_m5_exit_target_stop_sensitivity.py
```

## 4. ผลการศึกษาและข้อมูลดิบ

### ผลรวมตาม scenario

| Scenario | TP | SL | Closed | Implementable PnL | Mid PnL | Cost drag | OOS PnL | ES95 | ES99 | Max drawdown |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `forced_close_only_control` | ไม่ใช้ | ไม่ใช้ | 90 | 545.60 | 1089.50 | 543.90 | -78.44 | -59.56 | -62.56 | -0.370769 |
| `tp_10_stop_25` | 10% | 25% | 93 | -93.08 | 336.50 | 429.58 | -93.56 | -29.36 | -36.56 | -0.153230 |
| `tp_25_stop_50_baseline` | 25% | 50% | 93 | 108.92 | 535.50 | 426.58 | 133.44 | -37.56 | -41.56 | -0.172334 |
| `tp_50_stop_50` | 50% | 50% | 93 | 75.92 | 502.50 | 426.58 | 142.44 | -37.56 | -41.56 | -0.172334 |
| `tp_50_stop_75` | 50% | 75% | 92 | 270.96 | 703.00 | 432.04 | 288.52 | -52.56 | -60.56 | -0.244288 |
| `tp_100_stop_50` | 100% | 50% | 93 | -45.08 | 381.50 | 426.58 | -12.56 | -37.56 | -41.56 | -0.172334 |
| `tp_100_stop_100` | 100% | 100% | 91 | 364.04 | 802.00 | 437.96 | 262.56 | -57.76 | -61.56 | -0.334029 |

### ข้อสังเกตหลัก

- Scenario ที่ดีที่สุดตาม total implementable PnL ยังเป็น `forced_close_only_control` ที่ `$545.60`
- `tp_100_stop_100` ให้ OOS PnL ดีสุดใน grid นี้ที่ `$262.56` แต่ห้ามใช้เป็นตัวเลือก production เพราะเป็น OOS diagnostic หลังเปิดดูผลแล้ว
- TP/SL ที่แคบมาก เช่น `tp_10_stop_25` ลด max drawdown เหลือ `-0.153230` แต่ทำให้ PnL รวมติดลบ `-$93.08`
- `tp_25_stop_50_baseline` ดีขึ้นจาก M4.3 ในแง่ OOS PnL เป็น `$133.44` แต่ยังแพ้ forced close ในผลรวม
- ทุก scenario ยังมี label `under-sampled` และ `underpowered`
- Search log บันทึกครบ 7 trials และ DSR status คือ `blocked_under_sampled`

### Artifact อ้างอิง

- Summary: `reports/experiments/m5_exit_target_stop_sensitivity_summary.json`
- Report: `reports/experiments/m5_exit_target_stop_sensitivity_report.md`
- Search log: `reports/experiments/search_logs/m5_exit_target_stop_sensitivity_search_log.jsonl`
- Component summaries: `reports/experiments/m5_exit_target_stop_components/`

## 5. ปัญหา อุปสรรค และการแก้ไข

### ปัญหา 1: report renderer เรียก metric ผิดชื่อ

อาการ: การรัน `python scripts\run_m5_exit_target_stop_sensitivity.py` รอบแรกคำนวณผลเกือบเสร็จ แต่ล้มตอนเขียน report ด้วย `KeyError: 'exit_reason_counts'`

สาเหตุ: renderer ต้องการแสดงจำนวน exit reason แต่ `metrics_for_closed_trades` ที่ reuse จาก baseline ไม่ได้สร้าง key นี้

การแก้ไข: เพิ่มฟังก์ชัน `exit_reason_counts()` ใน runner M5.4 และเติมค่าเข้า `metrics` ตอน aggregate scenario

ผลหลังแก้: focused test ยังผ่าน และ runner สร้าง summary/report/search log สำเร็จ

### ข้อจำกัดสำคัญ

- ผลนี้ยังเป็น diagnostic เท่านั้น เพราะจำนวน trade ต่ำกว่าเกณฑ์ acceptance
- OOS ที่ดูดีในบาง TP/SL scenario ห้ามใช้เป็นการเลือก parameter สำหรับ production
- DSR ยัง blocked เพราะ sample ต่ำและยังไม่มี return distribution ที่แข็งแรงพอ
- ไม่มี paid API call และไม่มีข้อมูลใหม่เพิ่มในการทดลองนี้

## 6. ข้อสรุปและก้าวต่อไป

ข้อสรุป: ยังสรุปไม่ได้ในเชิง acceptance แต่ M5.4 ให้หลักฐาน diagnostic ว่า forced close ยังดีที่สุดตาม total implementable PnL ส่วน TP/SL บางชุดช่วยลด drawdown หรือทำให้ OOS ดูดีขึ้น แต่ยังไม่พอสำหรับเลือกใช้จริง

- Forced close ยังชนะในผลรวม จึงยังไม่มีเหตุผลพอจะเปลี่ยน exit rule จากหลักฐานชุดนี้
- TP/SL แคบลด downside บาง metric แต่ตัด upside จน PnL รวมแย่ลง
- TP/SL กว้างบางชุดทำให้ OOS ดีขึ้น แต่เป็นผลที่ห้าม tune จาก OOS
- Search log ครบ 7 trials ลดปัญหา cherry-picking แต่ DSR ยัง blocked เพราะ sample ต่ำ

ก้าวต่อไป:

1. อัปเดต `PROJECT_BRAIN.md` และ `IMPLEMENT_PLAN.md` ให้ระบุว่า M5.4 เสร็จแล้ว
2. รัน `python scripts\audit_research_logs.py` เพื่อยืนยัน log 007 และ push status
3. เดินต่อ M5.5 คือ VIX/VXV, macro-event และ NOVI/net-gamma-proxy filters โดยต้องรายงาน active trade count หลัง filter ทุกครั้ง
