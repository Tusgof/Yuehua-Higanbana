# บันทึกการวิจัย 022: H-A2 Lower-Resolution Proxy

## 1. ข้อมูลพื้นฐาน

- Timestamp UTC: `2026-07-05T07:39:54Z`
- โครงการ: SPY 0DTE - Higanbana
- หัวข้อ: H-A2 lower-resolution proxy
- ผู้บันทึก: Codex
- สถานะ: เสร็จสิ้น
- Artifact หลัก:
  - `experiments/h_a2_lower_resolution_proxy_preregistration.json`
  - `reports/experiments/h_a2_lower_resolution_proxy_summary.json`
  - `reports/experiments/h_a2_lower_resolution_proxy_report.md`
  - `reports/experiments/search_logs/h_a2_lower_resolution_proxy_search_log.jsonl`

## 2. วัตถุประสงค์

### อ่านแบบเร็ว

บันทึกนี้ถามว่า H-A2 ยังควรอยู่ต่อหรือไม่ โดยใช้ lower-resolution proxy แทนการไล่หา SPY 1-minute bars ทันที
ผลสำคัญคือ 1-minute bars เป็นเครื่องมือ ไม่ใช่สมมติฐาน รอบนี้ใช้ 5-minute/15-minute proxy และผล trade เดิมเพื่อดูทิศทางของ macro/VIX relationship
ข้อห้ามสรุป: ห้ามถือว่า lower-resolution proxy เป็น exact 2022 ORB replay หรือ E2 evidence


รอบนี้ต้องการตอบคำถามว่า H-A2 ยังควรอยู่ต่อหรือไม่ โดยไม่รีบไล่หา `SPY 1-minute bars` ของปี 2022 ก่อนรู้ว่าข้อมูลระดับนั้นจำเป็นจริงต่อสมมติฐานหรือไม่

แนวคิดหลักคือ `1-minute bars` เป็นเครื่องมือสำหรับ exact ORB backtest ไม่ใช่ตัวสมมติฐาน ดังนั้นรอบนี้จึงใช้ proxy ที่หยาบกว่า ได้แก่ 5-minute opening range, 15-minute opening momentum และผลลัพธ์ trade ที่มีอยู่แล้ว เพื่อดูว่าความสัมพันธ์ระหว่าง macro/VIX risk regime กับผลลัพธ์ของระบบมีทิศทางสอดคล้องกันหรือไม่

ความสำเร็จของรอบนี้ไม่ใช่การยืนยัน edge แต่คือการตัดสินใจระดับ E1 ว่า H-A2 ควรถูกลดน้ำหนัก, ถูกทำให้แคบลง, หรือยังควรถูกจัดลำดับให้ทำ exact-data work ต่อ

## 3. วิธีการและขั้นตอน

1. ยึด pre-registration จาก `experiments/h_a2_lower_resolution_proxy_preregistration.json`
2. ใช้ข้อมูล local เท่านั้น ไม่มี network call, ไม่มี paid data, ไม่มี IBKR request และไม่มี LLM call
3. อ่านชุดข้อมูลจาก `DATASETS` เดิมของ Sub-System A เพื่อใช้ช่วง 2023-03 ถึง 2024-12
4. คำนวณ proxy 2 แบบ:
   - 5-minute opening range: ใช้ช่วง 09:30-09:34 ET และดู decision bar เวลา 09:35 ET
   - 15-minute opening proxy: ใช้ช่วง 09:30-09:44 ET และดู decision bar เวลา 09:45 ET
5. ติดป้าย regime ด้วยข้อมูลที่รู้ก่อนตัดสินใจ:
   - prior-close VIX/VXV
   - scheduled same-day high-importance macro events
6. reconcile กับ existing exact-quote trade outcomes จาก baseline artifacts
7. บันทึก trial ทั้งหมด 7 รายการใน search log
8. สร้าง summary/report และ validate ผลลัพธ์

คำสั่งที่ใช้:

```powershell
python scripts\run_h_a2_lower_resolution_proxy.py
python scripts\validate_h_a2_lower_resolution_proxy_summary.py
python -m unittest tests.test_h_a2_lower_resolution_proxy
```

## 4. ผลการศึกษาและข้อมูลดิบ

### สถานะรวม

- `status`: `complete`
- `hypothesis_id`: `H-A2`
- `evidence_tier`: `E1`
- `conclusion`: ยังสรุปไม่ได้
- daily rows ทั้งหมด: 463
- measured proxy days: 444
- trial count: 7
- paper trading allowed: `false`

### ผล proxy 5-minute และ 15-minute

| Proxy | Measured days | Signal count | Signal rate | Risk avg follow-through | Non-risk avg follow-through | Risk - Non-risk |
|---|---:|---:|---:|---:|---:|---:|
| 5-minute | 444 | 93 | 0.209459 | -0.000530 | 0.001116 | -0.001646 |
| 15-minute | 444 | 67 | 0.150901 | -0.000566 | 0.000103 | -0.000669 |

การอ่านผล: ทั้ง 5-minute และ 15-minute proxy ให้ภาพเดียวกัน คือวันกลุ่ม risk-labeled มีค่า directional follow-through แย่กว่า non-risk days

### Existing trade outcome reconciliation

| Group | Trade days | Total implementable PnL | Avg implementable PnL | Win rate | Cost drag |
|---|---:|---:|---:|---:|---:|
| All | 90 | 545.60 | 6.062222 | 0.322222 | 543.90 |
| Combined risk | 26 | -274.56 | -10.56 | 0.192308 | 175.06 |
| Non-risk | 64 | 820.16 | 12.815 | 0.375000 | 368.84 |

ผล trade ที่มีอยู่แล้วสอดคล้องกับ proxy: non-risk days ทำได้ดีกว่า risk-labeled days อย่างชัดเจนในชุดข้อมูลปัจจุบัน

### Coherence assessment

- `proxy_supports_non_risk`: `true`
- `existing_trades_support_non_risk`: `true`
- `directionally_coherent`: `true`
- `five_min_risk_minus_non_risk`: -0.001646
- `fifteen_min_risk_minus_non_risk`: -0.000669
- `trade_avg_pnl_risk_minus_non_risk`: -23.375

การตีความ: ผลลัพธ์ไม่ได้พิสูจน์ edge แต่บอกว่าแนวคิดของ H-A2 ยังไม่ควรถูกทิ้งทันที เพราะ proxy และผล trade เดิมชี้ไปทางเดียวกัน

## 5. ปัญหา อุปสรรค และการแก้ไข

ไม่พบปัญหาด้านการรัน script ในรอบนี้

ข้อจำกัดสำคัญ:

- ผลนี้เป็น E1 lower-resolution proxy เท่านั้น
- ยังไม่ได้ทดสอบ exact 2022-10 ORB entry/exit
- ไม่ได้ซื้อข้อมูลใหม่ และไม่ได้เพิ่ม independent sample ใหม่
- existing option outcomes ยัง under-sampled และ underpowered
- MinTRL/PSR/DSR ยังไม่ถูกใช้เป็นหลักฐาน acceptance-grade
- ห้ามใช้ผลนี้อนุมัติ paper trading, operational validation หรือ real-money trading

## 6. ข้อสรุปและก้าวต่อไป

ข้อสรุป: H-A2 ยังสรุปไม่ได้ แต่ควรอยู่ต่อในสถานะ active E1 เพราะ lower-resolution proxy และ existing trade outcomes มีทิศทางสอดคล้องกันว่า risk-labeled days แย่กว่า non-risk days

เหตุผล:

- 5-minute proxy และ 15-minute proxy ให้สัญญาณไปในทิศทางเดียวกัน
- existing trade outcomes สอดคล้องกับ proxy โดย non-risk days มี avg implementable PnL ดีกว่า combined-risk days
- ผลนี้ช่วยจัดลำดับงานได้ แต่ยังไม่ใช่ evidence tier E2
- ยังไม่มีสิทธิ์ขอ IBKR bars หรือซื้อข้อมูลใหม่จากผลนี้เพียงอย่างเดียว

ก้าวต่อไป:

1. สร้าง decision artifact แยกต่างหากเพื่อพิจารณาว่าผล proxy นี้เพียงพอให้ทำ exact-data prioritization สำหรับ 2022 underlying-bar source หรือไม่
2. ถ้ายังไม่พอ ให้ทำให้ H-A2 แคบลงก่อน เช่น ระบุเฉพาะ non-risk / macro-exclusion mechanism ที่จะถูกทดสอบใน exact data
3. ห้ามเริ่ม paper trading จนกว่า research acceptance จะผ่าน E2 gate
