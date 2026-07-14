# บันทึกการวิจัย: H-A2 Normal/Control Exact Replay

## 1. ข้อมูลพื้นฐาน

- Timestamp UTC: `2026-07-07T14:13:08Z`
- โครงการ: SPY 0DTE - Higanbana
- หัวข้อ: replay trade จริงของ H-A2 ใน normal/control sample หนึ่งวัน
- ผู้บันทึก: Codex
- สถานะ: เสร็จสิ้น
- ระดับหลักฐาน: `E1`
- ข้อสรุป: `ยังสรุปไม่ได้`
- Artifact หลัก:
  - `experiments/h_a2_normal_control_exact_replay_preregistration.json`
  - `reports/diagnostics/h_a2_normal_control_exact_replay.json`
  - `reports/diagnostics/h_a2_normal_control_exact_replay.md`
  - `reports/diagnostics/search_logs/h_a2_normal_control_exact_replay_search_log.jsonl`

## 2. วัตถุประสงค์

### อ่านแบบเร็ว

รอบนี้ทำ exact replay เฉพาะวันที่ `2025-02-11` ซึ่งเป็นวันเดียวใน normal/control pack ที่ H-A2 ส่งสัญญาณครบตามกฎเดิม ผลของ trade เดียวนี้ขาดทุน: `mid_pnl = -22.00` และ `implementable_pnl = -26.56` หลังหักค่าธรรมเนียม แต่ sample มีแค่ 1 trade จึงยังสรุปไม่ได้ว่า H-A2 ใช้ได้หรือใช้ไม่ได้

คำถามของรอบนี้แคบมาก: เมื่อกฎ H-A2 เกิด signal จริง และมี option quote ครบที่ entry/forced close ถ้า replay ตาม bid/ask จริง ผลของ candidate trade เป็นอย่างไร รอบนี้ไม่ได้หาค่าใหม่ ไม่ได้ซื้อข้อมูลเพิ่ม และไม่ได้ทดสอบวันที่อื่น

## 3. วิธีการและขั้นตอน

1. ตรวจ preregistration ก่อนด้วย `scripts\validate_h_a2_normal_control_exact_replay_preregistration.py`
2. ใช้เฉพาะ raw DBN เดิมของ `2025-02-11` จาก normal/control pack
3. ใช้ direction `call`, entry `09:35 ET`, forced close `15:45 ET`, threshold `0.001`
4. เลือก strike ด้วย `nearest_discrete_strike_rounding`, target gap `1.48`, width `2.0`
5. รายงาน `mid_pnl` และ `implementable_pnl` แยกกัน โดย `implementable_pnl` ใช้ bid/ask และ fee `$0.64` ต่อ leg

คำสั่งตรวจหลัก:

```powershell
python scripts\validate_h_a2_normal_control_exact_replay_preregistration.py
python scripts\run_h_a2_normal_control_exact_replay.py
python scripts\validate_h_a2_normal_control_exact_replay.py
python -m unittest tests.test_h_a2_normal_control_exact_replay
```

## 4. ผลการศึกษาและข้อมูลดิบ

| Metric | ค่า |
|---|---:|
| Candidate date | `2025-02-11` |
| Direction | `call` |
| Underlying at entry | `603.52` |
| Underlying at forced close | `604.93` |
| Entry valid call rows | `91` |
| Forced-close valid call rows | `88` |
| Long call strike | `605.0` |
| Short call strike | `607.0` |
| Entry mid debit | `0.49` |
| Forced-close mid value | `0.27` |
| Mid PnL | `-22.00` |
| Entry implementable debit | `0.50` |
| Forced-close implementable credit | `0.26` |
| Gross implementable PnL before fees | `-24.00` |
| Total fees | `2.56` |
| Implementable PnL | `-26.56` |
| Cost drag vs mid | `4.56` |
| Sample count | `1` |

ขา option ที่เลือกคือ long `SPY 250211C605` และ short `SPY 250211C607` ทั้งสองขามี quote ครบทั้งตอนเข้าและตอน forced close จึงไม่มี blocker ด้านข้อมูลสำหรับ trade นี้

ผลสำคัญคือ trade เดียวนี้แพ้ แม้ underlying ขยับขึ้นจาก `603.52` เป็น `604.93` เพราะ vertical spread ที่เลือกเสียมูลค่าจากเวลาและ spread/cost มากกว่าประโยชน์จากทิศทางราคาในช่วงที่ถือ เมื่อนับ bid/ask และค่าธรรมเนียม ผลจริงที่ trade ได้แย่กว่า mid PnL อีก `$4.56`

## 5. ปัญหา อุปสรรค และการแก้ไข

ข้อจำกัดใหญ่ที่สุดคือมีเพียง 1 trade จึง `under-sampled` และ `underpowered` อย่างชัดเจน ผลนี้ใช้บอกพฤติกรรมของ candidate trade วันนี้ได้ แต่ใช้ตัดสิน H-A2 ทั้งสมมติฐานไม่ได้

สิ่งที่ห้ามสรุปจากรอบนี้:

- ห้ามบอกว่า H-A2 ผ่านหรือไม่ผ่านจาก trade เดียว
- ห้ามอ้าง `E2` หรือ acceptance-grade evidence
- ห้ามอนุมัติ `paper trading`, operational validation หรือ real-money trading
- ห้าม broaden ผลนี้ไปยังวันที่ไม่มี signal หรือวันที่ยังไม่ได้ replay
- ห้ามเปลี่ยน threshold `0.001` จากผลย้อนหลังนี้โดยไม่มี preregistration ใหม่

## 6. ข้อสรุปและก้าวต่อไป

ข้อสรุป: `ยังสรุปไม่ได้` เพราะ exact replay ครั้งนี้มีเพียง 1 candidate trade และ trade นั้นขาดทุน

สิ่งที่รอบนี้บอกได้จริงคือ pipeline ของ normal/control exact replay ทำงานได้ครบ ตั้งแต่เลือก strike จาก quote จริง คำนวณ `mid_pnl` แยกจาก `implementable_pnl` และบังคับ guardrail ไม่ให้ claim เกินหลักฐาน แต่ยังไม่มี sample size พอจะตัดสิน edge

ก้าวต่อไป:

1. ใช้ผลนี้เป็น `E1 single-candidate diagnostic evidence` เท่านั้น
2. วางแผน validation-data หรือ sample-expansion step ถัดไปแบบ pre-registered ก่อนซื้อข้อมูลหรือ replay เพิ่ม
3. ยังไม่ทำ `paper trading` หรือ operational validation จนกว่าจะมีหลักฐานระดับสูงกว่าและผ่าน acceptance gate
