# M5.6 Portfolio Construction Diagnostic

## Status
- Conclusion: ยังสรุปไม่ได้
- Reason: Portfolio construction is mathematically testable, but Sub-System B is not current-sizing feasible and every blended portfolio remains under-sampled/underpowered.
- Evidence type: real-data deterministic portfolio diagnostic, not an implementable allocation.
- No new paid data was downloaded.

## Methodology
```json
{
  "data_policy": "No new paid data was downloaded for this experiment.",
  "feasibility_policy": "Sub-System B allocation is checked against current $1,000 account, $300 Sub-System B allocation, and $20 risk budget constraints.",
  "fit_policy": "Risk parity and ES parity weights are fit on in-sample returns only, then reported on OOS without OOS tuning.",
  "fractional_contract_policy": "Blended weights are fractional diagnostic portfolios only. They are not directly tradable option-contract portfolios.",
  "scope": "Diagnostic allocation between Sub-System A ORB baseline and Sub-System B put-ratio baseline daily PnL."
}
```

## Search Log And DSR
- Search log: `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\reports\experiments\search_logs\m5_portfolio_construction_diagnostic_search_log.jsonl`
- Trial count: 5
- DSR status: `blocked_under_sampled`
- DSR reason: DSR is blocked because this is a multi-scenario allocation diagnostic, all scenarios are under-sampled, and Sub-System B is not current-sizing feasible.

## Scenario Summary
| Scenario | A weight | B weight | Days | Total PnL | OOS PnL | Sharpe | Sortino | MDD | ES95 | ES99 | Feasibility |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|:--|
| `subsystem_a_only_control` | 1.0 | 0.0 | 416 | 545.6 | -78.44 | 0.054618 | 0.125056 | -0.370769 | -47.8457 | -59.56 | `account_feasible_without_subsystem_b` |
| `subsystem_b_only_diagnostic` | 0.0 | 1.0 | 416 | -5973.44 | -3866.76 | 0.0527 | 0.740616 | -6.202878 | -161.4533 | -237.92 | `blocked_current_sizing` |
| `equal_weight_fractional_diagnostic` | 0.5 | 0.5 | 416 | -2713.92 | -1972.6 | 0.075254 | 0.598143 | -2.795771 | -86.4714 | -118.884 | `blocked_current_sizing` |
| `risk_parity_inverse_vol_in_sample` | 0.99470524 | 0.00529476 | 416 | 511.07 | -98.51 | 0.052155 | 0.115017 | -0.381438 | -47.8819 | -59.322 | `blocked_current_sizing` |
| `es_parity_inverse_es95_in_sample` | 0.72767643 | 0.27232357 | 416 | -1229.67 | -1110.05 | 0.062577 | 0.101291 | -1.341492 | -61.8805 | -74.878 | `blocked_current_sizing` |

## Baseline / Diagnostic Extremes
```json
{
  "baseline": {
    "daily_count": 416,
    "feasibility": {
      "all_subsystem_b_trades_fit_20_risk_budget": true,
      "all_subsystem_b_trades_fit_allocation": true,
      "notes": [
        "Sub-System B is not used in this scenario."
      ],
      "status": "account_feasible_without_subsystem_b",
      "subsystem_b_allocation": 0.0
    },
    "metrics": {
      "average_day_pnl": 1.3115,
      "day_count": 416,
      "ending_equity": 1545.6,
      "es95": -47.8457,
      "es99": -59.56,
      "max_drawdown": -0.370769,
      "payoff_ratio": 2.663,
      "sharpe_proxy": 0.054618,
      "sortino_proxy": 0.125056,
      "total_pnl": 545.6,
      "win_rate": 0.0697,
      "worst_day_loss": -62.56
    },
    "oos_metrics": {
      "average_day_pnl": -0.3456,
      "day_count": 227,
      "ending_equity": 1545.6,
      "es95": -50.31,
      "es99": -61.56,
      "max_drawdown": -0.370769,
      "payoff_ratio": 2.1243,
      "sharpe_proxy": -0.001325,
      "sortino_proxy": -0.002567,
      "total_pnl": -78.44,
      "win_rate": 0.0661,
      "worst_day_loss": -62.56
    },
    "scenario_id": "subsystem_a_only_control",
    "weights": {
      "subsystem_a": 1.0,
      "subsystem_b": 0.0
    }
  },
  "best": {
    "daily_count": 416,
    "feasibility": {
      "all_subsystem_b_trades_fit_20_risk_budget": true,
      "all_subsystem_b_trades_fit_allocation": true,
      "notes": [
        "Sub-System B is not used in this scenario."
      ],
      "status": "account_feasible_without_subsystem_b",
      "subsystem_b_allocation": 0.0
    },
    "metrics": {
      "average_day_pnl": 1.3115,
      "day_count": 416,
      "ending_equity": 1545.6,
      "es95": -47.8457,
      "es99": -59.56,
      "max_drawdown": -0.370769,
      "payoff_ratio": 2.663,
      "sharpe_proxy": 0.054618,
      "sortino_proxy": 0.125056,
      "total_pnl": 545.6,
      "win_rate": 0.0697,
      "worst_day_loss": -62.56
    },
    "oos_metrics": {
      "average_day_pnl": -0.3456,
      "day_count": 227,
      "ending_equity": 1545.6,
      "es95": -50.31,
      "es99": -61.56,
      "max_drawdown": -0.370769,
      "payoff_ratio": 2.1243,
      "sharpe_proxy": -0.001325,
      "sortino_proxy": -0.002567,
      "total_pnl": -78.44,
      "win_rate": 0.0661,
      "worst_day_loss": -62.56
    },
    "scenario_id": "subsystem_a_only_control",
    "weights": {
      "subsystem_a": 1.0,
      "subsystem_b": 0.0
    }
  },
  "worst": {
    "daily_count": 416,
    "feasibility": {
      "all_subsystem_b_trades_fit_20_risk_budget": false,
      "all_subsystem_b_trades_fit_allocation": true,
      "current_project_risk_budget": 20.0,
      "current_project_subsystem_b_allocation": 300.0,
      "notes": [
        "Sub-System B baseline is already marked failed for current $300 allocation and $20 risk budget.",
        "Fractional portfolio weights are diagnostic only; options contracts cannot be traded fractionally."
      ],
      "status": "blocked_current_sizing",
      "subsystem_b_allocation": 1000.0,
      "subsystem_b_max_defined_loss": 773.0,
      "subsystem_b_median_defined_loss": 566.0,
      "subsystem_b_min_defined_loss": 366.0
    },
    "metrics": {
      "average_day_pnl": -14.3592,
      "day_count": 416,
      "ending_equity": -4973.44,
      "es95": -161.4533,
      "es99": -237.92,
      "max_drawdown": -6.202878,
      "payoff_ratio": 1.8012,
      "sharpe_proxy": 0.0527,
      "sortino_proxy": 0.740616,
      "total_pnl": -5973.44,
      "win_rate": 0.2933,
      "worst_day_loss": -454.12
    },
    "oos_metrics": {
      "average_day_pnl": -17.0342,
      "day_count": 227,
      "ending_equity": -4973.44,
      "es95": -179.4533,
      "es99": -289.12,
      "max_drawdown": -6.24908,
      "payoff_ratio": 1.5816,
      "sharpe_proxy": 0.200548,
      "sortino_proxy": 0.241556,
      "total_pnl": -3866.76,
      "win_rate": 0.3084,
      "worst_day_loss": -454.12
    },
    "scenario_id": "subsystem_b_only_diagnostic",
    "weights": {
      "subsystem_a": 0.0,
      "subsystem_b": 1.0
    }
  }
}
```

## Interpretation
- Sub-System A only remains the cleanest account-feasible diagnostic control.
- Any allocation using Sub-System B is blocked for current sizing unless the strategy template, capital, or risk budget changes.
- Risk parity and ES parity are fit on in-sample only, but they still use fractional option exposure and are not directly tradable.
- Portfolio allocation cannot rescue a failed Sub-System B template without solving the underlying sizing and edge problems first.
