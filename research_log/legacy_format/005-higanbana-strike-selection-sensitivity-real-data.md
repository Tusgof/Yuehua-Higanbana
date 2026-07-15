# บันทึกการวิจัย: M5.2 Strike Selection Sensitivity

## 1. ข้อมูลพื้นฐาน

- Timestamp UTC: `2026-07-02T05:09:56Z`
- โครงการ: SPY 0DTE - Higanbana
- หัวข้อ: ทดสอบความไวของ Sub-System A ต่อการเลือก strike แบบ target gap / moneyness บนข้อมูลจริง
- ผู้บันทึก: Codex
- สถานะ: เสร็จสิ้นแบบมี delta blocker
- เครื่องมือ:
  - Python local scripts
  - Databento normalized local artifacts เท่านั้น
- Artifact หลัก:
  - `scripts/run_m5_strike_selection_sensitivity.py`
  - `reports/experiments/m5_strike_selection_sensitivity_summary.json`
  - `reports/experiments/m5_strike_selection_sensitivity_report.md`
  - `reports/experiments/search_logs/m5_strike_selection_sensitivity_search_log.jsonl`
  - `reports/experiments/m5_strike_selection_components/`

## 2. วัตถุประสงค์

### อ่านแบบเร็ว

บันทึกนี้ตรวจความไวของ Sub-System A ต่อการเลือก strike โดยใช้ข้อมูล option chain จริงที่มีอยู่
ผลสำคัญคือฝั่ง delta-based selection ยังทำไม่ได้ เพราะข้อมูลปัจจุบันไม่มี Greeks เช่น delta/gamma จึงทดลองเฉพาะ moneyness / target-gap ที่ตรวจได้จริง
ข้อห้ามสรุป: ห้ามอ้างว่า delta selection ถูกทดสอบแล้ว หรือเลือก strike rule จริงจากผล diagnostic นี้


การทดลองนี้ต้องตอบคำถามว่า Sub-System A ORB directional debit vertical ไวต่อการเลือก long strike แค่ไหน เมื่อใช้ข้อมูล option chain จริงที่มีอยู่

เป้าหมายเดิมของ M5.2 คือเปรียบเทียบ delta selection กับ moneyness / strike-gap selection แต่รอบนี้พบข้อจำกัดสำคัญ: normalized option quote ปัจจุบันไม่มี `delta`, `gamma`, implied volatility หรือ Greeks อื่น ๆ ดังนั้นการทำ delta-based selection แบบจริงจังยังทำไม่ได้

เพื่อไม่สร้างผลทดลองเทียม รอบนี้จึงทำเฉพาะฝั่ง moneyness / target-gap ที่พิสูจน์จากข้อมูลปัจจุบันได้ และบันทึกฝั่ง delta เป็น blocker อย่างชัดเจน

คำถามหลัก:

- ถ้าเลือก long strike ใกล้ breakout มากขึ้นหรือลึก OTM มากขึ้น ผลลัพธ์เปลี่ยนอย่างไร
- nearest discrete strike rounding ทำให้ target gap เพี้ยนมากแค่ไหน
- scenario ไหนดูดีที่สุดในเชิง diagnostic
- ผลดีพอจะเลือก strike rule จริงหรือยัง

## 3. วิธีการและขั้นตอน

1. อ่านสถานะจาก `PROJECT_BRAIN.md`, `IMPLEMENT_PLAN.md`, และ `AGENTS.md`
2. อ่าน LLM Wiki เรื่อง `Strike Selection For 0DTE Spreads` และ `SPY 0DTE Opening Range Breakout`
3. ตรวจ normalized option quotes แล้วพบว่าไม่มี Greeks จึงไม่ทำ delta proxy
4. เพิ่ม runner ใหม่ `scripts/run_m5_strike_selection_sensitivity.py`
5. ใช้ candidate days เดิมของ Sub-System A จาก Mar-Dec 2023 และ Jan-Dec 2024
6. สร้าง strike-selection grid 5 trials โดยใช้ target breakout-to-long strike gap:
   - `$0.25`
   - `$0.75`
   - `$1.25`
   - `$1.75`
   - `$1.48` เป็น baseline-like target
7. ใช้ nearest discrete strike rounding:
   - call: เลือก long call strike ใกล้ `underlying + target_gap`
   - put: เลือก long put strike ใกล้ `underlying - target_gap`
   - short strike ใช้ width ประมาณ `$2.00`
   - ไม่ใช้ interpolation
8. รัน PnL ด้วยเงื่อนไขคงที่:
   - fill model: `half_spread`
   - fee: `$0.64` ต่อ contract ต่อขา
   - exit model: `forced_close_only`
   - close fallback: `nearest_1545_window`
9. บันทึก search log ครบทุก trial
10. รายงาน DSR เป็น blocker เพราะ sample ยังน้อยและไม่มีการเลือก production parameter

## 4. ผลการศึกษาและข้อมูลดิบ

### ผลรวมตาม scenario

| Scenario | Target gap | Closed | Skipped | EV/trade | Implementable PnL | Cost drag | OOS PnL | Max drawdown | Avg realized gap | Gap breach rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `target_gap_0_25_width_2` | 0.25 | 90 | 3 | 7.0289 | 632.60 | 629.40 | -68.44 | -0.381069 | 0.507258 | 0.516129 |
| `target_gap_0_75_width_2` | 0.75 | 90 | 3 | 5.8956 | 530.60 | 593.40 | -169.44 | -0.402364 | 0.802957 | 0.440860 |
| `target_gap_1_25_width_2` | 1.25 | 90 | 3 | 3.4844 | 313.60 | 573.40 | -240.44 | -0.450386 | 1.190054 | 0.526882 |
| `target_gap_1_75_width_2` | 1.75 | 89 | 4 | 3.6984 | 329.16 | 531.34 | -172.88 | -0.382013 | 1.792204 | 0.440860 |
| `baseline_gap_1_48_width_2` | 1.48 | 90 | 3 | 6.2067 | 558.60 | 540.40 | -65.44 | -0.360269 | 1.480376 | 0.612903 |

### Delta selection assessment

- สถานะ: `blocked_missing_greeks`
- เหตุผล: option quote records มี strike, bid, ask, size, timestamp และ symbol แต่ไม่มี delta, gamma, implied volatility หรือ model inputs ที่พอจะใช้สร้าง delta rule ได้อย่าง defensible
- ไม่ใช้ proxy delta
- สิ่งที่ต้องมีก่อนทำ delta experiment:
  - provider Greeks ณ decision timestamp หรือ
  - implied-volatility model แบบ point-in-time ที่ผ่านการอนุมัติและ validate แล้ว

### สิ่งที่เห็นจากผลลัพธ์

- scenario ที่ดีที่สุดใน grid คือ `target_gap_0_25_width_2` ได้ implementable PnL `$632.60`
- baseline-like target gap `$1.48` ได้ `$558.60` และ OOS `$-65.44`
- scenario ที่แย่สุดใน grid คือ `target_gap_1_25_width_2` ได้ `$313.60` และ OOS `$-240.44`
- OOS ของทุก scenario ยังติดลบ
- gap breach rate สูงทุก scenario เพราะ SPY strike เป็น discrete strike จริง ไม่ใช่ continuous moneyness grid
- target gap ใกล้ breakout มากขึ้นดูดีกว่าใน sample นี้ แต่ยังห้ามสรุปว่าเป็น rule ที่ควรใช้จริง

### Sample adequacy

- closed trades สูงสุดต่อ scenario: 90
- labels: `under-sampled`, `underpowered`
- MinTRL: pending
- PSR: pending
- DSR: `blocked_under_sampled`
- Trial count: 5

## 5. ปัญหา อุปสรรค และการแก้ไข

1. ปัญหา: ข้อมูล option quote ไม่มี delta / Greeks
   - การแก้ไข: ไม่สร้าง proxy delta เอง และบันทึก blocker ตรง ๆ
   - ผลลัพธ์: รายงานไม่แกล้งเปรียบเทียบ delta กับ moneyness จากข้อมูลที่ไม่มี

2. ปัญหา: moneyness grid เป็นเลขต่อเนื่อง แต่ option chain จริงมี strike เป็นระดับราคา discrete
   - การแก้ไข: ใช้ nearest discrete strike rounding และบันทึก realized gap / gap breach rate
   - ผลลัพธ์: เห็นชัดว่า target gap เพี้ยนได้บ่อย โดย breach rate อยู่ประมาณ 44%-61%

3. ปัญหา: มีหลาย target gaps จึงมี multiple testing risk
   - การแก้ไข: เขียน search log ครบ 5 trials และระบุว่า best/worst เป็น diagnostic เท่านั้น
   - ผลลัพธ์: DSR ถูกบันทึกเป็น `blocked_under_sampled` ไม่ใช่หลักฐานเลือก production parameter

4. ปัญหา: sample ยังเล็ก
   - การแก้ไข: ติด label `under-sampled` และ `underpowered`
   - ผลลัพธ์: รายงานไม่สรุปเกินหลักฐาน

## 6. ข้อสรุปและก้าวต่อไป

ข้อสรุป: ยังสรุปไม่ได้ว่า strike-selection rule แบบใดดีกว่าจริง แต่รอบนี้ยืนยันได้ว่า moneyness / target-gap selection ส่งผลต่อ PnL ชัดเจน และการใช้ continuous moneyness โดยไม่ map กลับสู่ strike จริงจะทำให้ผลทดลองเพี้ยน

ผลที่ควรจำ:

- `target_gap_0_25_width_2` ทำ PnL รวมดีที่สุดใน grid ที่ `$632.60` แต่ OOS ยังติดลบ `$-68.44`
- `baseline_gap_1_48_width_2` ได้ `$558.60` และ OOS `$-65.44`
- `target_gap_1_25_width_2` แย่สุดที่ `$313.60` และ OOS `$-240.44`
- delta selection ยังทำไม่ได้จาก artifact ปัจจุบัน
- ทุก scenario ยัง under-sampled/underpowered

ก้าวต่อไป:

1. อัปเดต `PROJECT_BRAIN.md` และ `IMPLEMENT_PLAN.md` ว่า M5.2 เสร็จแบบมี delta blocker
2. รัน `python scripts\audit_research_logs.py` หลัง push log นี้ เพื่อยืนยันว่า next prefix เป็น `006-higanbana-`
3. เดินต่อ M5.3 entry-timing sensitivity โดยต้องมี search log และห้าม tune จาก OOS
4. ถ้าต้องกลับมาทำ delta selection จริง ต้องมี provider Greeks หรือ implied-volatility model ที่ validate แล้วก่อน
