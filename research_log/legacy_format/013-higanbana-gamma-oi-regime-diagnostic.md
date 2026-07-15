# บันทึกการวิจัย: H-G1 Gamma/OI Regime Diagnostic

## 1. ข้อมูลพื้นฐาน

- Timestamp UTC: `2026-07-03T05:52:17Z`
- โครงการ: SPY 0DTE - Higanbana
- หัวข้อ: ทดสอบ signed-OI gamma proxy ด้วยชุดวันที่ 12 วันตาม policy v2
- ผู้บันทึก: Codex
- สถานะ: เสร็จสิ้น
- Evidence tier: `E1`
- Hypothesis ID: `H-G1`
- เครื่องมือ:
  - Python local scripts
  - Databento OPRA `statistics` OI cache ที่ดาวน์โหลดไว้แล้ว
  - normalized SPY option quotes และ SPY bars ที่มีอยู่ในเครื่อง
- Artifact หลัก:
  - `scripts/run_h_g1_gamma_regime_diagnostic.py`
  - `data/derived/spy_0dte/h_g1_gamma_regime/option_quote_enriched_12_date_snapshot.jsonl`
  - `reports/diagnostics/h_g1_gamma_regime_enrichment_summary.json`
  - `reports/diagnostics/h_g1_gamma_regime_diagnostic_summary.json`
  - `reports/diagnostics/h_g1_gamma_regime_diagnostic_report.md`
  - `experiments/h_g1_gamma_regime_date_set_preregistration.json`
  - `docs/GAMMA_AGGREGATION_VALIDATION_POLICY.md`

## 2. วัตถุประสงค์

### อ่านแบบเร็ว

บันทึกนี้เริ่มตรวจ H-G1 ว่า gamma/OI proxy มีข้อมูลพอจะใช้แบ่ง regime ได้หรือไม่
ผลสำคัญคือรอบนี้เน้น data validity ของ pipeline ไม่ใช่การพิสูจน์ว่า gamma เป็น strategy filter ที่ทำเงินได้
ข้อห้ามสรุป: ห้ามเรียก signed-OI proxy ว่า true market-maker net gamma หรือใช้เป็น edge claim


รอบนี้ต้องตอบคำถามว่า H-G1 ซึ่งเป็นสมมติฐานเรื่อง `signed-OI gamma proxy` มีคุณภาพข้อมูลพอจะใช้เป็นสัญญาณต่อยอดไปยัง NOVI หรือ net-gamma filter ได้หรือยัง

สาเหตุที่ต้องทำรอบนี้คือ diagnostic เดิมมีแค่วันเดียวคือ `2024-01-03` และติด blocker หลักสามข้อ: coverage ไม่พอ, stability ไม่พอ, และยังตรวจ economic sign ไม่ได้เพราะมีข้อมูลแค่วันเดียว รอบนี้จึงใช้ชุดวันที่ 12 วันที่ pre-register ไว้ก่อนซื้อ OI เพื่อทดสอบข้าม low/normal/high volatility, macro/no-macro, in-sample/OOS

ความสำเร็จของรอบนี้ไม่ใช่การพิสูจน์ว่า strategy ทำเงิน แต่คือการพิสูจน์ว่า proxy นี้ผ่าน data-validity gates ตาม `GAMMA_AGGREGATION_VALIDATION_POLICY.md` v2 หรือถ้าไม่ผ่าน ต้องบอกให้ชัดว่าติดตรงไหน

## 3. วิธีการและขั้นตอน

1. อ่านสถานะโปรเจกต์จาก `PROJECT_BRAIN.md`, `IMPLEMENT_PLAN.md`, และ `AGENTS.md`
2. ตรวจ policy v2 และโค้ด v1 เดิม:
   - `scripts/enrich_option_quotes_greeks_oi_probe.py`
   - `scripts/run_gamma_aggregation_diagnostic.py`
   - `docs/GAMMA_AGGREGATION_VALIDATION_POLICY.md`
3. เพิ่มสคริปต์ H-G1.4 เพื่อทำสองงานในรอบเดียว:
   - enrich quote snapshot เวลา `09:35:00 ET` ของ 12 วันที่ pre-register
   - รัน diagnostic v2 โดยรายงาน raw-row coverage, bucket-weighted coverage, timestamp discipline, stability, economic sign, และ search log gate
4. รัน unit tests เฉพาะส่วน:

```powershell
python -m unittest tests.test_run_h_g1_gamma_regime_diagnostic tests.test_gamma_aggregation_diagnostic tests.test_enrich_option_quotes_greeks_oi_probe
```

5. รัน diagnostic จริงโดยไม่เรียก paid API เพิ่ม:

```powershell
python scripts\run_h_g1_gamma_regime_diagnostic.py
```

6. อัพเดท registry และแผน:
   - `experiments/hypothesis_registry.json`
   - `docs/HYPOTHESIS_REGISTRY.md`
   - `IMPLEMENT_PLAN.md`
   - `PROJECT_BRAIN.md`

## 4. ผลการศึกษาและข้อมูลดิบ

### ผลสรุปหลัก

| รายการ | ค่า |
|---|---:|
| Hypothesis | `H-G1` |
| Evidence tier | `E1` |
| สถานะ | `blocked` |
| ข้อสรุป | `ยังสรุปไม่ได้` |
| วันที่ในชุด pre-register | 12 |
| quote snapshot rows | 3,364 |
| computed Greeks rows | 2,095 |
| raw computed-Greeks rate | 0.622771 |
| underlying join rate | 0.842449 |
| OI join rate | 0.991082 |
| economic sign observations | 10 |
| full-day volatility correlation | -0.273079 |
| blocker หลัก | `coverage_gate:blocked` |

### Gate results

| Gate | Status | เหตุผล |
|---|---|---|
| Coverage | `blocked` | raw-row coverage และ bucket-weighted coverage ไม่ผ่าน |
| Timestamp discipline | `pass` | ไม่พบ future OI หรือ future underlying bar |
| Stability | `pass` | ครบ 12 วันตาม pre-registered regime set |
| Economic sign | `pass` | 10 observable dates ให้ correlation ระหว่าง net OI gamma proxy กับ full-day realized volatility เท่ากับ `-0.273079` |
| Search log | `pass` | ไม่มีการเลือก threshold, quartile, หรือ best bucket |

### รายละเอียดรายวัน

| Date | Quotes | Greeks | Underlying join | OI join | Required bucket blockers |
|---|---:|---:|---:|---:|---|
| 2023-03-13 | 260 | 0 | 0 | 260 | `otm_put_missing`, `atm_missing`, `otm_call_missing` |
| 2023-03-22 | 270 | 0 | 0 | 270 | `otm_put_missing`, `atm_missing`, `otm_call_missing` |
| 2023-07-12 | 262 | 190 | 262 | 262 | `otm_put_computed_rate_below_60pct` |
| 2023-08-09 | 254 | 199 | 254 | 254 | `otm_call_computed_rate_below_60pct` |
| 2023-10-27 | 330 | 235 | 330 | 330 | None |
| 2023-12-29 | 394 | 341 | 394 | 394 | None |
| 2024-01-03 | 124 | 59 | 124 | 124 | `otm_put_computed_rate_below_60pct` |
| 2024-05-21 | 218 | 197 | 218 | 218 | `otm_call_computed_rate_below_60pct` |
| 2024-08-05 | 272 | 209 | 272 | 242 | None |
| 2024-08-07 | 370 | 256 | 370 | 370 | None |
| 2024-10-31 | 394 | 238 | 394 | 394 | None |
| 2024-12-18 | 216 | 171 | 216 | 216 | `otm_call_computed_rate_below_60pct` |

### สิ่งที่ผลรอบนี้บอก

- H-G1 ไม่ผ่าน policy v2 เพราะ coverage gate ยังไม่ดีพอ
- ปัญหาใหญ่ที่สุดคือสองวันที่เลือกไว้ใน March 2023 มี option quotes และ OI แต่ไม่มี local SPY bars สำหรับวันนั้น ทำให้คำนวณ Greeks ไม่ได้เลย
- แม้ OI join rate สูงมาก (`0.991082`) แต่ยังใช้แทน coverage ทั้งหมดไม่ได้ เพราะต้องมี underlying price และ Greeks ด้วย
- Economic sign รอบนี้ไม่ขัดกับสมมติฐาน เพราะ correlation เป็นลบ แต่ผลนี้ยังใช้ยืนยัน H-G1 ไม่ได้ เนื่องจาก coverage gate เป็น hard gate
- ห้ามใช้ signed-OI gamma proxy เป็น NOVI/net-gamma strategy filter ในตอนนี้

## 5. ปัญหา อุปสรรค และการแก้ไข

### ปัญหาที่พบ

1. สคริปต์รันจริงรอบแรก error เพราะบาง row คำนวณ Greeks ได้ แต่ไม่มี `open_interest`
   - สิ่งที่เกิดขึ้น: aggregation เรียก `signed_gamma_proxy(row)` แล้วเจอ `KeyError: 'open_interest'`
   - การแก้ไข: ปรับ `_aggregate_gamma` ให้รวม gamma proxy เฉพาะ row ที่มีครบทั้ง Greeks, `open_interest`, และ `underlying_price`
   - ผลลัพธ์: rerun สำเร็จ และ test เพิ่มผ่าน

2. ชุดวันที่ 12 วันมี quote rows จำนวนมาก ถ้าคำนวณทุกนาทีทั้งวันจะช้าและไม่ตรงกับแนวคิด decision-time proxy
   - สิ่งที่เกิดขึ้น: วันที่บางวันมี quote หลายหมื่นถึงแสนแถว
   - การแก้ไข: ใช้ snapshot เวลา `09:35:00 ET` ต่อวันตามแนวคิด decision timestamp ของ policy
   - ผลลัพธ์: ได้ diagnostic ที่รันได้จริงและสอดคล้องกับการตัดสินใจก่อนเข้า trade

3. March 2023 สองวันที่ pre-register ไม่มี local SPY bars
   - สิ่งที่เกิดขึ้น: `2023-03-13` และ `2023-03-22` มี underlying join count เท่ากับ 0
   - การแก้ไข: ไม่เติมราคาแทนและไม่เดา underlying price แต่ปล่อยให้ coverage gate block ตามจริง
   - ผลลัพธ์: H-G1 ถูกระบุเป็น `active_blocked` อย่างโปร่งใส

### ข้อจำกัดสำคัญ

- ผลนี้ยังเป็น `E1` diagnostic เท่านั้น ไม่ใช่ acceptance-grade evidence
- Economic sign check ใช้ correlation แบบง่ายเพื่อดูทิศทางเบื้องต้น ไม่ใช่การพิสูจน์ causal mechanism
- Bucket-weighted coverage ยังมีข้อจำกัด เพราะ rows ที่คำนวณ IV/Gamma ไม่ได้ ไม่มี gamma exposure ให้ใช้เป็น denominator ได้โดยตรง จึงรายงาน OI-notional share เป็น proxy ประกอบ
- ยังไม่มี ORB strategy PnL split by gamma bucket ในรอบนี้ จึงยังไม่ใช่ strategy ablation

## 6. ข้อสรุปและก้าวต่อไป

ข้อสรุป: H-G1 ยังสรุปไม่ได้และยังห้ามใช้เป็น strategy filter เพราะไม่ผ่าน coverage gate ของ policy v2 ถึงแม้ stability, timestamp discipline, economic sign, และ search-log gate จะผ่านในรอบนี้

- ผลรอบนี้ดีกว่า v1 ตรงที่แก้ blocker เรื่อง stability และ economic sign ได้บางส่วน
- แต่ coverage เป็น hard gate และยังล้มเหลวทั้ง raw-row coverage กับ required-bucket coverage
- สาเหตุที่ชัดที่สุดคือ local SPY bars ขาดในสองวัน March 2023 และบาง moneyness bucket มี computed rate ต่ำกว่า 60%
- H-G1 จึงควรถูกบันทึกเป็น `active_blocked` ไม่ใช่ `validated` และยังไม่ควรถูก falsified เพราะ economic sign ไม่ได้ขัดกับสมมติฐาน

ก้าวต่อไป:

1. ทำ no-purchase data-quality review สำหรับ `2023-03-13` และ `2023-03-22` เพื่อดูว่าขาด SPY bars เพราะไฟล์ไม่มีจริง หรือเพราะ loader/dataset coverage map ผิด
2. ถ้าจะแก้ H-G1 ต่อ ให้เสนอ manifest v2 พร้อมเหตุผลก่อนเปลี่ยนวันที่หรือซื้อข้อมูลเพิ่ม
3. ระหว่าง H-G1 ยัง blocked ให้เดินงาน no-cost track ถัดไปคือ H-L1/H-L2 design docs ตาม `IMPLEMENT_PLAN.md`
4. ห้ามใช้ gamma proxy เป็น NOVI/net-gamma filter ใน backtest หรือ paper trading จนกว่า coverage gate จะผ่าน
