# บันทึกการวิจัย: H-A2 Mechanism Revision Audit

## 1. ข้อมูลพื้นฐาน

- Timestamp UTC: `2026-07-08T14:23:25Z`
- โครงการ: SPY 0DTE - Higanbana
- หัวข้อ: ตรวจกลไกว่า H-A2 แพ้เพราะอะไรหลัง exact replay สองเคส
- ผู้บันทึก: Codex
- สถานะ: เสร็จสิ้น
- ระดับหลักฐาน: `E1`
- ข้อสรุป: `ยังสรุปไม่ได้`
- Artifact หลัก:
  - `experiments/h_a2_mechanism_revision_preregistration.json`
  - `reports/diagnostics/h_a2_mechanism_revision_audit.json`
  - `reports/diagnostics/h_a2_mechanism_revision_audit.md`
  - `reports/diagnostics/search_logs/h_a2_mechanism_revision_audit_search_log.jsonl`

## 2. วัตถุประสงค์

### อ่านแบบเร็ว

รอบนี้ไม่ได้ถามว่า H-A2 มี edge แล้วหรือยัง แต่ถามให้แคบกว่านั้นว่า exact replay สองเคสล่าสุดแพ้เพราะ “ทายทิศทางผิด” หรือเพราะ “ทายทิศทางถูกแต่ option spread ยังไปไม่ถึงจุดที่คุ้มต้นทุน”

ผลคือ SPY ขยับขึ้นหลังเข้า trade ทั้งสองวัน ดังนั้นสัญญาณทิศทางไม่ได้ผิดแบบตรง ๆ แต่ call vertical ที่เลือกยังขาดทุน เพราะราคาปิดบังคับตอน `15:45 ET` ยังต่ำกว่า long strike ทั้งสองเคส และเมื่อรวม bid/ask กับค่าธรรมเนียมแล้ว `implementable_pnl` ติดลบมากกว่า `mid_pnl`

ความหมายสำคัญคือสมมติฐานเดิมของ H-A2 ยังหยาบเกินไป ถ้าจะทำต่อ ต้องถามเรื่องขนาดการไปต่อหลังเข้า trade, strike reachability และต้นทุนจริง ไม่ใช่ซื้อข้อมูลเพิ่มเพื่อทดสอบ rule เดิมซ้ำทันที

ห้ามสรุปว่ากลยุทธ์ H-A2 ใช้ได้ ห้ามสรุปว่ากลยุทธ์ ORB debit spread ล้มเหลวทั้งตระกูล และห้ามใช้ผลนี้อนุมัติ `paper trading`

วัตถุประสงค์ของ H-A2.60 คือใช้ข้อมูลที่มีอยู่แล้วมาตรวจกลไกของความล้มเหลว ก่อนตัดสินใจว่าจะซื้อข้อมูลเพิ่มหรือแก้สมมติฐานก่อน หากเราไม่ทำขั้นนี้ การเพิ่ม sample อาจกลายเป็นการจ่ายเงินเพื่อทดสอบคำถามที่ผิดตั้งแต่ต้น

## 3. วิธีการและขั้นตอน

1. ใช้ preregistration ของ H-A2.59 เป็นกรอบควบคุม
2. ใช้ exact replay สองเคสที่มีอยู่แล้วเท่านั้น คือ `2025-02-11` และ `2025-05-05`
3. ตรวจว่าทิศทางของ underlying หลังเข้า trade ถูกหรือผิด
4. ตรวจว่า forced-close price ไปถึง long strike ของ call vertical หรือไม่
5. รวมผล `mid_pnl`, `implementable_pnl` และ cost drag
6. ห้ามโหลดข้อมูลเพิ่ม ห้ามทำ exact replay เพิ่ม ห้ามเปลี่ยน threshold `0.001` และห้ามเลือก filter ใหม่จากผลลัพธ์นี้

คำสั่งตรวจหลัก:

```powershell
python scripts\run_h_a2_mechanism_revision_audit.py
python scripts\validate_h_a2_mechanism_revision_audit.py
python -m unittest tests.test_h_a2_mechanism_revision_audit
python -m unittest tests.test_audit_research_readiness
```

## 4. ผลการศึกษาและข้อมูลดิบ

| Metric | ค่า |
|---|---:|
| จำนวน exact replay ที่ตรวจ | `2` |
| จำนวนเคสที่ underlying ไปถูกทิศทาง | `2` |
| จำนวนเคสที่ option spread ยังขาดทุน | `2` |
| จำนวนเคสที่ forced-close price ยังไม่ถึง long strike | `2` |
| Total `mid_pnl` | `-50.00` |
| Total `implementable_pnl` | `-59.12` |
| Total cost drag vs mid | `9.12` |
| Sample status | `under-sampled` / `underpowered` |

รายละเอียดรายวัน:

| Date | Direction | Entry | Forced close | Long strike | `mid_pnl` | `implementable_pnl` |
|---|---|---:|---:|---:|---:|---:|
| `2025-02-11` | `call` | `603.52` | `604.93` | `605` | `-22.00` | `-26.56` |
| `2025-05-05` | `call` | `563.12` | `564.38` | `565` | `-28.00` | `-32.56` |

สองวันนี้ SPY ขึ้นหลังเข้า trade ทั้งคู่ แต่ยังขึ้นไม่พอเมื่อเทียบกับ strike ที่เลือกไว้ ตัวอย่างเช่นวันที่ `2025-02-11` เข้าแถว `603.52` และปิดบังคับที่ `604.93` แต่ long call อยู่ที่ `605` ส่วนวันที่ `2025-05-05` เข้าแถว `563.12` และปิดบังคับที่ `564.38` แต่ long call อยู่ที่ `565`

นี่ทำให้เราเห็นว่า “ทิศทางถูก” ไม่เท่ากับ “option spread ทำเงิน” สำหรับ 0DTE เพราะ option ต้องการทั้งทิศทาง ขนาดการเคลื่อนที่ เวลา และต้นทุนที่เหมาะสมพร้อมกัน

## 5. ปัญหา อุปสรรค และการแก้ไข

ข้อจำกัดหลักคือมี exact replay เพียง 2 trade จึงยังเป็น `E1` และยัง `under-sampled` / `underpowered` ไม่สามารถใช้แทน MinTRL/PSR หรือ acceptance-grade evidence ได้

สิ่งที่รอบนี้แก้ได้คือทำให้คำถามวิจัยคมขึ้น จากเดิมที่เหมือนถามว่า “clean ORB direction ใช้ได้ไหม” กลายเป็น “ORB debit vertical จะใช้ได้ก็ต่อเมื่อ post-entry move ใหญ่พอจะไปถึง strike และชนะต้นทุนจริงหรือไม่”

สิ่งที่ห้ามสรุปจากรอบนี้:

- ห้ามบอกว่า H-A2 มี edge แล้ว
- ห้ามบอกว่า H-A2 ล้มเหลวทั้งตระกูล
- ห้ามซื้อข้อมูลเพิ่มจากผลนี้ทันทีโดยไม่มี preregistration ใหม่
- ห้ามเปลี่ยน threshold `0.001` จากผลสองเคสนี้
- ห้ามเลือก filter ใหม่จาก OOS หลังเห็นผล
- ห้ามอนุมัติ `paper trading`, operational validation หรือ real-money trading
- ห้ามอ้าง `E2`

## 6. ข้อสรุปและก้าวต่อไป

ข้อสรุป: `ยังสรุปไม่ได้` เพราะ sample ยังเล็กมาก แต่รอบนี้ตอบคำถามกลไกได้ชัดขึ้นว่า current locked condition ยังไม่ควรขยาย sample ต่อแบบเดิม

เหตุผลคือสองเคสที่ replay แล้วให้ภาพเดียวกัน: underlying ไปถูกทาง แต่ option spread ยังแพ้ เพราะ movement ไม่พอเมื่อเทียบกับ long strike และต้นทุนจริง ดังนั้นปัญหาไม่ได้อยู่แค่การคัดวันว่า macro/VIX สะอาดหรือไม่ แต่อยู่ที่การวัดว่า post-entry move ใหญ่พอสำหรับ payoff ของ spread หรือไม่

ก้าวต่อไป:

1. Pre-register H-A2.61 เป็น train-only revised rule ที่เน้น cost-adjusted post-entry magnitude, strike reachability และ implementable friction
2. ยังไม่ซื้อข้อมูลเพิ่มและยังไม่ทำ exact replay expansion จนกว่า H-A2.61 จะนิยาม rule ใหม่และ guardrail ชัดเจน
3. ทุกผลในรอบถัดไปต้องยังแยก `mid_pnl` กับ `implementable_pnl` และต้องรายงาน `under-sampled` / `underpowered` ถ้า sample ยังไม่พอ
