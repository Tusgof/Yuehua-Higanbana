# Databento Pilot PnL Report

## สถานะ
- ข้อสรุป: ยังสรุปไม่ได้
- ประเภทหลักฐาน: pilot PnL หนึ่งเดือน จำนวน trade ต่ำมาก ยังไม่ใช่หลักฐานว่า strategy มี edge
- Entry: limit-at-mid model
- Exit: forced close 15:45 ET ใช้ bid/ask liquidation price
- Fee per contract: `0.0`
- Fill model: `mid`
- Close fallback: `strict_1545`
- Exit model: `forced_close_only`

## Metrics
```json
{
  "average_net_pnl": -0.5,
  "best_trade": 1.0,
  "candidate_days": 2,
  "closed_trades": 2,
  "max_drawdown": -0.001998,
  "sharpe_proxy": -0.333333,
  "skipped_trades": 0,
  "total_net_pnl": -1.0,
  "win_rate": 0.5,
  "worst_trade": -2.0
}
```

## Status Counts
```json
{
  "closed_forced_1545": 2
}
```

## ข้อจำกัด
- ใช้ข้อมูล pilot window เท่านั้น จึงต่ำกว่าเกณฑ์ N >= 500 มาก
- ยังไม่รวม VIX/VXV, macro, news/LLM gate, target/stop intraday และ fill retry
- วันที่ไม่มี close quote ครบถูก skip ไม่เติมราคาแทนเอง
- ค่า commission ตั้งเป็น 0 ในรอบนี้เพื่อไม่แอบสมมติ broker fee; ต้องทำ sensitivity ต่อ
