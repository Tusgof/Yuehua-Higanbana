# H-A2 Locked-Condition Signal Attribution Report

- Status: `complete`
- Hypothesis: `H-A2`
- Evidence tier: `E1`
- Conclusion: `ยังสรุปไม่ได้`
- Locked threshold: `0.001`

## Result

The locked threshold remains cleanly fixed, but the full condition is not known at the original 09:35 ET entry decision because it includes a 15-minute conflict check. Treat it as delayed-entry candidate and diagnostic proxy only.

## Classification

- Full-condition classification: `delayed_entry_candidate_and_diagnostic_proxy_only`
- Deployable original-entry filter allowed: `False`
- Delayed-entry candidate allowed: `True`
- Diagnostic proxy only: `True`

## Timestamp Audit

| Feature | Window ET | Known by 09:35 ET | Gap minutes |
|:--|:--|:--:|--:|
| `proxy_5m_followthrough` | `09:30:00-09:35:00` | `True` | 0 |
| `no_adverse_measured_15m_conflict` | `09:30:00-09:45:00` | `False` | 10 |

## Guardrails

- No threshold search.
- No new OOS-selected filter.
- No network, paid data, IBKR request, GDELT retry, or LLM call.
- No paper-trading, operational-validation, real-money, or E2 claim.

## Next Safe Action

Either run a separately pre-registered delayed-entry H-A2 test using local artifacts only, or revise H-A2 toward a timestamp-clean original-entry rule. Do not run exact replay, paid data, IBKR request, LLM call, paper trading, or E2 claim from H-A2.27.
