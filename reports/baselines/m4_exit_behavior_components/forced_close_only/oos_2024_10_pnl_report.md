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
  "average_net_pnl": 63.94,
  "best_trade": 114.44,
  "candidate_days": 2,
  "closed_trades": 2,
  "max_drawdown": 0.0,
  "sharpe_proxy": 1.266139,
  "skipped_trades": 0,
  "total_cost_drag": 11.62,
  "total_implementable_pnl": 127.88,
  "total_mid_pnl": 139.5,
  "win_rate": 1.0,
  "worst_trade": 13.44
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
  "closed_trades": 2,
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
  "note": "Need at least 3 closed trades to remove both best and worst trades.",
  "removed_trade_count": 0,
  "status": "insufficient_trades"
}
```

## Status Counts
```json
{
  "closed_forced_1545": 2
}
```

## Limitations
- Uses only this pilot window, so it remains far below N >= 500.
- MinTRL/PSR stay `pending` until a real experiment return distribution exists.
- Does not yet include VIX/VXV, macro, news/LLM gate, target/stop intraday, or fill retry.
- Days without complete close quotes are skipped rather than filled with invented prices.
