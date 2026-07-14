# บันทึกการวิจัย: H-A2 Macro-Conditioned ORB Re-Analysis

## 1. ข้อมูลพื้นฐาน

- Timestamp UTC: `2026-07-03T03:23:17Z`
- โครงการ: SPY 0DTE - Higanbana
- หัวข้อ: วิเคราะห์ผล M5.5 ใหม่ภายใต้สมมติฐาน H-A2
- ผู้บันทึก: Codex
- สถานะ: เสร็จสิ้น
- เครื่องมือ:
  - Python local scripts
  - Hypothesis registry
  - Evidence-tier validator
- Artifact หลัก:
  - `scripts/run_h_a2_macro_conditioned_reanalysis.py`
  - `tests/test_h_a2_macro_conditioned_reanalysis.py`
  - `reports/experiments/h_a2_macro_conditioned_reanalysis_summary.json`
  - `reports/experiments/h_a2_macro_conditioned_reanalysis_report.md`
  - `reports/experiments/m5_regime_filter_sensitivity_summary.json`
  - `reports/experiments/search_logs/m5_regime_filter_sensitivity_search_log.jsonl`

## 2. วัตถุประสงค์

### อ่านแบบเร็ว

บันทึกนี้เริ่มเปลี่ยนกรอบจาก experiment-number มาเป็น hypothesis-led โดยกลับมาดู H-A2 ว่า macro/VIX condition อาจเกี่ยวกับ ORB edge หรือไม่
ผลสำคัญคือเป็น re-analysis ระดับ E1 เท่านั้น ใช้เพื่อจัดลำดับคำถามต่อ ไม่ใช่ validation ของ edge
ข้อห้ามสรุป: ห้ามข้ามไป exact replay, paid data หรือ paper trading จากผล re-analysis นี้เพียงอย่างเดียว


รอบนี้ต้องตอบคำถามว่า ผลทดลอง M5.5 เดิมซึ่งพบว่า `exclude_high_importance_macro_same_day` ดูดีกว่า baseline สามารถนับเป็นหลักฐานของสมมติฐาน H-A2 ได้แค่ระดับไหน

H-A2 คือสมมติฐานว่า edge ของ ORB อาจไม่ได้อยู่ในทุกวันแบบไม่เลือกเงื่อนไข แต่เกิดในวันที่ไม่มี scheduled macro event สำคัญ เพราะวัน macro อาจทำให้ opening range ถูกครอบงำด้วยการ reposition ก่อนข่าวและการ reprice หลังข่าว มากกว่าความไม่สมดุลของ order flow ที่วิ่งต่อทั้งวัน

ความสำเร็จของรอบนี้ไม่ใช่การพิสูจน์ว่า H-A2 ผ่าน แต่คือการตีความหลักฐานเดิมอย่างตรงไปตรงมา: ผูกผล M5.5 เข้ากับ `hypothesis_id=H-A2`, ระบุ `evidence_tier=E1`, บันทึก 9-trial search contamination, และระบุชัดว่าทำไมยังห้ามใช้เป็นหลักฐานระดับ E2 หรือ operational validation

## 3. วิธีการและขั้นตอน

1. อ่านสถานะโครงการจาก `PROJECT_BRAIN.md`, `IMPLEMENT_PLAN.md`, และ `AGENTS.md`
2. อ่าน hypothesis registry เพื่อยืนยันว่า `H-A2` เป็น active hypothesis หลัง `H-A1` ถูก kill แบบ `falsified-as-stated`
3. อ่านผลเดิมจาก M5.5:
   - `reports/experiments/m5_regime_filter_sensitivity_summary.json`
   - `reports/experiments/search_logs/m5_regime_filter_sensitivity_search_log.jsonl`
4. สร้าง script re-analysis ที่ไม่ซื้อข้อมูลใหม่และไม่ rerun grid เพิ่ม:

```powershell
python scripts\run_h_a2_macro_conditioned_reanalysis.py
```

5. รัน test เฉพาะเพื่อยืนยันว่า output เป็น `E1`, ไม่ใช่ acceptance:

```powershell
python -m unittest tests.test_h_a2_macro_conditioned_reanalysis
```

6. อัปเดต `experiments/hypothesis_registry.json` ให้ H-A2 ชี้ไปยัง artifact ใหม่

## 4. ผลการศึกษาและข้อมูลดิบ

### ผลสรุปหลัก

| รายการ | ค่า |
|---|---:|
| Source trials จาก M5.5 | 9 |
| Evidence tier | E1 |
| Conclusion | ยังสรุปไม่ได้ |
| New paid data | 0 |
| H-A2 summary | `reports/experiments/h_a2_macro_conditioned_reanalysis_summary.json` |
| H-A2 report | `reports/experiments/h_a2_macro_conditioned_reanalysis_report.md` |

### เปรียบเทียบ scenario สำคัญ

| Scenario | Closed trades | Total implementable PnL | OOS implementable PnL | Sharpe proxy | OOS Sharpe proxy | Cost drag | ES95 | Max drawdown |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `unfiltered_control` | 90 | 545.6 | -78.44 | 0.118064 | 0.01581 | 543.9 | -59.56 | -0.370769 |
| `exclude_high_importance_macro_same_day` | 64 | 820.16 | 240.96 | 0.199493 | 0.133578 | 368.84 | -53.81 | -0.221838 |
| `exclude_major_macro_same_day` | 70 | 601.8 | 95.72 | 0.147296 | 0.0647 | 396.2 | -57.06 | -0.277636 |

### Delta เทียบ baseline

| Scenario | Closed-trade delta | Total PnL delta | OOS PnL delta | Sharpe delta | OOS Sharpe delta |
|---|---:|---:|---:|---:|---:|
| `exclude_high_importance_macro_same_day` | -26 | 274.56 | 319.4 | 0.081429 | 0.117768 |
| `exclude_major_macro_same_day` | -20 | 56.2 | 174.16 | 0.029232 | 0.04889 |

### สิ่งที่ผลรอบนี้สนับสนุน

- `exclude_high_importance_macro_same_day` ทำให้ total implementable PnL เพิ่มจาก `545.6` เป็น `820.16`
- OOS implementable PnL เปลี่ยนจาก `-78.44` เป็น `240.96`
- กฎ macro ใช้ scheduled event ที่รู้ได้ก่อนตัดสินใจเข้า position จึงไม่ใช่ post-event lookahead ในตัวมันเอง

### สิ่งที่ยังไม่ผ่าน

- ผลนี้มาจาก grid เดิม 9 trials จึงมี selection bias
- กลุ่ม retained trades เหลือ 64 trades รวม และ OOS เหลือ 34 trades จึงยัง under-sampled และ underpowered
- DSR ยัง blocked เพราะยังไม่มี acceptance-grade return distribution, effective independent trial count, null Sharpe threshold, skew/kurtosis, และ autocorrelation diagnostics
- ยังไม่มี reference/pre-break coverage และ high-VIX coverage ที่ดีพอ

## 5. ปัญหา อุปสรรค และการแก้ไข

### ปัญหาที่พบ

1. PowerShell ในเครื่องนี้ไม่มี parameter `Get-Date -AsUTC`
   - สิ่งที่เกิดขึ้น: คำสั่ง timestamp ด้วย `Get-Date -AsUTC` failed
   - การแก้ไข: ใช้ `[DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ')`
   - ผลลัพธ์: ได้ timestamp UTC สำหรับ log รอบนี้สำเร็จ

2. H-A2 re-analysis ต้องไม่ทำให้ M5.5 เดิมสับสน
   - สิ่งที่เกิดขึ้น: M5.5 เป็น experiment เดิม ส่วน H-A2.2 เป็นการตีความใหม่ภายใต้ hypothesis registry
   - การแก้ไข: สร้าง artifact ใหม่ชื่อ `h_a2_macro_conditioned_reanalysis_*` แยกจาก `m5_regime_filter_sensitivity_*`
   - ผลลัพธ์: หลักฐาน H-A2 มี path แยกและระบุ `hypothesis_id=H-A2`

### ข้อจำกัดสำคัญ

- รอบนี้ไม่ได้ซื้อข้อมูลใหม่และไม่ได้เพิ่ม sample
- ยังห้ามสรุปว่า macro filter ผ่าน
- ยังห้ามใช้ผลนี้สำหรับ paper trading หรือ real-money execution
- ผลยังเป็น E1 diagnostic evidence เท่านั้น

## 6. ข้อสรุปและก้าวต่อไป

ข้อสรุป: ยังสรุปไม่ได้ แต่ H-A2 มี diagnostic clue ที่ควรขุดต่อ เพราะ macro exclusion ทำให้ผลดีขึ้นในข้อมูลเดิม แม้ยังติด search contamination, sample adequacy, DSR, pre-break coverage, และ high-VIX coverage

- ผลนี้ช่วยจัด H-A2 ให้เป็น hypothesis ที่มีเหตุผลมากกว่า H-A1 แบบ unconditional
- การเพิ่ม PnL หลัง exclude macro days ยังเป็นเพียงสัญญาณตั้งต้น ไม่ใช่ edge ที่ validated
- จุดอ่อนหลักคือการเลือก filter หลังเห็นผลจาก 9 trials
- ถ้าจะยกระดับเป็น E2 ต้องใช้ข้อมูล fresh/pre-registered และต้องผ่าน MinTRL/PSR/DSR กับ big-day dependency และ regime coverage

ก้าวต่อไป:

1. ทำ H-A2.3 เพื่อตรวจว่า cached Aug 2024 high-VIX windows มี labeling gap หรือ ORB silence จริง
2. ถ้า H-A2.3 ยังสนับสนุนแนวทางนี้ ให้ estimate ค่าใช้จ่าย 2022 H2 top 2-3 VIX months ก่อนซื้อข้อมูล
3. ห้าม claim E2 หรือ operational validation จนกว่าจะมี fresh validation data และ DSR/MinTRL/PSR ครบ
