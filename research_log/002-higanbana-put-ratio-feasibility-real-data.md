# บันทึกการวิจัย: Put Ratio Feasibility บนข้อมูลจริง

## 1. ข้อมูลพื้นฐาน

- Timestamp UTC: `2026-07-01T15:44:27Z`
- โครงการ: SPY 0DTE - Higanbana
- หัวข้อ: Sub-System B capped-risk put ratio spread feasibility บนข้อมูลจริง
- ผู้บันทึก: Codex
- สถานะ: เสร็จสิ้น
- เครื่องมือ:
  - `scripts/run_m4_subsystem_b_feasibility.py`
  - `python scripts\audit_research_logs.py`
- Artifact หลัก:
  - `reports/baselines/subsystem_b_put_ratio_feasibility_summary.json`
  - `reports/baselines/subsystem_b_put_ratio_feasibility_report.md`
  - `scripts/run_m4_subsystem_b_feasibility.py`

## 2. วัตถุประสงค์

### อ่านแบบเร็ว

บันทึกนี้ตรวจ Sub-System B แบบ capped-risk put ratio spread ว่าโครงสร้างและ sizing เบื้องต้นทำได้จริงหรือไม่ภายใต้พอร์ตเล็ก
ผลสำคัญคือ feasibility ไม่เท่ากับ edge กลยุทธ์นี้มี tail risk และข้อจำกัดด้านขนาดพอร์ต จึงต้องใช้หลักฐานมากกว่านี้ก่อนถือว่าใช้ได้จริง
ข้อห้ามสรุป: ห้ามใช้ผล feasibility เป็นคำยืนยันว่ากลยุทธ์ทำกำไรได้หรือพร้อมเทรด


การทดลองรอบนี้ต้องตอบคำถามว่า Sub-System B แบบ capped-risk put ratio spread สามารถประกอบโครงสร้างและใส่ขนาดภายใต้บัญชีเริ่มต้น `$1,000` ได้จริงหรือไม่ ก่อนนำไปทดสอบ filter, timing model, หรือ portfolio construction ต่อ

จุดสำคัญของรอบนี้คือ feasibility ไม่ใช่การพิสูจน์ edge ขั้นสุดท้าย เพราะ Sub-System B มี tail risk สูงกว่า Sub-System A และต้องใช้ sample มากกว่า การทดลองจึงแยกคำถามออกเป็นสองชั้น: โครงสร้าง defined-risk ทำได้ไหม และขนาดความเสี่ยงต่อ 1 ชุด fit กับ `$300` allocation / `$20` risk budget หรือไม่

## 3. วิธีการและขั้นตอน

1. ใช้ข้อมูลจริงที่มีอยู่จาก Mar-Dec 2023 เป็น in-sample และ Jan-Dec 2024 เป็น OOS
2. เลือก entry ที่ 10:00 ET หรือ quote ล่าสุดก่อน 10:00 ET ภายในหน้าต่าง 09:55-10:00 ET
3. ปิด news filter และ LLM filter ทั้งหมด
4. สร้าง put ratio spread แบบ fixed template:
   - Buy 1 near-ATM put
   - Sell 2 puts ใกล้ moneyness `0.99`
   - Buy 1 protective wing อย่างน้อย `$10` ต่ำกว่า short strike
5. ใช้ nearest discrete strike rounding เพื่อเลือก strike จริงใน chain
6. ปิดสถานะด้วย forced close ใกล้ 15:45 ET
7. คำนวณ `mid_pnl`, `implementable_pnl`, cost drag, max defined loss, feasibility ต่อบัญชี `$1,000`, allocation `$300`, และ risk budget `$20`

คำสั่งหลัก:

```powershell
python scripts\run_m4_subsystem_b_feasibility.py
python scripts\audit_research_logs.py
```

พารามิเตอร์สำคัญ:

| Parameter | Value |
|---|---:|
| Account equity | `$1000` |
| Sub-System B allocation | `$300` |
| 2% risk budget | `$20` |
| Near moneyness | `1.0` |
| Short moneyness | `0.99` |
| Protective wing gap | `$10` |
| Fee | `$0.64` per contract |

## 4. ผลการศึกษาและข้อมูลดิบ

### Feasibility

| Metric | Value |
|---|---:|
| Checked trades | 412 |
| Fit `$1000` account | 412 |
| Fit `$300` allocation | 0 |
| Fit `$20` risk budget | 0 |
| Minimum defined loss | 366.0 |
| Median defined loss | 566.0 |
| Maximum defined loss | 773.0 |

### ภาพรวม PnL

| Metric | Value |
|---|---:|
| Closed trades | 412 |
| Total mid PnL | -857.5 |
| Total implementable PnL | -5973.44 |
| Cost drag | 5115.94 |
| Average trade PnL | -14.4986 |
| Win rate | 0.2961 |
| Payoff ratio | 1.8012 |
| Sharpe proxy | 0.052955 |
| Sortino proxy | 0.747806 |
| Max drawdown | -6.202878 |
| ES95 | -161.4533 |
| ES99 | -237.92 |
| Worst-day loss | -454.12 |

### แยกตามช่วงเวลา

| Split | Coverage | Closed trades | Implementable PnL | Mid PnL | Cost drag | Fit `$300` allocation | Fit `$20` risk budget | Labels |
|---|---|---:|---:|---:|---:|---:|---:|---|
| in-sample | 2023-03-28 ถึง 2023-12-29 | 189 | -2106.68 | 26.5 | 2133.18 | 0/189 | 0/189 | under-sampled, underpowered |
| OOS | 2024-01-02 ถึง 2024-12-31 | 223 | -3866.76 | -884.0 | 2982.76 | 0/223 | 0/223 | under-sampled, underpowered |

### สิ่งที่ดี

- โครงสร้าง defined-risk สามารถประกอบได้ 412 ครั้งบนข้อมูลจริง
- ทุก trade มี max defined loss ต่ำกว่าเงินทั้งบัญชี `$1,000`
- Report แยก `mid_pnl` และ `implementable_pnl` ชัดเจน ทำให้เห็นว่า cost drag สูงมาก

### สิ่งที่ไม่ผ่าน

- ไม่มี trade ใด fit กับ allocation `$300` ของ Sub-System B
- ไม่มี trade ใด fit กับ risk budget `$20` ตามกติกา 2% ของบัญชี
- OOS implementable PnL เป็น `-3866.76`
- Cost drag รวม `5115.94` ใหญ่กว่าขาดทุนสุทธิ แปลว่า bid/ask และค่าธรรมเนียมเป็นปัญหาใหญ่
- Sample ยังต่ำกว่า `N >= 500` และ Sub-System B ต้องการ sample มากกว่าเพราะ tail risk จึงยังติด `under-sampled` และ `underpowered`

### Big-day dependency

หลังตัด top/bottom 5% ของ trade ตาม `implementable_pnl`:

| Metric | Original | Retained |
|---|---:|---:|
| Closed trades | 412 | 370 |
| Total implementable PnL | -5973.44 | -9229.4 |
| Sharpe proxy | -0.114291 | -0.249113 |

การตีความ: ผลไม่ได้พึ่งพาวันดีไม่กี่วันในทางที่ทำให้ดูดีเกินจริง แต่ระบบยังแย่ลงเมื่อเอา extreme trades ออก จึงไม่ใช่สัญญาณเชิงบวก

## 5. ปัญหา อุปสรรค และการแก้ไข

1. ปัญหา: normalized JSONL บางไฟล์มี UTF-8 BOM ทำให้ `json.loads` อ่านบรรทัดแรกไม่ได้
   การแก้ไข: ปรับ loader ใน `scripts/run_m4_subsystem_b_feasibility.py` ให้ใช้ `utf-8-sig`
   ผลลัพธ์: script อ่านไฟล์จริงได้ครบ

2. ปัญหา: การรันข้อมูลจริงรอบหนึ่งชน timeout ก่อนจบ
   การแก้ไข: รันซ้ำด้วย timeout ยาวขึ้น เพราะเป็นงานอ่านไฟล์ local ขนาดใหญ่ ไม่ใช่ network/API call
   ผลลัพธ์: summary และ report ถูกสร้างสำเร็จ

ข้อจำกัดสำคัญ:

- นี่เป็น fixed template feasibility ไม่ใช่ logistic timing model จาก paper
- ยังไม่ได้ทดสอบ variant ของ wing gap, moneyness, stop-loss หรือ allocation
- ผล `ไม่ผ่าน` นี้หมายถึง template ปัจจุบันไม่ fit sizing/risk ของบัญชี ไม่ใช่การลบ Sub-System B ออกจาก research scope ถาวร

## 6. ข้อสรุปและก้าวต่อไป

ข้อสรุป: ไม่ผ่านสำหรับการใช้งานภายใต้บัญชี `$1,000` ด้วยกติกา allocation `$300` และ risk budget `$20` เพราะ trade ที่ประกอบได้ทั้งหมดมี max defined loss ขั้นต่ำ `366.0`

- Sub-System B ปัจจุบันเป็น defined-risk แต่ขนาดความเสี่ยงต่อ 1 ชุดใหญ่เกินบัญชีตามกติกา sizing
- ผล edge ยังสรุปเชิงสถิติไม่ได้ เพราะ sample ต่ำกว่าเป้าหมายและเป็น fixed no-filter template
- ก่อนนำ Sub-System B ไป portfolio construction ต้องแก้โจทย์ feasibility ก่อน เช่น sizing, capital, wing design, หรือใช้ paper trading เพื่อ operational validation เท่านั้นหลัง research pass

ก้าวต่อไป:

1. ทำ M4.3 เพื่อเปรียบเทียบ forced-close-only กับ target/stop behavior เป็น diagnostic โดยไม่ tune บน OOS
2. บันทึก Sub-System B ไว้ว่าไม่ fit กับ `$300` allocation / `$20` risk budget ใน `PROJECT_BRAIN.md` และ `IMPLEMENT_PLAN.md`
3. หากกลับมาแก้ Sub-System B ภายหลัง ให้สร้าง hypothesis ใหม่เรื่อง sizing/capital/wing gap แยกจาก baseline รอบนี้
4. ใช้ research log ถัดไปเป็น `003-higanbana-...md` เมื่อ experiment round ถัดไปเสร็จจริง
