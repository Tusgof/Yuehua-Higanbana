# M4.1 Sub-System A ORB Baseline

## Status
- Conclusion: ยังสรุปไม่ได้
- Evidence type: real-data baseline, no news filter, no LLM filter.
- Closed trades: 90
- This is a completed baseline experiment round, but not acceptance-grade evidence.

## Method
```json
{
  "chronological_policy": "2023-03-01..2023-12-29 in-sample, 2024-01-02..2024-12-31 OOS; no OOS tuning from this report",
  "close_fallback": "nearest_1545_window",
  "entry_model": "limit-style entry priced by fill model; no entry market orders",
  "exit_model": "forced_close_only",
  "fee_per_contract": 0.64,
  "fill_model": "half_spread",
  "llm_filter": "disabled",
  "news_filter": "disabled",
  "strike_mapping": "nearest discrete strike selection inherited from generated strategy legs"
}
```

## Overall Metrics
```json
{
  "average_trade_pnl": 6.0622,
  "es95": -59.56,
  "es99": -62.56,
  "max_drawdown": -0.370769,
  "payoff_ratio": 2.663,
  "sharpe_proxy": 0.118064,
  "sortino_proxy": 0.578039,
  "total_cost_drag": 543.9,
  "total_implementable_pnl": 545.6,
  "total_mid_pnl": 1089.5,
  "trade_count": 90,
  "win_rate": 0.3222,
  "worst_day_loss": -62.56
}
```

## Split Metrics

| Split | Coverage | Closed | Net PnL | Mid PnL | Cost Drag | Sharpe Proxy | MDD | Benchmark PnL on $1000 | Labels |
|:--|:--|--:|--:|--:|--:|--:|--:|--:|:--|
| `in_sample` | `2023-03-01` to `2023-12-29` | 41 | 624.04 | 849.0 | 224.96 | 0.226229 | -0.170819 | 204.02 | under-sampled, underpowered |
| `oos` | `2024-01-02` to `2024-12-31` | 49 | -78.44 | 240.5 | 318.94 | 0.01581 | -0.550922 | 236.87 | under-sampled, underpowered |

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

## DSR
```json
{
  "reason": "This baseline run does not select best parameters from a search grid.",
  "status": "not_applicable",
  "trial_count": 1
}
```

## Conclusion
ข้อสรุป: ยังสรุปไม่ได้

- Closed trades remain far below the N >= 500 prior target and MinTRL/PSR remain pending.
- OOS results are reported as evidence, not as tuning input.
- M4 should continue to Sub-System B feasibility and baseline work before deterministic filters or LLM gates are tested.
