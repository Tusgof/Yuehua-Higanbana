# บันทึกการวิจัย: M5.5 Regime Filter Sensitivity

## 1. ข้อมูลพื้นฐาน

- Timestamp UTC: `2026-07-02T07:14:54Z`
- โครงการ: SPY 0DTE - Higanbana
- หัวข้อ: ทดสอบ VIX/VXV, macro-event filter และสถานะ NOVI/net-gamma ของ Sub-System A
- ผู้บันทึก: Codex
- สถานะ: เสร็จสิ้นแบบ diagnostic
- เครื่องมือ:
  - Python local scripts
  - Cboe VIX/VIX3M canonical archive
  - Official macro calendar canonical archive
  - Databento normalized local artifacts เท่านั้น
- Artifact หลัก:
  - `scripts/run_m5_regime_filter_sensitivity.py`
  - `tests/test_m5_regime_filter_sensitivity.py`
  - `reports/experiments/m5_regime_filter_sensitivity_summary.json`
  - `reports/experiments/m5_regime_filter_sensitivity_report.md`
  - `reports/experiments/search_logs/m5_regime_filter_sensitivity_search_log.jsonl`
  - `reports/experiments/m5_regime_filter_components/`

## 2. วัตถุประสงค์

### อ่านแบบเร็ว

บันทึกนี้ตรวจว่า regime filters เช่น macro/VIX ช่วยหรือลดคุณภาพของ Sub-System A อย่างไร
ผลสำคัญคือ filter ทำให้จำนวน trade ลดลง จึงต้องระวัง sample size และไม่สรุปจาก Sharpe/PnL ที่เหลือตัวอย่างน้อย
ข้อห้ามสรุป: ห้ามมอง filter ที่กำไรดีขึ้นว่าเป็น edge จนกว่าจะผ่าน under-sampled/underpowered checks


การทดลองนี้ต้องการตอบว่า deterministic regime filters เช่น VIX/VXV และ scheduled macro events ช่วยปรับคุณภาพผลลัพธ์ของ Sub-System A ORB directional debit vertical ได้หรือไม่ โดยใช้ข้อมูลจริงที่มีอยู่แล้วและไม่ซื้อข้อมูลเพิ่ม

รอบก่อนหน้า M5.1-M5.4 ทดสอบ cost/latency, strike, entry timing และ exit target/stop แล้ว แต่ยังไม่ได้ตอบว่าการคัดวันตาม regime ลด tail risk หรือเพิ่มผลตอบแทนได้จริงหรือไม่ รอบนี้จึงทดสอบ filter ที่วัดได้จริงก่อน แล้วแยก NOVI/net-gamma ออกเป็น blocker หากข้อมูลไม่พอ

ความสำเร็จของรอบนี้ไม่ใช่การเลือก production filter แต่คือการได้ผล diagnostic ที่มี pre/post-filter trade count, search log, DSR blocker, mid-vs-implementable PnL, OOS split, ES, drawdown และข้อจำกัดเรื่อง sample size อย่างครบถ้วน

## 3. วิธีการและขั้นตอน

1. อ่านสถานะจาก `PROJECT_BRAIN.md`, `IMPLEMENT_PLAN.md`, และ `AGENTS.md`
2. ตรวจ local LLM Wiki ก่อนใช้เหตุผลด้าน regime filter และ net gamma:
   - `wiki/concepts/regime-filtering-for-zero-dte.md`
   - `wiki/concepts/market-maker-net-gamma.md`
   - `wiki/concepts/backtest-validation-protocol.md`
3. ใช้ Sub-System A ORB directional debit vertical บนข้อมูลจริงเดิม:
   - in-sample: 2023-03-01 ถึง 2023-12-29
   - OOS: 2024-01-02 ถึง 2024-12-31
4. ใช้ VIX/VXV แบบ `previous_available_close_before_trade_date` เท่านั้น เพื่อไม่ใช้ same-day close ที่ยังไม่รู้ก่อน market open
5. ใช้ macro calendar แบบ scheduled same-day event เพราะเป็นข้อมูลที่รู้ล่วงหน้าก่อนเข้าเทรด
6. ทดสอบ 9 scenarios:
   - `unfiltered_control`
   - `vix_15_25_prev_close`
   - `vix_below_25_prev_close`
   - `vix_below_30_prev_close`
   - `term_structure_not_inverted_prev_close`
   - `vix_15_25_and_non_inverted_prev_close`
   - `exclude_high_importance_macro_same_day`
   - `exclude_major_macro_same_day`
   - `vix_15_25_non_inverted_exclude_major_macro`
7. บันทึกทุก trial ลง search log และตั้ง DSR เป็น `blocked_under_sampled`
8. ระบุ `NOVI/net-gamma` เป็น blocker เพราะข้อมูลปัจจุบันไม่มี Greeks, open interest, dealer inventory หรือ position reconstruction

คำสั่งที่ใช้:

```powershell
python -m unittest tests.test_m5_regime_filter_sensitivity
python scripts\audit_paid_costs.py
python scripts\run_m5_regime_filter_sensitivity.py
```

## 4. ผลการศึกษาและข้อมูลดิบ

### ผลรวมตาม scenario

| Scenario | Candidates | Filtered | Closed | Implementable PnL | OOS PnL | Max drawdown |
|---|---:|---:|---:|---:|---:|---:|
| `unfiltered_control` | 93 | 0 | 90 | 545.60 | -78.44 | -0.370769 |
| `vix_15_25_prev_close` | 93 | 49 | 44 | -141.64 | -83.32 | -0.455703 |
| `vix_below_25_prev_close` | 93 | 0 | 90 | 545.60 | -78.44 | -0.370769 |
| `vix_below_30_prev_close` | 93 | 0 | 90 | 545.60 | -78.44 | -0.370769 |
| `term_structure_not_inverted_prev_close` | 93 | 0 | 90 | 545.60 | -78.44 | -0.370769 |
| `vix_15_25_and_non_inverted_prev_close` | 93 | 49 | 44 | -141.64 | -83.32 | -0.455703 |
| `exclude_high_importance_macro_same_day` | 93 | 28 | 64 | 820.16 | 240.96 | -0.221838 |
| `exclude_major_macro_same_day` | 93 | 22 | 70 | 601.80 | 95.72 | -0.277636 |
| `vix_15_25_non_inverted_exclude_major_macro` | 93 | 57 | 36 | -342.16 | -84.64 | -0.560351 |

### ข้อสังเกตหลัก

- `exclude_high_importance_macro_same_day` เป็น scenario ที่ดีที่สุดเชิง diagnostic: implementable PnL `$820.16`, OOS PnL `$240.96`, max drawdown `-0.221838`
- `exclude_major_macro_same_day` ดีขึ้นกว่า control แต่ไม่แรงเท่า high-importance macro filter: implementable PnL `$601.80`, OOS PnL `$95.72`
- VIX threshold แบบ `15-25` ทำให้ผลแย่ลง เหลือ 44 closed trades และ implementable PnL `-$141.64`
- `vix_below_25`, `vix_below_30`, และ `term_structure_not_inverted` ไม่เปลี่ยนผลจาก control เพราะใน sample ปัจจุบัน filter เหล่านี้ไม่ได้ตัด trade ออก
- combined filter ที่เข้มเกินไปเหลือ 36 trades และผลแย่สุด: implementable PnL `-$342.16`
- ทุก scenario ยังมี label `under-sampled` และ `underpowered`
- Search log บันทึกครบ 9 trials และ DSR status คือ `blocked_under_sampled`

### NOVI / net-gamma

รอบนี้ไม่ได้ทดสอบ NOVI/net-gamma proxy เพราะข้อมูลที่มียังไม่พอสำหรับสูตรที่ defensible

ข้อมูลที่ยังขาด:

- gamma หรือ model inputs สำหรับคำนวณ gamma
- open interest หรือ position inventory
- scaling convention ของ contract exposure
- นโยบาย decision-time availability ว่าข้อมูลนี้รู้ได้ก่อนเข้าเทรดจริงหรือไม่

## 5. ปัญหา อุปสรรค และการแก้ไข

### ปัญหาที่พบ

1. Runner รอบแรก timeout หลัง 124 วินาที
   - การแก้ไข: รันใหม่ด้วย timeout ที่ยาวขึ้น
   - ผลลัพธ์: experiment completed และสร้าง summary/report/search log สำเร็จ

2. คำสั่งสรุป JSON ครั้งหนึ่งใช้ bash heredoc ซึ่ง PowerShell ไม่รองรับ
   - การแก้ไข: เปลี่ยนเป็น `python -c`
   - ผลลัพธ์: ได้ตาราง scenario summary ที่ต้องการ

3. `Get-Date -AsUTC` ใช้ไม่ได้ใน PowerShell รุ่นนี้
   - การแก้ไข: ใช้ `[DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ')`
   - ผลลัพธ์: ได้ timestamp UTC สำหรับ research log

### ข้อจำกัดสำคัญ

- ผลที่ดูดีของ macro filter อาจเป็นผลจาก sample เล็ก และการตัดวันบางกลุ่มออก ไม่ใช่ edge ที่แข็งแรง
- ห้ามเลือก macro filter เป็น production rule จากผลรอบนี้ เพราะ sample หลัง filter เหลือ 64 หรือ 70 trades เท่านั้น
- VIX/VXV ใช้ previous close อย่างถูกต้อง แต่ sample ปัจจุบันอาจไม่มี regime กว้างพอให้เห็นผลของ threshold บางแบบ
- NOVI/net-gamma ยัง blocked และไม่ควรใช้ proxy ปลอมจาก bid/ask หรือ volume อย่างเดียว

## 6. ข้อสรุปและก้าวต่อไป

ข้อสรุป: ยังสรุปไม่ได้ แต่ macro-event filters มีสัญญาณ diagnostic ที่ควรติดตามต่อ ส่วน NOVI/net-gamma ต้องรอ input ที่วัดได้จริงก่อน

- `exclude_high_importance_macro_same_day` ให้ผลดีที่สุดในรอบนี้ แต่ยัง under-sampled และ underpowered
- VIX `15-25` ไม่ช่วยใน sample ปัจจุบัน และทำให้ผลรวมแย่ลง
- combined filter ที่เข้มเกินไปลด sample มากจนผลไม่น่าเชื่อถือ
- NOVI/net-gamma ถูก block อย่างถูกต้อง เพราะไม่มีข้อมูลพอสำหรับสูตรที่ป้องกันการเดา

ก้าวต่อไป:

1. อัปเดต `PROJECT_BRAIN.md` และ `IMPLEMENT_PLAN.md` ให้บันทึกว่า M5.5 เสร็จแบบ diagnostic
2. รัน verification รวมหลังอัปเดตเอกสาร
3. เดินหน้า M5.6 portfolio construction เฉพาะในฐานะ diagnostic หาก Sub-System A/B return series เพียงพอสำหรับการเปรียบเทียบเบื้องต้น
