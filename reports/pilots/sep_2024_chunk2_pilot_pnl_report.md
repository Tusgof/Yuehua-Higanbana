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
  "average_net_pnl": -56.5,
  "best_trade": -56.5,
  "candidate_days": 1,
  "closed_trades": 1,
  "max_drawdown": -0.0565,
  "sharpe_proxy": null,
  "skipped_trades": 0,
  "total_net_pnl": -56.5,
  "win_rate": 0.0,
  "worst_trade": -56.5
}
```

## Status Counts
```json
{
  "closed_forced_1545": 1
}
```

## ข้อจำกัด
- ใช้ข้อมูล pilot window เท่านั้น จึงต่ำกว่าเกณฑ์ N >= 500 มาก
- ยังไม่รวม VIX/VXV, macro, news/LLM gate, target/stop intraday และ fill retry
- วันที่ไม่มี close quote ครบถูก skip ไม่เติมราคาแทนเอง
- ค่า commission ตั้งเป็น 0 ในรอบนี้เพื่อไม่แอบสมมติ broker fee; ต้องทำ sensitivity ต่อ
