# บันทึกการวิจัย: H-G1 Gamma/OI v3 Bucket Policy Diagnostic

## 1. ข้อมูลพื้นฐาน

- Timestamp UTC: `2026-07-03T16:02:46Z`
- โครงการ: SPY 0DTE - Higanbana
- หัวข้อ: H-G1 manifest v3 bucket policy diagnostic
- ผู้บันทึก: Codex
- สถานะ: เสร็จสิ้น
- เครื่องมือ:
  - `scripts\run_h_g1_manifest_v3_bucket_failure_diagnostic.py`
  - `tests\test_run_h_g1_manifest_v3_bucket_failure_diagnostic.py`
- Artifact หลัก:
  - `reports\diagnostics\h_g1_manifest_v3_bucket_failure_diagnostic.json`
  - `reports\diagnostics\h_g1_manifest_v3_bucket_failure_diagnostic.md`
  - `data\derived\spy_0dte\h_g1_gamma_regime\option_quote_enriched_manifest_v3_snapshot.jsonl`
  - `reports\diagnostics\h_g1_gamma_regime_diagnostic_summary_v3.json`

## 2. วัตถุประสงค์

### อ่านแบบเร็ว

บันทึกนี้ตรวจ bucket policy ของ H-G1 v3 ว่าการแบ่ง moneyness/option bucket เหมาะกับการประเมิน gamma/OI proxy หรือไม่
ผลสำคัญคือปัญหา bucket policy ส่งผลต่อ coverage และความน่าเชื่อถือของ proxy มาก จึงต้องแก้ก่อน strategy use
ข้อห้ามสรุป: ห้าม ignore bucket failure แล้วนำ proxy ไปใช้เป็น filter จริง


รอบนี้ต้องการตอบคำถามว่า 5 date/bucket cells ที่ยังไม่ผ่านใน H-G1.14 เกิดจากอะไรแน่ ระหว่าง Black-Scholes bracket failure, moneyness mix, quote spread/คุณภาพราคา, OI concentration หรือ snapshot selection

เหตุผลที่ต้องทำรอบนี้คือ H-G1.14 ทำให้ raw-row coverage, timestamp discipline, stability, economic sign และ search-log gate ผ่านแล้ว แต่ bucket-weighted coverage ยัง fail อยู่ ถ้ายังไม่รู้สาเหตุ เราไม่ควรแก้ policy หรือซื้อข้อมูลเพิ่ม เพราะจะเสี่ยงปรับกฎเพื่อให้ผ่านย้อนหลังโดยไม่มีเหตุผลเชิงกลไกรองรับ

ความสำเร็จของรอบนี้ไม่ใช่การทำให้ H-G1 ผ่าน แต่คือการระบุสาเหตุของ bucket failure ให้แคบพอจนเลือก next safe action ได้โดยไม่ claim ว่า NOVI/net-gamma ใช้เป็น strategy filter ได้แล้ว

## 3. วิธีการและขั้นตอน

1. อ่าน artifact จาก H-G1.14:
   - `reports\diagnostics\h_g1_gamma_regime_diagnostic_summary_v3.json`
   - `data\derived\spy_0dte\h_g1_gamma_regime\option_quote_enriched_manifest_v3_snapshot.jsonl`

2. เพิ่ม diagnostic script เพื่อวิเคราะห์ failed buckets โดยไม่ใช้ network และไม่ใช้ paid data เพิ่ม:

```powershell
python -m unittest tests.test_run_h_g1_manifest_v3_bucket_failure_diagnostic
python -m compileall scripts\run_h_g1_manifest_v3_bucket_failure_diagnostic.py
```

3. รัน diagnostic จริง:

```powershell
python scripts\run_h_g1_manifest_v3_bucket_failure_diagnostic.py
```

4. Diagnostic ตรวจสิ่งต่อไปนี้สำหรับแต่ละ failed bucket:
   - จำนวน row, computed row และ blocked row
   - OI-notional share ที่ยัง compute ได้
   - สัดส่วน blocked row ที่เป็น `opposite-right` เมื่อเทียบกับ bucket
   - bid/ask spread และ spread เทียบกับ mid
   - `mid_minus_intrinsic`
   - timestamp snapshot counts
   - top blocked rows ตาม OI-notional

## 4. ผลการศึกษาและข้อมูลดิบ

### ผลรวม

| Metric | Value |
|---|---:|
| Status | `diagnostic_complete_h_g1_still_blocked` |
| Evidence tier | `E1` |
| Total rows | 2,822 |
| Failed buckets reviewed | 5 |
| Blocked rows inside failed buckets | 55 |
| Opposite-right blocked rows | 55 |
| Opposite-right blocked row share | 1.0 |
| Minimum computed OI-notional share | 0.880098 |
| Weak notional failure count | 0 |

### Failed buckets

| Date | Failed bucket | Blocked rows | Opposite-right blocked rows | Computed OI-notional share |
|---|---|---:|---:|---:|
| 2023-08-09 | `otm_call` | 12 | 12 | 0.939224 |
| 2023-09-13 | `otm_put` | 10 | 10 | 0.880098 |
| 2024-01-03 | `otm_put` | 11 | 11 | 0.906923 |
| 2024-05-21 | `otm_call` | 9 | 9 | 0.984773 |
| 2024-12-18 | `otm_call` | 13 | 13 | 0.965892 |

### ข้อค้นพบหลัก

ทุก blocked row ใน 5 failed buckets เป็น `opposite-right` ทั้งหมด

- ใน `otm_call` bucket แถวที่ block เป็น put ที่ strike สูงกว่า underlying หรือเป็น ITM put
- ใน `otm_put` bucket แถวที่ block เป็น call ที่ strike ต่ำกว่า underlying หรือเป็น ITM call
- ทุก failed bucket มี timestamp snapshot เดียวกันที่ 09:35 ET จึงไม่ใช่ปัญหา snapshot selection แบบหลายเวลา
- OI-notional ที่ compute ได้ยังสูงทุก bucket ขั้นต่ำ 0.880098 จึงไม่ใช่ปัญหา OI join ขาดหนัก
- `mid_minus_intrinsic` ของ blocked rows ส่วนใหญ่ต่ำกว่า intrinsic เล็กน้อย ซึ่งทำให้ Black-Scholes IV bisection หา IV ไม่ได้

การตีความ: ปัญหาหลักคือ bucket policy ปัจจุบันแบ่งด้วย moneyness อย่างเดียว ทำให้ required buckets ผสม option คนละด้านเข้าไป เช่น `otm_call` รวมทั้ง call OTM และ put ITM เมื่อคิด row-rate ทั้ง bucket จึง fail แม้ฝั่งที่สอดคล้องกับ bucket จะ compute ได้และ OI-notional ส่วนใหญ่ยังอยู่

## 5. ปัญหา อุปสรรค และการแก้ไข

1. ปัญหา: H-G1.14 บอกได้ว่า bucket-weighted coverage fail แต่ยังบอกสาเหตุไม่พอ
   - การแก้ไข: เพิ่ม diagnostic แยกสาเหตุระดับ row และ bucket
   - ผลลัพธ์: ระบุได้ว่า 55/55 blocked rows เป็น `opposite-right` จาก moneyness-only bucket policy

2. ปัญหา: ไม่ควรแก้ policy เพื่อให้ผ่านย้อนหลังทันที
   - การแก้ไข: รอบนี้บันทึกผลเป็น E1 diagnostic เท่านั้น และยังคงสถานะ H-G1 เป็น blocked
   - ผลลัพธ์: ยังห้ามใช้ NOVI/net-gamma เป็น strategy filter

### ข้อจำกัดสำคัญ

- ผลนี้ยังไม่ใช่ strategy acceptance
- ยังไม่มี MinTRL/PSR สำหรับผลตอบแทนของ strategy ที่ใช้ gamma proxy
- ยังไม่ได้ pre-register policy ใหม่ เช่น side-aware bucket gate หรือ OI/gamma-notional gate
- Research log นี้ยังไม่ได้ push ไป GitHub เพราะมีคำสั่งล่าสุดให้หยุด push ชั่วคราว

## 6. ข้อสรุปและก้าวต่อไป

ข้อสรุป: H-G1.15 ระบุได้ว่าสาเหตุหลักของ manifest v3 bucket failure คือ bucket-definition/policy problem จากการใช้ moneyness-only buckets ที่ผสม `opposite-right` ITM options เข้าไป ไม่ใช่ปัญหา OI join, timestamp หรือการซื้อข้อมูลไม่พอ

- H-G1 ยังสรุปไม่ได้ และยังเป็น E1 diagnostic
- ห้าม claim ว่า signed-OI gamma proxy valid แล้ว
- ห้ามใช้ NOVI/net-gamma เป็น strategy filter
- การซื้อ OI เพิ่มยังไม่ใช่ next safe action เพราะ blocker ที่พบเป็น policy-definition issue มากกว่า data availability issue

ก้าวต่อไป:

1. ทำ policy review แบบ pre-registered สำหรับ H-G1 bucket gate โดยเปรียบเทียบ side-aware bucket gate กับ OI/gamma-notional gate
2. กำหนดล่วงหน้าว่า policy ใหม่ต้องผ่านเงื่อนไขอะไรโดยไม่ปรับเพื่อให้ผล v3 ผ่านย้อนหลังอย่างไม่มีเหตุผล
3. หลัง policy review ผ่านแล้ว ค่อย rerun H-G1 diagnostic ด้วย policy ใหม่บน manifest v3 เดิม โดยยังห้าม strategy-use claim
4. อัปเดต `PROJECT_BRAIN.md`, `IMPLEMENT_PLAN.md`, และ hypothesis registry ให้สะท้อนว่า H-G1.15 complete แต่ H-G1 ยัง blocked
