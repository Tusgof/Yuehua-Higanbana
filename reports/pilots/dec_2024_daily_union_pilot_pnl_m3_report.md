# Databento Pilot PnL Report

## Status
- Conclusion: Inconclusive
- Evidence type: real-data pilot PnL, still far below acceptance-grade trade count.
- Entry: limit-at-mid model
- Exit: forced close 15:45 ET uses bid/ask liquidation price for `implementable_pnl`
- Fee per contract: `0.64`
- Fill model: `half_spread`
- Close fallback: `nearest_1545_window`
- Exit model: `forced_close_only`

## Metrics
```json
{
  "average_net_pnl": 72.7733,
  "best_trade": 121.44,
  "candidate_days": 3,
  "closed_trades": 3,
  "max_drawdown": -0.00756,
  "sharpe_proxy": 1.271669,
  "skipped_trades": 0,
  "total_cost_drag": 60.68,
  "total_implementable_pnl": 218.32,
  "total_mid_pnl": 279.0,
  "win_rate": 0.6667,
  "worst_trade": -7.56
}
```

## PnL Model
```json
{
  "fee_per_contract_per_side": 0.64,
  "implementable_pnl": "Entry uses configured fill_model; exit liquidates longs at bid and shorts at ask; fees are subtracted.",
  "mid_pnl": "Entry and exit at mid price, with no fees; comparison control only."
}
```

## Sample Adequacy
```json
{
  "closed_trades": 3,
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

## Big-Day Dependency Check
```json
{
  "method": "remove_top_and_bottom_5pct_by_implementable_pnl",
  "original_closed_trades": 3,
  "original_sharpe_proxy": 1.271669,
  "original_total_implementable_pnl": 218.32,
  "removed_each_side": 1,
  "removed_trade_count": 2,
  "retained_closed_trades": 1,
  "retained_sharpe_proxy": null,
  "retained_total_implementable_pnl": 104.44,
  "status": "pass"
}
```

## Status Counts
```json
{
  "closed_forced_1545": 3
}
```

## Limitations
- Uses only this pilot window, so it remains far below N >= 500.
- MinTRL/PSR stay `pending` until a real experiment return distribution exists.
- Does not yet include VIX/VXV, macro, news/LLM gate, target/stop intraday, or fill retry.
- Days without complete close quotes are skipped rather than filled with invented prices.
