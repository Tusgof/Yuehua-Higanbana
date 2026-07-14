# บันทึกการวิจัย 023: H-B2 Falsification Review

## 1. ข้อมูลพื้นฐาน

- Timestamp UTC: `2026-07-05T09:47:07Z`
- โครงการ: SPY 0DTE - Higanbana
- หัวข้อ: H-B2 falsification review
- ผู้บันทึก: Codex
- สถานะ: เสร็จสิ้น
- Artifact หลัก:
  - `reports/experiments/h_b2_subsystem_b_scale_summary.json`
  - `reports/experiments/h_b2_falsification_review.json`
  - `reports/experiments/h_b2_falsification_review.md`
  - `scripts/run_h_b2_falsification_review.py`
  - `scripts/validate_h_b2_falsification_review.py`

## 2. วัตถุประสงค์

### อ่านแบบเร็ว

บันทึกนี้ตัดสินว่า H-B2 put-ratio-with-wing ควรถูกนำกลับมา active หรือควรถูก park ต่อ หลังทดสอบพอร์ตจำลอง `$10k` และ `$25k`
ผลสำคัญคือ grid ปัจจุบันยังไม่ผ่านเงื่อนไขให้ resurrect เป็น active edge แต่ไม่ใช่การลบ Sub-System B ออกจากโครงการทั้งหมด
ข้อห้ามสรุป: ห้ามใช้ผลนี้อนุมัติ paper trading และห้ามสรุปว่า idea ตระกูลนี้หมดทางอย่างถาวร


รอบนี้ต้องการตอบคำถามว่า H-B2 หรือ Sub-System B แบบ put-ratio-with-wing ที่ทดสอบด้วยพอร์ตจำลอง `$10k` และ `$25k` ควรถูกนำกลับมาเป็น active research track หรือควรถูก park ต่อ หลังจากผล diagnostic เดิมไม่พบ scenario ที่มีทั้ง total implementable PnL และ OOS implementable PnL เป็นบวกพร้อมกัน

ความสำเร็จของรอบนี้ไม่ใช่การหา edge ใหม่ แต่คือการตัดสินใจอย่างมีวินัยว่า grid ปัจจุบันผ่านเงื่อนไขให้ทำต่อหรือไม่ โดยต้องไม่สรุปเกินหลักฐาน ไม่ใช้ผลนี้อนุมัติ paper trading และไม่ลบ Sub-System B ทั้งหมดออกจากขอบเขตโครงการเพียงเพราะ mechanism ชุดนี้ไม่ผ่าน

## 3. วิธีการและขั้นตอน

1. ใช้ผลเดิมจาก `reports/experiments/h_b2_subsystem_b_scale_summary.json`
2. อ่านหลักคิดจาก local LLM Wiki เรื่อง `minimum-track-record-length.md` และ `probabilistic-sharpe-ratio.md`
3. สร้าง `scripts/run_h_b2_falsification_review.py` เพื่อสรุปผลทั้ง 8 scenarios ของ H-B2
4. คำนวณ PSR แบบ conservative สำหรับ null Sharpe `0` จาก return series ที่มีอยู่ในแต่ละ scenario
5. ตรวจว่าแต่ละ scenario ผ่าน pre-registered keep-active rule หรือไม่
6. สร้าง validator เพื่อป้องกันการอ้างเกินหลักฐาน เช่น paper trading allowed หรือ acceptance-grade falsification
7. รัน focused tests และ validator

คำสั่งที่ใช้:

```powershell
python scripts\run_h_b2_falsification_review.py
python scripts\validate_h_b2_falsification_review.py
python -m unittest tests.test_h_b2_falsification_review
```

## 4. ผลการศึกษาและข้อมูลดิบ

### สถานะรวม

- `status`: `review_complete`
- `hypothesis_id`: `H-B2`
- `evidence_tier`: `E1`
- `conclusion`: ไม่ผ่าน
- `decision`: `keep_h_b2_parked_current_grid_not_resurrected`
- `current_grid_failed_preregistered_keep_active_rule`: `true`
- `acceptance_grade_falsified`: `false`
- `paper_trading_allowed`: `false`
- `paid_data_used`: `false`
- `network_used`: `false`
- `llm_called`: `false`

### Scenario review

| Scenario | Trades | Total implementable PnL | OOS implementable PnL | Sharpe proxy | PSR(SR>0) | สถานะตัวอย่าง |
|---|---:|---:|---:|---:|---:|---|
| `account_10000_wing_5` | 413 | -5604.56 | -3332.88 | -0.082674 | 0.057628 | under-sampled, underpowered |
| `account_25000_wing_5` | 413 | -5604.56 | -3332.88 | -0.102007 | 0.026729 | under-sampled, underpowered |
| `account_10000_wing_10` | 90 | -784.80 | -686.68 | -0.058111 | 0.296930 | under-sampled, underpowered |
| `account_25000_wing_10` | 412 | -5973.44 | -3866.76 | -0.108110 | 0.019990 | under-sampled, underpowered |
| `account_10000_wing_15` | 0 | 0.00 | 0.00 | ไม่ได้วัด | ไม่ได้วัด | under-sampled, underpowered |
| `account_25000_wing_15` | 406 | -5729.72 | -3641.04 | -0.103341 | 0.024275 | under-sampled, underpowered |
| `account_10000_wing_20` | 0 | 0.00 | 0.00 | ไม่ได้วัด | ไม่ได้วัด | under-sampled, underpowered |
| `account_25000_wing_20` | 0 | 0.00 | 0.00 | ไม่ได้วัด | ไม่ได้วัด | under-sampled, underpowered |

### การตีความหลัก

ไม่มี scenario ใดผ่านเงื่อนไข keep-active ที่ pre-register ไว้ เพราะไม่มีกรณีที่ทั้ง total implementable PnL และ OOS implementable PnL เป็นบวกพร้อมกัน

อย่างไรก็ตาม ผลนี้ยังไม่ใช่ acceptance-grade falsification ของ Sub-System B ทั้งหมด เพราะทุก scenario ยังมี label `under-sampled` หรือ `underpowered` และบาง scenario ไม่มี eligible trade เลย การตัดสินใจที่เหมาะสมจึงเป็นการ park H-B2 grid ปัจจุบัน ไม่ใช่การลบทิ้งทั้งกลุ่มกลยุทธ์ Sub-System B

## 5. ปัญหา อุปสรรค และการแก้ไข

พบปัญหาเล็กน้อยด้าน environment: PowerShell รุ่นนี้ไม่มี `Get-Date -AsUTC` จึงใช้ `[DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ')` เพื่อสร้าง timestamp UTC แทน

ข้อจำกัดสำคัญ:

- ผลนี้เป็น E1 review ไม่ใช่ E2 validation
- PSR ที่คำนวณเป็น conservative diagnostic จาก return series ที่มีอยู่ ไม่ใช่ใบอนุมัติ deploy
- current grid failure ไม่ได้แปลว่า Sub-System B ทุกแบบเป็นไปไม่ได้
- ห้ามใช้ผลนี้อนุมัติ paper trading, operational validation หรือ real-money trading
- ห้ามซื้อข้อมูลเพิ่มเพื่อ H-B2 จากผลนี้เพียงอย่างเดียว

## 6. ข้อสรุปและก้าวต่อไป

ข้อสรุป: H-B2 current grid ไม่ผ่านเงื่อนไขให้ resurrect และควรถูก park ต่อ แต่ยังไม่ควรสรุปว่า Sub-System B ทุก mechanism ตายถาวร

เหตุผล:

- ทุก scenario ที่มี trade มี total implementable PnL ติดลบ
- ทุก scenario ที่มี OOS trade มี OOS implementable PnL ติดลบ
- ไม่มี scenario ใดผ่าน pre-registered keep-active rule
- บาง scenario มี PSR(SR>0) ต่ำมาก เช่น `account_25000_wing_10` = 0.019990 และ `account_25000_wing_15` = 0.024275
- แต่ sample adequacy ยังติด `under-sampled` / `underpowered` จึงไม่ควรอ้างว่าเป็น acceptance-grade falsification

ก้าวต่อไป:

1. คงสถานะ H-B2 เป็น parked และไม่ใช้ current grid สำหรับ paper trading
2. กลับไปให้น้ำหนักกับ H-A2 และ News-Unblock เมื่อ external blockers คลี่คลาย
3. ถ้าจะกลับมาทำ Sub-System B ต้องเริ่มจาก revised hypothesis ที่ระบุ mechanism ใหม่ ไม่ใช่ซื้อข้อมูลเพิ่มให้ grid เดิม
