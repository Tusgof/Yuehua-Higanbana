# บันทึกการวิจัย: H-A2 Proxy-First Robustness

## 1. ข้อมูลพื้นฐาน

- Timestamp UTC: `2026-07-07T07:39:02Z`
- โครงการ: SPY 0DTE - Higanbana
- หัวข้อ: ตรวจว่า H-A2 ยังน่าศึกษาต่อหรือไม่ โดยใช้ `proxy` ก่อน exact replay
- ผู้บันทึก: Codex
- สถานะ: เสร็จสิ้น
- ระดับหลักฐาน: `E1`
- ข้อสรุป: `ยังสรุปไม่ได้`
- Artifact หลัก:
  - `experiments/h_a2_proxy_first_robustness_preregistration.json`
  - `reports/experiments/h_a2_proxy_first_robustness_summary.json`
  - `reports/experiments/h_a2_proxy_first_robustness_report.md`
  - `reports/experiments/search_logs/h_a2_proxy_first_robustness_search_log.jsonl`

## 2. วัตถุประสงค์

### อ่านแบบเร็ว

รอบนี้ไม่ได้พยายามพิสูจน์ว่า H-A2 ทำเงินได้แล้ว แต่ถามคำถามที่พื้นกว่านั้น: ถ้ายังไม่มีข้อมูล exact replay ครบ เราพอเห็นร่องรอยเชิงกลไกที่ควรตามต่อหรือไม่ ผลคือ `proxy` หลายแบบยังชี้ไปทางเดียวกันพอสมควร แต่ยังใช้ยืนยัน edge ไม่ได้ เพราะไม่ใช่ผลเข้าออก option จริง

ประเด็นสำคัญคือ `1-minute bars` จำเป็นต่อ exact replay แต่ไม่ได้แปลว่าทุกคำถามของสมมติฐานต้องรอข้อมูลละเอียดระดับนั้นก่อนเสมอ รอบนี้จึงใช้ข้อมูลที่มีอยู่เพื่อตรวจทิศทางของกลไกก่อนตัดสินใจซื้อหรือไล่ข้อมูลเพิ่ม

## 3. วิธีการและขั้นตอน

1. ใช้ข้อมูลในเครื่องเท่านั้น ไม่มี network ไม่มี paid data ไม่มี IBKR และไม่มี LLM
2. เทียบสัญญาณระดับวันกับ `5-minute proxy`, `15-minute proxy`, และผล trade เดิมที่มีอยู่
3. ใช้ chronological split ไม่ใช้ random split และไม่ปรับค่าโดยดู OOS
4. เก็บ trial ไว้ใน search log และไม่เลือกผลที่ดีที่สุดเพื่ออ้าง acceptance

คำสั่งตรวจหลัก:

```powershell
python scripts\validate_h_a2_proxy_first_robustness_summary.py
python -m unittest tests.test_h_a2_proxy_first_robustness
```

## 4. ผลการศึกษาและข้อมูลดิบ

| Metric | ค่า |
|---|---:|
| Daily rows | `463` |
| วันที่วัด 5-minute proxy ได้ | `444` |
| วันที่วัด 15-minute proxy ได้ | `444` |
| Trade days เดิม | `90` |
| In-sample / OOS split | `211 / 252` |
| Trial count | `4` |
| Evidence tier | `E1` |

ผลที่อ่านได้คือ H-A2 ยังไม่ควรถูกทิ้งทันที เพราะสัญญาณจากหลายมุมยังไปในทิศทางเดียวกัน: วันที่ถูกจัดว่าเสี่ยงดูแย่กว่าวันที่สะอาดกว่า ทั้งใน `proxy` และใน trade outcome เดิม อย่างไรก็ตาม ข้อมูลนี้ยังเป็นแค่การดูเงาของกลไก ไม่ใช่การ replay option entry/exit จริง จึงยังไม่รู้ว่าถ้าเทรดจริงตาม bid/ask แล้วผลจะรอดหรือไม่

## 5. ปัญหา อุปสรรค และการแก้ไข

ข้อจำกัดหลักคือ `proxy` ไม่ใช่ deployable return และจำนวน trade จริงยังน้อยเกินสำหรับ `MinTRL` / `PSR` ระดับ acceptance ผลนี้จึงเหมาะกับการจัดลำดับงาน ไม่เหมาะกับการตัดสินว่ากลยุทธ์ผ่านแล้ว

สิ่งที่ห้ามสรุปจากรอบนี้:

- ห้ามบอกว่า H-A2 ผ่านหรือพร้อม `paper trading`
- ห้ามบอกว่า exact 2022-10 ORB entry/exit ถูกทดสอบแล้ว
- ห้ามยกระดับผลนี้เป็น `E2`

## 6. ข้อสรุปและก้าวต่อไป

ข้อสรุป: `ยังสรุปไม่ได้` แต่ H-A2 ยังมีเหตุผลพอให้ศึกษาต่อในฐานะ `E1 prioritization evidence`

หลักฐานรอบนี้บอกว่า “ควรตรวจต่ออย่างมีวินัย” ไม่ใช่ “ควรเทรด” ก้าวต่อไปควรเน้น exact replay หรือ sample expansion ที่ลงทะเบียนล่วงหน้า ไม่ใช่เพิ่ม filter ไปเรื่อย ๆ เพราะเห็นตัวเลขบางตัวดูดี

ก้าวต่อไป:

1. ใช้ผลนี้ช่วยจัดลำดับงาน exact replay เมื่อข้อมูลพร้อม
2. ห้ามใช้ผลนี้เปิด `paper trading` หรืออ้าง edge
