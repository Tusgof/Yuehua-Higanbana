# H-A2 Lower-Resolution Proxy Test

## Status
- Hypothesis: `H-A2`
- Evidence tier: `E1`
- Conclusion: ยังสรุปไม่ได้
- Reason: The proxy and existing trade outcomes are directionally coherent with H-A2 risk-filter intuition, but the evidence is E1 only, under-sampled, and not an exact 2022 ORB test.
- Network used: `False`
- Paid data used: `False`
- Paper trading allowed: `False`

## Proxy Summary
| Proxy | Measured days | Signals | Signal rate | Risk avg follow-through | Non-risk avg follow-through |
|:--|--:|--:|--:|--:|--:|
| 5m | 444 | 93 | 0.209459 | -0.00053 | 0.001116 |
| 15m | 444 | 67 | 0.150901 | -0.000566 | 0.000103 |

## Existing Trade Reconciliation
| Group | Trade days | Total implementable PnL | Avg implementable PnL | Win rate | Cost drag |
|:--|--:|--:|--:|--:|--:|
| `all` | 90 | 545.6 | 6.062222 | 0.322222 | 543.9 |
| `combined_risk` | 26 | -274.56 | -10.56 | 0.192308 | 175.06 |
| `non_risk` | 64 | 820.16 | 12.815 | 0.375 | 368.84 |
| `high_importance_macro` | 26 | -274.56 | -10.56 | 0.192308 | 175.06 |
| `no_high_importance_macro` | 64 | 820.16 | 12.815 | 0.375 | 368.84 |

## Coherence Assessment
```json
{
  "directionally_coherent": true,
  "existing_trades_support_non_risk": true,
  "fifteen_min_risk_minus_non_risk": -0.000669,
  "five_min_risk_minus_non_risk": -0.001646,
  "interpretation": "Risk-labeled macro/VIX days underperform non-risk days in both lower-resolution proxies and existing trade outcomes.",
  "proxy_supports_non_risk": true,
  "trade_avg_pnl_risk_minus_non_risk": -23.375
}
```

## Tier Blockers
- `E1 lower-resolution proxy only`
- `No exact 2022-10 ORB entries/exits tested`
- `No new independent data`
- `Existing option outcomes remain under-sampled and underpowered`
- `No E2 acceptance claim`
- `No paper trading, operational validation, or real-money approval`

## Next Safe Action

Keep H-A2 active and implement the exact-data prioritization decision only after reviewing whether the proxy result justifies a narrowly scoped 2022 underlying-bar source plan.
