# บันทึกการวิจัย: ORB Baseline บนข้อมูลจริง

## 1. ข้อมูลพื้นฐาน

- Timestamp UTC: `2026-07-01T14:45:45Z`
- โครงการ: SPY 0DTE - Higanbana
- หัวข้อ: Sub-System A ORB baseline บนข้อมูลจริงโดยไม่ใช้ข่าวและไม่ใช้ LLM
- ผู้บันทึก: Codex
- สถานะ: เสร็จสิ้น
- เครื่องมือ:
  - `scripts/run_m4_subsystem_a_baseline.py`
  - `python scripts\audit_research_logs.py`
- Artifact หลัก:
  - `reports/baselines/subsystem_a_orb_baseline_summary.json`
  - `reports/baselines/subsystem_a_orb_baseline_report.md`
  - `reports/baselines/subsystem_a_components/`
  - `scripts/run_m4_subsystem_a_baseline.py`

## 2. วัตถุประสงค์

### อ่านแบบเร็ว

บันทึกนี้ตั้ง baseline ของ Sub-System A ก่อนใส่ข่าวหรือ LLM คำถามคือ ORB directional debit vertical spread บนข้อมูลจริงมีพื้นฐานพอให้ศึกษาต่อหรือไม่
ผลสำคัญคือ baseline ยังไม่ใช่หลักฐานว่า edge ผ่าน แต่เป็นฐานเปรียบเทียบสำหรับการทดลองถัดไป ต้องอ่านคู่กับ `mid_pnl`, `implementable_pnl`, cost drag, in-sample/OOS และ sample adequacy
ข้อห้ามสรุป: ห้ามใช้บันทึกนี้เป็นเหตุผลอนุมัติ paper trading หรือ real-money trading


การทดลองรอบนี้ต้องตอบคำถามพื้นฐานก่อนว่า Sub-System A แบบ ORB directional debit vertical spread มีหลักฐานเริ่มต้นที่ควรนำไปทำ filter, parameter search, news gate หรือ LLM gate ต่อหรือไม่ ถ้า baseline ที่ไม่ใช้ข่าวและไม่ใช้ LLM ยังอ่อนมาก การเพิ่มความซับซ้อนภายหลังอาจทำให้เราหลงกับตัวเลขมากกว่าค้นพบ edge จริง

ความสำเร็จของรอบนี้ไม่ใช่การพิสูจน์ว่ากลยุทธ์ผ่าน แต่คือการสร้าง baseline ที่ตรวจสอบได้บนข้อมูลจริง โดยต้องแยก `mid_pnl` ออกจาก `implementable_pnl`, แสดง cost drag, แยก in-sample กับ OOS ตามเวลา, ใส่ sample adequacy labels, ทำ big-day dependency check และสรุปอย่างตรงไปตรงมาว่าหลักฐานอยู่ระดับไหน

## 3. วิธีการและขั้นตอน

1. ใช้ข้อมูลจริงที่มีอยู่จาก Mar-Dec 2023 เป็น in-sample และ Jan-Dec 2024 เป็น OOS
2. รัน baseline โดยปิด news filter และ LLM filter ทั้งหมด
3. ใช้ entry แบบ limit-style ที่คำนวณจาก fill model ไม่ใช้ market order ตอนเข้า
4. ใช้ `half_spread` fill model, ค่าธรรมเนียม `$0.64` ต่อ contract และ forced close เป็น exit หลัก
5. สร้าง summary/report ที่รวม metric ระดับ overall, in-sample, OOS, sample adequacy, DSR และ big-day dependency
6. ตรวจ research-log audit เพื่อยืนยันว่า experiment ที่เสร็จแล้วต้องมี log หมายเลข `001`

คำสั่งหลัก:

```powershell
python scripts\run_m4_subsystem_a_baseline.py
python scripts\audit_research_logs.py
```

พารามิเตอร์สำคัญจาก report:

| Parameter | Value |
|---|---|
| News filter | disabled |
| LLM filter | disabled |
| Fill model | half_spread |
| Fee | `$0.64` per contract |
| Exit model | forced_close_only |
| Close fallback | nearest_1545_window |
| Chronological policy | in-sample 2023-03-01 ถึง 2023-12-29, OOS 2024-01-02 ถึง 2024-12-31 |

## 4. ผลการศึกษาและข้อมูลดิบ

### ภาพรวม

| Metric | Value |
|---|---:|
| Closed trades | 90 |
| Total mid PnL | 1089.5 |
| Total implementable PnL | 545.6 |
| Cost drag | 543.9 |
| Average trade PnL | 6.0622 |
| Win rate | 0.3222 |
| Payoff ratio | 2.663 |
| Sharpe proxy | 0.118064 |
| Sortino proxy | 0.578039 |
| Max drawdown | -0.370769 |
| ES95 | -59.56 |
| ES99 | -62.56 |
| Worst-day loss | -62.56 |

### แยกตามช่วงเวลา

| Split | Coverage | Candidate days | Closed trades | Implementable PnL | Mid PnL | Cost drag | Sharpe proxy | Max drawdown | SPY benchmark PnL on `$1000` | Labels |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| in-sample | 2023-03-01 ถึง 2023-12-29 | 42 | 41 | 624.04 | 849.0 | 224.96 | 0.226229 | -0.170819 | 204.02 | under-sampled, underpowered |
| OOS | 2024-01-02 ถึง 2024-12-31 | 51 | 49 | -78.44 | 240.5 | 318.94 | 0.01581 | -0.550922 | 236.87 | under-sampled, underpowered |

### สิ่งที่ดี

- Pipeline สามารถสร้าง baseline จริงได้ครบจากข้อมูล option quote และ SPY bar ที่มีอยู่
- ผลลัพธ์แยก `mid_pnl` กับ `implementable_pnl` ชัดเจน ทำให้เห็นว่า cost drag กินกำไรเชิงอุดมคติไป `543.9`
- ไม่มีการใช้ข่าว, LLM, หรือ parameter search จึงยังไม่ปนกับปัญหา prompt overfitting หรือ multiple testing

### สิ่งที่ยังไม่ผ่าน

- จำนวน trade ทั้งหมดมีแค่ `90` ต่ำกว่า prior target `N >= 500` มาก จึงต้องติดป้าย `under-sampled` และ `underpowered`
- OOS ปี 2024 มี `implementable_pnl = -78.44` ขณะที่ SPY benchmark บนเงิน `$1000` เป็น `236.87`
- Big-day dependency บอกว่าหลังตัด extreme top/bottom 5% ออก กำไรเหลือเพียง `59.2` และ Sharpe proxy ลดจาก `0.092203` เหลือ `0.013201` แปลว่าผลรวมยังเปราะบางต่อวันสุดโต่ง
- MinTRL และ PSR ยังเป็น `pending_return_distribution` จึงห้ามใช้ point Sharpe เป็นข้อสรุปเชิงยอมรับกลยุทธ์

### DSR และ search log

รอบนี้มี `trial_count = 1` และไม่ได้เลือกค่าที่ดีที่สุดจาก parameter grid ดังนั้น DSR เป็น `not_applicable` ไม่ใช่ blocker ของรอบนี้ แต่การทดลอง filter หรือ TP/SL ในอนาคตต้องมี search log และ DSR หรือ DSR blocker เสมอ

## 5. ปัญหา อุปสรรค และการแก้ไข

1. ปัญหา: ก่อนสร้าง log, `python scripts\audit_research_logs.py` รายงาน `missing_research_log:subsystem_a_orb_baseline_summary`
   การแก้ไข: สร้างไฟล์ log ตามลำดับแรกเป็น `001-higanbana-orb-baseline-real-data.md`
   ผลลัพธ์: รอ verify หลัง commit และ push ไปยัง repository ของ research log

2. ปัญหา: ผล `big_day_dependency.status` ใน artifact เป็น `pass` แต่ตัวเลข retained PnL และ retained Sharpe ลดลงแรง
   การแก้ไข: บันทึกการตีความไว้ใน log ว่าผลนี้ยังแสดงความเปราะบาง แม้ helper จะให้สถานะ `pass`
   ผลลัพธ์: ไม่อ้างว่ากลยุทธ์ robust เกินกว่าหลักฐาน

ข้อจำกัดสำคัญ:

- ข้อมูลยังน้อยเกินกว่าจะสรุประดับ acceptance-grade
- OOS ถูกใช้เป็น evidence report เท่านั้น ไม่ใช้เพื่อ tune parameter
- Baseline นี้ครอบคลุม Sub-System A เท่านั้น ยังไม่ได้ตอบความเป็นไปได้ของ Sub-System B

## 6. ข้อสรุปและก้าวต่อไป

ข้อสรุป: ยังสรุปไม่ได้ว่า Sub-System A ORB baseline มี edge ที่ใช้งานได้จริง เพราะตัวอย่างน้อย, OOS ขาดทุนหลังต้นทุน, และผลรวมเปราะบางต่อ trade สุดโต่ง

- Baseline นี้มีประโยชน์ในฐานะจุดอ้างอิงก่อนเพิ่ม filter หรือ LLM แต่ยังไม่ผ่าน research acceptance
- `implementable_pnl` สำคัญกว่า `mid_pnl` สำหรับการตัดสินใจ เพราะต้นทุนกินส่วนต่างไปประมาณครึ่งหนึ่งของ mid PnL รวม
- ผล OOS ปี 2024 ไม่สนับสนุนการเดินหน้าไป operational validation
- ต้องทำ baseline ของ Sub-System B และ diagnostic เพิ่มก่อนเริ่มทดลอง LLM/news gate

ก้าวต่อไป:

1. รัน M4.2 เพื่อทดสอบ Sub-System B capped-risk put ratio baseline และ feasibility สำหรับบัญชี `$1,000`
2. รัน M4.3 เพื่อเปรียบเทียบ forced-close-only กับ target/stop เป็น diagnostic โดยไม่ tune บน OOS
3. ปรับ report helper ให้ตีความ big-day dependency เป็น fragility warning เมื่อ retained Sharpe หรือ retained PnL ลดลงแรง
4. เก็บ research log ถัดไปเป็น `002-higanbana-...md` เมื่อ experiment round ถัดไปเสร็จจริง
