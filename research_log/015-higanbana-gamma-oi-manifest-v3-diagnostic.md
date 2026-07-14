# บันทึกการวิจัย: H-G1 Gamma/OI Manifest v3 Diagnostic

## 1. ข้อมูลพื้นฐาน

- Timestamp UTC: `2026-07-03T15:44:30Z`
- โครงการ: SPY 0DTE - Higanbana
- หัวข้อ: H-G1 manifest v3 gamma/OI diagnostic
- ผู้บันทึก: Codex
- สถานะ: เสร็จสิ้น
- เครื่องมือ:
  - `scripts\run_h_g1_gamma_regime_diagnostic.py`
  - `scripts\audit_research_readiness.py`
  - `scripts\validate_hypothesis_registry.py`
  - `scripts\validate_evidence_tiers.py`
- Artifact หลัก:
  - `experiments\h_g1_gamma_regime_date_set_preregistration_v3.json`
  - `reports\diagnostics\h_g1_gamma_regime_diagnostic_summary_v3.json`
  - `reports\diagnostics\h_g1_gamma_regime_diagnostic_report_v3.md`
  - `reports\diagnostics\h_g1_gamma_regime_enrichment_summary_v3.json`
  - `data\derived\spy_0dte\h_g1_gamma_regime\option_quote_enriched_manifest_v3_snapshot.jsonl`
  - `reports\data_cost\h_g1_gamma_oi_download_result.json`
  - `reports\data_cost\h_g1_gamma_oi_download_result_v3_replacement.json`

## 2. วัตถุประสงค์

### อ่านแบบเร็ว

บันทึกนี้ตรวจ manifest v3 ของ H-G1 หลังปรับชุดข้อมูลและ policy เพื่อดูว่าข้อมูล gamma/OI พร้อมกว่าเดิมหรือไม่
ผลสำคัญคือยังอยู่ในชั้น diagnostic ของ data quality และ timestamp discipline
ข้อห้ามสรุป: ห้ามใช้ manifest v3 pass/fail เป็นคำตอบว่า gamma filter ทำกำไรได้


รอบนี้ต้องการตอบคำถามว่า manifest v3 ซึ่งแทน `2023-07-12` ด้วย `2023-09-13` สามารถทำให้ H-G1 ผ่าน data-validity gate ได้หรือไม่ หลังจาก manifest v2 ยังติด required-bucket coverage failure อยู่ 5 จุด

ความสำเร็จของรอบนี้ไม่ใช่การพิสูจน์ว่า gamma proxy ใช้เทรดได้ แต่คือการตรวจว่า `signed-OI gamma proxy` มีคุณภาพข้อมูลพอจะเข้าสู่ขั้นวิจัยต่อหรือยัง โดยต้องผ่าน coverage, timestamp discipline, stability, economic sign, และ search-log gates โดยไม่ claim strategy edge เกินหลักฐาน

## 3. วิธีการและขั้นตอน

1. ตรวจสถานะก่อนรัน

```powershell
python scripts\validate_hypothesis_registry.py
python scripts\validate_evidence_tiers.py
python scripts\validate_h_g1_regime_date_set.py --manifest-path experiments\h_g1_gamma_regime_date_set_preregistration_v3.json
python -m unittest tests.test_audit_research_readiness tests.test_audit_paid_costs tests.test_download_h_g1_gamma_oi_data tests.test_validate_hypothesis_registry
python scripts\audit_paid_costs.py
python scripts\audit_research_readiness.py
```

2. รัน H-G1.14 diagnostic ครั้งแรกด้วย manifest v3 และ replacement OI download result

```powershell
python scripts\run_h_g1_gamma_regime_diagnostic.py --manifest-path experiments\h_g1_gamma_regime_date_set_preregistration_v3.json --oi-download-result-path reports\data_cost\h_g1_gamma_oi_download_result_v3_replacement.json --output-jsonl data\derived\spy_0dte\h_g1_gamma_regime\option_quote_enriched_manifest_v3_snapshot.jsonl --enrichment-summary-output reports\diagnostics\h_g1_gamma_regime_enrichment_summary_v3.json --diagnostic-summary-output reports\diagnostics\h_g1_gamma_regime_diagnostic_summary_v3.json --diagnostic-report-output reports\diagnostics\h_g1_gamma_regime_diagnostic_report_v3.md
```

ผลรอบแรกผิดเงื่อนไข เพราะใช้เฉพาะ OI ของ `2023-09-13` และ probe `2024-01-03` ทำให้ OI ของอีก 8 วันที่มีอยู่แล้วไม่ถูกโหลดเข้า diagnostic

3. แก้ script แบบแคบให้รองรับ OI download result หลายไฟล์

เพิ่ม `--additional-oi-download-result-path` ใน `scripts\run_h_g1_gamma_regime_diagnostic.py` และเพิ่ม test ใน `tests\test_run_h_g1_gamma_regime_diagnostic.py` เพื่อยืนยันว่า primary download result กับ replacement download result ถูก merge เข้าด้วยกัน

```powershell
python -m unittest tests.test_run_h_g1_gamma_regime_diagnostic
```

4. รัน H-G1.14 diagnostic ใหม่ด้วย OI ครบชุด

```powershell
python scripts\run_h_g1_gamma_regime_diagnostic.py --manifest-path experiments\h_g1_gamma_regime_date_set_preregistration_v3.json --oi-download-result-path reports\data_cost\h_g1_gamma_oi_download_result.json --additional-oi-download-result-path reports\data_cost\h_g1_gamma_oi_download_result_v3_replacement.json --output-jsonl data\derived\spy_0dte\h_g1_gamma_regime\option_quote_enriched_manifest_v3_snapshot.jsonl --enrichment-summary-output reports\diagnostics\h_g1_gamma_regime_enrichment_summary_v3.json --diagnostic-summary-output reports\diagnostics\h_g1_gamma_regime_diagnostic_summary_v3.json --diagnostic-report-output reports\diagnostics\h_g1_gamma_regime_diagnostic_report_v3.md
```

## 4. ผลการศึกษาและข้อมูลดิบ

### ผลรวมของ diagnostic

| Metric | Value |
|---|---:|
| Status | `blocked` |
| Evidence tier | `E1` |
| Date count | 10 |
| Quote rows | 2,822 |
| Computed Greeks rows | 2,089 |
| Computed Greeks rate | 0.740255 |
| Underlying join rate | 1.0 |
| Open interest join rate | 0.989369 |
| Economic sign observations | 10 |
| Full-day volatility correlation | -0.199367 |

### Gate results

| Gate | Status | Notes |
|---|---|---|
| Raw-row coverage | `pass` | computed Greeks, underlying join, และ OI join ผ่าน threshold |
| Bucket-weighted coverage | `blocked` | required bucket บางช่องยังมี computed rate ต่ำกว่า 60% |
| Timestamp discipline | `pass` | ไม่พบ future timestamp leakage ใน diagnostic |
| Stability | `pass` | manifest v3 ยังครอบคลุม regime ขั้นต่ำ |
| Economic sign | `pass` | observation count 10 และ correlation เป็นลบตามทิศทางที่คาด |
| Search log | `pass` | ไม่มีการเลือก threshold, quartile, หรือ bucket ที่ดีที่สุดหลังเห็นผล |

### Bucket failures ที่ยังไม่ผ่าน

| Date | Failed bucket |
|---|---|
| 2023-08-09 | `otm_call_computed_rate_below_60pct` |
| 2023-09-13 | `otm_put_computed_rate_below_60pct` |
| 2024-01-03 | `otm_put_computed_rate_below_60pct` |
| 2024-05-21 | `otm_call_computed_rate_below_60pct` |
| 2024-12-18 | `otm_call_computed_rate_below_60pct` |

### Per-date summary

| Date | Quotes | Greeks | Underlying | OI | Required bucket blocker |
|---|---:|---:|---:|---:|---|
| 2023-08-09 | 254 | 199 | 254 | 254 | `otm_call_computed_rate_below_60pct` |
| 2023-09-13 | 250 | 184 | 250 | 250 | `otm_put_computed_rate_below_60pct` |
| 2023-10-27 | 330 | 235 | 330 | 330 | None |
| 2023-12-29 | 394 | 341 | 394 | 394 | None |
| 2024-01-03 | 124 | 59 | 124 | 124 | `otm_put_computed_rate_below_60pct` |
| 2024-05-21 | 218 | 197 | 218 | 218 | `otm_call_computed_rate_below_60pct` |
| 2024-08-05 | 272 | 209 | 272 | 242 | None |
| 2024-08-07 | 370 | 256 | 370 | 370 | None |
| 2024-10-31 | 394 | 238 | 394 | 394 | None |
| 2024-12-18 | 216 | 171 | 216 | 216 | `otm_call_computed_rate_below_60pct` |

### การเปลี่ยนแปลงจาก v2 เป็น v3

| Metric | manifest v2 repair | manifest v3 |
|---|---:|---:|
| Date count | 10 | 10 |
| Quote rows | 2,834 | 2,822 |
| Computed Greeks rows | 2,095 | 2,089 |
| Computed Greeks rate | 0.739238 | 0.740255 |
| Underlying join rate | 1.0 | 1.0 |
| Open interest join rate | 0.989414 | 0.989369 |
| Economic sign correlation | -0.273079 | -0.199367 |
| Required bucket failure count | 5 | 5 |
| Final status | `blocked` | `blocked` |

## 5. ปัญหา อุปสรรค และการแก้ไข

1. ปัญหา: การรันครั้งแรกใช้ OI download result ไม่ครบ
   - สิ่งที่เกิดขึ้น: `open_interest_join_rate` เหลือ 0.13253 เพราะ script ใช้เฉพาะ `h_g1_gamma_oi_download_result_v3_replacement.json`
   - การแก้ไข: เพิ่ม argument `--additional-oi-download-result-path` เพื่อรวม OI เดิม 11 วันกับ OI replacement 1 วัน
   - ผลลัพธ์: หลัง rerun, `open_interest_join_rate` กลับมาเป็น 0.989369 และใช้ข้อมูลครบตาม manifest v3

2. ปัญหา: rerun รอบที่รวม OI ครบโดน timeout ของ command
   - สิ่งที่เกิดขึ้น: command timeout หลังประมาณ 124 วินาที
   - การแก้ไข: ตรวจไฟล์ output หลัง timeout และพบว่าไฟล์ summary ถูกเขียนสมบูรณ์แล้ว ไม่มี process ค้าง
   - ผลลัพธ์: อ่าน `reports\diagnostics\h_g1_gamma_regime_diagnostic_summary_v3.json` แล้วได้ผล diagnostic ครบ

### ข้อจำกัดสำคัญ

- ผลนี้ยังเป็น evidence tier `E1` เท่านั้น
- H-G1 ยังไม่ใช่ strategy acceptance และยังไม่มี MinTRL/PSR ของ strategy return
- แม้ economic sign จะผ่านในรอบนี้ แต่ coverage gate ยังเป็น blocker หลัก จึงห้ามใช้ NOVI/net-gamma เป็น strategy filter
- Research log นี้ยังไม่ได้ push ไป GitHub เพราะมีคำสั่งล่าสุดให้หยุดการ push ชั่วคราว

## 6. ข้อสรุปและก้าวต่อไป

ข้อสรุป: H-G1 manifest v3 ทำให้ raw-row coverage และ economic-sign gate ผ่าน แต่ยังสรุปไม่ได้ เพราะ bucket-weighted coverage ยังไม่ผ่าน 5 date/bucket cells

- การแทน `2023-07-12` ด้วย `2023-09-13` ไม่ได้แก้ blocker หลักของ H-G1
- ปัญหาไม่ได้อยู่ที่ OI join หรือ underlying join แล้ว เพราะทั้งสองผ่าน threshold
- blocker ตอนนี้แคบลงเหลือ bucket-level IV/Greeks computed-rate failures
- ห้าม claim ว่า signed-OI gamma proxy valid แล้ว
- ห้ามใช้ NOVI/net-gamma เป็น strategy filter

ก้าวต่อไป:

1. สร้าง v3 bucket-failure diagnostic เพื่อแยกสาเหตุของทั้ง 5 failed buckets
2. ตรวจว่า failure เกิดจาก Black-Scholes bracket, bid/ask/mid คุณภาพต่ำ, moneyness bucket mix, หรือ snapshot selection
3. ถ้าเป็นปัญหา data quality ของวันที่เฉพาะเจาะจง ให้ทำ replacement-date plan ก่อนคิดเรื่อง paid OI pull เพิ่ม
4. ถ้าเป็นปัญหา enrichment logic หรือ policy threshold ให้ทำ policy review เป็นเอกสารแยก และห้ามปรับ policy เพื่อให้ผ่านย้อนหลังโดยไม่มีเหตุผลเชิงกลไกรองรับ
