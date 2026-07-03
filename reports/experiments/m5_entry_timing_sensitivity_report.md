# M5.3 Entry Timing Sensitivity

## Status
- Conclusion: ยังสรุปไม่ได้
- Reason: Entry timing can be compared on current real artifacts, but all scenarios remain under-sampled and underpowered.
- Evidence type: real-data deterministic sensitivity, diagnostic only.
- No new paid data was downloaded.

## Methodology
```json
{
  "chronological_policy": "2023-03-01..2023-12-29 in-sample, 2024-01-02..2024-12-31 OOS; no OOS tuning from this report.",
  "data_policy": "No new paid data was downloaded for this experiment.",
  "scope": "Sub-System A ORB breakout-time sensitivity and Sub-System B fixed put-ratio entry-snapshot sensitivity.",
  "selection_policy": "Best scenarios are diagnostic only. No production entry time is selected from this under-sampled grid.",
  "subsystem_a_policy": "Recompute opening range and breakout decision for each candidate breakout timestamp.",
  "subsystem_b_policy": "Use exact 09:55..10:00 put snapshots for the existing capped put-ratio feasibility template."
}
```

## Search Log And DSR
- Search log: `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\reports\experiments\search_logs\m5_entry_timing_sensitivity_search_log.jsonl`
- Trial count: 12
- DSR status: `blocked_under_sampled`
- DSR reason: DSR is blocked because this is a multi-scenario timing grid, all scenarios are under-sampled, and no production timing rule is selected.

## Scenario Summary
| Scenario | Sub-System | Entry | Closed | Net PnL | Mid PnL | Cost Drag | OOS PnL | MDD | Labels |
|:--|:--|:--|--:|--:|--:|--:|--:|--:|:--|
| `sub_a_orb_breakout_0935` | `sub_a` | `09:35:00` | 90 | 539.6 | 1080.0 | 540.4 | -84.44 | -0.370283 | under-sampled, underpowered |
| `sub_a_orb_breakout_0936` | `sub_a` | `09:36:00` | 76 | -741.56 | -334.0 | 407.56 | -694.84 | -0.878399 | under-sampled, underpowered |
| `sub_a_orb_breakout_0937` | `sub_a` | `09:37:00` | 77 | -405.12 | 35.5 | 440.62 | -501.52 | -0.583488 | under-sampled, underpowered |
| `sub_a_orb_breakout_0938` | `sub_a` | `09:38:00` | 65 | 26.6 | 399.5 | 372.9 | -338.92 | -0.427538 | under-sampled, underpowered |
| `sub_a_orb_breakout_0939` | `sub_a` | `09:39:00` | 75 | -188.0 | 294.5 | 482.5 | -248.52 | -0.693697 | under-sampled, underpowered |
| `sub_a_orb_breakout_1000` | `sub_a` | `10:00:00` | 76 | -501.56 | -70.0 | 431.56 | -559.32 | -0.751 | under-sampled, underpowered |
| `sub_b_put_ratio_entry_0955` | `sub_b` | `09:55:00` | 412 | -6098.44 | -1431.0 | 4667.44 | -4394.76 | -5.688661 | under-sampled, underpowered |
| `sub_b_put_ratio_entry_0956` | `sub_b` | `09:56:00` | 412 | -6401.44 | -1737.5 | 4663.94 | -4452.76 | -6.430365 | under-sampled, underpowered |
| `sub_b_put_ratio_entry_0957` | `sub_b` | `09:57:00` | 412 | -6070.44 | -1386.5 | 4683.94 | -4253.76 | -5.737225 | under-sampled, underpowered |
| `sub_b_put_ratio_entry_0958` | `sub_b` | `09:58:00` | 412 | -5855.44 | -1168.0 | 4687.44 | -4131.76 | -5.488867 | under-sampled, underpowered |
| `sub_b_put_ratio_entry_0959` | `sub_b` | `09:59:00` | 412 | -5827.44 | -1146.0 | 4681.44 | -3944.76 | -5.721647 | under-sampled, underpowered |
| `sub_b_put_ratio_entry_1000` | `sub_b` | `10:00:00` | 412 | -5973.44 | -857.5 | 5115.94 | -3866.76 | -6.202878 | under-sampled, underpowered |

## Baseline Scenarios
```json
{
  "sub_a": {
    "closed_trades": 90,
    "entry_time": "09:35:00",
    "metrics": {
      "average_trade_pnl": 5.9956,
      "es95": -59.56,
      "es99": -62.56,
      "max_drawdown": -0.370283,
      "payoff_ratio": 2.7958,
      "sharpe_proxy": 0.116795,
      "sortino_proxy": 0.561109,
      "total_cost_drag": 540.4,
      "total_implementable_pnl": 539.6,
      "total_mid_pnl": 1080.0,
      "trade_count": 90,
      "win_rate": 0.3111,
      "worst_day_loss": -62.56
    },
    "oos_metrics": {
      "average_trade_pnl": -1.7233,
      "es95": -61.56,
      "es99": -62.56,
      "max_drawdown": -0.551754,
      "payoff_ratio": 2.3315,
      "sharpe_proxy": 0.015099,
      "sortino_proxy": 0.05802,
      "total_cost_drag": 315.44,
      "total_implementable_pnl": -84.44,
      "total_mid_pnl": 231.0,
      "trade_count": 49,
      "win_rate": 0.2857,
      "worst_day_loss": -62.56
    },
    "scenario_id": "sub_a_orb_breakout_0935",
    "subsystem": "sub_a"
  },
  "sub_b": {
    "closed_trades": 412,
    "entry_time": "10:00:00",
    "feasibility": {
      "all_trades_fit_20_risk_budget": false,
      "all_trades_fit_300_allocation": false,
      "allocation_300_feasible_count": 0,
      "checked_trades": 412,
      "risk_budget_20_feasible_count": 0
    },
    "metrics": {
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
    },
    "oos_metrics": {
      "average_trade_pnl": -17.3397,
      "es95": -179.4533,
      "es99": -289.12,
      "max_drawdown": -4.1424,
      "payoff_ratio": 1.5816,
      "sharpe_proxy": -0.05504,
      "sortino_proxy": -0.037936,
      "total_cost_drag": 2982.76,
      "total_implementable_pnl": -3866.76,
      "total_mid_pnl": -884.0,
      "trade_count": 223,
      "win_rate": 0.3139,
      "worst_day_loss": -454.12
    },
    "scenario_id": "sub_b_put_ratio_entry_1000",
    "subsystem": "sub_b"
  }
}
```

## Best Diagnostic Scenarios
```json
{
  "sub_a": {
    "closed_trades": 90,
    "entry_time": "09:35:00",
    "metrics": {
      "average_trade_pnl": 5.9956,
      "es95": -59.56,
      "es99": -62.56,
      "max_drawdown": -0.370283,
      "payoff_ratio": 2.7958,
      "sharpe_proxy": 0.116795,
      "sortino_proxy": 0.561109,
      "total_cost_drag": 540.4,
      "total_implementable_pnl": 539.6,
      "total_mid_pnl": 1080.0,
      "trade_count": 90,
      "win_rate": 0.3111,
      "worst_day_loss": -62.56
    },
    "oos_metrics": {
      "average_trade_pnl": -1.7233,
      "es95": -61.56,
      "es99": -62.56,
      "max_drawdown": -0.551754,
      "payoff_ratio": 2.3315,
      "sharpe_proxy": 0.015099,
      "sortino_proxy": 0.05802,
      "total_cost_drag": 315.44,
      "total_implementable_pnl": -84.44,
      "total_mid_pnl": 231.0,
      "trade_count": 49,
      "win_rate": 0.2857,
      "worst_day_loss": -62.56
    },
    "scenario_id": "sub_a_orb_breakout_0935",
    "subsystem": "sub_a"
  },
  "sub_b": {
    "closed_trades": 412,
    "entry_time": "09:59:00",
    "feasibility": {
      "all_trades_fit_20_risk_budget": false,
      "all_trades_fit_300_allocation": false,
      "allocation_300_feasible_count": 0,
      "checked_trades": 412,
      "risk_budget_20_feasible_count": 0
    },
    "metrics": {
      "average_trade_pnl": -14.1443,
      "es95": -154.2152,
      "es99": -229.32,
      "max_drawdown": -5.721647,
      "payoff_ratio": 1.7679,
      "sharpe_proxy": 0.024487,
      "sortino_proxy": 0.025804,
      "total_cost_drag": 4681.44,
      "total_implementable_pnl": -5827.44,
      "total_mid_pnl": -1146.0,
      "trade_count": 412,
      "win_rate": 0.301,
      "worst_day_loss": -458.12
    },
    "oos_metrics": {
      "average_trade_pnl": -17.6895,
      "es95": -173.7033,
      "es99": -282.4533,
      "max_drawdown": -4.2964,
      "payoff_ratio": 1.5358,
      "sharpe_proxy": 0.044756,
      "sortino_proxy": 0.044649,
      "total_cost_drag": 2688.26,
      "total_implementable_pnl": -3944.76,
      "total_mid_pnl": -1256.5,
      "trade_count": 223,
      "win_rate": 0.3184,
      "worst_day_loss": -458.12
    },
    "scenario_id": "sub_b_put_ratio_entry_0959",
    "subsystem": "sub_b"
  }
}
```

## Interpretation
- Entry-time variants are search trials; they must not be selected as production rules from this under-sampled result.
- Sub-System A variants recompute the ORB range at each timestamp, so this is not just latency replay.
- Sub-System B variants use the existing fixed put-ratio template and still need separate capital/structure research before feasibility can pass.
