# บันทึกการวิจัย 021: H-A2 2022-10 Coarse Stress Review

## 1. ข้อมูลพื้นฐาน
- **วันที่สร้างรายงาน**: 2026-07-05
- **สมมติฐาน**: H-A2 Macro-Conditioned ORB Edge
- **หลักฐานระดับ**: E1 diagnostic เท่านั้น
- **รายงานหลัก**: `reports/diagnostics/h_a2_2022_10_coarse_stress_review.json`
- **รายงานอ่านง่าย**: `reports/diagnostics/h_a2_2022_10_coarse_stress_review.md`
- **pre-registration**: `experiments/h_a2_2022_10_coarse_stress_review_preregistration.json`

## 2. วัตถุประสงค์

### อ่านแบบเร็ว

บันทึกนี้ตรวจ October 2022 แบบ coarse stress ว่า option quote, VIX และ macro context ที่มีอยู่พอคุ้มต่อการทำ H-A2 exact rerun ต่อหรือไม่
ผลสำคัญคือ SPY 1-minute bars ไม่ใช่สมมติฐาน แต่เป็นข้อมูลสำหรับ exact ORB replay รอบนี้ยังไม่มี underlying bar สำหรับ exact entry/exit
ข้อห้ามสรุป: ห้ามเรียกผลนี้ว่า ORB exact test หรือ edge validation

การทดลองนี้เกิดจากการแก้กรอบคิดสำคัญ: `SPY 1-minute bars` ไม่ใช่สมมติฐาน แต่เป็นเพียงข้อมูลละเอียดระดับหนึ่งที่ใช้ทดสอบสมมติฐานได้

คำถามรอบนี้จึงไม่ใช่ "หา 1-minute bars ให้ได้ก่อน" แต่เป็น:

> เดือน October 2022 ที่เราซื้อ option quote มาแล้ว มีบริบทความผันผวน ข่าวมหภาค และ 0DTE quote เพียงพอไหมที่จะยังคุ้มต่อการทำ H-A2 exact rerun ต่อ

ผลลัพธ์จากงานนี้ห้ามใช้ยืนยัน edge, ห้ามอนุมัติ paper trading, และห้ามเรียกว่าเป็นการทดสอบ ORB จริง เพราะยังไม่มีข้อมูล underlying bar สำหรับคำนวณจุดเข้าออกแบบ exact

## 3. วิธีการและขั้นตอน
ใช้ข้อมูลที่มีอยู่แล้วเท่านั้น ไม่มีการซื้อข้อมูลเพิ่ม ไม่มี network call ไม่มี IBKR request และไม่มี LLM call

ข้อมูลที่ใช้:
- `reports/data_cost/databento_normalization_summary_h_a2_2022_10_stress.json`
- `data/normalized/spy_0dte/vix_vxv/vix_vxv.jsonl`
- `data/normalized/spy_0dte/macro_calendar/macro_event.jsonl`

วิธีตรวจ:
- นับ trading day ในช่วง `2022-10-03` ถึง `2022-10-31`
- ตรวจว่าวันไหนมี 0DTE option quote ใช้ได้
- ตรวจ VIX แบบ same-day close เพื่อ diagnostic เท่านั้น
- ตรวจ VIX prior close เพื่อใช้เป็น proxy ที่ไม่มองอนาคต
- ตรวจ high-importance macro event ในวันเดียวกัน
- ดู overlap ระหว่าง quote availability, VIX regime, และ macro event

## 4. ผลการศึกษาและข้อมูลดิบ
ผลรวม:
- trading days ทั้งหมด: 21 วัน
- วันที่มี 0DTE quote ใช้ได้: 13 วัน
- วันที่ไม่มี 0DTE quote: 8 วัน
- วันที่ same-day VIX สูงกว่า 25: 21 วัน
- วันที่ same-day VIX สูงกว่า 30: 11 วัน
- วันที่ prior-close VIX สูงกว่า 25: 21 วัน
- วันที่ prior-close VIX สูงกว่า 30: 12 วัน
- วันที่มี high-importance macro event: 5 วัน
- วันที่มี 0DTE quote และทับกับ high/stress VIX: 13 วัน
- วันที่มี 0DTE quote และทับกับ high-importance macro event: 3 วัน
- วันที่มี 0DTE quote และเป็น non-macro high-VIX day: 10 วัน

วันที่มี 0DTE quote ใช้ได้:
`2022-10-03`, `2022-10-05`, `2022-10-07`, `2022-10-10`, `2022-10-12`, `2022-10-14`, `2022-10-17`, `2022-10-19`, `2022-10-21`, `2022-10-24`, `2022-10-26`, `2022-10-28`, `2022-10-31`

วันที่มี 0DTE quote และ high-importance macro event:
`2022-10-07`, `2022-10-12`, `2022-10-28`

สถานะผลลัพธ์:
- `status`: `continue_exact_rerun_research`
- `conclusion`: ยังสรุปไม่ได้

ความหมายคือ October 2022 มีบริบท stress/regime เพียงพอให้ H-A2 ยังไม่ควรถูกตัดทิ้งจากการขาด 1-minute bars เพียงอย่างเดียว แต่ผลนี้ยังเป็นแค่ตัวช่วยจัดลำดับงาน ไม่ใช่หลักฐานว่า strategy ทำกำไรได้

## 5. ปัญหา อุปสรรค และการแก้ไข
ข้อจำกัดหลัก:
- ยังไม่มี `SPY 1-minute bars` สำหรับ October 2022 จึงยังทดสอบ ORB entry/exit แบบ exact ไม่ได้
- ไม่มี strategy PnL, Sharpe, PSR, DSR, MinTRL หรือ big-day dependency จากงานนี้
- same-day VIX close ใช้ได้แค่ diagnostic เพราะเป็นข้อมูลหลังตลาดปิด ไม่ใช่ข้อมูลที่รู้ก่อนเข้าเทรด
- macro calendar เป็น event-risk proxy ไม่ใช่ข่าวจริงแบบ timestamp-clean และไม่ใช่หลักฐาน LLM/news

การแก้ไขกรอบคิด:
- แยกสมมติฐานออกจาก resolution ของข้อมูล
- ยืนยันว่า missing 1-minute bars บล็อกเฉพาะ exact ORB backtest ไม่ได้บล็อกการประเมินกลไกในระดับหยาบ
- บังคับให้รายงานระบุ evidence tier และ guardrails ชัดเจน

## 6. ข้อสรุปและก้าวต่อไป
ข้อสรุปคือ H-A2 ยังควรอยู่ในสถานะ active สำหรับการวิจัยต่อ แต่ยังไม่มีสิทธิ์ขยับไป paper trading หรือ operational validation

ก้าวต่อไปที่ปลอดภัย:
- ห้ามขอ IBKR bars จากรายงานนี้เพียงอย่างเดียว
- ใช้ผล E1 นี้เพื่อตัดสินใจว่าจะทำ pre-registration รอบถัดไปแบบใด:
  - lower-resolution proxy ที่ยอมลดระดับ claim อย่างชัดเจน หรือ
  - exact SPY bar source plan ถ้ายังเห็นว่าจำเป็นต่อคำถาม H-A2
- ทุกทางเลือกต้องยึดสมมติฐานก่อน แล้วค่อยเลือก data resolution ที่จำเป็น ไม่ใช่ไล่ซื้อข้อมูลละเอียดโดยยังไม่ชัดว่าตอบคำถามอะไร
