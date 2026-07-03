# Jan 2024 Pilot PnL Report

## สถานะ
- ข้อสรุป: ยังสรุปไม่ได้
- ประเภทหลักฐาน: pilot PnL หนึ่งเดือน จำนวน trade ต่ำมาก ยังไม่ใช่หลักฐานว่า strategy มี edge
- Entry: limit-at-mid model
- Exit: forced close 15:45 ET ใช้ bid/ask liquidation price
- Fee per contract: `0.0`

## Metrics
```json
{
  "average_net_pnl": 67.5,
  "best_trade": 150.0,
  "candidate_days": 6,
  "closed_trades": 4,
  "max_drawdown": -0.019305,
  "sharpe_proxy": 0.965444,
  "skipped_trades": 2,
  "total_net_pnl": 270.0,
  "win_rate": 0.75,
  "worst_trade": -25.0
}
```

## Status Counts
```json
{
  "closed_forced_1545": 4,
  "missing_quotes": 2
}
```

## ข้อจำกัด
- ใช้ข้อมูล Jan 2024 เท่านั้น จึงต่ำกว่าเกณฑ์ N >= 500 มาก
- ยังไม่รวม VIX/VXV, macro, news/LLM gate, target/stop intraday และ fill retry
- วันที่ไม่มี close quote ครบถูก skip ไม่เติมราคาแทนเอง
- ค่า commission ตั้งเป็น 0 ในรอบนี้เพื่อไม่แอบสมมติ broker fee; ต้องทำ sensitivity ต่อ
