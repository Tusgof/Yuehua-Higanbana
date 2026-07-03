# M5.4 Exit Target/Stop Sensitivity

## Status
- Conclusion: ยังสรุปไม่ได้
- Reason: Exit target/stop grid is useful diagnostically, but all scenarios remain under-sampled and underpowered; no production TP/SL is selected.
- Evidence type: real-data deterministic sensitivity, diagnostic only.
- No new paid data was downloaded.

## Methodology
```json
{
  "chronological_policy": "2023-03-01..2023-12-29 in-sample, 2024-01-02..2024-12-31 OOS; no OOS tuning from this report.",
  "data_policy": "No new paid data was downloaded for this experiment.",
  "entry_policy": "Entry market orders remain prohibited; baseline entry uses half-spread fill and skips missing quotes.",
  "exit_policy": "Grid tests profit-target and stop-loss thresholds using available intraday quotes; unresolved trades force-close by 15:45 ET fallback.",
  "scope": "Sub-System A ORB directional debit vertical on current real-data artifacts only.",
  "selection_policy": "Best/worst scenarios are diagnostic only. Do not select production TP/SL from this under-sampled grid."
}
```

## Search Log And DSR
- Search log: `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\reports\experiments\search_logs\m5_exit_target_stop_sensitivity_search_log.jsonl`
- Trial count: 7
- DSR status: `blocked_under_sampled`
- DSR reason: DSR is blocked because this is a multi-scenario TP/SL grid, all scenarios are under-sampled, and no production exit rule is selected.

## Scenario Summary
| Scenario | TP | SL | Closed | Mid PnL | Implementable PnL | Cost Drag | OOS PnL | ES95 | ES99 | MDD | Exit reasons |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|:--|
| `forced_close_only_control` | None | None | 90 | 1089.5 | 545.6 | 543.9 | -78.44 | -59.56 | -62.56 | -0.370769 | `{"forced_1545": 90}` |
| `tp_10_stop_25` | 0.1 | 0.25 | 93 | 336.5 | -93.08 | 429.58 | -93.56 | -29.36 | -36.56 | -0.15323 | `{"profit_target_10pct": 70, "stop_loss_25pct": 23}` |
| `tp_25_stop_50_baseline` | 0.25 | 0.5 | 93 | 542.0 | 108.92 | 433.08 | 133.44 | -33.76 | -37.56 | -0.092626 | `{"profit_target_25pct": 63, "stop_loss_50pct": 30}` |
| `tp_50_stop_50` | 0.5 | 0.5 | 93 | 693.5 | 252.92 | 440.58 | 353.44 | -35.36 | -38.56 | -0.153478 | `{"profit_target_50pct": 48, "stop_loss_50pct": 45}` |
| `tp_50_stop_75` | 0.5 | 0.75 | 92 | 697.0 | 261.48 | 435.52 | 370.0 | -47.96 | -56.56 | -0.165718 | `{"forced_1545": 1, "profit_target_50pct": 54, "stop_loss_75pct": 37}` |
| `tp_100_stop_50` | 1.0 | 0.5 | 92 | 888.0 | 447.48 | 440.52 | 239.0 | -36.16 | -38.56 | -0.248591 | `{"forced_1545": 1, "profit_target_100pct": 38, "stop_loss_50pct": 53}` |
| `tp_100_stop_100` | 1.0 | 1.0 | 91 | 802.0 | 364.04 | 437.96 | 262.56 | -57.76 | -61.56 | -0.334029 | `{"forced_1545": 11, "profit_target_100pct": 44, "stop_loss_100pct": 36}` |

## Baseline Scenario
```json
{
  "closed_trades": 90,
  "metrics": {
    "average_trade_pnl": 6.0622,
    "es95": -59.56,
    "es99": -62.56,
    "exit_reason_counts": {
      "forced_1545": 90
    },
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
  "oos_metrics": {
    "average_trade_pnl": -1.6008,
    "es95": -61.56,
    "es99": -62.56,
    "max_drawdown": -0.550922,
    "payoff_ratio": 2.1243,
    "sharpe_proxy": 0.01581,
    "sortino_proxy": 0.062356,
    "total_cost_drag": 318.94,
    "total_implementable_pnl": -78.44,
    "total_mid_pnl": 240.5,
    "trade_count": 49,
    "win_rate": 0.3061,
    "worst_day_loss": -62.56
  },
  "profit_target_pct": null,
  "scenario_id": "forced_close_only_control",
  "stop_loss_pct": null
}
```

## Best/Worst Diagnostic Scenarios
```json
{
  "best": {
    "closed_trades": 90,
    "metrics": {
      "average_trade_pnl": 6.0622,
      "es95": -59.56,
      "es99": -62.56,
      "exit_reason_counts": {
        "forced_1545": 90
      },
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
    "oos_metrics": {
      "average_trade_pnl": -1.6008,
      "es95": -61.56,
      "es99": -62.56,
      "max_drawdown": -0.550922,
      "payoff_ratio": 2.1243,
      "sharpe_proxy": 0.01581,
      "sortino_proxy": 0.062356,
      "total_cost_drag": 318.94,
      "total_implementable_pnl": -78.44,
      "total_mid_pnl": 240.5,
      "trade_count": 49,
      "win_rate": 0.3061,
      "worst_day_loss": -62.56
    },
    "profit_target_pct": null,
    "scenario_id": "forced_close_only_control",
    "stop_loss_pct": null
  },
  "worst": {
    "closed_trades": 93,
    "metrics": {
      "average_trade_pnl": -1.0009,
      "es95": -29.36,
      "es99": -36.56,
      "exit_reason_counts": {
        "profit_target_10pct": 70,
        "stop_loss_25pct": 23
      },
      "max_drawdown": -0.15323,
      "payoff_ratio": 0.2666,
      "sharpe_proxy": -0.088008,
      "sortino_proxy": -0.109032,
      "total_cost_drag": 429.58,
      "total_implementable_pnl": -93.08,
      "total_mid_pnl": 336.5,
      "trade_count": 93,
      "win_rate": 0.7419,
      "worst_day_loss": -36.56
    },
    "oos_metrics": {
      "average_trade_pnl": -1.8345,
      "es95": -31.2267,
      "es99": -36.56,
      "max_drawdown": -0.122994,
      "payoff_ratio": 0.2283,
      "sharpe_proxy": -0.136306,
      "sortino_proxy": -0.226362,
      "total_cost_drag": 238.06,
      "total_implementable_pnl": -93.56,
      "total_mid_pnl": 144.5,
      "trade_count": 51,
      "win_rate": 0.7451,
      "worst_day_loss": -36.56
    },
    "profit_target_pct": 0.1,
    "scenario_id": "tp_10_stop_25",
    "stop_loss_pct": 0.25
  }
}
```

## Interpretation
- TP/SL variants are search trials; they must not be selected as production rules from this under-sampled result.
- OOS deltas are reported for diagnosis only and are not tuning input.
- Implementable PnL is the deployable reference; Mid PnL is a control.
