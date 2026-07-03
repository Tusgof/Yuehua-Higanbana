# Higanbana Multimonth Pilot Summary

## สถานะ
- Split: `in_sample`
- ช่วงข้อมูล: `2023-09-01` ถึง `2023-12-29`
- ข้อสรุป: ยังสรุปไม่ได้
- ความหมาย: นี่เป็นการรวมผล pilot หลายเดือนเพื่อดูภาพรวมก่อนโหลดข้อมูลเพิ่ม ยังไม่ใช่หลักฐานยืนยัน edge

## Adapter Totals
```json
{
  "bar_rows": 42401,
  "calendar_days": 83,
  "candidate_ready_days": 16,
  "quote_rows": 3235766,
  "status_counts": {
    "candidate_ready": 16,
    "no_trade": 67
  }
}
```

## PnL Models
### `forced_close_only`
```json
{
  "average_net_pnl": 22.6875,
  "best_trade": 155.0,
  "candidate_days": 16,
  "closed_trades": 16,
  "exit_model": "forced_close_only",
  "max_drawdown": -0.122877,
  "sharpe_proxy": 0.2947,
  "skipped_trades": 0,
  "status_counts": {
    "closed_forced_1545": 16
  },
  "total_net_pnl": 363.0,
  "win_rate": 0.375,
  "worst_trade": -54.0
}
```

### `target_stop_25_50`
```json
{
  "average_net_pnl": -0.9375,
  "best_trade": 27.0,
  "candidate_days": 16,
  "closed_trades": 16,
  "exit_model": "target_stop_25_50",
  "max_drawdown": -0.055556,
  "sharpe_proxy": -0.05452,
  "skipped_trades": 0,
  "status_counts": {
    "closed_profit_target_25pct": 9,
    "closed_stop_loss_50pct": 7
  },
  "total_net_pnl": -15.0,
  "win_rate": 0.5625,
  "worst_trade": -34.0
}
```

## ข้อจำกัด
- จำนวน trade ยังต่ำกว่าเกณฑ์ N >= 500 มาก จึงยังสรุประบบไม่ได้
- ผลนี้รวมเฉพาะ Sub-System A pilot ที่มีข้อมูล Databento ครบแล้ว
- ยังไม่รวม VIX/VXV, macro, news/LLM gate, Sub-System B, และ fill retry แบบ production
- ห้ามใช้ผล OOS เพื่อ tune parameter; report นี้ตั้งใจแยก split ต่อหนึ่งไฟล์
