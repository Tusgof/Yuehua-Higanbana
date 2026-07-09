# H-A2 Residual Adverse-Day Analysis

- Status: `complete`
- Conclusion: `ยังสรุปไม่ได้`
- Evidence tier: `E1`
- Research log required: `True`
- Source preregistration: `experiments\h_a2_residual_adverse_day_analysis_preregistration.json`
- Source summary: `reports\experiments\h_a2_lower_resolution_proxy_summary.json`
- Search log: `reports\diagnostics\search_logs\h_a2_residual_adverse_day_analysis_search_log.jsonl`

## Sample Counts

| Bucket | Count |
|:--|--:|
| Daily rows | 463 |
| Trade days | 90 |
| Non-risk trade days | 64 |
| Non-risk losing trade days | 40 |
| Macro-only trade days | 26 |
| Macro-only losing trade days | 21 |

## Residual Loss Profile

- Non-risk loss rate: `0.625`
- Average non-risk losing implementable PnL: `-32.935`
- OOS loss share inside non-risk losses: `0.525`
- Negative 5-minute followthrough loss share: `0.75`

## Macro-Only Loss Profile

- Macro-only loss rate: `0.807692`
- Average macro-only losing implementable PnL: `-34.940952`
- Macro event type counts: `{'CPI': 8, 'FOMC_DECISION': 1, 'FOMC_MINUTES': 1, 'JOLTS': 6, 'NFP': 2, 'PCE': 4}`

## Decision

- Decision: `revise_h_a2_before_exact_replay`
- Revise H-A2: `True`
- Park H-A2: `False`
- Prioritize exact replay: `True`
- Next safe action: Pre-register a revised H-A2 condition that adds opening-followthrough failure-mode checks before any exact replay, paid data, IBKR request, LLM call, or paper trading.

## Guardrails

- No network, paid data, broker request, IBKR request, GDELT live retry, or LLM call was used.
- No paper trading, operational validation, real-money launch, or E2 claim is allowed.
- This analysis is E1 diagnostic evidence only.
