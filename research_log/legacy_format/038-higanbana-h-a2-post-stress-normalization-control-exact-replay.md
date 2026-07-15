# บันทึกการวิจัย: H-A2 Post-Stress Normalization/Control Exact Replay

## 1. ข้อมูลพื้นฐาน

- Timestamp UTC: `2026-07-08T08:04:13Z`
- โครงการ: SPY 0DTE - Higanbana
- หัวข้อ: exact replay ของ candidate วันที่ `2025-05-05`
- ผู้บันทึก: Codex
- สถานะ: เสร็จสิ้น
- ระดับหลักฐาน: `E1`
- ข้อสรุป: `ยังสรุปไม่ได้`
- Artifact หลัก:
  - `experiments/h_a2_post_stress_normalization_control_exact_replay_preregistration.json`
  - `reports/diagnostics/h_a2_post_stress_normalization_control_exact_replay.json`
  - `reports/diagnostics/h_a2_post_stress_normalization_control_exact_replay.md`
  - `reports/diagnostics/search_logs/h_a2_post_stress_normalization_control_exact_replay_search_log.jsonl`

## 2. วัตถุประสงค์

### อ่านแบบเร็ว

รอบนี้ถามว่า candidate วันที่ `2025-05-05` ซึ่งได้จาก post-stress normalization/control pack ถ้านำมาทำ exact replay ตามกฎเดิมของ H-A2 จะออกมาเป็นกำไรหรือขาดทุน

ผลคือ trade นี้ขาดทุนทั้งแบบ `mid_pnl` และ `implementable_pnl` โดย `implementable_pnl = -32.56` ดอลลาร์ หลังรวม bid/ask และค่าธรรมเนียมแล้ว

ผลนี้ยังไม่ได้แปลว่า H-A2 ล้มเหลวทั้งหมด เพราะมีตัวอย่างแค่ 1 trade แต่ก็เป็นสัญญาณลบอีกจุดหนึ่งที่บอกว่า candidate ที่ผ่าน filter ไม่ได้แปลว่าจะทำกำไรเสมอ

คำถามของรอบนี้ไม่ใช่ “H-A2 มี edge หรือยัง” แต่เป็น “candidate ใหม่หนึ่งวันที่ผ่านกฎล็อกเดิม เมื่อลงรายละเอียดถึง option legs จริงแล้ว ผลเทรดเป็นอย่างไร”

## 3. วิธีการและขั้นตอน

1. ตรวจ preregistration ของ H-A2.56 ก่อนรัน replay
2. ใช้เฉพาะข้อมูล local ที่ดาวน์โหลดไว้แล้วใน `post_stress_normalization_control_pack`
3. ใช้ candidate date เดียวคือ `2025-05-05`
4. คงกฎเดิมไว้ทั้งหมด: decision time `09:35 ET`, threshold `0.001`, forced close `15:45 ET`
5. เลือก strike ด้วยวิธี nearest discrete strike rounding
6. แยกผลเป็น `mid_pnl` และ `implementable_pnl`
7. รวมค่าธรรมเนียม `$0.64` ต่อ leg และไม่ใช้ข้อมูลเพิ่มจาก API, IBKR, LLM หรือ GDELT

คำสั่งตรวจหลัก:

```powershell
python scripts\validate_h_a2_post_stress_normalization_control_exact_replay_preregistration.py
python scripts\run_h_a2_post_stress_normalization_control_exact_replay.py
python scripts\validate_h_a2_post_stress_normalization_control_exact_replay.py
python -m unittest tests.test_h_a2_post_stress_normalization_control_exact_replay
```

## 4. ผลการศึกษาและข้อมูลดิบ

| Metric | ค่า |
|---|---:|
| Candidate date | `2025-05-05` |
| Direction | `call` |
| Entry time | `09:35 ET` |
| Forced close | `15:45 ET` |
| Underlying at entry | `563.12` |
| Underlying at forced close | `564.38` |
| Long call strike | `565` |
| Short call strike | `567` |
| Entry mid debit | `0.55` |
| Forced-close mid value | `0.27` |
| `mid_pnl` | `-28.00` |
| Entry implementable debit | `0.56` |
| Forced-close implementable credit | `0.26` |
| Gross implementable PnL before fees | `-30.00` |
| Total fees | `2.56` |
| `implementable_pnl` | `-32.56` |
| Cost drag vs mid | `4.56` |
| Sample count | `1` |

วันที่ `2025-05-05` ราคา SPY ขยับขึ้นจากระดับ entry ไปถึง forced close แต่ call spread ที่เลือกจริงยังขาดทุน เพราะ long call และ short call เสื่อมค่าลงเมื่อเทียบกับราคาเข้า ผลลัพธ์จึงบอกว่า “ทิศทางของ underlying ถูกทาง” ไม่เพียงพอสำหรับกำไรของ option spread หาก timing, strike และ premium movement ไม่สนับสนุน

ต้นทุนจริงทำให้ผลแย่กว่า mid อีก `4.56` ดอลลาร์ นี่เป็นเหตุผลที่ระบบต้องแยก `mid_pnl` ออกจาก `implementable_pnl` เสมอ เพราะตัวเลข mid ดูดีกว่าผลที่เทรดได้จริง

## 5. ปัญหา อุปสรรค และการแก้ไข

ข้อจำกัดใหญ่ที่สุดคือรอบนี้มีเพียง 1 trade จึงเป็น `under-sampled` และ `underpowered` อย่างชัดเจน ยังไม่สามารถคำนวณ MinTRL/PSR เพื่อยืนยัน edge ได้อย่างมีน้ำหนัก

สิ่งที่ห้ามสรุปจากรอบนี้:

- ห้ามบอกว่า H-A2 ผ่านหรือมี edge แล้ว
- ห้ามบอกว่า H-A2 ล้มเหลวทั้งหมดจาก trade เดียว
- ห้ามอ้าง `E2` หรือ acceptance-grade evidence
- ห้ามอนุมัติ `paper trading`, operational validation หรือ real-money trading
- ห้ามเปลี่ยน threshold `0.001` หรือเพิ่ม filter ใหม่จากผลของ trade นี้
- ห้ามซื้อข้อมูลเพิ่มแบบกว้างโดยไม่มีคำถามวิจัยและแผน sample/regime ที่ชัดเจน

สิ่งที่รอบนี้ช่วยให้เห็นคือ candidate จาก sample expansion สองชุดล่าสุดยังไม่ได้ให้ภาพที่ดี: normal/control candidate `2025-02-11` ขาดทุน และ post-stress normalization/control candidate `2025-05-05` ก็ขาดทุนเช่นกัน

## 6. ข้อสรุปและก้าวต่อไป

ข้อสรุป: `ยังสรุปไม่ได้` เพราะ trade เดียวไม่พอพิสูจน์หรือฆ่าสมมติฐาน H-A2 แต่ผลของ candidate นี้เป็นลบ และควรถูกนับเป็นหลักฐาน E1 ที่ทำให้เราต้องระวังมากขึ้น

เมื่อรวมกับ exact replay ก่อนหน้า ภาพที่เริ่มเห็นคือกฎ H-A2 ที่ล็อกไว้ยังหา candidate ได้น้อย และ candidate ที่ replay แล้วสองครั้งยังขาดทุนหลังต้นทุนจริงทั้งคู่ นี่ไม่ได้จบสมมติฐาน แต่บอกว่าขั้นต่อไปควรตั้งคำถามให้คมขึ้นว่า filter ปัจจุบันเลือกวันที่ดีจริงหรือแค่เลือกวันที่ข้อมูลพร้อม

ก้าวต่อไป:

1. รวมผล exact replay ของ `2025-02-11` และ `2025-05-05` เป็น decision artifact แบบสั้น เพื่อเลือกว่าจะ sample expansion ต่อหรือ revise hypothesis ก่อน
2. ถ้าจะซื้อข้อมูลเพิ่ม ต้องผูกกับคำถามเรื่อง sample size และ market regime โดยตรง ไม่ใช่ซื้อเพิ่มเพื่อหวังให้ N โตอย่างเดียว
3. ถ้าจะ revise hypothesis ต้องระบุให้ชัดว่า ORB ต้องการ regime แบบไหน และอะไรจะทำให้สมมติฐานถูก falsify
