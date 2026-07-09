# H-A2 Proxy-First Robustness Report

- Conclusion: ยังสรุปไม่ได้ (E1)
- Daily rows: 463
- Measured 5m / 15m days: 444 / 444
- Existing trade days: 90
- Directionally consistent: True
- 5m non-risk minus risk: 0.001646
- 15m non-risk minus risk: 0.000669
- Existing trade non-risk minus risk: 23.375

## Macro / VIX Buckets

| Bucket | Days | 5m avg | 15m avg | Trade days | Avg implementable PnL |
|:--|--:|--:|--:|--:|--:|
| macro_only | 108 | -0.00053 | -0.000566 | 26 | -10.56 |
| vix_risk_only | 6 | None | None | 0 | None |
| macro_plus_vix_risk | 1 | None | None | 0 | None |
| no_macro_no_vix_risk | 348 | 0.001116 | 0.000103 | 64 | 12.815 |

## Guardrails

- No network, paid data, broker request, new provider, or LLM call was used.
- This is not exact 2022-10 ORB replay and does not approve paper trading.
- Next safe action: Use H-A2.19 as E1 prioritization evidence only: proxy evidence remains directionally coherent, but exact 2022-10 ORB replay still requires real 2022 SPY bars before any E2 claim.
