# Databento Pilot PnL Report

## สถานะ
- ข้อสรุป: ยังสรุปไม่ได้
- ประเภทหลักฐาน: pilot PnL หนึ่งเดือน จำนวน trade ต่ำมาก ยังไม่ใช่หลักฐานว่า strategy มี edge
- Entry: limit-at-mid model
- Exit: forced close 15:45 ET ใช้ bid/ask liquidation price
- Fee per contract: `0.0`
- Fill model: `mid`
- Close fallback: `strict_1545`
- Exit model: `target_stop_25_50`

## Metrics
```json
{
  "average_net_pnl": 3.8333,
  "best_trade": 27.0,
  "candidate_days": 6,
  "closed_trades": 6,
  "max_drawdown": -0.04931,
  "sharpe_proxy": 0.178123,
  "skipped_trades": 0,
  "total_net_pnl": 23.0,
  "win_rate": 0.6667,
  "worst_trade": -34.0
}
```

## Status Counts
```json
{
  "closed_profit_target_25pct": 4,
  "closed_stop_loss_50pct": 2
}
```

## ข้อจำกัด
- ใช้ข้อมูล pilot window เท่านั้น จึงต่ำกว่าเกณฑ์ N >= 500 มาก
- ยังไม่รวม VIX/VXV, macro, news/LLM gate, target/stop intraday และ fill retry
- วันที่ไม่มี close quote ครบถูก skip ไม่เติมราคาแทนเอง
- ค่า commission ตั้งเป็น 0 ในรอบนี้เพื่อไม่แอบสมมติ broker fee; ต้องทำ sensitivity ต่อ
