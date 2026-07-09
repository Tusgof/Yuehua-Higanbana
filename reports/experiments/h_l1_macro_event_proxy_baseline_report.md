# H-L1 Macro-Event Proxy Baseline Report

- Conclusion: ยังสรุปไม่ได้ (E1)
- Not LLM/news evidence: True
- Deterministic signal present: True

## Combined Macro / VIX Baseline

| Bucket | Days | 5m avg | 15m avg | Trade days | Avg implementable PnL | Adverse trade-day rate |
|:--|--:|--:|--:|--:|--:|--:|
| macro_event_only | 108 | -0.00053 | -0.000566 | 26 | -10.56 | 0.807692 |
| vix_risk_only | 6 | None | None | 0 | None | None |
| macro_plus_vix_risk | 1 | None | None | 0 | None | None |
| no_macro_no_vix_risk | 348 | 0.001116 | 0.000103 | 64 | 12.815 | 0.625 |

## Guardrails

- No network, paid data, GDELT retry, broker request, new provider, or LLM call was used.
- This result cannot validate an LLM gate or real news sentiment.
- Next safe action: Keep live LLM research blocked, but continue timestamp-clean news collection when source cooldown/policy allows; future LLM scores must beat this deterministic baseline.
