# M4.3 Exit Behavior Diagnostic

## สถานะ
- ข้อสรุป: ยังสรุปไม่ได้
- ประเภทหลักฐาน: diagnostic บนข้อมูลจริง ไม่ใช่การเลือกพารามิเตอร์เพื่อใช้งานจริง
- เหตุผล: Target/stop diagnostics improved some OOS metrics, but the report is under-sampled and OOS results are not allowed as tuning input.

## วิธีทดสอบ
```json
{
  "chronological_policy": "2023-03-01..2023-12-29 in-sample, 2024-01-02..2024-12-31 OOS; no OOS tuning from this diagnostic report",
  "close_fallback": "nearest_1545_window",
  "diagnostic_scope": "Compare two pre-existing exit behaviors on identical Sub-System A candidate days.",
  "entry_model": "limit-style entry priced by fill model; no entry market orders",
  "exit_models": [
    "forced_close_only",
    "target_stop_25_50"
  ],
  "fee_per_contract": 0.64,
  "fill_model": "half_spread",
  "llm_filter": "disabled",
  "news_filter": "disabled",
  "not_parameter_optimization": true,
  "selection_policy": "Do not select a live exit model from this OOS diagnostic; use it to decide the next pre-registered hypothesis only.",
  "strike_mapping": "nearest discrete strike selection inherited from generated strategy legs"
}
```

## ผลรวม

| Exit model | Closed | Implementable PnL | Mid PnL | Cost drag | Sharpe proxy | Max DD | Worst day | Exit reasons |
|:--|--:|--:|--:|--:|--:|--:|--:|:--|
| `forced_close_only` | 90 | 545.6 | 1089.5 | 543.9 | 0.118064 | -0.370769 | -62.56 | `{"forced_1545": 90}` |
| `target_stop_25_50` | 93 | 108.92 | 542.0 | 433.08 | 0.063578 | -0.092626 | -37.56 | `{"profit_target_25pct": 63, "stop_loss_50pct": 30}` |

## OOS Delta
```json
{
  "base_exit_model": "forced_close_only",
  "challenger_exit_model": "target_stop_25_50",
  "cost_drag_delta": -77.88,
  "implementable_pnl_delta": 211.88,
  "max_drawdown_delta": 0.479293,
  "mid_pnl_delta": 134.0,
  "sharpe_proxy_delta": 0.100728,
  "trade_count_delta": 2,
  "worst_day_loss_delta": 26.0
}
```

## Split Metrics
### `forced_close_only`

| Split | Closed | PnL | Sharpe proxy | Max DD | Worst day | Labels |
|:--|--:|--:|--:|--:|--:|:--|
| `in_sample` | 41 | 624.04 | 0.226229 | -0.170819 | -57.56 | under-sampled, underpowered |
| `oos` | 49 | -78.44 | 0.01581 | -0.550922 | -62.56 | under-sampled, underpowered |

### `target_stop_25_50`

| Split | Closed | PnL | Sharpe proxy | Max DD | Worst day | Labels |
|:--|--:|--:|--:|--:|--:|:--|
| `in_sample` | 42 | -24.52 | -0.028533 | -0.092626 | -37.56 | under-sampled, underpowered |
| `oos` | 51 | 133.44 | 0.116538 | -0.071629 | -36.56 | under-sampled, underpowered |

## Sample Adequacy
```json
{
  "closed_trades": 90,
  "labels": [
    "under-sampled",
    "underpowered"
  ],
  "minimum_trade_count_prior": 500,
  "mintrl_status": "pending_return_distribution",
  "power_note": "Point Sharpe is diagnostic only until MinTRL/PSR are calculated on an experiment return distribution.",
  "psr_status": "pending_return_distribution"
}
```

## Big-Day Dependency
### `forced_close_only`
```json
{
  "method": "remove_top_and_bottom_5pct_by_implementable_pnl",
  "original_closed_trades": 90,
  "original_sharpe_proxy": 0.092203,
  "original_total_implementable_pnl": 545.6,
  "removed_each_side": 5,
  "removed_trade_count": 10,
  "retained_closed_trades": 80,
  "retained_sharpe_proxy": 0.013201,
  "retained_total_implementable_pnl": 59.2,
  "status": "pass"
}
```
### `target_stop_25_50`
```json
{
  "method": "remove_top_and_bottom_5pct_by_implementable_pnl",
  "original_closed_trades": 93,
  "original_sharpe_proxy": 0.053941,
  "original_total_implementable_pnl": 108.92,
  "removed_each_side": 5,
  "removed_trade_count": 10,
  "retained_closed_trades": 83,
  "retained_sharpe_proxy": 0.015908,
  "retained_total_implementable_pnl": 19.52,
  "status": "pass"
}
```

## DSR
```json
{
  "reason": "This diagnostic compares two pre-specified exit behaviors and does not select a best Sharpe for deployment.",
  "selected_for_deployment": null,
  "status": "not_applicable",
  "trial_count": 2
}
```

## ข้อจำกัด
- ผลนี้ยัง `under-sampled` และ `underpowered` จึงห้ามใช้ยืนยัน edge หรือเลือก exit model สำหรับ live
- OOS ใช้เป็นหลักฐานวินิจฉัยเท่านั้น ไม่ใช้ tune พารามิเตอร์
- ถ้าจะทดสอบ target/stop ต่อ ต้องตั้งสมมติฐานใหม่ล่วงหน้าและมี search log/DSR discipline
