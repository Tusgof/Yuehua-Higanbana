# บันทึกการวิจัย: M5.1 Transaction Cost And Execution Latency Sensitivity

## 1. ข้อมูลพื้นฐาน

- Timestamp UTC: `2026-07-02T04:53:27Z`
- โครงการ: SPY 0DTE - Higanbana
- หัวข้อ: ทดสอบความไวของ Sub-System A ต่อ transaction cost และ execution latency บนข้อมูลจริง
- ผู้บันทึก: Codex
- สถานะ: เสร็จสิ้น
- เครื่องมือ:
  - Python local scripts
  - Databento normalized local artifacts เท่านั้น
- Artifact หลัก:
  - `scripts/run_m5_transaction_cost_latency_sensitivity.py`
  - `scripts/run_jan2024_pilot_pnl.py`
  - `reports/experiments/m5_transaction_cost_latency_sensitivity_summary.json`
  - `reports/experiments/m5_transaction_cost_latency_sensitivity_report.md`
  - `reports/experiments/search_logs/m5_transaction_cost_latency_sensitivity_search_log.jsonl`
  - `reports/experiments/m5_transaction_cost_latency_components/`

## 2. วัตถุประสงค์

### อ่านแบบเร็ว

บันทึกนี้ถามว่า Sub-System A เปราะต่อ transaction cost และ execution latency แค่ไหน เมื่อเปลี่ยน fee, spread stress และเวลาการเข้า order
ผลสำคัญคือใช้เพื่อวัด friction drag ระหว่าง `mid_pnl` กับ `implementable_pnl` ไม่ใช่เพื่อเลือก scenario ที่สวยที่สุด
ข้อห้ามสรุป: ห้ามเลือก parameter จาก OOS หรือใช้ mid-price PnL เป็นผลที่เทรดได้จริง


การทดลองนี้ต้องตอบคำถามว่า Sub-System A ORB directional debit vertical ยังดูมีความหวังแค่ไหน เมื่อเปลี่ยนสมมติฐานต้นทุนและความล่าช้าในการเข้า order

จุดสำคัญของรอบนี้คือไม่ใช่การหา scenario ที่ดีที่สุดเพื่อเลือกใช้จริง แต่เป็นการวัดความเปราะของผลลัพธ์:

- ถ้าใช้ mid price แบบอุดมคติ ผลต่างจาก PnL ที่เทรดได้จริงใหญ่แค่ไหน
- ถ้าใช้ fee `$0.64` ต่อ contract ต่อขา ผลลัพธ์ลดลงเท่าไหร่
- ถ้า fee สูงขึ้นเป็น `$1.00` ต่อ contract ต่อขา ผลลัพธ์ยังไหวไหม
- ถ้าราคา entry แย่ลงแบบ `full_spread_stress` ผลลัพธ์ยังเหลือ edge หรือไม่
- ถ้า entry ช้า 1-2 นาที ผลลัพธ์และ OOS เปลี่ยนแค่ไหน

กติกาสำคัญ: ใช้ข้อมูลจริงที่มีอยู่เท่านั้น ไม่ซื้อข้อมูลเพิ่ม ไม่ใช้ข่าว ไม่ใช้ LLM และไม่เลือก parameter จาก OOS

## 3. วิธีการและขั้นตอน

1. อ่านสถานะจาก `PROJECT_BRAIN.md`, `IMPLEMENT_PLAN.md`, และ `AGENTS.md`
2. อ่านแนวคิดจาก LLM Wiki เรื่อง implementable option PnL และ backtest validation
3. เพิ่ม `entry_latency_minutes` ใน `scripts/run_jan2024_pilot_pnl.py`
   - ค่าเริ่มต้นคือ 0 นาที เพื่อไม่ให้ผลเดิมเปลี่ยน
   - ถ้า latency ทำให้ไม่มี quote ณ เวลา entry ใหม่ ให้ skip trade ไม่เติมราคาจำลอง
4. เพิ่ม test สำหรับกรณี latency มี quote และ latency ไม่มี quote
5. เพิ่ม runner ใหม่ `scripts/run_m5_transaction_cost_latency_sensitivity.py`
6. รัน scenario grid ทั้งหมด 8 trials บน dataset ปัจจุบัน ตั้งแต่ Mar-Dec 2023 และ Jan-Dec 2024
7. เขียน search log ทุก trial เพื่อป้องกัน selection bias
8. สร้าง summary/report และบันทึกว่า DSR ยัง blocked เพราะ sample ยังน้อยและไม่ได้เลือก parameter สำหรับ deployment

Scenario grid:

| Scenario | Fill model | Fee | Entry latency |
|---|---|---:|---:|
| `mid_fee_0_latency_0_control` | `mid` | 0.00 | 0 |
| `mid_fee_0_latency_2_control` | `mid` | 0.00 | 2 |
| `half_spread_fee_064_latency_0_baseline` | `half_spread` | 0.64 | 0 |
| `half_spread_fee_064_latency_1` | `half_spread` | 0.64 | 1 |
| `half_spread_fee_064_latency_2` | `half_spread` | 0.64 | 2 |
| `half_spread_fee_100_latency_0` | `half_spread` | 1.00 | 0 |
| `full_spread_stress_fee_064_latency_0` | `full_spread_stress` | 0.64 | 0 |
| `full_spread_stress_fee_100_latency_1` | `full_spread_stress` | 1.00 | 1 |

## 4. ผลการศึกษาและข้อมูลดิบ

### ผลรวมตาม scenario

| Scenario | Closed | Skipped | Mid PnL | Implementable PnL | Cost drag | Drag ratio | OOS PnL | Max drawdown |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `mid_fee_0_latency_0_control` | 90 | 3 | 1089.50 | 866.50 | 223.00 | 0.204681 | 96.50 | -0.297821 |
| `mid_fee_0_latency_2_control` | 90 | 3 | 605.00 | 382.00 | 223.00 | 0.368595 | -205.50 | -0.405087 |
| `half_spread_fee_064_latency_0_baseline` | 90 | 3 | 1089.50 | 545.60 | 543.90 | 0.499220 | -78.44 | -0.370769 |
| `half_spread_fee_064_latency_1` | 90 | 3 | 713.50 | 169.60 | 543.90 | 0.762299 | -301.44 | -0.471521 |
| `half_spread_fee_064_latency_2` | 90 | 3 | 605.00 | 60.60 | 544.40 | 0.899835 | -381.44 | -0.508742 |
| `half_spread_fee_100_latency_0` | 90 | 3 | 1089.50 | 416.00 | 673.50 | 0.618173 | -149.00 | -0.403794 |
| `full_spread_stress_fee_064_latency_0` | 90 | 3 | 1089.50 | 364.60 | 724.90 | 0.665351 | -177.44 | -0.417258 |
| `full_spread_stress_fee_100_latency_1` | 90 | 3 | 713.50 | -141.00 | 854.50 | 1.197617 | -472.00 | -0.594849 |

### ภาพสำคัญจากผลลัพธ์

- Scenario control แบบ `mid_fee_0_latency_0_control` ได้ implementable PnL 866.50 แต่ยังไม่ใช่ผลที่เทรดได้จริง เพราะ mid price เป็นแค่ตัวควบคุม
- Baseline ที่ใกล้เคียงการเทรดกว่า คือ `half_spread_fee_064_latency_0_baseline` ได้ implementable PnL 545.60 แต่ cost drag สูงถึง 543.90 หรือประมาณ 49.92% ของ mid PnL
- แค่ entry ช้า 1 นาที ภายใต้ fee `$0.64` และ `half_spread` implementable PnL ลดจาก 545.60 เหลือ 169.60
- entry ช้า 2 นาที ภายใต้เงื่อนไขเดียวกัน เหลือเพียง 60.60 และ OOS เป็น -381.44
- stress ที่หนักสุดใน grid คือ `full_spread_stress_fee_100_latency_1` พลิกผลรวมเป็น -141.00 และ OOS เป็น -472.00

### Sample adequacy

- closed trades สูงสุดต่อ scenario: 90
- labels: `under-sampled`, `underpowered`
- MinTRL: pending
- PSR: pending
- DSR: `blocked_under_sampled`
- Trial count: 8

### Big-day dependency

ทุก scenario มี big-day dependency check ใน summary component ของตนเอง ผลโดยรวมยังเป็น diagnostic เท่านั้น เพราะ sample เล็กและ Sharpe proxy อ่อนไหวต่อ extreme trades

### ข้อสรุปเชิงข้อมูล

ผลนี้บอกว่ากลยุทธ์ไวต่อต้นทุนและ latency มาก โดยเฉพาะเมื่อ OOS ถูกดูแยกต่างหาก ผล baseline ที่เป็นบวกในภาพรวมยังไม่ควรถูกตีความว่าเป็น edge ที่ deploy ได้ เพราะ:

- sample ยังมีแค่ 90 closed trades
- OOS baseline ยังติดลบ
- cost drag ใหญ่เกือบครึ่งหนึ่งของ mid PnL
- latency เพียง 1-2 นาทีทำให้ผลลัพธ์แย่ลงแรง
- stress scenario สามารถทำให้ผลรวมติดลบได้

## 5. ปัญหา อุปสรรค และการแก้ไข

1. ปัญหา: runner แบบเดิมจะต้องโหลด quote ซ้ำหลายรอบถ้ารันทีละ scenario
   - การแก้ไข: runner M5.1 โหลด quote ต่อ dataset ครั้งเดียว แล้ววน scenario ใน memory
   - ผลลัพธ์: รัน 8 scenarios บนข้อมูลปัจจุบันเสร็จในประมาณ 5 นาที โดยไม่เรียก paid API

2. ปัญหา: latency อาจทำให้ไม่มี quote ณ เวลา entry ใหม่
   - การแก้ไข: ถ้า quote ที่เลื่อนเวลาแล้วไม่ครบทุก leg ให้ skip trade ไม่เติมราคาสมมติ
   - ผลลัพธ์: ยังคงวินัยข้อมูลจริงและไม่สร้าง PnL เทียม

3. ปัญหา: grid มีหลาย scenario จึงมีความเสี่ยง selection bias
   - การแก้ไข: เขียน search log ครบทุก 8 trials และระบุว่า best/worst เป็น diagnostic เท่านั้น
   - ผลลัพธ์: DSR ถูกบันทึกเป็น `blocked_under_sampled` ไม่ใช่การเลือก parameter เพื่อใช้งานจริง

4. ปัญหา: sample ยังต่ำกว่าเกณฑ์ที่ควรเชื่อถือมาก
   - การแก้ไข: ติด label `under-sampled` และ `underpowered` ใน report
   - ผลลัพธ์: รายงานไม่สรุปเกินหลักฐาน

## 6. ข้อสรุปและก้าวต่อไป

ข้อสรุป: ยังสรุปไม่ได้ว่า Sub-System A ผ่านเกณฑ์ด้าน execution robustness แต่การทดลองนี้ให้สัญญาณเตือนชัดเจนว่ากลยุทธ์ไวต่อต้นทุนและ latency มาก

ผลที่ควรจำ:

- Baseline `half_spread + $0.64 fee + 0 latency` ได้ implementable PnL 545.60 แต่ OOS เป็น -78.44
- latency 1 นาทีทำให้ baseline-like scenario ลดลงเหลือ 169.60
- latency 2 นาทีทำให้เหลือ 60.60
- stress หนักสุดทำให้ผลรวมเป็น -141.00
- ทุกผลยัง under-sampled/underpowered

ก้าวต่อไป:

1. อัปเดต `PROJECT_BRAIN.md` และ `IMPLEMENT_PLAN.md` ว่า M5.1 เสร็จแล้ว
2. รัน `python scripts\audit_research_logs.py` หลัง push log นี้ เพื่อยืนยันว่า next prefix เป็น `005-higanbana-`
3. เดินต่อ M5.2 strike-selection experiment โดยต้องเปิดเผย discrete strike mapping ให้ชัดเจน
4. ห้ามใช้ผล M5.1 เพื่อเลือก production parameter จนกว่าจะมี sample เพียงพอและ DSR/MinTRL/PSR พร้อมกว่าเดิม
