# NEXT_USER_INPUTS.md

## Current State

สถานะนี้อ้างอิงจาก `PROJECT_BRAIN.md`, `IMPLEMENT_PLAN.md`, `scripts\audit_paid_costs.py`, `scripts\audit_research_logs.py`, และ `scripts\audit_research_readiness.py` ล่าสุด ณ 2026-07-06

- โปรเจกต์ใช้ `hypothesis-led execution`: เลข experiment เป็นตัวอ้างอิง ไม่ใช่ลำดับบังคับ
- Research log ต่อเนื่องครบ `001` ถึง `033`
- log ล่าสุดที่ push แล้วคือ `033-higanbana-h-a2-independent-validation-feasibility.md`
- prefix ถัดไปสำหรับ completed real experiment คือ `034-higanbana-`
- conclusion labels ที่ใช้ในรายงานคือ `ผ่าน`, `ไม่ผ่าน`, และ `ยังสรุปไม่ได้`
- Current cost guard ใช้ไป `$119.989706` จาก stop threshold `$125`
- Headroom ก่อนต้องหยุดเพราะ cost guard คือ `$5.010294`
- H-A2.36 independent validation feasibility diagnostic เสร็จแล้ว เป็น E1 diagnostic evidence และยัง `ยังสรุปไม่ได้`
- ผลสำคัญของ H-A2.36:
  - rule แบบ `09:35:00` ET และ threshold `0.001` ถูกคงไว้
  - ไม่เปลี่ยน threshold
  - ไม่เพิ่ม OOS-selected filter
  - ไม่ใช้ paid data
  - ไม่ใช้ live cost estimate
  - ไม่ใช้ IBKR, exact replay, LLM, หรือ GDELT retry
  - no-paid sources ช่วยวางแผน validation gaps และ regime requirements ได้
  - no-paid sources ยังเพิ่ม independent implementable SPY 0DTE PnL days ไม่ได้
  - retained OOS ยังมีเพียง 14 trade days
  - high-VIX retained validation coverage ยังขาด
  - MinTRL/PSR acceptance ยังไม่ผ่าน
- Next safe H-A2 work คือ pre-register narrow paid-cost estimate plan สำหรับ independent validation windows
- H-A2 exact 2022-10 ORB replay ยังติด real SPY 2022-10 underlying bars
- News/LLM exact path ยังติด real timestamp-clean news cases และ GDELT cooldown/upstream response
- H-G1 ยัง parked หลัง H-G1.24a ไม่พบ no-paid local overlap เพิ่ม
- H-B2 current grid ยัง parked/not resurrected หลัง H-B2.5 falsification review
- Acceptance/operations ยัง blocked เพราะยังไม่มี strategy hypothesis ระดับ E2+

สถานะนี้ยังไม่ใช่หลักฐานว่าเจอ deployable trading edge และยังไม่อนุญาต paper trading, operational validation, หรือ real-money launch

## What The User Needs To Do Now

ยังไม่จำเป็นต้องทำอะไรทันที ถ้าจะให้ Codex เดินงานต่อในระดับ no-paid/no-network/no-broker/no-LLM

ถ้าจะเดิน exact path หรือ paid path ภายหลัง สิ่งที่ต้องเตรียมคือ:

| Input | Needed For | Why It Is Needed | When To Provide |
|:--|:--|:--|:--|
| Local TWS/Gateway API readiness | Exact H-A2 2022-10 ORB replay | ต้องใช้ real 2022-10 SPY 1-minute bars สำหรับ exact entry/exit replay | เมื่อจะ chase exact replay |
| GDELT cooldown clearance or approved news source | Exact H-L1 live news/LLM research | LLM prompt research ต้องใช้ real timestamp-clean news cases | หลัง source policy/cooldown พร้อม |
| Databento top-up or explicit paid-data direction | Any paid pull above current headroom | Current headroom เหลือ `$5.010294`; cap extension ต้องเป็น real payment ใน account เดิม | ก่อน paid pull ที่จะเกิน headroom |
| New provider direction | Alpaca/news provider/paid source fallback | New data source หรือ access method ต้องมี direction ชัดเจน | เมื่อ proxy work บอกว่า exact data ยังควร chase |
| IBKR options permission status | Paper/live operational validation | Operational validation ต้องใช้ account capability | หลัง research acceptance เข้าใกล้ E2+ |
| Email alert settings | Real alert delivery | ต้องมี SMTP/API และ recipient สำหรับ real sends | ช่วง operational validation |
| Real-money launch direction | Live trading | Hard launch gate ต้องมี explicit direction และ checklist pass | หลัง E2+ research acceptance และ operational gates ผ่านเท่านั้น |

## Safe Next Work Without User Input

- Pre-register H-A2 narrow paid-cost estimate plan สำหรับ independent validation windows
- ระบุ exact periods, required fields, regime/sample gaps, cost guard prerequisites, และ forbidden actions
- แยก paid-cost estimate planning ออกจาก live estimate/download ให้ชัด
- คง H-A2 rule แบบ `09:35:00` ET และ threshold `0.001`
- ห้าม claim delayed-entry edge จาก artifact ปัจจุบัน
- ห้าม reuse original 09:35 PnL เป็น delayed-entry PnL
- ห้ามเพิ่ม OOS-selected filter ใหม่
- ห้าม run exact replay, buy data, run live cost estimate, request IBKR bars, call LLMs, retry GDELT, approve paper trading, หรือ claim E2 จาก H-A2.36
- หลัง artifact ถัดไป ต้องรัน validators, readiness audits, paid-cost audit, research-log audit, full tests, และ fixture pipeline ตาม verification loop
- ใช้ L.7 เป็น deterministic macro/VIX baseline ที่ future real-news หรือ LLM scores ต้อง beat

## Still Blocked

- Exact H-A2 2022-10 ORB replay จนกว่าจะมี real 2022-10 SPY underlying bars
- Live GDELT retry ขณะที่ command plan ยังรายงาน cooldown และ `live_retry_allowed=false`
- H-L1 live prompt-family experiment จนกว่าจะมี real timestamp-clean news cases
- H-G1 metadata cost check, paid gamma data pull, new gamma ablation, strategy use, paper trading approval, หรือ true net-gamma claim จาก artifact ปัจจุบัน
- H-B2 new work บน current grid เว้นแต่ hypothesis ถูก revise ด้วย mechanism ใหม่หรือ user ให้ direction ชัดเจน
- Paper trading, operational validation, และ real-money launch จนกว่า E2+ research acceptance และ operational gates จะผ่าน
