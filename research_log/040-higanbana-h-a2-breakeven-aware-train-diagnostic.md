# บันทึกการวิจัย: H-A2 Breakeven-Aware Train Diagnostic

## 1. ข้อมูลพื้นฐาน

- Timestamp UTC: `2026-07-08T15:33:44Z`
- โครงการ: SPY 0DTE - Higanbana
- หัวข้อ: ตรวจว่า H-A2 มีข้อมูลพอสร้างกฎ breakeven-aware หรือยัง
- ผู้บันทึก: Codex
- สถานะ: เสร็จสิ้น
- ระดับหลักฐาน: `E1`
- ข้อสรุป: `ยังสรุปไม่ได้`
- Artifact หลัก:
  - `experiments/h_a2_breakeven_aware_rule_preregistration.json`
  - `reports/diagnostics/h_a2_breakeven_aware_rule_train_diagnostic.json`
  - `reports/diagnostics/h_a2_breakeven_aware_rule_train_diagnostic.md`
  - `reports/diagnostics/search_logs/h_a2_breakeven_aware_rule_train_diagnostic_search_log.jsonl`

## 2. วัตถุประสงค์

### อ่านแบบเร็ว

รอบนี้ถามว่า หลังจากรู้แล้วว่า H-A2 แพ้เพราะ option spread ไปไม่ถึงจุดคุ้มทุน เรามีข้อมูล train ที่พอจะสร้างกฎแบบ `breakeven-aware` หรือยัง

ผลคือยังไม่พอ ข้อมูล train ที่มีอยู่ช่วยทดลองตัวแทนของปัญหาได้ เช่น ดูว่า `proxy_5m directional followthrough` ที่สูงขึ้นสัมพันธ์กับผลลัพธ์ดีขึ้นหรือไม่ แต่ยังไม่มีข้อมูลสำคัญของ option จริงในแต่ละวัน เช่น long strike ที่เลือก, entry debit, bid/ask width และ liquidity จึงยังล็อกกฎเทรดจริงไม่ได้

ความหมายคือการซื้อข้อมูลเพิ่มอาจจำเป็น แต่ต้องซื้อแบบเจาะจงเพื่อเติม field ที่ตอบสมมติฐานนี้ ไม่ใช่ซื้อ calendar กว้าง ๆ หรือทดสอบ rule เดิมซ้ำไปเรื่อย ๆ

ห้ามสรุปว่า H-A2 ผ่าน ห้ามเลือก threshold ใดเป็นกฎเทรด ห้ามใช้ผลนี้อนุมัติ `paper trading` และห้ามอ้างว่าเป็นหลักฐาน `E2`

## 3. วิธีการและขั้นตอน

1. ใช้ H-A2.61 เป็น preregistration ควบคุม
2. ใช้ข้อมูล local เท่านั้น ไม่มี network, ไม่มี paid data และไม่มี broker request
3. ใช้ train split จาก `h_a2_lower_resolution_proxy_summary.json` เพื่อทำ surrogate trials
4. ใช้ exact replay สองเคสจาก H-A2.60 เป็น sanity check ของกลไก ไม่ใช้เป็นตัวเลือกกฎ
5. ตรวจว่าข้อมูลที่มีพอคำนวณ cost-adjusted strike reachability สำหรับ train distribution หรือไม่
6. บันทึกทุก trial ลง search log และไม่เลือก trial ใดเป็นกฎเทรด

คำสั่งตรวจหลัก:

```powershell
python scripts\run_h_a2_breakeven_aware_rule_train_diagnostic.py
python scripts\validate_h_a2_breakeven_aware_rule_train_diagnostic.py
python -m unittest tests.test_h_a2_breakeven_aware_rule_train_diagnostic
```

## 4. ผลการศึกษาและข้อมูลดิบ

| Metric | ค่า |
|---|---:|
| จำนวน train non-risk trade days | `30` |
| จำนวน surrogate train trials | `6` |
| จำนวน exact replay sanity cases | `2` |
| จำนวน exact replay ที่ไปถึง target | `0` |
| สถานะ true breakeven rule lock | `false` |
| สถานะ paid data approval | `false` |

ใน exact replay สองเคส SPY ไปถูกทิศทาง แต่ยังไม่ถึง long strike ที่ทำให้ call vertical คุ้มต้นทุน:

| Date | Entry | Close | Long strike | Required move | Realized move | Shortfall | Implementable PnL |
|---|---:|---:|---:|---:|---:|---:|---:|
| `2025-02-11` | `603.52` | `604.93` | `605.00` | `1.48` | `1.41` | `0.07` | `-26.56` |
| `2025-05-05` | `563.12` | `564.38` | `565.00` | `1.88` | `1.26` | `0.62` | `-32.56` |

Surrogate train trials แสดงภาพเบื้องต้นว่า followthrough ที่แรงขึ้นสัมพันธ์กับผลลัพธ์ train ที่ดีขึ้น แต่ยังเป็นเพียงตัวแทน ไม่ใช่กฎ option ที่ใช้ได้จริง:

| Trial | Train days | Avg implementable PnL | Loss rate |
|---|---:|---:|---:|
| baseline non-risk | `30` | `19.306667` | `0.633333` |
| followthrough >= `0` | `17` | `61.616471` | `0.352941` |
| followthrough >= `0.001` | `16` | `67.44` | `0.3125` |
| followthrough >= `0.002` | `15` | `73.706667` | `0.266667` |
| followthrough >= `0.003` | `13` | `86.132308` | `0.230769` |
| followthrough >= `0.005` | `8` | `131.815` | `0.0` |

ตัวเลขเหล่านี้บอกว่าปัญหาน่าขุดต่อ แต่ไม่อนุญาตให้เลือก threshold เพราะข้อมูลที่ใช้ยังไม่รู้ว่าแต่ละวัน option spread จริงมี strike gap, debit, bid/ask และ liquidity อย่างไร

## 5. ปัญหา อุปสรรค และการแก้ไข

ข้อจำกัดหลักคือข้อมูล train ที่มีตอนนี้ยังไม่ใช่ข้อมูล payoff geometry ของ option ที่ครบพอ มันมีผลลัพธ์รวมและ proxy ของ underlying แต่ไม่มี field สำคัญที่ต้องใช้ล็อกกฎแบบ `breakeven-aware`

สิ่งที่ยังขาด:

- long strike และ short strike ที่เลือกใน train distribution
- entry mid debit และ entry implementable debit
- bid/ask width ตอนเข้า trade
- quote size หรือ liquidity proxy ตอนเข้า trade
- forced-close spread value ที่เทียบกับ entry cost ได้ครบทุก train candidate
- regime coverage ที่พอคำนวณ `MinTRL` และ `PSR`

สิ่งที่ห้ามสรุปจากรอบนี้:

- ห้ามสรุปว่า H-A2 ผ่าน
- ห้ามสรุปว่า threshold `0.005` เป็นกฎที่ควรเทรด
- ห้ามบอกว่าพร้อม `paper trading`
- ห้ามซื้อข้อมูลกว้าง ๆ โดยไม่ระบุ field/window/regime ที่ต้องการ

## 6. ข้อสรุปและก้าวต่อไป

ข้อสรุป: `ยังสรุปไม่ได้` เพราะ H-A2.62 ยืนยันว่ากรอบ breakeven-aware ถูกทางกว่าเดิม แต่ข้อมูล local train ที่มีอยู่ยังไม่พอสำหรับล็อกกฎ option จริง

สิ่งที่ควรทำต่อคือ H-A2.63: pre-register targeted data/regime expansion plan โดยระบุให้ชัดว่าจะต้องใช้ข้อมูล option-chain field ไหน เวลาไหน และ regime ไหน เพื่อคำนวณ entry strike mapping, entry debit, bid/ask width, liquidity, forced-close value และ sample adequacy ก่อนซื้อข้อมูลหรือทดสอบ OOS เพิ่ม
