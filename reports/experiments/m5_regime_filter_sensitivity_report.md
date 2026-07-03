# M5.5 Regime Filter Sensitivity

## Status
- Conclusion: ยังสรุปไม่ได้
- Reason: VIX/VXV and macro filters are measurable on current real data, but all filtered scenarios remain under-sampled and underpowered. NOVI/net-gamma remains blocked because required inputs are missing.
- Evidence type: real-data deterministic filter sensitivity, diagnostic only.
- No new paid data was downloaded.

## Methodology
```json
{
  "chronological_policy": "2023-03-01..2023-12-29 in-sample, 2024-01-02..2024-12-31 OOS; no OOS tuning from this report.",
  "data_policy": "No new paid data was downloaded for this experiment.",
  "macro_policy": "Use official scheduled same-day macro events as ex-ante known calendar blockers.",
  "novi_net_gamma_policy": "Blocked. Current normalized option quotes do not include Greeks, open interest, dealer inventory, or position reconstruction inputs.",
  "scope": "Sub-System A ORB directional debit vertical on current real-data artifacts only.",
  "selection_policy": "Best/worst scenarios are diagnostic only. Do not select production filters from this under-sampled grid.",
  "vix_policy": "Use previous available Cboe VIX/VIX3M close before the trade date, never same-day close before market open."
}
```

## Search Log And DSR
- Search log: `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\reports\experiments\search_logs\m5_regime_filter_sensitivity_search_log.jsonl`
- Trial count: 9
- DSR status: `blocked_under_sampled`
- DSR reason: DSR is blocked because this is a multi-scenario filter grid, all scenarios are under-sampled, and no production regime filter is selected.

## NOVI / Net-Gamma Blocker
```json
{
  "reason": "A defensible NOVI/net-gamma proxy needs option Greeks, open interest or position reconstruction, and a documented scaling convention. Current normalized option_quote artifacts contain bid/ask, sizes, timestamps, strikes, and rights, but not the required inventory/gamma inputs.",
  "required_inputs": [
    "gamma or model inputs to compute gamma",
    "open interest or position inventory",
    "contract multiplier/scaling convention",
    "decision-time availability policy"
  ],
  "status": "blocked_missing_inputs"
}
```

## Scenario Summary
| Scenario | Candidates | Filtered | Closed | Retention | Mid PnL | Implementable PnL | Cost Drag | OOS PnL | ES95 | ES99 | MDD | Labels |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|:--|
| `unfiltered_control` | 93 | 0 | 90 | 0.967742 | 1089.5 | 545.6 | 543.9 | -78.44 | -59.56 | -62.56 | -0.370769 | `under-sampled,underpowered` |
| `vix_15_25_prev_close` | 93 | 49 | 44 | 0.473118 | 143.0 | -141.64 | 284.64 | -83.32 | -59.8933 | -61.56 | -0.455703 | `under-sampled,underpowered` |
| `vix_below_25_prev_close` | 93 | 0 | 90 | 0.967742 | 1089.5 | 545.6 | 543.9 | -78.44 | -59.56 | -62.56 | -0.370769 | `under-sampled,underpowered` |
| `vix_below_30_prev_close` | 93 | 0 | 90 | 0.967742 | 1089.5 | 545.6 | 543.9 | -78.44 | -59.56 | -62.56 | -0.370769 | `under-sampled,underpowered` |
| `term_structure_not_inverted_prev_close` | 93 | 0 | 90 | 0.967742 | 1089.5 | 545.6 | 543.9 | -78.44 | -59.56 | -62.56 | -0.370769 | `under-sampled,underpowered` |
| `vix_15_25_and_non_inverted_prev_close` | 93 | 49 | 44 | 0.473118 | 143.0 | -141.64 | 284.64 | -83.32 | -59.8933 | -61.56 | -0.455703 | `under-sampled,underpowered` |
| `exclude_high_importance_macro_same_day` | 93 | 28 | 64 | 0.688172 | 1189.0 | 820.16 | 368.84 | 240.96 | -53.81 | -57.56 | -0.221838 | `under-sampled,underpowered` |
| `exclude_major_macro_same_day` | 93 | 22 | 70 | 0.752688 | 998.0 | 601.8 | 396.2 | 95.72 | -57.06 | -61.56 | -0.277636 | `under-sampled,underpowered` |
| `vix_15_25_non_inverted_exclude_major_macro` | 93 | 57 | 36 | 0.387097 | -147.0 | -342.16 | 195.16 | -84.64 | -59.56 | -61.56 | -0.560351 | `under-sampled,underpowered` |

## Baseline / Diagnostic Extremes
```json
{
  "baseline": {
    "candidate_days_before_filter": 93,
    "closed_trades": 90,
    "filtered_out_trades": 0,
    "metrics": {
      "average_trade_pnl": 6.0622,
      "es95": -59.56,
      "es99": -62.56,
      "filter_retention_rate": 0.967742,
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
      "filter_retention_rate": 0.960784,
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
    "scenario_id": "unfiltered_control"
  },
  "best": {
    "candidate_days_before_filter": 93,
    "closed_trades": 64,
    "filtered_out_trades": 28,
    "metrics": {
      "average_trade_pnl": 12.815,
      "es95": -53.81,
      "es99": -57.56,
      "filter_retention_rate": 0.688172,
      "max_drawdown": -0.221838,
      "payoff_ratio": 2.7043,
      "sharpe_proxy": 0.199493,
      "sortino_proxy": 1.097362,
      "total_cost_drag": 368.84,
      "total_implementable_pnl": 820.16,
      "total_mid_pnl": 1189.0,
      "trade_count": 64,
      "win_rate": 0.375,
      "worst_day_loss": -57.56
    },
    "oos_metrics": {
      "average_trade_pnl": 7.0871,
      "es95": -54.56,
      "es99": -55.56,
      "filter_retention_rate": 0.666667,
      "max_drawdown": -0.321882,
      "payoff_ratio": 2.1394,
      "sharpe_proxy": 0.133578,
      "sortino_proxy": 0.676391,
      "total_cost_drag": 204.54,
      "total_implementable_pnl": 240.96,
      "total_mid_pnl": 445.5,
      "trade_count": 34,
      "win_rate": 0.3824,
      "worst_day_loss": -55.56
    },
    "scenario_id": "exclude_high_importance_macro_same_day"
  },
  "worst": {
    "candidate_days_before_filter": 93,
    "closed_trades": 36,
    "filtered_out_trades": 57,
    "metrics": {
      "average_trade_pnl": -9.5044,
      "es95": -59.56,
      "es99": -61.56,
      "filter_retention_rate": 0.387097,
      "max_drawdown": -0.560351,
      "payoff_ratio": 2.2701,
      "sharpe_proxy": -0.100643,
      "sortino_proxy": -0.3507,
      "total_cost_drag": 195.16,
      "total_implementable_pnl": -342.16,
      "total_mid_pnl": -147.0,
      "trade_count": 36,
      "win_rate": 0.2222,
      "worst_day_loss": -61.56
    },
    "oos_metrics": {
      "average_trade_pnl": -4.4547,
      "es95": -61.56,
      "es99": -61.56,
      "filter_retention_rate": 0.372549,
      "max_drawdown": -0.28892,
      "payoff_ratio": 1.7848,
      "sharpe_proxy": -0.036812,
      "sortino_proxy": -0.141389,
      "total_cost_drag": 106.64,
      "total_implementable_pnl": -84.64,
      "total_mid_pnl": 22.0,
      "trade_count": 19,
      "win_rate": 0.3158,
      "worst_day_loss": -61.56
    },
    "scenario_id": "vix_15_25_non_inverted_exclude_major_macro"
  }
}
```

## Interpretation
- VIX/VXV filters use prior close only, so they are available before the entry decision.
- Macro filters use scheduled same-day event dates, not realized post-event outcomes.
- All filtered results shrink an already small sample, so they remain diagnostic.
- NOVI/net-gamma is not tested because the current dataset lacks the inputs needed for a defensible proxy.
