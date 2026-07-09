# H-G1 Gamma Strategy Ablation Diagnostic

## Status
- Hypothesis: `H-G1`
- Status: `complete_underpowered`
- Evidence tier: `E1`
- Conclusion: ยังสรุปไม่ได้
- Strategy use allowed: `False`
- Paper trading allowed: `False`
- Network used: `False`
- Paid data used: `False`

## Coverage
- Baseline closed trades: 90
- Gamma dates: 10
- Intersection closed trades: 2
- Excluded baseline closed trades: 88
- Covered trade dates: `2023-10-27, 2024-12-18`

## Train-Only Threshold
```json
{
  "bottom_bucket_count": 2,
  "cutoff": 31651573.7778,
  "method": "bottom_tercile_by_ceiling_count",
  "thresholds_frozen_before_oos": true,
  "train_date_count": 4,
  "train_values": [
    {
      "date": "2023-10-27",
      "net_oi_gamma_proxy": -263366694.684101
    },
    {
      "date": "2023-08-09",
      "net_oi_gamma_proxy": 31651573.7778
    },
    {
      "date": "2023-09-13",
      "net_oi_gamma_proxy": 54327921.802996
    },
    {
      "date": "2023-12-29",
      "net_oi_gamma_proxy": 1150453555.763625
    }
  ]
}
```

## Variant Results

| Variant | Active | Skipped | Mid PnL | Implementable PnL | Cost Drag | Sharpe | Max DD | ES95 | Labels |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|:--|
| `baseline_quant_only` | 2 | 0 | 288.0 | 230.88 | 57.12 | 6.498713 | 0.0 | 104.44 | under-sampled, underpowered |
| `skip_negative_gamma_proxy_days` | 0 | 2 | 0 | 0 | 0 | None | 0.0 | None | under-sampled, underpowered |
| `skip_extreme_negative_gamma_proxy_days` | 0 | 2 | 0 | 0 | 0 | None | 0.0 | None | under-sampled, underpowered |
| `positive_gamma_proxy_only` | 0 | 2 | 0 | 0 | 0 | None | 0.0 | None | under-sampled, underpowered |

## DSR / Big-Day Dependency
- DSR status: `not_applicable_no_best_sharpe_selection`
- DSR reason: The preregistered selection rule forbids best-Sharpe selection; all four trials are logged and no variant is selected for deployment.
- Big-day dependency status: `blocked_insufficient_observations`
- Big-day reason: The intersection sample has fewer than 3 active trades for every variant, so removing the most extreme 5% winner and loser cannot produce a stable recomputed series.

## Tier Blockers
- `intersection_sample_too_small`
- `under-sampled`
- `underpowered`
- `mintrl_psr_blocked_insufficient_observations`
- `all_gamma_variants_collapse_or_reduce_the_trade_sample`
- `no_e2_acceptance`
- `signed_oi_gamma_proxy_is_not_true_market_maker_net_gamma`

## Next Actions
1. Do not use H-G1 as a trading filter from this diagnostic.
2. Decide whether H-G1 should be parked or whether a separate sample-expansion plan is justified.
3. Return to News-Unblock N.7 if prioritizing timestamp-clean news before further gamma work.
