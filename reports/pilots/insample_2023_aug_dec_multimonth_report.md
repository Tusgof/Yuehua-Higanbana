# Higanbana Multimonth Pilot Summary

## สถานะ
- Split: `in_sample`
- ช่วงข้อมูล: `2023-08-01` ถึง `2023-12-29`
- ข้อสรุป: ยังสรุปไม่ได้
- ความหมาย: นี่เป็นการรวมผล pilot หลายเดือนเพื่อดูภาพรวมก่อนโหลดข้อมูลเพิ่ม ยังไม่ใช่หลักฐานยืนยัน edge

## Adapter Totals
```json
{
  "bar_rows": 54316,
  "calendar_days": 106,
  "candidate_ready_days": 22,
  "quote_rows": 4093396,
  "status_counts": {
    "candidate_ready": 22,
    "no_trade": 84
  }
}
```

## PnL Models
### `forced_close_only`
```json
{
  "average_net_pnl": 14.0,
  "best_trade": 155.0,
  "candidate_days": 22,
  "closed_trades": 22,
  "exit_model": "forced_close_only",
  "max_drawdown": -0.200971,
  "sharpe_proxy": 0.2028,
  "skipped_trades": 0,
  "status_counts": {
    "closed_forced_1545": 22
  },
  "total_net_pnl": 308.0,
  "win_rate": 0.3182,
  "worst_trade": -54.0
}
```

### `target_stop_25_50`
```json
{
  "average_net_pnl": -0.6364,
  "best_trade": 27.0,
  "candidate_days": 22,
  "closed_trades": 22,
  "exit_model": "target_stop_25_50",
  "max_drawdown": -0.064769,
  "sharpe_proxy": -0.039434,
  "skipped_trades": 0,
  "status_counts": {
    "closed_profit_target_25pct": 13,
    "closed_stop_loss_50pct": 9
  },
  "total_net_pnl": -14.0,
  "win_rate": 0.5909,
  "worst_trade": -34.0
}
```

## ข้อจำกัด
- จำนวน trade ยังต่ำกว่าเกณฑ์ N >= 500 มาก จึงยังสรุประบบไม่ได้
- ผลนี้รวมเฉพาะ Sub-System A pilot ที่มีข้อมูล Databento ครบแล้ว
- ยังไม่รวม VIX/VXV, macro, news/LLM gate, Sub-System B, และ fill retry แบบ production
- ห้ามใช้ผล OOS เพื่อ tune parameter; report นี้ตั้งใจแยก split ต่อหนึ่งไฟล์
