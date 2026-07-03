# Higanbana Multimonth Pilot Summary

## สถานะ
- Split: `in_sample`
- ช่วงข้อมูล: `2023-07-03` ถึง `2023-12-29`
- ข้อสรุป: ยังสรุปไม่ได้
- ความหมาย: นี่เป็นการรวมผล pilot หลายเดือนเพื่อดูภาพรวมก่อนโหลดข้อมูลเพิ่ม ยังไม่ใช่หลักฐานยืนยัน edge

## Adapter Totals
```json
{
  "bar_rows": 64643,
  "calendar_days": 126,
  "candidate_ready_days": 27,
  "quote_rows": 4841537,
  "status_counts": {
    "candidate_ready": 27,
    "no_trade": 99
  }
}
```

## PnL Models
### `forced_close_only`
```json
{
  "average_net_pnl": 18.9231,
  "best_trade": 170.0,
  "candidate_days": 27,
  "closed_trades": 26,
  "exit_model": "forced_close_only",
  "max_drawdown": -0.170511,
  "sharpe_proxy": 0.267506,
  "skipped_trades": 1,
  "status_counts": {
    "closed_forced_1545": 26,
    "missing_quotes": 1
  },
  "total_net_pnl": 492.0,
  "win_rate": 0.3846,
  "worst_trade": -54.0
}
```

### `target_stop_25_50`
```json
{
  "average_net_pnl": -0.037,
  "best_trade": 27.0,
  "candidate_days": 27,
  "closed_trades": 27,
  "exit_model": "target_stop_25_50",
  "max_drawdown": -0.063953,
  "sharpe_proxy": -0.002433,
  "skipped_trades": 0,
  "status_counts": {
    "closed_profit_target_25pct": 16,
    "closed_stop_loss_50pct": 11
  },
  "total_net_pnl": -1.0,
  "win_rate": 0.5926,
  "worst_trade": -34.0
}
```

## ข้อจำกัด
- จำนวน trade ยังต่ำกว่าเกณฑ์ N >= 500 มาก จึงยังสรุประบบไม่ได้
- ผลนี้รวมเฉพาะ Sub-System A pilot ที่มีข้อมูล Databento ครบแล้ว
- ยังไม่รวม VIX/VXV, macro, news/LLM gate, Sub-System B, และ fill retry แบบ production
- ห้ามใช้ผล OOS เพื่อ tune parameter; report นี้ตั้งใจแยก split ต่อหนึ่งไฟล์
