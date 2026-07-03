# Databento Pilot Adapter Report

## สถานะ
- ข้อสรุป: ยังสรุปไม่ได้
- ประเภทหลักฐาน: data-join pilot หนึ่งเดือน ไม่ใช่ผล backtest ที่พิสูจน์ edge
- Coverage: 2024-06-03 to 2024-06-28
- SPY bar rows: 9878
- Option quote rows: 685963
- Candidate-ready days: 5 / 19

## Status Counts
```json
{
  "candidate_ready": 5,
  "no_trade": 14
}
```

## ความหมาย
- `candidate_ready` หมายถึงมี RTH SPY bars, มี ORB breakout/no-breakout logic, มี option quotes ที่เวลา entry, และประกอบ Sub-System A vertical ได้
- รายงานนี้ยังไม่คำนวณ PnL, fill, slippage, stop, forced close, Sharpe, หรือ drawdown
- ขั้นถัดไปคือใช้ candidate-ready days ไปต่อกับ fill/backtest engine แบบ bid/ask จริง
