# M4.2 Sub-System B Put Ratio Feasibility

## Status
- Conclusion: ไม่ผ่าน
- Evidence type: real-data diagnostic feasibility and baseline, no news filter, no LLM filter.
- Closed trades: 412
- This is not acceptance-grade evidence.

## Method
```json
{
  "account_equity": 1000.0,
  "chronological_policy": "2023-03-01..2023-12-29 in-sample, 2024-01-02..2024-12-31 OOS; no OOS tuning from this report",
  "entry_time": "10:00 ET or nearest available quote at/before 10:00",
  "exit_model": "forced_close_1545",
  "fee_per_contract": 0.64,
  "llm_filter": "disabled",
  "near_moneyness": 1.0,
  "news_filter": "disabled",
  "protective_wing_gap": 10.0,
  "risk_budget_2pct": 20.0,
  "short_moneyness": 0.99,
  "strike_mapping": "nearest discrete strike rounding; wing must be at least $10 below short strike",
  "subsystem_b_allocation": 300.0
}
```

## Feasibility
```json
{
  "account_1000_feasible_count": 412,
  "all_trades_fit_1000_account": true,
  "all_trades_fit_20_risk_budget": false,
  "all_trades_fit_300_allocation": false,
  "allocation_300_feasible_count": 0,
  "checked_trades": 412,
  "max_defined_loss": 773.0,
  "median_defined_loss": 566.0,
  "min_defined_loss": 366.0,
  "risk_budget_20_feasible_count": 0
}
```

## Overall Metrics
```json
{
  "average_trade_pnl": -14.4986,
  "es95": -161.4533,
  "es99": -237.92,
  "max_drawdown": -6.202878,
  "payoff_ratio": 1.8012,
  "sharpe_proxy": 0.052955,
  "sortino_proxy": 0.747806,
  "total_cost_drag": 5115.94,
  "total_implementable_pnl": -5973.44,
  "total_mid_pnl": -857.5,
  "trade_count": 412,
  "win_rate": 0.2961,
  "worst_day_loss": -454.12
}
```

## Split Metrics

| Split | Coverage | Closed | Net PnL | Mid PnL | Cost Drag | Sharpe Proxy | MDD | Fits $300 Allocation | Fits $20 Risk Budget | Labels |
|:--|:--|--:|--:|--:|--:|--:|--:|--:|--:|:--|
| `in_sample` | `2023-03-28` to `2023-12-29` | 189 | -2106.68 | 26.5 | 2133.18 | 0.077533 | -2.398303 | 0/189 | 0/189 | under-sampled, underpowered |
| `oos` | `2024-01-02` to `2024-12-31` | 223 | -3866.76 | -884.0 | 2982.76 | -0.05504 | -4.1424 | 0/223 | 0/223 | under-sampled, underpowered |

## Sample Adequacy
```json
{
  "closed_trades": 412,
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
```json
{
  "method": "remove_top_and_bottom_5pct_by_implementable_pnl",
  "original_closed_trades": 412,
  "original_sharpe_proxy": -0.114291,
  "original_total_implementable_pnl": -5973.44,
  "removed_each_side": 21,
  "removed_trade_count": 42,
  "retained_closed_trades": 370,
  "retained_sharpe_proxy": -0.249113,
  "retained_total_implementable_pnl": -9229.4,
  "status": "pass"
}
```

## DSR
```json
{
  "reason": "This feasibility run uses one fixed template and does not select best parameters from a search grid.",
  "status": "not_applicable",
  "trial_count": 1
}
```

## Conclusion
ข้อสรุป: ไม่ผ่าน

- The fixed capped-risk put ratio template does not fit the current $300 Sub-System B allocation or $20 risk budget on any closed trade.
- Edge remains under-sampled and underpowered, so this should be read as a feasibility failure, not a final proof that all Sub-System B variants are invalid.
- The result must not be used as a tuned strategy because no logistic timing model or regime filter is active.
- M4 should continue to forced-close versus target/stop diagnostics after this baseline/feasibility evidence is logged.
