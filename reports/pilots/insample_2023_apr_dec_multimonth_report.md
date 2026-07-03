# Higanbana Multimonth Pilot Summary

## สถานะ
- Split: `in_sample`
- ช่วงข้อมูล: `2023-04-03` ถึง `2023-12-29`
- ข้อสรุป: ยังสรุปไม่ได้
- ความหมาย: นี่เป็นการรวมผล pilot หลายเดือนเพื่อดูภาพรวมก่อนโหลดข้อมูลเพิ่ม ยังไม่ใช่หลักฐานยืนยัน edge

## Adapter Totals
```json
{
  "bar_rows": 98399,
  "calendar_days": 188,
  "candidate_ready_days": 42,
  "quote_rows": 7223984,
  "status_counts": {
    "candidate_ready": 42,
    "no_trade": 146
  }
}
```

## PnL Models
### `forced_close_only`
```json
{
  "average_net_pnl": 18.7805,
  "best_trade": 170.0,
  "candidate_days": 42,
  "closed_trades": 41,
  "exit_model": "forced_close_only",
  "max_drawdown": -0.13874,
  "sharpe_proxy": 0.266964,
  "skipped_trades": 1,
  "status_counts": {
    "closed_forced_1545": 41,
    "missing_quotes": 1
  },
  "total_net_pnl": 770.0,
  "win_rate": 0.3659,
  "worst_trade": -54.0
}
```

### `target_stop_25_50`
```json
{
  "average_net_pnl": 1.0238,
  "best_trade": 27.0,
  "candidate_days": 42,
  "closed_trades": 42,
  "exit_model": "target_stop_25_50",
  "max_drawdown": -0.06568,
  "sharpe_proxy": 0.067885,
  "skipped_trades": 0,
  "status_counts": {
    "closed_profit_target_25pct": 27,
    "closed_stop_loss_50pct": 15
  },
  "total_net_pnl": 43.0,
  "win_rate": 0.6429,
  "worst_trade": -34.0
}
```

## ข้อจำกัด
- จำนวน trade ยังต่ำกว่าเกณฑ์ N >= 500 มาก จึงยังสรุประบบไม่ได้
- ผลนี้รวมเฉพาะ Sub-System A pilot ที่มีข้อมูล Databento ครบแล้ว
- ยังไม่รวม VIX/VXV, macro, news/LLM gate, Sub-System B, และ fill retry แบบ production
- ห้ามใช้ผล OOS เพื่อ tune parameter; report นี้ตั้งใจแยก split ต่อหนึ่งไฟล์
