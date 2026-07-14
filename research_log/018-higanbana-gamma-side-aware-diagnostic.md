# บันทึกการวิจัย: H-G1 Gamma Side-Aware Diagnostic

## 1. ข้อมูลพื้นฐาน

- Timestamp UTC: `2026-07-03T17:15:51Z`
- โครงการ: SPY 0DTE - Higanbana
- หัวข้อ: H-G1 gamma diagnostic ภายใต้ side-aware required-bucket policy
- ผู้บันทึก: Codex
- สถานะ: เสร็จสิ้น
- เครื่องมือ:
  - `scripts\run_h_g1_gamma_regime_diagnostic.py`
  - `tests\test_run_h_g1_gamma_regime_diagnostic.py`
- Artifact หลัก:
  - `experiments\h_g1_side_aware_bucket_policy_adoption.json`
  - `reports\diagnostics\h_g1_gamma_regime_diagnostic_summary_v3_side_aware.json`
  - `reports\diagnostics\h_g1_gamma_regime_diagnostic_report_v3_side_aware.md`
  - `reports\diagnostics\h_g1_gamma_regime_enrichment_summary_v3_side_aware.json`
  - `data\derived\spy_0dte\h_g1_gamma_regime\option_quote_enriched_manifest_v3_side_aware_snapshot.jsonl`

## 2. วัตถุประสงค์

### อ่านแบบเร็ว

บันทึกนี้ทดลอง side-aware bucket policy สำหรับ H-G1 เพื่อให้ bucket สอดคล้องกับฝั่ง option มากขึ้น เช่น put/call/ATM
ผลสำคัญคือช่วยให้ data-validity diagnostic มีเหตุผลขึ้น แต่ยังเป็น proxy pipeline ไม่ใช่ strategy acceptance
ข้อห้ามสรุป: ห้ามใช้ side-aware diagnostic เป็นหลักฐานว่า NOVI/net-gamma ใช้เทรดได้


รอบนี้ต้องการตอบคำถามว่า หลังจาก H-G1.18 adopt `candidate_b_side_aware_required_bucket` เป็น policy สำหรับ diagnostic rerun แล้ว H-G1 gamma/OI proxy จะผ่าน data-validity gates หรือไม่ โดยใช้ manifest v3 rows เดิมเท่านั้น

ความสำเร็จของรอบนี้ไม่ใช่การพิสูจน์ว่า NOVI/net-gamma ใช้เป็น strategy filter ได้ แต่คือการตรวจว่า proxy data pipeline ผ่าน coverage, timestamp discipline, stability, economic-sign และ search-log gates ภายใต้ `h_g1_required_bucket_policy_v3_side_aware` หรือไม่

## 3. วิธีการและขั้นตอน

1. เพิ่ม side-aware required-bucket policy mode ใน `scripts\run_h_g1_gamma_regime_diagnostic.py`
   - `otm_put` ใช้เฉพาะ put rows ที่ moneyness `< 0.995`
   - `otm_call` ใช้เฉพาะ call rows ที่ moneyness `> 1.005`
   - `atm` ใช้ call/put rows ที่ `0.995 <= moneyness <= 1.005`
   - opposite-right ITM rows ยังถูกรายงานแยก แต่ไม่ใช้ตัดสิน required-bucket pass/fail

2. เพิ่ม unit test เพื่อยืนยันว่า opposite-right ITM rows ไม่ถูกซ่อน และไม่ทำให้ side-aware required bucket fail

```powershell
python -m unittest tests.test_run_h_g1_gamma_regime_diagnostic
```

3. รัน diagnostic ด้วย manifest v3 เดิม, OI download เดิม, replacement OI เดิม และ policy adoption artifact จาก H-G1.18

```powershell
python scripts\run_h_g1_gamma_regime_diagnostic.py `
  --manifest-path experiments\h_g1_gamma_regime_date_set_preregistration_v3.json `
  --additional-oi-download-result-path reports\data_cost\h_g1_gamma_oi_download_result_v3_replacement.json `
  --output-jsonl data\derived\spy_0dte\h_g1_gamma_regime\option_quote_enriched_manifest_v3_side_aware_snapshot.jsonl `
  --enrichment-summary-output reports\diagnostics\h_g1_gamma_regime_enrichment_summary_v3_side_aware.json `
  --diagnostic-summary-output reports\diagnostics\h_g1_gamma_regime_diagnostic_summary_v3_side_aware.json `
  --diagnostic-report-output reports\diagnostics\h_g1_gamma_regime_diagnostic_report_v3_side_aware.md `
  --research-log-slug higanbana-gamma-side-aware-diagnostic `
  --research-log-path research_log\018-higanbana-gamma-side-aware-diagnostic.md `
  --policy-adoption-path experiments\h_g1_side_aware_bucket_policy_adoption.json
```

4. ตรวจข้อจำกัดของรอบนี้:
   - `network_used=false`
   - `paid_data_used=false`
   - `strategy_pnl_used=false`
   - `strategy_use_allowed=false`

## 4. ผลการศึกษาและข้อมูลดิบ

### ผลรวมของ diagnostic

| Metric | Value |
|---|---:|
| Status | `pass_diagnostic_only` |
| Conclusion | `ผ่าน` |
| Evidence tier | `E1` |
| Policy id | `h_g1_required_bucket_policy_v3_side_aware` |
| Date count | 10 |
| Quote rows | 2,822 |
| Computed Greeks rows | 2,089 |
| Network used | `false` |
| Paid data used | `false` |
| Strategy PnL used | `false` |
| Strategy use allowed | `false` |

### Validation gates

| Gate | Status | Key metric |
|---|---|---|
| Coverage | `pass` | raw computed Greeks rate `0.740255`; side-aware required-bucket OI-notional share `0.999271` |
| Timestamp discipline | `pass` | no timestamp blocker reported |
| Stability | `pass` | 10 pre-registered dates covered |
| Economic sign | `pass` | full-day volatility correlation `-0.199367` |
| Search log | `pass` | no gamma threshold, quartile, or best bucket selected |

### Bucket policy result

Side-aware policy removed the specific blocker from H-G1.14/H-G1.17. Required-bucket failures are now `{}` under `h_g1_required_bucket_policy_v3_side_aware`.

Opposite-right ITM rows were not hidden:

| Opposite-right ITM category | Count |
|---|---:|
| `otm_call_opposite_right_put_rows` | 123 |
| `otm_put_opposite_right_call_rows` | 124 |

### Interpretation

การตีความ: รอบนี้ทำให้ H-G1 ผ่านเฉพาะ data-validity diagnostic ภายใต้ policy ใหม่ หมายความว่า pipeline ของ signed-OI gamma proxy พร้อมพอสำหรับขั้นต่อไปของการตรวจ acceptance blockers หรือ strategy-independent validation แต่ยังไม่ใช่หลักฐานว่าใช้เทรดได้

## 5. ปัญหา อุปสรรค และการแก้ไข

1. ปัญหา: unit test แรกคาดว่า overall coverage gate ต้องผ่านทันที แต่ raw-row coverage ยังสามารถ fail ได้แม้ side-aware bucket gate ผ่าน
   - การแก้ไข: ปรับ test ให้แยกความหมายระหว่าง `bucket_weighted_coverage.status` กับ overall `coverage.status`
   - ผลลัพธ์: test สะท้อน policy จริงมากขึ้น และยังไม่ลด guard ของ raw-row coverage

2. ปัญหา: ระหว่างรัน diagnostic มี `UserWarning: Discarding nonzero nanoseconds in conversion.`
   - การแก้ไข: บันทึกเป็น warning จาก timestamp conversion ของ Databento/DBN path ยังไม่พบว่าเป็น blocker เพราะ timestamp discipline gate ผ่าน
   - ผลลัพธ์: diagnostic สำเร็จและไม่มี blockers

### ข้อจำกัดสำคัญ

- ผลนี้เป็น E1 diagnostic เท่านั้น ไม่ใช่ E2 strategy evidence
- ยังไม่มี MinTRL/PSR/DSR สำหรับ strategy return ที่ใช้ gamma proxy
- ยังไม่มี strategy ablation ว่าใช้ NOVI/net-gamma แล้ว PnL, drawdown, ES95/ES99 หรือ benchmark comparison ดีขึ้นจริง
- Higanbana ยังไม่มี true dealer/customer inventory จึงยังห้ามเรียกว่า true market-maker net gamma
- Research log นี้ยังไม่ได้ push ไป GitHub เพราะคำสั่งล่าสุดของผู้ใช้ให้หยุด push ชั่วคราว

## 6. ข้อสรุปและก้าวต่อไป

ข้อสรุป: H-G1 ผ่านเฉพาะ side-aware data-validity diagnostic แล้ว แต่ยังไม่ผ่านเป็น strategy edge หรือ trading gate

- Coverage gate ผ่านหลังใช้ `h_g1_required_bucket_policy_v3_side_aware`
- Raw-row coverage ยังผ่านเหมือน manifest v3 เดิม
- Stability, timestamp discipline, economic-sign และ search-log gates ผ่าน
- Strategy use ยังเป็น `diagnostic_only_not_strategy_ready`
- ห้ามใช้ NOVI/net-gamma เป็น strategy filter จนกว่าจะผ่าน acceptance/reporting gates สำหรับกลยุทธ์จริง

ก้าวต่อไป:
1. อัปเดต `PROJECT_BRAIN.md`, `IMPLEMENT_PLAN.md`, hypothesis registry และ readiness audit ให้ระบุว่า H-G1.19 เสร็จแล้ว
2. เพิ่ม readiness next action ใหม่สำหรับ H-G1 หลัง data-validity pass เช่น strategy-independent acceptance blocker review
3. รัน verification ทั้งชุด
4. รอคำสั่งผู้ใช้ก่อน push research log ไป GitHub
