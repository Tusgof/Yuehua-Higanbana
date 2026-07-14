# บันทึกการวิจัย: H-B2 Sub-System B Simulated-Scale Diagnostic

## 1. ข้อมูลพื้นฐาน

- Timestamp UTC: `2026-07-03T04:35:29Z`
- โครงการ: SPY 0DTE - Higanbana
- หัวข้อ: ทดสอบ Sub-System B ที่บัญชีจำลอง $10k และ $25k
- ผู้บันทึก: Codex
- สถานะ: เสร็จสิ้น
- Evidence tier: `E1`
- Hypothesis ID: `H-B2`
- เครื่องมือ:
  - Python local scripts
  - H-B2 pre-registration manifest
  - Hypothesis registry
- Artifact หลัก:
  - `experiments/h_b2_subsystem_b_scale_preregistration.json`
  - `scripts/validate_h_b2_preregistration.py`
  - `scripts/run_h_b2_subsystem_b_scale.py`
  - `reports/experiments/h_b2_subsystem_b_scale_summary.json`
  - `reports/experiments/h_b2_subsystem_b_scale_report.md`
  - `reports/experiments/h_b2_subsystem_b_scale_search_log.json`

## 2. วัตถุประสงค์

### อ่านแบบเร็ว

บันทึกนี้ตรวจ Sub-System B ที่พอร์ตจำลองใหญ่ขึ้น เช่น `$10k` และ `$25k` เพื่อดูว่าปัญหาเดิมเป็นเพราะพอร์ตเล็กเกินไปหรือกลไกไม่ดีพอ
ผลสำคัญคือการเพิ่มขนาดพอร์ตช่วยให้เห็น feasibility ชัดขึ้น แต่ยังไม่ได้ทำให้ H-B2 กลับมาเป็น edge ที่ผ่าน
ข้อห้ามสรุป: ห้ามใช้ simulated scale เป็นข้ออ้างว่า Sub-System B พร้อมใช้งานจริง


รอบนี้ต้องตอบคำถามว่า Sub-System B แบบ put-ratio-with-wing ยังควรอยู่ในแผนวิจัยหรือไม่ ถ้าแยกออกจากข้อจำกัดบัญชีเล็ก $1,000 เดิม ซึ่ง H-B1 ถูก falsified ไปแล้วเพราะไม่มี trade ใด fit `allocation_300` หรือ `risk_budget_20`

H-B2 ไม่ได้พยายามพิสูจน์ว่าสามารถเทรดจริงด้วยบัญชีปัจจุบันได้ แต่ทดสอบว่าโครงสร้าง `long 1 near-ATM put / short 2 downside puts / long 1 protective wing` มีสัญญาณเชิงโครงสร้างหรือไม่เมื่อใช้บัญชีจำลอง $10k และ $25k พร้อม wing grid ที่ pre-register ก่อนรัน

ความสำเร็จของรอบนี้คือมี manifest ที่ lock ตัวแปรก่อนรัน มี search log ครบทุก trial แยก `mid_pnl` และ `implementable_pnl` ชัดเจน และไม่อ้างว่าเป็น evidence ระดับพร้อม paper trading หรือ deployment

## 3. วิธีการและขั้นตอน

1. อ่านสถานะโครงการจาก `PROJECT_BRAIN.md`, `IMPLEMENT_PLAN.md`, และ `AGENTS.md`
2. อ่านผล H-B1 เดิมจาก `reports/baselines/subsystem_b_put_ratio_feasibility_summary.json`
3. สร้าง pre-registration manifest สำหรับ H-B2:
   - account sizes: `$10,000` และ `$25,000`
   - wing grid: `$5`, `$10`, `$15`, `$20`
   - sizing rule: `1` spread ต่อวันเท่านั้น ไม่มี fractional contracts
   - eligibility rule: `max_defined_loss <= 5%` ของบัญชีจำลอง
   - data policy: ใช้ cached data เท่านั้น ไม่ซื้อข้อมูลใหม่
4. ตรวจ manifest:

```powershell
python scripts\validate_h_b2_preregistration.py
```

5. รัน H-B2 diagnostic:

```powershell
python scripts\run_h_b2_subsystem_b_scale.py
```

6. ตรวจ unit tests เฉพาะส่วน:

```powershell
python -m unittest tests.test_validate_h_b2_preregistration
python -m unittest tests.test_run_h_b2_subsystem_b_scale
```

## 4. ผลการศึกษาและข้อมูลดิบ

### ผลสรุปหลัก

| รายการ | ค่า |
|---|---:|
| Hypothesis | `H-B2` |
| Evidence tier | `E1` |
| Trial count | 8 |
| New paid data | 0 |
| Positive total + positive OOS scenarios | 0 |
| Recommendation | `consider_falsification_after_mintrl_falsify_review` |
| Summary | `reports/experiments/h_b2_subsystem_b_scale_summary.json` |
| Report | `reports/experiments/h_b2_subsystem_b_scale_report.md` |
| Search log | `reports/experiments/h_b2_subsystem_b_scale_search_log.json` |

### ผลราย scenario

| Scenario | Account | Wing | Eligible trades | Total implementable PnL | OOS implementable PnL | Mid PnL | Cost drag | Drag ratio | ES95 | Max drawdown |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `account_10000_wing_5` | 10000 | 5 | 413 | -5604.56 | -3332.88 | -441.0 | 5163.56 | 11.708753 | -141.6914 | -0.588764 |
| `account_25000_wing_5` | 25000 | 5 | 413 | -5604.56 | -3332.88 | -441.0 | 5163.56 | 11.708753 | -141.6914 | -0.235506 |
| `account_10000_wing_10` | 10000 | 10 | 90 | -784.8 | -686.68 | 354.5 | 1139.3 | 3.213822 | -196.12 | -0.151096 |
| `account_25000_wing_10` | 25000 | 10 | 412 | -5973.44 | -3866.76 | -857.5 | 5115.94 | 5.966111 | -161.4533 | -0.25023 |
| `account_10000_wing_15` | 10000 | 15 | 0 | 0 | 0 | 0 | 0 | ไม่ได้วัด | ไม่ได้วัด | 0.0 |
| `account_25000_wing_15` | 25000 | 15 | 406 | -5729.72 | -3641.04 | -702.0 | 5027.72 | 7.161994 | -168.739 | -0.240695 |
| `account_10000_wing_20` | 10000 | 20 | 0 | 0 | 0 | 0 | 0 | ไม่ได้วัด | ไม่ได้วัด | 0.0 |
| `account_25000_wing_20` | 25000 | 20 | 0 | 0 | 0 | 0 | 0 | ไม่ได้วัด | ไม่ได้วัด | 0.0 |

### สิ่งที่ผลรอบนี้บอก

- ไม่มี scenario ใดที่ได้ทั้ง total implementable PnL เป็นบวกและ OOS implementable PnL เป็นบวกพร้อมกัน
- `account_10000_wing_10` เป็นกรณีเดียวที่ mid PnL เป็นบวก (`354.5`) แต่หลังหัก implementable cost แล้วกลายเป็น `-784.8`
- Cost drag สูงมาก โดยกรณีที่ mid PnL เป็นบวกมี drag ratio `3.213822` ซึ่งสูงกว่าเกณฑ์ warning `0.60` หลายเท่า
- บัญชี $25k ช่วยให้ trade จำนวนมาก fit risk budget ใน wing `$10` และ `$15` แต่ไม่ได้เปลี่ยนสัญญาณ PnL ให้ดีขึ้น
- Wing `$20` ไม่ fit เลยภายใต้กฎ 5% ทั้ง $10k และ $25k

### สิ่งที่ยังไม่ผ่าน

- ทุก scenario ยังติด `under-sampled` และ `underpowered`
- DSR ยัง blocked เพราะเป็น 8-trial grid search
- ผลนี้ยังเป็น `E1` diagnostic เท่านั้น
- ห้ามใช้เป็นสัญญาณสำหรับ paper trading หรือ real-money execution

## 5. ปัญหา อุปสรรค และการแก้ไข

### ปัญหาที่พบ

1. Runner รอบแรกอ่าน cached data ซ้ำตามจำนวน wing gap ทำให้ timeout
   - สิ่งที่เกิดขึ้น: `python scripts\run_h_b2_subsystem_b_scale.py` timeout ที่ 120 วินาที และอีกครั้งที่ 420 วินาที
   - การแก้ไข: ปรับ runner ให้โหลด dataset ครั้งเดียว แล้วประเมินทุก wing gap จากข้อมูลใน memory
   - ผลลัพธ์: รันสำเร็จในรอบถัดมาและสร้าง summary/report/search log ได้ครบ

2. PowerShell รุ่นนี้ไม่มี `Get-Date -AsUTC`
   - สิ่งที่เกิดขึ้น: คำสั่ง timestamp ด้วย `Get-Date -AsUTC` failed
   - การแก้ไข: ใช้ `[DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ')`
   - ผลลัพธ์: ได้ timestamp UTC สำหรับ log สำเร็จ

### ข้อจำกัดสำคัญ

- Sizing rule รอบนี้ตั้งไว้ที่ `1` spread ต่อวันเท่านั้น จึงยังไม่ได้ทดสอบ position sizing แบบหลายสัญญา
- ผลนี้ใช้ cached data เดิม ไม่ได้เพิ่ม regime ใหม่
- การสรุปว่า H-B2 falsified อย่างเป็นทางการยังควรอิง MinTRL_falsify review และ registry decision log ไม่ใช่ดูตัวเลข PnL อย่างเดียว
- ต่อให้ H-B2 เคยผ่านในอนาคต ก็ไม่ได้แปลว่า tradable บัญชี $1k ปัจจุบันทันที

## 6. ข้อสรุปและก้าวต่อไป

ข้อสรุป: ยังสรุปไม่ได้ในเชิง acceptance-grade แต่ H-B2 ได้หลักฐานเชิงลบที่แรงมากต่อโครงสร้าง put-ratio-with-wing ภายใต้กฎที่ pre-register แล้ว เพราะทุก scenario ที่มี trade จริงให้ implementable PnL และ OOS PnL ติดลบ หรือไม่ fit sizing เลย

- H-B2 ไม่ได้แสดงสัญญาณว่าการเพิ่มพอร์ตเป็น $10k/$25k เพียงอย่างเดียวจะแก้ปัญหา Sub-System B
- ปัญหาหลักไม่ใช่แค่บัญชีเล็ก แต่รวมถึง cost drag และโครงสร้าง PnL หลัง bid/ask กับ fee
- กรณี wing `$10` ที่บัญชี `$10k` มี mid PnL บวก แต่ implementable PnL ติดลบ แปลว่า friction อาจกิน edge เชิงทฤษฎีจนหมด
- ผลนี้ควรถูกใช้เพื่อพิจารณา park หรือ falsify H-B2 หลังตรวจ MinTRL_falsify และ decision criteria ใน registry

ก้าวต่อไป:

1. อัพเดท `experiments/hypothesis_registry.json` ให้ H-B2 ชี้ไปยัง H-B2 diagnostic artifact และบันทึก decision ว่า `scale_diagnostic_completed`
2. อัพเดท `IMPLEMENT_PLAN.md` ให้ H-B2.1-H-B2.3 เป็น complete และ H-B2.4 เป็นขั้นตัดสินหลัง review
3. อัพเดท `PROJECT_BRAIN.md` ให้ Current Verified State ระบุผล H-B2 และ next safe action
4. รัน verification เต็ม: registry validator, evidence-tier validator, research-log audit, unit tests และ fixture pipeline
