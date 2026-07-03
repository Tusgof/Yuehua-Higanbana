# Higanbana Multimonth Pilot Summary

## สถานะ
- Split: `in_sample`
- ช่วงข้อมูล: `2023-05-01` ถึง `2023-12-29`
- ข้อสรุป: ยังสรุปไม่ได้
- ความหมาย: นี่เป็นการรวมผล pilot หลายเดือนเพื่อดูภาพรวมก่อนโหลดข้อมูลเพิ่ม ยังไม่ใช่หลักฐานยืนยัน edge

## Adapter Totals
```json
{
  "bar_rows": 87999,
  "calendar_days": 169,
  "candidate_ready_days": 35,
  "quote_rows": 6493122,
  "status_counts": {
    "candidate_ready": 35,
    "no_trade": 134
  }
}
```

## PnL Models
### `forced_close_only`
```json
{
  "average_net_pnl": 18.3529,
  "best_trade": 170.0,
  "candidate_days": 35,
  "closed_trades": 34,
  "exit_model": "forced_close_only",
  "max_drawdown": -0.153789,
  "sharpe_proxy": 0.261202,
  "skipped_trades": 1,
  "status_counts": {
    "closed_forced_1545": 34,
    "missing_quotes": 1
  },
  "total_net_pnl": 624.0,
  "win_rate": 0.3824,
  "worst_trade": -54.0
}
```

### `target_stop_25_50`
```json
{
  "average_net_pnl": -0.3714,
  "best_trade": 27.0,
  "candidate_days": 35,
  "closed_trades": 35,
  "exit_model": "target_stop_25_50",
  "max_drawdown": -0.069268,
  "sharpe_proxy": -0.023015,
  "skipped_trades": 0,
  "status_counts": {
    "closed_profit_target_25pct": 20,
    "closed_stop_loss_50pct": 15
  },
  "total_net_pnl": -13.0,
  "win_rate": 0.5714,
  "worst_trade": -34.0
}
```

## ข้อจำกัด
- จำนวน trade ยังต่ำกว่าเกณฑ์ N >= 500 มาก จึงยังสรุประบบไม่ได้
- ผลนี้รวมเฉพาะ Sub-System A pilot ที่มีข้อมูล Databento ครบแล้ว
- ยังไม่รวม VIX/VXV, macro, news/LLM gate, Sub-System B, และ fill retry แบบ production
- ห้ามใช้ผล OOS เพื่อ tune parameter; report นี้ตั้งใจแยก split ต่อหนึ่งไฟล์
