# M5.1 Transaction Cost And Execution Latency Sensitivity

## Status
- Conclusion: ยังสรุปไม่ได้
- Reason: The sensitivity run is useful for diagnosing cost and latency fragility, but all scenarios remain under-sampled and underpowered.
- Evidence type: real-data deterministic sensitivity, diagnostic only.
- No new paid data was downloaded.

## Methodology
```json
{
  "chronological_policy": "2023-03-01..2023-12-29 in-sample, 2024-01-02..2024-12-31 OOS; no OOS tuning from this report.",
  "data_policy": "No new paid data was downloaded for this experiment.",
  "entry_policy": "Entry market orders remain prohibited; latency scenarios require complete delayed-entry quotes or skip the trade.",
  "exit_policy": "Forced close only, nearest 15:45 fallback may use 15:44..15:40 quotes only and never after 15:45 ET.",
  "scope": "Sub-System A ORB directional debit vertical on current real-data artifacts only.",
  "selection_policy": "No production scenario is selected from this grid; best/worst are diagnostic only."
}
```

## Search Log And DSR
- Search log: `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\reports\experiments\search_logs\m5_transaction_cost_latency_sensitivity_search_log.jsonl`
- Trial count: 8
- DSR status: `blocked_under_sampled`
- DSR reason: DSR is recorded as a blocker because this is a multi-scenario diagnostic grid, all scenarios are under-sampled, and no production parameter is selected.

## Scenario Summary
| Scenario | Fill | Fee | Latency | Closed | Skipped | Mid PnL | Implementable PnL | Cost Drag | Drag Ratio | OOS PnL | MDD |
|:--|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| `mid_fee_0_latency_0_control` | `mid` | 0.0 | 0 | 90 | 3 | 1089.5 | 866.5 | 223.0 | 0.204681 | 96.5 | -0.297821 |
| `mid_fee_0_latency_2_control` | `mid` | 0.0 | 2 | 90 | 3 | 605.0 | 382.0 | 223.0 | 0.368595 | -205.5 | -0.405087 |
| `half_spread_fee_064_latency_0_baseline` | `half_spread` | 0.64 | 0 | 90 | 3 | 1089.5 | 545.6 | 543.9 | 0.49922 | -78.44 | -0.370769 |
| `half_spread_fee_064_latency_1` | `half_spread` | 0.64 | 1 | 90 | 3 | 713.5 | 169.6 | 543.9 | 0.762299 | -301.44 | -0.471521 |
| `half_spread_fee_064_latency_2` | `half_spread` | 0.64 | 2 | 90 | 3 | 605.0 | 60.6 | 544.4 | 0.899835 | -381.44 | -0.508742 |
| `half_spread_fee_100_latency_0` | `half_spread` | 1.0 | 0 | 90 | 3 | 1089.5 | 416.0 | 673.5 | 0.618173 | -149.0 | -0.403794 |
| `full_spread_stress_fee_064_latency_0` | `full_spread_stress` | 0.64 | 0 | 90 | 3 | 1089.5 | 364.6 | 724.9 | 0.665351 | -177.44 | -0.417258 |
| `full_spread_stress_fee_100_latency_1` | `full_spread_stress` | 1.0 | 1 | 90 | 3 | 713.5 | -141.0 | 854.5 | 1.197617 | -472.0 | -0.594849 |

## Baseline Scenario
```json
{
  "closed_trades": 90,
  "entry_latency_minutes": 0,
  "fee_per_contract": 0.64,
  "fill_model": "half_spread",
  "metrics": {
    "average_trade_pnl": 6.0622,
    "es95": -59.56,
    "es99": -62.56,
    "friction_drag_ratio": 0.49922,
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
  },
  "scenario_id": "half_spread_fee_064_latency_0_baseline",
  "skipped_trades": 3
}
```

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

## Interpretation
- Mid PnL is only a control. Deployable interpretation must use implementable PnL.
- Latency scenarios skip trades when delayed-entry quotes are missing; they do not invent prices.
- Best and worst scenarios are reported for diagnosis only, not parameter selection.
- The current sample remains too small for acceptance-grade cost or latency conclusions.
