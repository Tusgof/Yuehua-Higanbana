# บันทึกการวิจัย: H-A2 Normal/Control Import Diagnostic

## 1. ข้อมูลพื้นฐาน

- Timestamp UTC: `2026-07-07T07:08:31Z`
- โครงการ: SPY 0DTE - Higanbana
- หัวข้อ: ตรวจว่า normal/control data pack อ่านได้และมี candidate trade หรือไม่
- ผู้บันทึก: Codex
- สถานะ: เสร็จสิ้น
- ระดับหลักฐาน: `E1`
- ข้อสรุป: `ยังสรุปไม่ได้`
- Artifact หลัก:
  - `experiments/h_a2_normal_control_import_diagnostic_preregistration.json`
  - `reports/diagnostics/h_a2_normal_control_import_diagnostic.json`
  - `reports/diagnostics/h_a2_normal_control_import_diagnostic.md`
  - `reports/diagnostics/search_logs/h_a2_normal_control_import_diagnostic_search_log.jsonl`

## 2. วัตถุประสงค์

### อ่านแบบเร็ว

รอบนี้ตรวจ normal/control data pack 10 วันว่าเปิดอ่านได้ครบไหม timestamp ตรงไหม และกฎ H-A2 แบบ locked `09:35 ET` เจอวันที่ควร trade จริงหรือไม่ ผลคือข้อมูลอ่านได้ครบทุกวัน และพบ candidate-ready เพียง 1 วันคือ `2025-02-11` แต่รอบนี้ยังไม่ได้ทำ exact replay หรือคำนวณ PnL

นี่คือขั้นตรวจความพร้อมของข้อมูล ไม่ใช่ผลกำไรของกลยุทธ์ ความสำเร็จของรอบนี้คือรู้ว่าข้อมูลพอใช้ต่อ และรู้ว่าควร replay วันไหนแบบจำกัดขอบเขต

## 3. วิธีการและขั้นตอน

1. ใช้เฉพาะข้อมูล normal/control ที่ดาวน์โหลดไว้แล้ว ไม่มี download เพิ่ม
2. อ่าน SPY bars และ OPRA `cbbo-1m` grouped files ระหว่าง `2025-02-03` ถึง `2025-02-14`
3. ตรวจว่า `09:35 ET` และ `15:45 ET` มีข้อมูลครบ และ quote อยู่ในวัน ET ที่ถูกต้อง
4. reconstruct locked H-A2 `09:35 ET` signal ด้วย threshold `0.001`
5. ห้ามคำนวณ PnL จนกว่าจะมี exact-replay preregistration แยก

คำสั่งตรวจหลัก:

```powershell
python scripts\validate_h_a2_normal_control_import_diagnostic.py
python -m unittest tests.test_h_a2_normal_control_import_diagnostic
```

## 4. ผลการศึกษาและข้อมูลดิบ

| Metric | ค่า |
|---|---:|
| Dates in pack | `10` |
| SPY bar rows | `3,900` |
| OPRA quote rows | `35,284,142` |
| 0DTE rows | `935,372` |
| 0DTE valid-mid rows | `557,254` |
| Timestamp alignment pass | `10 / 10` |
| Clean macro/VIX dates | `7` |
| Locked signal true dates | `1` |
| Candidate-ready dates | `2025-02-11` |
| Candidate data blocked count | `0` |

ผลคือ data pack ใช้ต่อได้จริง ทั้ง 10 วันผ่าน timestamp alignment และไม่มีวันที่ candidate ถูก block เพราะข้อมูลไม่ครบ แต่กฎที่ล็อกไว้เจอ candidate เพียงวันเดียว จึงต้องแยก exact replay เป็นงานถัดไปที่แคบมาก

## 5. ปัญหา อุปสรรค และการแก้ไข

ข้อจำกัดคือ 9 จาก 10 วันไม่มี candidate trade ตามกฎที่ล็อกไว้ และรอบนี้ยังไม่ compute `mid_pnl` หรือ `implementable_pnl` จึงยังบอกอะไรเรื่องผลตอบแทนไม่ได้

สิ่งที่ห้ามสรุปจากรอบนี้:

- ห้ามบอกว่า H-A2 ทำกำไรหรือขาดทุนจาก normal/control pack แล้ว
- ห้ามอ้าง `E2` หรืออนุมัติ `paper trading`
- ห้าม broaden เกิน `2025-02-11` โดยไม่มี preregistration ใหม่

## 6. ข้อสรุปและก้าวต่อไป

ข้อสรุป: `ยังสรุปไม่ได้` แต่ข้อมูล normal/control พร้อมสำหรับ exact replay แบบจำกัดขอบเขต

รอบนี้ทำให้รู้ว่าปัญหาไม่ได้อยู่ที่ import หรือ timestamp แล้ว แต่ sample ที่เกิด signal ยังเล็กมาก งานถัดไปจึงต้อง replay เฉพาะ candidate เดียวนี้ก่อน แล้วค่อยตัดสินใจเรื่อง sample expansion

ก้าวต่อไป:

1. รัน bounded exact-replay diagnostic สำหรับ `2025-02-11` เท่านั้น
2. รายงาน `mid_pnl` และ `implementable_pnl` แยกกันตาม preregistration แยก
