# M5.2 Strike Selection Sensitivity

## Status
- Conclusion: ยังสรุปไม่ได้
- Reason: Moneyness/target-gap scenarios can be evaluated on current real data, but delta-based selection is blocked because normalized option quotes do not contain Greeks.
- Evidence type: real-data deterministic strike-selection sensitivity, diagnostic only.
- No new paid data was downloaded.

## Methodology
```json
{
  "chronological_policy": "2023-03-01..2023-12-29 in-sample, 2024-01-02..2024-12-31 OOS; no OOS tuning from this report.",
  "data_policy": "No new paid data was downloaded for this experiment.",
  "delta_policy": "Delta selection is not run because the current normalized Databento option_quote records contain no delta, implied volatility, or Greeks fields. No proxy delta is substituted.",
  "scope": "Sub-System A ORB directional debit vertical on current real-data artifacts only.",
  "selection_policy": "Best/worst scenarios are diagnostic only. No production strike rule is selected from this under-sampled grid.",
  "strike_mapping": "nearest_discrete_strike_rounding; no interpolation; long strike maps from target breakout-to-long gap to the nearest tradable SPY 0DTE strike in the breakout direction."
}
```

## Delta Selection Assessment
```json
{
  "proxy_used": false,
  "reason": "Current normalized option_quote artifacts contain strike, bid, ask, sizes, timestamps, and symbols, but no delta, gamma, implied volatility, or model inputs needed for a defensible delta selection rule.",
  "required_before_delta_experiment": [
    "provider Greeks at decision timestamp, or",
    "approved point-in-time implied-volatility model with documented inputs and validation"
  ],
  "status": "blocked_missing_greeks"
}
```

## Search Log And DSR
- Search log: `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\reports\experiments\search_logs\m5_strike_selection_sensitivity_search_log.jsonl`
- Trial count: 5
- DSR status: `blocked_under_sampled`
- DSR reason: DSR is recorded as a blocker because this is a multi-scenario diagnostic grid, all scenarios are under-sampled, and no production strike rule is selected.

## Scenario Summary
| Scenario | Target gap | Closed | Skipped | EV/trade | Implementable PnL | Cost Drag | OOS PnL | MDD | Avg gap | Breach rate |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| `target_gap_0_25_width_2` | 0.25 | 90 | 3 | 7.0289 | 632.6 | 629.4 | -68.44 | -0.381069 | 0.507258 | 0.516129 |
| `target_gap_0_75_width_2` | 0.75 | 90 | 3 | 5.8956 | 530.6 | 593.4 | -169.44 | -0.402364 | 0.802957 | 0.44086 |
| `target_gap_1_25_width_2` | 1.25 | 90 | 3 | 3.4844 | 313.6 | 573.4 | -240.44 | -0.450386 | 1.190054 | 0.526882 |
| `target_gap_1_75_width_2` | 1.75 | 89 | 4 | 3.6984 | 329.16 | 531.34 | -172.88 | -0.382013 | 1.792204 | 0.44086 |
| `baseline_gap_1_48_width_2` | 1.48 | 90 | 3 | 6.2067 | 558.6 | 540.4 | -65.44 | -0.360269 | 1.480376 | 0.612903 |

## Best Diagnostic Scenario
```json
{
  "closed_trades": 90,
  "mapping_summary": {
    "average_abs_gap_error": 0.330914,
    "average_realized_long_gap": 0.507258,
    "average_realized_width": 2.005376,
    "gap_tolerance": 0.25,
    "gap_tolerance_breach_count": 48,
    "gap_tolerance_breach_rate": 0.516129,
    "interpolation_used": false,
    "mapped_candidate_days": 93,
    "mapping_method": "nearest_discrete_strike_rounding",
    "max_long_moneyness": 1.002129,
    "min_long_moneyness": 0.997701
  },
  "metrics": {
    "average_ev_per_trade": 7.0289,
    "average_trade_pnl": 7.0289,
    "es95": -74.76,
    "es99": -79.56,
    "max_drawdown": -0.381069,
    "payoff_ratio": 1.7774,
    "sharpe_proxy": 0.124164,
    "sortino_proxy": 0.516546,
    "total_cost_drag": 629.4,
    "total_implementable_pnl": 632.6,
    "total_mid_pnl": 1262.0,
    "trade_count": 90,
    "win_rate": 0.4111,
    "worst_day_loss": -79.56
  },
  "scenario_id": "target_gap_0_25_width_2",
  "skipped_trades": 3,
  "target_gap": 0.25
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
- This report tests moneyness/target-gap mapping only. Delta selection is blocked, not approximated.
- Nearest discrete strike rounding is explicit; no continuous moneyness interpolation is used.
- Best and worst scenarios are reported for diagnosis only, not parameter selection.
- The current sample remains too small for acceptance-grade strike-selection conclusions.
