# บันทึกการวิจัย: H-G1 Gamma Strategy Ablation Diagnostic

## 1. ข้อมูลพื้นฐาน

- Timestamp UTC: `2026-07-04T06:44:26Z`
- โครงการ: SPY 0DTE - Higanbana
- หัวข้อ: H-G1 gamma strategy ablation diagnostic
- ผู้บันทึก: Codex
- สถานะ: เสร็จสิ้น
- เครื่องมือ:
  - `scripts\run_h_g1_gamma_strategy_ablation.py`
  - `scripts\validate_h_g1_gamma_strategy_ablation_summary.py`
  - `tests\test_h_g1_gamma_strategy_ablation.py`
- Artifact หลัก:
  - `reports\experiments\h_g1_gamma_strategy_ablation_summary.json`
  - `reports\experiments\h_g1_gamma_strategy_ablation_summary.md`
  - `reports\experiments\search_logs\h_g1_gamma_strategy_ablation_search_log.jsonl`
  - `experiments\h_g1_gamma_strategy_ablation_preregistration.json`

## 2. วัตถุประสงค์

### อ่านแบบเร็ว

บันทึกนี้ทดสอบ gamma-filtered variants เทียบกับ baseline เพื่อดูว่า signed-OI gamma proxy ช่วยกรอง Sub-System A ได้หรือไม่
ผลสำคัญคือเป็น ablation diagnostic ต้องอ่านพร้อม sample size, MinTRL/PSR blocker, DSR policy และข้อห้ามเรื่อง true market-maker net gamma
ข้อห้ามสรุป: ห้ามใช้ผล ablation เป็น paper trading approval หรือ E2 claim


รอบนี้ทดสอบคำถามว่า `signed-OI gamma proxy` ที่ผ่าน data-validity diagnostic ใน H-G1.19 สามารถช่วยกรอง Sub-System A ORB baseline ได้หรือยัง โดยทำตาม preregistration H-G1.21 แบบไม่เพิ่ม paid data, ไม่เพิ่ม variant, ไม่ tune OOS และไม่ใช้ข้อมูลนอกเวลาที่กำหนด

ความสำเร็จของรอบนี้ไม่ใช่การหาเลขให้สวย แต่คือการสร้าง ablation ที่ตรวจสอบได้ว่า baseline เดิมเทียบกับ gamma-filtered variants แล้วเกิดอะไรขึ้นจริง พร้อมรายงาน sample size, MinTRL/PSR blocker, DSR policy, big-day dependency และข้อห้ามเรื่อง `true market-maker net gamma`

## 3. วิธีการและขั้นตอน

1. ใช้ preregistration เป็นตัวควบคุมการทดลอง:
   - `experiments\h_g1_gamma_strategy_ablation_preregistration.json`
2. โหลด Sub-System A baseline closed trades จาก:
   - `reports\baselines\subsystem_a_components\*_pnl_summary.json`
3. โหลด gamma proxy จาก H-G1 side-aware diagnostic:
   - `reports\diagnostics\h_g1_gamma_regime_diagnostic_summary_v3_side_aware.json`
   - `reports\diagnostics\h_g1_gamma_regime_enrichment_summary_v3_side_aware.json`
4. Join เฉพาะวันที่ baseline trade มี gamma proxy ตรงกันเท่านั้น เพื่อไม่แกล้งขยาย coverage เกินจริง
5. รัน 4 variants ที่ preregister ไว้:
   - `baseline_quant_only`
   - `skip_negative_gamma_proxy_days`
   - `skip_extreme_negative_gamma_proxy_days`
   - `positive_gamma_proxy_only`
6. Fit threshold ของ `skip_extreme_negative_gamma_proxy_days` จาก train dates เท่านั้น โดยใช้กลุ่มล่างสุดหนึ่งในสามแบบ `ceil(n/3)`
7. รันคำสั่งตรวจสอบ:

```powershell
& "D:\Fogust\Workspace\Investment\Project\Yuehua Investment Lab\.venv\Scripts\python.exe" -m unittest tests.test_h_g1_gamma_strategy_ablation
& "D:\Fogust\Workspace\Investment\Project\Yuehua Investment Lab\.venv\Scripts\python.exe" scripts\run_h_g1_gamma_strategy_ablation.py
& "D:\Fogust\Workspace\Investment\Project\Yuehua Investment Lab\.venv\Scripts\python.exe" scripts\validate_h_g1_gamma_strategy_ablation_summary.py
```

## 4. ผลการศึกษาและข้อมูลดิบ

### ผลสรุปหลัก

| รายการ | ค่า |
|---|---:|
| Status | `complete_underpowered` |
| Conclusion | `ยังสรุปไม่ได้` |
| Evidence tier | `E1` |
| Baseline closed trades ทั้งหมด | 90 |
| Gamma dates ทั้งหมด | 10 |
| Closed trades ที่ชนกับ gamma proxy | 2 |
| Closed trades ที่ถูก exclude เพราะไม่มี gamma proxy | 88 |
| Network used | `false` |
| Paid data used | `false` |
| Strategy use allowed | `false` |
| Paper trading allowed | `false` |

### Coverage ที่ใช้จริง

มี baseline closed trades ที่ชนกับ gamma proxy แค่ 2 วัน:

| Date | Split | Volatility bucket | Macro flag |
|---|---|---|---|
| `2023-10-27` | train | normal | high-importance macro |
| `2024-12-18` | OOS | high | high-importance macro |

ดังนั้น sample นี้ไม่พอสำหรับการสรุป edge, MinTRL, PSR, DSR acceptance หรือ big-day dependency ที่มีความหมายทางสถิติ

### Variant comparison

| Variant | Active trades | Skipped trades | Mid PnL | Implementable PnL | Cost drag | Sharpe | Label |
|---|---:|---:|---:|---:|---:|---:|---|
| `baseline_quant_only` | 2 | 0 | 288.0 | 230.88 | 57.12 | 6.498713 | under-sampled / underpowered |
| `skip_negative_gamma_proxy_days` | 0 | 2 | 0 | 0 | 0 | null | under-sampled / underpowered |
| `skip_extreme_negative_gamma_proxy_days` | 0 | 2 | 0 | 0 | 0 | null | under-sampled / underpowered |
| `positive_gamma_proxy_only` | 0 | 2 | 0 | 0 | 0 | null | under-sampled / underpowered |

### สิ่งที่ผลลัพธ์บอกได้

- วันที่มี trade ทั้งสองวันมี `signed-OI gamma proxy` ติดลบ
- Gamma filters ทั้งสามแบบจึงตัด trade ออกหมด
- ใน sample เล็กมากนี้ baseline ได้ implementable PnL `230.88` จาก 2 trades แต่ตัวเลขนี้ไม่มีน้ำหนักพอจะสรุปว่า baseline ดีจริง
- ผลที่ gamma filters เป็น 0 trade ก็ไม่มีน้ำหนักพอจะสรุปว่า gamma filter แย่จริง
- สิ่งเดียวที่สรุปได้อย่างมั่นใจคือ H-G1 ตอนนี้ยังมีปัญหา sample coverage สำหรับ strategy ablation

### DSR, MinTRL/PSR และ big-day dependency

| Gate | Status | เหตุผล |
|---|---|---|
| MinTRL | `blocked_insufficient_observations` | active trades มี 0-2 รายการ |
| PSR | `blocked_insufficient_observations` | return distribution สั้นเกินไป |
| DSR | `not_applicable_no_best_sharpe_selection` | ไม่ได้เลือก best Sharpe และ log ครบ 4 trials |
| Big-day dependency | `blocked_insufficient_observations` | ทุก variant มี active trades ต่ำกว่า 3 |

## 5. ปัญหา อุปสรรค และการแก้ไข

### ปัญหาที่พบ

1. PowerShell ในเครื่องนี้ไม่มีพารามิเตอร์ `Get-Date -AsUTC`
   - วิธีแก้: ใช้ `[DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ')`
   - ผลลัพธ์: ได้ timestamp UTC สำหรับ research log สำเร็จ

2. Gamma proxy coverage ไม่ชนกับ baseline trades ส่วนใหญ่
   - อาการ: baseline closed trades มี 90 รายการ แต่ชนกับ gamma proxy date set แค่ 2 รายการ
   - วิธีแก้: รายงานแบบ `intersection_only` และแยก excluded trades 88 รายการอย่างชัดเจน
   - ผลลัพธ์: ไม่เกิดการอ้าง coverage เกินจริง

### ข้อจำกัดสำคัญ

- ผลนี้เป็น E1 diagnostic เท่านั้น ไม่ใช่ E2 acceptance
- ห้ามใช้ `H-G1.22` เพื่ออนุมัติ NOVI/net-gamma filter, paper trading หรือ live trading
- `signed-OI gamma proxy` ไม่ใช่ `true market-maker net gamma`
- Sample มีเพียง 1 train trade และ 1 OOS trade จึงไม่พอสำหรับ regime conclusion
- Research log ยังไม่ได้ push ไป GitHub เพราะผู้ใช้สั่งหยุดการ push ไว้ก่อน

## 6. ข้อสรุปและก้าวต่อไป

ข้อสรุป: H-G1.22 เสร็จสิ้นแล้ว แต่ผลคือ `ยังสรุปไม่ได้` เพราะ strategy-ablation sample มีแค่ 2 trades และ gamma filters ทำให้ active trades เหลือ 0

- การทดลองทำตาม preregistration: 4 variants, train-only threshold, no OOS tuning, no paid data, no network
- ผลไม่ได้สนับสนุนการใช้ gamma filter เป็น trading gate
- ผลก็ยังไม่พอจะฆ่า H-G1 ถาวร เพราะปัญหาหลักคือ coverage/sample size ไม่ใช่หลักฐานเชิงสถิติที่แข็งแรง
- รายงานแยก mid PnL, implementable PnL และ cost drag แล้ว แต่ MinTRL/PSR/big-day dependency ยังถูก block เพราะ sample สั้นเกินไป

ก้าวต่อไป:

1. อัปเดต `IMPLEMENT_PLAN.md` และ `PROJECT_BRAIN.md` ให้ระบุว่า H-G1.22 เสร็จแล้วและยังเป็น E1 diagnostic
2. รัน verification loop เต็มตาม Operating Commands
3. เลือก next safe action ระหว่าง park/ออกแบบ sample-expansion decision สำหรับ H-G1 หรือกลับไป News-Unblock N.7 เพื่อหา timestamp-clean news cases
