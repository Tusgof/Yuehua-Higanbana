# บันทึกการวิจัย: H-G1 Gamma/OI Manifest v2 Repair Diagnostic

## 1. ข้อมูลพื้นฐาน

- Timestamp UTC: `2026-07-03T08:13:51Z`
- โครงการ: SPY 0DTE - Higanbana
- หัวข้อ: H-G1 manifest v2 repair diagnostic
- ผู้บันทึก: Codex
- สถานะ: เสร็จสิ้น
- เครื่องมือ:
  - Databento metadata cost check
  - `scripts\validate_h_g1_regime_date_set.py`
  - `scripts\run_h_g1_gamma_regime_diagnostic.py`
- Artifact หลัก:
  - `experiments\h_g1_gamma_regime_date_set_preregistration_v2.json`
  - `reports\diagnostics\h_g1_gamma_regime_diagnostic_summary_v2_10date.json`
  - `reports\diagnostics\h_g1_gamma_regime_diagnostic_report_v2_10date.md`
  - `reports\diagnostics\h_g1_gamma_regime_enrichment_summary_v2_10date.json`
  - `data\derived\spy_0dte\h_g1_gamma_regime\option_quote_enriched_10_date_snapshot_v2.jsonl`

## 2. วัตถุประสงค์

### อ่านแบบเร็ว

บันทึกนี้ซ่อมและตรวจ manifest v2 ของ H-G1 เพื่อแก้ปัญหาข้อมูล gamma/OI ที่ทำให้ diagnostic ก่อนหน้ายังไม่น่าเชื่อพอ
ผลสำคัญคือเป็นงานซ่อม data pipeline และ coverage ไม่ใช่ strategy result
ข้อห้ามสรุป: ห้ามถือว่าการซ่อม manifest คือการผ่าน H-G1 ในเชิงกลยุทธ์


รอบนี้ต้องการตอบคำถามเฉพาะของ H-G1 ว่า blocker จากผลวิเคราะห์ก่อนหน้าเกิดจาก `SPY bars` ของวันที่ `2023-03-13` และ `2023-03-22` หายจริงหรือไม่ และถ้าตัดปัญหานี้ออกแล้ว signed-OI gamma proxy จะผ่าน data-validity gate ขั้นต้นหรือยัง

ความสำเร็จของรอบนี้ไม่ใช่การยืนยันว่า H-G1 ใช้เทรดได้ แต่คือการแยกสาเหตุให้ชัดว่า H-G1 ยังติดเพราะข้อมูล underlying หาย หรือยังติดเพราะ bucket-level IV/Greeks coverage ไม่พอ

## 3. วิธีการและขั้นตอน

1. ตรวจ cost guard ก่อนทำ paid action

```powershell
python scripts\audit_paid_costs.py
```

ผลคือ cost guard ยังผ่าน โดย working usage อยู่ที่ `$109.082227` และเหลือ headroom `$15.917773` ใต้ stop threshold `$125`

2. ทดลอง estimate cost เพื่อซ่อม `SPY bars` เฉพาะสองวันที่หาย

```powershell
python scripts\plan_databento_spy_bars.py --live-cost --start '2023-03-13T13:30:00+00:00' --end '2023-03-13T20:00:00+00:00' --output-path 'data\raw\spy_0dte\databento\spy_bars\mar_2023_2023_03_13_spy_ohlcv_1m.dbn.zst' --plan-path 'reports\data_cost\databento_spy_bars_plan_2023_03_13_h_g1_repair.json' --report-path 'reports\data_cost\databento_spy_bars_plan_2023_03_13_h_g1_repair.md'

python scripts\plan_databento_spy_bars.py --live-cost --start '2023-03-22T13:30:00+00:00' --end '2023-03-22T20:00:00+00:00' --output-path 'data\raw\spy_0dte\databento\spy_bars\mar_2023_2023_03_22_spy_ohlcv_1m.dbn.zst' --plan-path 'reports\data_cost\databento_spy_bars_plan_2023_03_22_h_g1_repair.json' --report-path 'reports\data_cost\databento_spy_bars_plan_2023_03_22_h_g1_repair.md'
```

ทั้งสองคำสั่งถูก Databento ปฏิเสธด้วย `data_start_before_available_start` เพราะ `EQUS.MINI` เริ่มมีข้อมูลที่ `2023-03-28` ดังนั้นการซ่อมสองวันนั้นจาก provider เดิมทำไม่ได้

3. สร้าง manifest v2 โดยไม่ซื้อข้อมูลเพิ่ม

manifest v2 ตัด `2023-03-13` และ `2023-03-22` ออกเพราะเป็นวันที่ซ่อมไม่ได้ตามข้อจำกัด provider ไม่ใช่เพราะผล gamma ไม่ดี จากนั้นล็อก 10 วันที่เหลือซึ่งมี quote, OI, และ SPY bars ใช้งานได้

4. ตรวจ manifest v2

```powershell
python -m unittest tests.test_validate_h_g1_regime_date_set
python scripts\validate_h_g1_regime_date_set.py --manifest-path experiments\h_g1_gamma_regime_date_set_preregistration_v2.json
```

5. rerun diagnostic ด้วย output แยกของ v2

```powershell
python scripts\run_h_g1_gamma_regime_diagnostic.py --manifest-path experiments\h_g1_gamma_regime_date_set_preregistration_v2.json --output-jsonl data\derived\spy_0dte\h_g1_gamma_regime\option_quote_enriched_10_date_snapshot_v2.jsonl --enrichment-summary-output reports\diagnostics\h_g1_gamma_regime_enrichment_summary_v2_10date.json --diagnostic-summary-output reports\diagnostics\h_g1_gamma_regime_diagnostic_summary_v2_10date.json --diagnostic-report-output reports\diagnostics\h_g1_gamma_regime_diagnostic_report_v2_10date.md
```

## 4. ผลการศึกษาและข้อมูลดิบ

### ผลที่ดีขึ้น

| Metric | v1 12-date diagnostic | v2 10-date repair diagnostic |
|---|---:|---:|
| Date count | 12 | 10 |
| Quote rows | 3364 | 2834 |
| Computed Greeks rows | 2095 | 2095 |
| Computed Greeks rate | 0.622771 | 0.739238 |
| Underlying join rate | 0.842449 | 1.0 |
| Open interest join rate | ไม่ได้สรุปใน v1 row นี้ | 0.989414 |
| Raw-row coverage gate | ไม่ผ่าน | ผ่าน |
| Stability gate | ผ่าน | ผ่าน |
| Economic sign gate | ผ่าน | ผ่าน |
| Final status | blocked | blocked |

manifest v2 ผ่าน validator:

| Regime dimension | Count |
|---|---:|
| Total dates | 10 |
| Low volatility | 4 |
| Normal volatility | 3 |
| High volatility | 3 |
| In-sample | 4 |
| OOS | 6 |
| High-importance macro | 5 |
| No high-importance macro | 5 |
| Unique calendar months | 9 |

### ผลที่ยังไม่ผ่าน

H-G1 v2 ยัง blocked เพราะ `bucket_weighted_coverage_gate_failed` แม้ raw-row coverage จะผ่านแล้ว

| Date | Required bucket blocker |
|---|---|
| 2023-07-12 | `otm_put_computed_rate_below_60pct` |
| 2023-08-09 | `otm_call_computed_rate_below_60pct` |
| 2024-01-03 | `otm_put_computed_rate_below_60pct` |
| 2024-05-21 | `otm_call_computed_rate_below_60pct` |
| 2024-12-18 | `otm_call_computed_rate_below_60pct` |

ผลเชิงเศรษฐศาสตร์ของ proxy ยังเป็นเพียง diagnostic:

- Observation count: `10`
- Correlation ระหว่าง decision-time net OI gamma proxy กับ same-day realized volatility: `-0.273079`
- ทิศทางนี้สอดคล้องกับสมมติฐานแบบคร่าว ๆ แต่ยังห้ามใช้เป็น strategy filter เพราะ coverage gate ยังไม่ผ่าน

## 5. ปัญหา อุปสรรค และการแก้ไข

1. ปัญหา: Databento ไม่สามารถซ่อม `SPY bars` ของ `2023-03-13` และ `2023-03-22`
   - สิ่งที่เกิดขึ้น: `metadata.get_cost` ตอบ `422 data_start_before_available_start`
   - การแก้ไข: ไม่ download และสร้าง manifest v2 ที่ตัดสองวันนี้ออก โดยเก็บ v1 ไว้เป็นหลักฐาน
   - ผลลัพธ์: v2 แยกปัญหา missing underlying ออกได้สำเร็จ

2. ปัญหา: H-G1 ยังไม่ผ่านแม้ raw-row coverage ดีขึ้น
   - สิ่งที่เกิดขึ้น: required bucket บางฝั่งมี IV/Greeks computed rate ต่ำกว่า 60%
   - การแก้ไข: บันทึก blocker รายวันและห้ามใช้ NOVI/net-gamma เป็น strategy filter
   - ผลลัพธ์: next action ชัดขึ้น คือวิเคราะห์ bucket failures หรือทำ manifest v3 replacement-date plan ก่อนคิดเรื่อง paid OI pull เพิ่ม

### ข้อจำกัดสำคัญ

- v2 มี 10 วัน ไม่ใช่ original 12-date target ดังนั้นถ้าผ่านก็ยังเป็น repair diagnostic ไม่ใช่ H-G1 full validation
- ผลยังเป็น evidence tier `E1`
- ยังไม่มี MinTRL/PSR ของ strategy return เพราะ H-G1 รอบนี้เป็น data-validity proxy test ไม่ใช่ strategy backtest

## 6. ข้อสรุปและก้าวต่อไป

ข้อสรุป: H-G1 manifest v2 ช่วยยืนยันว่า missing SPY bars ของสองวัน March 2023 เป็นปัญหาจาก provider availability และเมื่อแยกออกแล้ว raw-row coverage ผ่าน แต่ H-G1 ยังสรุปไม่ได้เพราะ required-bucket computed Greeks coverage ยังไม่ผ่าน

- ห้าม claim ว่า signed-OI gamma proxy valid แล้ว
- ห้ามใช้ NOVI/net-gamma เป็น strategy filter
- blocker หลักเปลี่ยนจาก missing underlying เป็น bucket-level IV/Greeks coverage
- v2 เป็นการซ่อม diagnostic ไม่ใช่การเลือกผลที่ดีขึ้นจาก gamma outcome เพราะตัดวันที่ซ่อมไม่ได้ตามข้อจำกัดข้อมูลเท่านั้น

ก้าวต่อไป:

1. วิเคราะห์สาเหตุ bucket failures ทั้ง 5 วันว่าเกิดจาก bid/ask/mid อยู่นอก Black-Scholes bracket, moneyness bucket, หรือ snapshot selection
2. ถ้า bucket failures เกิดจาก date quality ให้ทำ manifest v3 replacement-date plan ก่อน paid OI pull ใหม่
3. ถ้า bucket failures เกิดจากวิธี compute IV/Greeks ให้แก้ enrichment logic หรือ policy gate ก่อนซื้อข้อมูลเพิ่ม
4. รอ user อนุญาตก่อน push research log ขึ้น GitHub เพราะรอบนี้มีคำสั่งให้หยุดอัพ GitHub ชั่วคราว
