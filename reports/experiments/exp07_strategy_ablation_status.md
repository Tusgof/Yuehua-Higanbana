# Exp07 Strategy Ablation Status

- Plan version: `exp07-strategy-ablation-v1`
- Experiment id: `exp07_cost_latency`
- Status: `blocked`
- Reason: Real strategy ablation is blocked until required data archives and sample size exist.

## Variants

| Variant | Status | Can Block Trade | Raw LLM Gate | Guarded Policy |
|:--|:--|:--:|:--:|:--:|
| baseline_quant_only | `blocked` | False | False | False |
| guarded_policy_gate | `blocked` | True | False | True |
| raw_llm_observation_only | `blocked` | False | True | False |

## Blockers

- `requires_minimum_trade_count_500`
- `requires_real_news_archive`
- `requires_wider_spy_0dte_data`

## Strategy Data Evidence

- Closed trades: 90 / 500
- Quote rows: 21503220

## Required Metrics

- `trade_count`
- `skip_rate`
- `total_net_pnl`
- `sharpe`
- `sortino`
- `max_drawdown`
- `es95`
- `es99`
- `worst_day_loss`
- `win_rate`
- `payoff_ratio`
- `cost_drag`
- `benchmark_return`
