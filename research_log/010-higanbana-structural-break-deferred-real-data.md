# บันทึกการวิจัย: M5.7 Structural-Break Assessment

## 1. ข้อมูลพื้นฐาน

- Timestamp UTC: `2026-07-02T07:33:25Z`
- โครงการ: SPY 0DTE - Higanbana
- หัวข้อ: ตรวจความพร้อมของการทดสอบ structural break รอบวันที่ 2022-05-11
- ผู้บันทึก: Codex
- สถานะ: ยกเลิก/เลื่อนการทดสอบแบบมีหลักฐาน
- เครื่องมือ:
  - Python local scripts
  - Strategy data readiness audit
  - Local LLM Wiki
- Artifact หลัก:
  - `scripts/run_m5_structural_break_assessment.py`
  - `tests/test_m5_structural_break_assessment.py`
  - `reports/experiments/m5_structural_break_assessment_summary.json`
  - `reports/experiments/m5_structural_break_assessment_report.md`

## 2. วัตถุประสงค์

### อ่านแบบเร็ว

บันทึกนี้บันทึกประเด็น structural break ว่าข้อมูลและตลาดอาจเปลี่ยน regime ระหว่างช่วงเวลา ทำให้ผลย้อนหลังใช้เหมารวมไม่ได้
ผลสำคัญคือ structural-break assessment ยังถูกจำกัดด้วยข้อมูลและ sample ที่มี จึงเป็นกรอบเตือนความเสี่ยงมากกว่าข้อสรุปสุดท้าย
ข้อห้ามสรุป: ห้ามถือว่าผลจากช่วงเดียวแทนทุก regime ของตลาดได้


รอบนี้ต้องตอบคำถามว่าเราสามารถทดสอบ structural break รอบวันที่ `2022-05-11` ได้จริงหรือยัง โดยไม่ใช้ข้อมูลผิดช่วงเวลาและไม่สร้างผลทดลองปลอมขึ้นมาจากข้อมูลที่ไม่มี

เหตุผลที่ต้องทำรอบนี้คือแผนของโปรเจกต์ยอมรับสมมติฐานแบบ post-2022 ได้ก็ต่อเมื่อมีการทดสอบ structural break อย่างตรงไปตรงมา แต่การทดสอบแบบนี้ต้องมีข้อมูลทั้งฝั่ง reference/pre-break, post-break train, และ OOS ตามลำดับเวลา

ความสำเร็จของรอบนี้ไม่จำเป็นต้องเป็นการได้ผลสถิติ ถ้าข้อมูลไม่พอ ความสำเร็จคือการระบุ blocker ให้ชัดเจนว่าทำไมยังทดสอบไม่ได้ และต้องมีข้อมูลอะไรจึงจะปลดล็อกได้

## 3. วิธีการและขั้นตอน

1. อ่าน Boot Sequence จาก `PROJECT_BRAIN.md`, `IMPLEMENT_PLAN.md`, และ `AGENTS.md`
2. ตรวจ local LLM Wiki ที่เกี่ยวกับการแยกข้อมูลตามเวลาและ sample adequacy:
   - `wiki/concepts/backtest-validation-protocol.md`
   - `wiki/concepts/train-test-validation-for-time-series.md`
   - `wiki/concepts/minimum-track-record-length.md`
3. รัน readiness audit เพื่อยืนยัน coverage ปัจจุบัน:

```powershell
python scripts\audit_strategy_data_readiness.py
```

4. สร้างและรัน M5.7 assessment:

```powershell
python -m unittest tests.test_m5_structural_break_assessment
python scripts\run_m5_structural_break_assessment.py
```

5. แบ่งข้อมูลเป็น 3 ช่วงตามแผน:
   - reference/pre-break: `2019-01-01` ถึง `2022-05-10`
   - post-break train: `2022-05-11` ถึง `2023-12-31`
   - OOS: `2024-01-01` ถึงข้อมูลล่าสุดที่มี
6. ใช้กฎตัดสินว่า structural-break statistics จะรันได้ก็ต่อเมื่อทั้ง 3 ช่วงมี option coverage และ closed trades จริง

## 4. ผลการศึกษาและข้อมูลดิบ

### Coverage ตามช่วงเวลา

| Period | Required window | Actual window | Datasets | Candidate days | Closed trades | Quote rows | SPY bar rows |
|---|---|---|---:|---:|---:|---:|---:|
| `reference_pre_break` | 2019-01-01 ถึง 2022-05-10 | ไม่มี | 0 | 0 | 0 | 0 | 0 |
| `post_break_train` | 2022-05-11 ถึง 2023-12-31 | 2023-03-01 ถึง 2023-12-29 | 1 | 42 | 41 | 8,145,550 | 100,365 |
| `oos` | 2024-01-01 ถึง current available | 2024-01-02 ถึง 2024-12-31 | 22 | 51 | 49 | 13,357,670 | 132,148 |

### Blockers

- `requires_reference_pre_break_option_coverage`
- `requires_reference_pre_break_closed_trades`
- `requires_minimum_trade_count_500`

### ผลที่สำคัญ

- ไม่มีข้อมูล option quote ของ SPY 0DTE ในช่วง reference/pre-break ก่อน `2022-05-11`
- มีข้อมูล post-break train บางส่วน เริ่มจริงที่ `2023-03-01` ไม่ได้เริ่มตั้งแต่ `2022-05-11`
- มี OOS ปี 2024 แต่ห้ามใช้ OOS เพื่อ tune หรือแทนข้อมูล pre-break
- closed trades รวมปัจจุบันมี 90 เทรด ยังต่ำกว่า rough prior floor ที่ `N >= 500`
- M5.7 จึงไม่ได้รัน structural-break performance statistics เพราะจะกลายเป็นการเปรียบเทียบที่ไม่ตอบคำถามจริง

## 5. ปัญหา อุปสรรค และการแก้ไข

### ปัญหาที่พบ

1. ข้อมูล reference/pre-break ไม่มี
   - สิ่งที่เกิดขึ้น: audit พบว่า period `2019-01-01` ถึง `2022-05-10` มี 0 datasets, 0 candidate days, และ 0 closed trades
   - การแก้ไข: ไม่รันสถิติ structural break และสร้าง `m5_structural_break_assessment_summary.json` เพื่อบันทึก blocker
   - ผลลัพธ์: M5.7 ถูกเลื่อนอย่างมีหลักฐาน ไม่ใช่การสรุปผลจากข้อมูลที่ไม่ครบ

2. sample ยังต่ำกว่าขั้นต่ำ
   - สิ่งที่เกิดขึ้น: readiness audit รายงาน 90 closed trades เทียบกับ prior floor `N >= 500`
   - การแก้ไข: ติด blocker `requires_minimum_trade_count_500` และคง label `under-sampled` / `underpowered`
   - ผลลัพธ์: ไม่มีการอ้าง Sharpe หรือ structural-break conclusion แบบ acceptance-grade

### ข้อจำกัดสำคัญ

- รอบนี้เป็น coverage assessment ไม่ใช่ backtest performance result
- ยังไม่มี PSR/MinTRL เพราะยังไม่มี return distribution ที่พอสำหรับ acceptance-grade structural-break comparison
- ถ้าจะรัน M5.7 จริง ต้องเพิ่มข้อมูลก่อนปี `2022-05-11` หรือแก้สมมติฐานการวิจัยอย่างเป็นทางการ

## 6. ข้อสรุปและก้าวต่อไป

ข้อสรุป: ยังสรุปไม่ได้ และต้อง defer M5.7 เพราะไม่มี reference/pre-break SPY 0DTE option coverage ก่อนวันที่ `2022-05-11`

- การทดสอบ structural break ต้องมีข้อมูลทั้งก่อนและหลัง break point
- ข้อมูลปัจจุบันมีเฉพาะ post-break train บางส่วนและ OOS ปี 2024
- การใช้เฉพาะข้อมูลหลังปี 2022 จะไม่ตอบคำถามว่าเกิด structural break จริงหรือไม่
- การไม่รันสถิติในรอบนี้เป็นทางเลือกที่ถูกต้องกว่า เพราะช่วยกันผลทดลองหลอก

ก้าวต่อไป:

1. อัปเดต `PROJECT_BRAIN.md` และ `IMPLEMENT_PLAN.md` ให้ระบุว่า M5.7 ถูก defer เพราะไม่มี pre-break coverage
2. รัน `python scripts\audit_research_logs.py` เพื่อยืนยันว่า log `010` ถูกนับถูกต้อง
3. ถ้าจะปลดล็อก M5.7 ในอนาคต ให้ตัดสินใจก่อนว่าจะซื้อ/หา SPY 0DTE option coverage ช่วง `2019-01-01` ถึง `2022-05-10` หรือจะปรับสมมติฐานให้ไม่ต้องพึ่ง pre-break comparison
4. หลังปิดเอกสารและ verification ให้เดินต่อ Milestone 6 เฉพาะส่วนที่ไม่ต้องใช้ real-news archive หรือระบุ blocker ให้ชัดเจนถ้ายังทำต่อไม่ได้
