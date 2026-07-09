# H-A2 Revised Opening-Followthrough Condition Report

- Status: `complete`
- Conclusion: `ยังสรุปไม่ได้`
- Evidence tier: `E1`
- Locked threshold: `0.001`
- Selected trial: `train_threshold_0.001`
- Search log: `reports\experiments\search_logs\h_a2_revised_opening_followthrough_condition_search_log.jsonl`

## Sample Counts

| Bucket | Count |
|:--|--:|
| Baseline train non-risk trades | 30 |
| Baseline OOS non-risk trades | 34 |
| Revised train trades | 16 |
| Revised OOS trades | 13 |
| Skipped OOS trades | 21 |

## Train-Only Threshold And OOS Holdout

| Split | Baseline trades | Baseline loss rate | Revised trades | Revised loss rate | Revised avg PnL |
|:--|--:|--:|--:|--:|--:|
| Train | 30 | 0.633333 | 16 | 0.3125 | 67.44 |
| OOS | 34 | 0.617647 | 13 | 0.076923 | 72.901538 |

## Decision

- Decision: `prioritize_exact_replay_when_external_bar_blocker_clears`
- Next safe action: Keep the revised condition as E1 prioritization evidence and prioritize exact replay when the 2022 SPY bar blocker clears; no paid data, IBKR request, LLM call, or paper trading is approved from this result.

## Guardrails

- No network, paid data, broker request, IBKR request, GDELT live retry, or LLM call was used.
- No paper trading, operational validation, real-money launch, exact 2022 ORB replay, or E2 claim is allowed.
- This analysis is E1 diagnostic evidence only.
