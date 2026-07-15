# บันทึกการวิจัย: H-G1 Gamma Bucket Policy Comparison

## 1. ข้อมูลพื้นฐาน

- Timestamp UTC: `2026-07-03T16:40:44Z`
- โครงการ: SPY 0DTE - Higanbana
- หัวข้อ: H-G1 bucket policy comparison
- ผู้บันทึก: Codex
- สถานะ: เสร็จสิ้น
- เครื่องมือ:
  - `scripts\run_h_g1_bucket_policy_comparison.py`
  - `tests\test_run_h_g1_bucket_policy_comparison.py`
- Artifact หลัก:
  - `experiments\h_g1_bucket_policy_review_preregistration.json`
  - `reports\diagnostics\h_g1_bucket_policy_comparison.json`
  - `reports\diagnostics\h_g1_bucket_policy_comparison.md`
  - `reports\diagnostics\h_g1_manifest_v3_bucket_failure_diagnostic.json`
  - `data\derived\spy_0dte\h_g1_gamma_regime\option_quote_enriched_manifest_v3_snapshot.jsonl`

## 2. วัตถุประสงค์

### อ่านแบบเร็ว

บันทึกนี้เปรียบเทียบ bucket policy หลายแบบของ H-G1 เพื่อหาว่า policy ไหนไม่บิดเบือน coverage และ timestamp discipline เกินไป
ผลสำคัญคือเป็น policy comparison ของข้อมูล ไม่ใช่การเลือก strategy rule ที่ผ่านแล้ว
ข้อห้ามสรุป: ห้ามมอง policy ที่ดูดีที่สุดเป็น edge โดยยังไม่มี strategy return series


รอบนี้ต้องตอบคำถามแคบ ๆ ว่า policy bucket แบบใดควรถูกนำไปทำ policy adoption review รอบถัดไป หลังจาก H-G1.15 พบว่าสาเหตุหลักของ bucket failure คือ moneyness-only bucket ผสม option คนละฝั่งเข้าไปใน required bucket

ความสำเร็จของรอบนี้ไม่ใช่การทำให้ H-G1 ผ่าน และไม่ใช่การพิสูจน์ว่า NOVI/net-gamma ใช้เป็น strategy filter ได้ แต่คือการเปรียบเทียบ candidate policies ที่ pre-register ไว้ใน H-G1.16 โดยใช้ manifest-v3 rows เดิมเท่านั้น ห้ามใช้ paid data ใหม่ ห้ามเปลี่ยนวัน และห้ามใช้ strategy PnL เพื่อเลือก policy

## 3. วิธีการและขั้นตอน

1. อ่าน pre-registration ของ H-G1.16:
   - `experiments\h_g1_bucket_policy_review_preregistration.json`

2. อ่านข้อมูล manifest-v3 เดิมและผล H-G1.15:
   - `data\derived\spy_0dte\h_g1_gamma_regime\option_quote_enriched_manifest_v3_snapshot.jsonl`
   - `reports\diagnostics\h_g1_gamma_regime_diagnostic_summary_v3.json`
   - `reports\diagnostics\h_g1_manifest_v3_bucket_failure_diagnostic.json`

3. สร้างและทดสอบ diagnostic script สำหรับเปรียบเทียบ candidate policies:

```powershell
python -m unittest tests.test_run_h_g1_bucket_policy_comparison
python -m compileall scripts\run_h_g1_bucket_policy_comparison.py
```

4. รัน diagnostic จริง:

```powershell
python scripts\run_h_g1_bucket_policy_comparison.py
```

5. ยืนยันข้อจำกัดของรอบนี้:
   - `network_used=false`
   - `paid_data_used=false`
   - `strategy_pnl_used=false`
   - `policy_adopted_now=false`
   - `strategy_use_allowed=false`

## 4. ผลการศึกษาและข้อมูลดิบ

### ผลรวม

| Metric | Value |
|---|---:|
| Status | `policy_review_complete_h_g1_still_blocked` |
| Conclusion | `ยังสรุปไม่ได้` |
| Evidence tier | `E1` |
| Allowed output status | `policy_review_only` |
| Source rows | 2,822 |
| Date count | 10 |
| Network used | `false` |
| Paid data used | `false` |
| Strategy PnL used | `false` |
| Strategy use allowed | `false` |

### Candidate comparison

| Candidate | Gate | Status | Passed dates | Blocked dates | Failures | Warnings |
|---|---|---|---:|---:|---:|---:|
| `candidate_a_current_v2_moneyness_only` | `moneyness_only` | `policy_candidate_blocked` | 5 | 5 | 5 | 0 |
| `candidate_b_side_aware_required_bucket` | `side_aware` | `policy_candidate_passes_coverage_review` | 10 | 0 | 0 | 0 |
| `candidate_c_notional_weighted_coverage` | `notional_weighted` | `policy_candidate_blocked` | 9 | 1 | 1 | 5 |

### การตีความผล

ผลที่สำคัญที่สุดคือ `candidate_b_side_aware_required_bucket` ผ่าน coverage review ครบ 10 จาก 10 วัน โดยไม่ต้องใช้ paid data ใหม่ ไม่ต้องเปลี่ยน manifest date และไม่ต้องใช้ strategy PnL

สาเหตุที่ผลนี้มีเหตุผลเชิงกลไกคือ H-G1.15 ชี้ว่า blocked rows ใน failed buckets เป็น opposite-right ITM rows ที่เกิดจาก bucket แบบ moneyness-only ดังนั้น side-aware bucket แก้ปัญหาตรงจุดกว่า current v2 policy

อย่างไรก็ตาม ผลนี้ยังเป็นเพียง policy review เท่านั้น ไม่ใช่ signal validation และไม่ใช่ strategy validation

## 5. ปัญหา อุปสรรค และการแก้ไข

### ข้อจำกัดสำคัญ

1. รอบนี้ไม่ได้ทดสอบ PnL ของ strategy
2. รอบนี้ไม่ได้เพิ่มวันใหม่หรือ regime ใหม่
3. รอบนี้ไม่ได้พิสูจน์ว่า signed-OI gamma proxy ใช้งานเป็น net-gamma จริงได้
4. รอบนี้ไม่ได้อนุญาตให้ใช้ NOVI/net-gamma เป็น strategy filter
5. Evidence tier ยังเป็น `E1` เท่านั้น

### ปัญหาที่พบหลังเผยแพร่

หลังจาก push บันทึกขึ้น GitHub พบว่าไฟล์นี้มี encoding เพี้ยนในเนื้อหาภาษาไทย จึงแก้ไขไฟล์เดิมเลข `017` แทนการสร้างไฟล์ใหม่ เพื่อรักษาลำดับ research log และให้สอดคล้องกับกฎว่า revision ของ experiment เดิมต้องอัปเดต log เดิม

## 6. ข้อสรุปและก้าวต่อไป

ข้อสรุป: รอบนี้ยังสรุปไม่ได้ว่า H-G1 ใช้เป็นกลยุทธ์ได้ แต่ `candidate_b_side_aware_required_bucket` เป็น candidate ที่เหมาะสมที่สุดสำหรับ policy adoption review รอบถัดไป

เหตุผล:

- current v2 moneyness-only policy ยัง fail 5 วัน
- side-aware required bucket ผ่านครบ 10 วัน
- notional-weighted policy ยังมี 1 failure และ 5 warnings
- การเลือก policy ไม่ได้ใช้ strategy PnL จึงลดความเสี่ยงจากการเลือก policy เพื่อ fit ผลกำไร
- ผลนี้ยังไม่พอสำหรับ strategy use, paper trading, หรือ real-money trading

ก้าวต่อไป:

1. สร้าง explicit policy adoption artifact สำหรับ `candidate_b_side_aware_required_bucket`
2. รัน H-G1 gamma diagnostic ใหม่ภายใต้ side-aware required-bucket policy
3. ถ้า diagnostic ผ่าน ให้ทำ acceptance blocker review ก่อนแตะ strategy filter
4. ห้ามใช้ NOVI/net-gamma เป็น strategy filter จนกว่าจะมี strategy-ablation evidence ที่ผ่าน sample, MinTRL/PSR, และ acceptance gates
