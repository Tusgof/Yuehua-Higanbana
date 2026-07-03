# Databento Pilot Adapter Report

## สถานะ
- ข้อสรุป: ยังสรุปไม่ได้
- ประเภทหลักฐาน: data-join pilot หนึ่งเดือน ไม่ใช่ผล backtest ที่พิสูจน์ edge
- Coverage: 2024-08-05 to 2024-08-09
- SPY bar rows: 2880
- Option quote rows: 244084
- Candidate-ready days: 0 / 5

## Status Counts
```json
{
  "no_trade": 5
}
```

## ความหมาย
- `candidate_ready` หมายถึงมี RTH SPY bars, มี ORB breakout/no-breakout logic, มี option quotes ที่เวลา entry, และประกอบ Sub-System A vertical ได้
- รายงานนี้ยังไม่คำนวณ PnL, fill, slippage, stop, forced close, Sharpe, หรือ drawdown
- ขั้นถัดไปคือใช้ candidate-ready days ไปต่อกับ fill/backtest engine แบบ bid/ask จริง
