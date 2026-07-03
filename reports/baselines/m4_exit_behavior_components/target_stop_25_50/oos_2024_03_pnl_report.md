# Databento Pilot PnL Report

## Status
- Conclusion: Inconclusive
- Evidence type: real-data pilot PnL, still far below acceptance-grade trade count.
- Entry: limit-at-mid model
- Exit: forced close 15:45 ET uses bid/ask liquidation price for `implementable_pnl`
- Fee per contract: `0.64`
- Fill model: `half_spread`
- Close fallback: `nearest_1545_window`
- Exit model: `target_stop_25_50`

## Metrics
```json
{
  "average_net_pnl": -1.56,
  "best_trade": 12.44,
  "candidate_days": 4,
  "closed_trades": 4,
  "max_drawdown": -0.031725,
  "sharpe_proxy": -0.086334,
  "skipped_trades": 0,
  "total_cost_drag": 18.24,
  "total_implementable_pnl": -6.24,
  "total_mid_pnl": 12.0,
  "win_rate": 0.75,
  "worst_trade": -32.56
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
  "closed_trades": 4,
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
  "original_closed_trades": 4,
  "original_sharpe_proxy": -0.086334,
  "original_total_implementable_pnl": -6.24,
  "removed_each_side": 1,
  "removed_trade_count": 2,
  "retained_closed_trades": 2,
  "retained_sharpe_proxy": 4.626667,
  "retained_total_implementable_pnl": 13.88,
  "status": "pass"
}
```

## Status Counts
```json
{
  "closed_profit_target_25pct": 3,
  "closed_stop_loss_50pct": 1
}
```

## Limitations
- Uses only this pilot window, so it remains far below N >= 500.
- MinTRL/PSR stay `pending` until a real experiment return distribution exists.
- Does not yet include VIX/VXV, macro, news/LLM gate, target/stop intraday, or fill retry.
- Days without complete close quotes are skipped rather than filled with invented prices.
