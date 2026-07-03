# Databento Pilot Adapter Report

## สถานะ
- ข้อสรุป: ยังสรุปไม่ได้
- ประเภทหลักฐาน: data-join pilot หนึ่งเดือน ไม่ใช่ผล backtest ที่พิสูจน์ edge
- Coverage: 2023-05-01 to 2023-05-31
- SPY bar rows: 12110
- Option quote rows: 850098
- Candidate-ready days: 1 / 22

## Status Counts
```json
{
  "candidate_ready": 1,
  "no_trade": 21
}
```

## ความหมาย
- `candidate_ready` หมายถึงมี RTH SPY bars, มี ORB breakout/no-breakout logic, มี option quotes ที่เวลา entry, และประกอบ Sub-System A vertical ได้
- รายงานนี้ยังไม่คำนวณ PnL, fill, slippage, stop, forced close, Sharpe, หรือ drawdown
- ขั้นถัดไปคือใช้ candidate-ready days ไปต่อกับ fill/backtest engine แบบ bid/ask จริง
