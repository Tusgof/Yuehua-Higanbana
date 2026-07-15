# บันทึกการวิจัย: M5.6 Portfolio Construction Diagnostic

## 1. ข้อมูลพื้นฐาน

- Timestamp UTC: `2026-07-02T07:24:10Z`
- โครงการ: SPY 0DTE - Higanbana
- หัวข้อ: ทดสอบการจัดพอร์ตระหว่าง Sub-System A และ Sub-System B แบบ diagnostic
- ผู้บันทึก: Codex
- สถานะ: เสร็จสิ้นแบบ diagnostic
- เครื่องมือ:
  - Python local scripts
  - Sub-System A baseline summary
  - Sub-System B feasibility summary
- Artifact หลัก:
  - `scripts/run_m5_portfolio_construction_diagnostic.py`
  - `tests/test_m5_portfolio_construction_diagnostic.py`
  - `reports/experiments/m5_portfolio_construction_diagnostic_summary.json`
  - `reports/experiments/m5_portfolio_construction_diagnostic_report.md`
  - `reports/experiments/search_logs/m5_portfolio_construction_diagnostic_search_log.jsonl`
  - `reports/experiments/m5_portfolio_construction_components/`

## 2. วัตถุประสงค์

### อ่านแบบเร็ว

บันทึกนี้ตรวจ portfolio construction เพื่อดูว่าการรวม Sub-System A/B และ sizing เปลี่ยน risk/return อย่างไร
ผลสำคัญคือเป็น diagnostic ระดับพอร์ต ไม่ใช่การอนุมัติใช้พอร์ตจริง เพราะกลยุทธ์ย่อยยังมี blocker และ sample ยังจำกัด
ข้อห้ามสรุป: ห้ามใช้ผล portfolio diagnostic ข้ามขั้นไป paper trading โดยที่ edge ของระบบย่อยยังไม่ผ่าน


การทดลองนี้ต้องการตอบว่า portfolio construction ระหว่าง Sub-System A และ Sub-System B ช่วยให้พอร์ตอยู่รอดดีขึ้นหรือไม่ เมื่อเทียบกับการใช้ Sub-System A อย่างเดียว

เหตุผลที่ต้องทำรอบนี้คือ M4.1 แสดงว่า Sub-System A ยังสรุปไม่ได้แต่มีผลรวมเป็นบวก ส่วน M4.2 แสดงว่า Sub-System B แบบ current sizing ไม่ผ่าน เพราะไม่มี trade ใด fit `$300` allocation หรือ `$20` risk budget เลย ดังนั้น M5.6 ต้องแยกให้ชัดระหว่าง “พอร์ตจำลองเชิงคณิตศาสตร์” กับ “พอร์ตที่เทรดได้จริงในบัญชี $1,000”

ความสำเร็จของรอบนี้คือการได้ comparison ที่มี equal weight, risk parity, ES parity, OOS split, drawdown, ES95/ES99, big-day dependency, search log, DSR blocker และ feasibility label โดยไม่อ้างว่า portfolio ใดพร้อมใช้งานจริง

## 3. วิธีการและขั้นตอน

1. อ่านสถานะจาก `PROJECT_BRAIN.md`, `IMPLEMENT_PLAN.md`, และ `AGENTS.md`
2. ตรวจ local LLM Wiki ก่อนกำหนดแนวทาง portfolio/risk allocation:
   - `wiki/concepts/risk-parity.md`
   - `wiki/concepts/portfolio-optimization.md`
   - `wiki/concepts/position-sizing.md`
3. ใช้ input จาก real-data baseline เดิม:
   - `reports/baselines/subsystem_a_orb_baseline_summary.json`
   - `reports/baselines/subsystem_b_put_ratio_feasibility_summary.json`
4. สร้าง daily PnL union ของ Sub-System A และ B โดย date ที่ strategy ไม่มี trade ให้ PnL เป็น `0`
5. ทดสอบ 5 allocation scenarios:
   - `subsystem_a_only_control`
   - `subsystem_b_only_diagnostic`
   - `equal_weight_fractional_diagnostic`
   - `risk_parity_inverse_vol_in_sample`
   - `es_parity_inverse_es95_in_sample`
6. Fit weight ของ risk parity และ ES parity จาก in-sample เท่านั้น แล้วรายงาน OOS โดยไม่ใช้ OOS เป็นตัวเลือก parameter
7. บันทึกทุก allocation trial ลง search log
8. ตั้ง DSR เป็น `blocked_under_sampled`
9. ตรวจ feasibility ของ Sub-System B เทียบกับบัญชี `$1,000`, allocation เดิม `$300`, และ risk budget `$20`

คำสั่งที่ใช้:

```powershell
python -m unittest tests.test_m5_portfolio_construction_diagnostic
python scripts\audit_paid_costs.py
python scripts\run_m5_portfolio_construction_diagnostic.py
```

## 4. ผลการศึกษาและข้อมูลดิบ

### ผลรวมตาม scenario

| Scenario | Weight A | Weight B | Total PnL | OOS PnL | Max drawdown | Feasibility |
|---|---:|---:|---:|---:|---:|---|
| `subsystem_a_only_control` | 1.00000000 | 0.00000000 | 545.60 | -78.44 | -0.370769 | `account_feasible_without_subsystem_b` |
| `subsystem_b_only_diagnostic` | 0.00000000 | 1.00000000 | -5973.44 | -3866.76 | -6.202878 | `blocked_current_sizing` |
| `equal_weight_fractional_diagnostic` | 0.50000000 | 0.50000000 | -2713.92 | -1972.60 | -2.795771 | `blocked_current_sizing` |
| `risk_parity_inverse_vol_in_sample` | 0.99470524 | 0.00529476 | 511.07 | -98.51 | -0.381438 | `blocked_current_sizing` |
| `es_parity_inverse_es95_in_sample` | 0.72767643 | 0.27232357 | -1229.67 | -1110.05 | -1.341492 | `blocked_current_sizing` |

### ข้อสังเกตหลัก

- Sub-System A only เป็น scenario เดียวที่ไม่แตะ Sub-System B และจึงไม่ติด sizing blocker ของ B
- Sub-System B only ทำให้พอร์ตจำลองติดลบหนักมาก: total PnL `-$5973.44`, OOS `-$3866.76`, max drawdown `-6.202878`
- Equal weight ทำให้ผลรวมแย่ลงมาก เพราะดึง Sub-System B ที่ยังไม่ผ่านเข้าพอร์ต
- Risk parity แบบ inverse volatility ลดน้ำหนัก B เหลือ `0.00529476` แต่ยังไม่ช่วย เพราะผลรวม `$511.07` ต่ำกว่า A-only และ OOS แย่กว่า A-only
- ES parity ให้น้ำหนัก B `0.27232357` และผลเสียชัดเจน: total PnL `-$1229.67`, OOS `-$1110.05`
- ทุก scenario ยัง `under-sampled` และ `underpowered`
- Search log บันทึกครบ 5 trials และ DSR status คือ `blocked_under_sampled`

### ข้อจำกัดด้านการเทรดจริง

Blended portfolio ทั้งหมดที่มี Sub-System B เป็นเพียง fractional diagnostic เท่านั้น เพราะออปชันเทรดเป็นเศษสัญญาไม่ได้

Sub-System B ยังมีข้อจำกัดเดิม:

- max defined loss: `$773.00`
- median defined loss: `$566.00`
- min defined loss: `$366.00`
- fit `$300` allocation: `0/412`
- fit `$20` risk budget: `0/412`

ดังนั้น portfolio construction ไม่สามารถแก้ปัญหา Sub-System B ได้ จนกว่าจะมีการออกแบบ sizing, capital, หรือ strategy template ใหม่

## 5. ปัญหา อุปสรรค และการแก้ไข

### ปัญหาที่พบ

ไม่พบปัญหาทาง execution ในรอบนี้

### ข้อจำกัดสำคัญ

- Daily PnL union มี 416 วัน ซึ่งยังต่ำกว่า prior floor 500 observations
- ผล portfolio เป็น diagnostic ไม่ใช่ deployable allocation
- Risk parity และ ES parity ใช้ fractional weights ซึ่งไม่สามารถส่ง order ออปชันจริงได้โดยตรง
- Sub-System B baseline มีสถานะ `ไม่ผ่าน` อยู่แล้ว จึงไม่ควรถูก portfolio construction กลบปัญหาหลัก
- ยังไม่มี MinTRL/PSR/DSR acceptance-grade calculation เพราะ sample ยังไม่พอ

## 6. ข้อสรุปและก้าวต่อไป

ข้อสรุป: ยังสรุปไม่ได้ แต่ผลรอบนี้ไม่สนับสนุนการผสม Sub-System B เข้าพอร์ตภายใต้ current sizing

- A-only เป็น diagnostic control ที่ดีที่สุดและเป็น scenario เดียวที่ไม่ติด blocker ของ Sub-System B
- Equal weight, risk parity, และ ES parity ไม่ช่วยให้ OOS ดีขึ้น
- Sub-System B ต้องแก้ที่ strategy design หรือ sizing ก่อน ไม่ใช่แก้ด้วย portfolio weighting
- ห้ามนำ fractional portfolio weights ไปใช้เป็น production allocation

ก้าวต่อไป:

1. อัปเดต `PROJECT_BRAIN.md` และ `IMPLEMENT_PLAN.md` ให้บันทึกว่า M5.6 เสร็จแบบ diagnostic
2. รัน verification รวมหลังอัปเดตเอกสาร
3. ประเมิน M5.7 structural-break testing ว่าจะทำได้หรือควร defer เพราะยังไม่มี reference/pre-break data
