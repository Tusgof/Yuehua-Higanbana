# บันทึกการวิจัย: M5.3 Entry Timing Sensitivity

## 1. ข้อมูลพื้นฐาน

- Timestamp UTC: `2026-07-02T05:48:38Z`
- โครงการ: SPY 0DTE - Higanbana
- หัวข้อ: ทดสอบความไวของผลลัพธ์ต่อเวลาเข้า trade ของ Sub-System A และ Sub-System B
- ผู้บันทึก: Codex
- สถานะ: เสร็จสิ้นแบบ diagnostic
- เครื่องมือ:
  - Python local scripts
  - Databento normalized local artifacts เท่านั้น
- Artifact หลัก:
  - `scripts/run_m5_entry_timing_sensitivity.py`
  - `reports/experiments/m5_entry_timing_sensitivity_summary.json`
  - `reports/experiments/m5_entry_timing_sensitivity_report.md`
  - `reports/experiments/search_logs/m5_entry_timing_sensitivity_search_log.jsonl`
  - `reports/experiments/m5_entry_timing_components/`

## 2. วัตถุประสงค์

### อ่านแบบเร็ว

บันทึกนี้ตรวจว่าเวลาเข้า trade มีผลต่อ Sub-System A และ Sub-System B มากแค่ไหน โดยยังใช้ข้อมูลจริงในเครื่องและไม่ซื้อข้อมูลเพิ่ม
ผลสำคัญคือ timing เป็นตัวแปรที่กระทบผลลัพธ์ แต่รอบนี้เป็น sensitivity diagnostic ไม่ใช่การเลือกเวลาเข้า trade จาก OOS เพื่อใช้จริง
ข้อห้ามสรุป: ห้ามถือว่าเวลาที่ดีที่สุดใน grid คือ rule ที่ผ่าน validation แล้ว


การทดลองนี้ต้องการตอบว่าเวลาเข้า trade มีผลต่อ Sub-System A และ Sub-System B มากแค่ไหน เมื่อใช้ข้อมูล option chain จริงที่มีอยู่แล้ว ไม่ใช่ข้อมูลจำลอง และไม่ซื้อข้อมูลเพิ่ม

สำหรับ Sub-System A คำถามสำคัญคือ ORB แบบ 9:35 AM ET ยังเป็นจุดเข้าเหมาะสมที่สุดหรือไม่ หากเปลี่ยนเวลาคำนวณ opening range และ breakout เป็น 9:36, 9:37, 9:38, 9:39 หรือ 10:00 AM ET ผลลัพธ์จะเปลี่ยนอย่างไร

สำหรับ Sub-System B คำถามคือ fixed capped-risk put ratio spread ที่เคยไม่ผ่านด้านขนาดพอร์ต จะดีขึ้นหรือแย่ลงไหมถ้าเลื่อน entry snapshot ในช่วง 9:55-10:00 AM ET โดยยังไม่เปลี่ยนโครงสร้าง กลยุทธ์ หรือ sizing rule

## 3. วิธีการและขั้นตอน

1. อ่านสถานะโครงการจาก `PROJECT_BRAIN.md`, `IMPLEMENT_PLAN.md`, และ `AGENTS.md`
2. ตรวจ local LLM Wiki ที่เกี่ยวข้อง:
   - `wiki/concepts/spy-zero-dte-opening-range-breakout.md`
   - `wiki/concepts/zero-dte-conditional-trading-rules.md`
3. เพิ่ม runner ใหม่ `scripts/run_m5_entry_timing_sensitivity.py`
4. สร้าง scenario grid รวม 12 trials:
   - Sub-System A: `09:35`, `09:36`, `09:37`, `09:38`, `09:39`, `10:00`
   - Sub-System B: `09:55`, `09:56`, `09:57`, `09:58`, `09:59`, `10:00`
5. สำหรับ Sub-System A:
   - คำนวณ opening range และ breakout ใหม่ตามเวลาแต่ละ scenario
   - เลือก vertical spread จาก option quotes ที่ timestamp นั้น
   - ใช้ `half_spread`, fee `$0.64` ต่อ contract ต่อขา และ forced close 15:45 ET
6. สำหรับ Sub-System B:
   - ใช้ fixed capped put ratio template เดิม
   - ใช้ exact put snapshot ตามเวลาเข้า 9:55-10:00
   - ตรวจ feasibility ต่อ `account $1,000`, allocation `$300`, และ risk budget `$20`
7. บันทึก search log ครบทุก trial และกำหนด DSR เป็น blocker เพราะเป็น parameter grid ที่ sample ยังไม่พอ

คำสั่งที่ใช้:

```powershell
python -m unittest tests.test_m5_entry_timing_sensitivity
python scripts\run_m5_entry_timing_sensitivity.py
```

## 4. ผลการศึกษาและข้อมูลดิบ

### ผลรวมตาม scenario

| Scenario | Sub-System | Entry | Closed | Implementable PnL | Mid PnL | Cost drag | OOS PnL | Max drawdown |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `sub_a_orb_breakout_0935` | A | 09:35 | 90 | 539.60 | 1080.00 | 540.40 | -84.44 | -0.370283 |
| `sub_a_orb_breakout_0936` | A | 09:36 | 76 | -741.56 | -334.00 | 407.56 | -694.84 | -0.878399 |
| `sub_a_orb_breakout_0937` | A | 09:37 | 77 | -405.12 | 35.50 | 440.62 | -501.52 | -0.583488 |
| `sub_a_orb_breakout_0938` | A | 09:38 | 65 | 26.60 | 399.50 | 372.90 | -338.92 | -0.427538 |
| `sub_a_orb_breakout_0939` | A | 09:39 | 75 | -188.00 | 294.50 | 482.50 | -248.52 | -0.693697 |
| `sub_a_orb_breakout_1000` | A | 10:00 | 76 | -501.56 | -70.00 | 431.56 | -559.32 | -0.751000 |
| `sub_b_put_ratio_entry_0955` | B | 09:55 | 412 | -6098.44 | -1431.00 | 4667.44 | -4394.76 | -5.688661 |
| `sub_b_put_ratio_entry_0956` | B | 09:56 | 412 | -6401.44 | -1737.50 | 4663.94 | -4452.76 | -6.430365 |
| `sub_b_put_ratio_entry_0957` | B | 09:57 | 412 | -6070.44 | -1386.50 | 4683.94 | -4253.76 | -5.737225 |
| `sub_b_put_ratio_entry_0958` | B | 09:58 | 412 | -5855.44 | -1168.00 | 4687.44 | -4131.76 | -5.488867 |
| `sub_b_put_ratio_entry_0959` | B | 09:59 | 412 | -5827.44 | -1146.00 | 4681.44 | -3944.76 | -5.721647 |
| `sub_b_put_ratio_entry_1000` | B | 10:00 | 412 | -5973.44 | -857.50 | 5115.94 | -3866.76 | -6.202878 |

### ข้อสังเกตหลัก

- Sub-System A scenario ที่ดีที่สุดในเชิง diagnostic คือ `09:35` ซึ่งเป็น baseline เดิม
- การเลื่อน Sub-System A ไป 9:36-10:00 ทำให้ผลรวมแย่ลงเกือบทุกกรณี และ OOS ทุก scenario ยังติดลบ
- Sub-System B ยังไม่ผ่านด้าน feasibility ไม่ว่าเข้าที่ 9:55, 9:56, 9:57, 9:58, 9:59 หรือ 10:00
- Sub-System B ที่ดูดีที่สุดเชิง implementable PnL คือ 9:59 แต่ยังขาดทุนรวม `-5827.44` และไม่มี trade ไหนผ่าน allocation `$300` หรือ risk budget `$20`
- ทุก scenario ยังมี label `under-sampled` และ `underpowered`
- DSR status คือ `blocked_under_sampled` เพราะเป็น timing grid 12 trials และยังไม่ควรเลือก production timing จาก sample นี้

## 5. ปัญหา อุปสรรค และการแก้ไข

### ปัญหา 1: runner รอบแรก timeout

อาการ: `python scripts\run_m5_entry_timing_sensitivity.py` รอบแรก timeout หลัง 900 วินาที

สาเหตุ: สคริปต์เวอร์ชันแรกอ่านข้อมูล option quote ขนาดใหญ่ซ้ำตามจำนวน scenario ทำให้ประมวลผลช้าเกินจำเป็น

การแก้ไข: ปรับ runner เป็น dataset-first processing คือโหลดแต่ละ dataset หนึ่งครั้ง แล้วประเมินทุก scenario ใน pass เดียว

ผลหลังแก้: รันสำเร็จ และสร้าง summary/report/search log ครบ

### ข้อจำกัดสำคัญ

- ผลนี้ยังเป็น diagnostic เท่านั้น เพราะจำนวน trade ยังต่ำกว่าเกณฑ์ acceptance
- Sub-System A 9:35 ดูดีที่สุดในข้อมูลนี้ แต่ห้ามเลือก production rule จาก OOS ที่เปิดดูแล้ว
- Sub-System B ยังใช้ template เดิม จึงเป็นการยืนยันปัญหา feasibility ของ template ไม่ใช่ข้อพิสูจน์ว่า Sub-System B ทุกแบบใช้ไม่ได้
- ไม่มี paid API call และไม่มีข้อมูลใหม่เพิ่มในการทดลองนี้

## 6. ข้อสรุปและก้าวต่อไป

ข้อสรุป: ยังสรุปไม่ได้ในเชิง acceptance แต่ M5.3 ให้หลักฐาน diagnostic ว่า Sub-System A ไม่ได้ดีขึ้นจากการเลื่อน entry timing และ Sub-System B ยังไม่ผ่าน feasibility ภายใต้ template เดิม

- Sub-System A: 9:35 ยังเป็น scenario ที่ดีที่สุดใน grid นี้ แต่ OOS ยังติดลบ จึงยังไม่ใช่หลักฐานพอสำหรับ deployment
- Sub-System B: เวลาเข้าใกล้ 10:00 ไม่แก้ปัญหาขนาดพอร์ตหรือ risk budget
- Search log ครบ 12 trials จึงลดปัญหา cherry-picking แต่ DSR ยัง blocked เพราะ sample ไม่พอ

ก้าวต่อไป:

1. อัปเดต `PROJECT_BRAIN.md` และ `IMPLEMENT_PLAN.md` ให้ระบุว่า M5.3 เสร็จแล้ว
2. รัน `python scripts\audit_research_logs.py` เพื่อยืนยัน log 006 และ push status
3. เดินต่อ M5.4 exit target/stop sensitivity พร้อม search log และ DSR blocker
