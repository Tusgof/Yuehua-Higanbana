# H-A2 Breakeven-Aware Rule Train Diagnostic

- Status: `complete`
- Evidence tier: `E1`
- Conclusion: `ยังสรุปไม่ได้`
- Decision: `write_targeted_data_regime_expansion_plan`

## Main Finding

Train-only surrogate trials can describe directional followthrough behavior, but the local train rows do not contain the per-candidate entry strike mapping, implementable debit, bid/ask width, and liquidity fields needed to lock a true breakeven-aware option rule.

## Feature Audit

- Train trade days checked: `30`
- Can lock true breakeven-aware rule: `False`
- Missing fields:
  - `train_distribution_nearest_discrete_long_strike`
  - `train_distribution_short_strike_width`
  - `train_distribution_entry_mid_debit`
  - `train_distribution_entry_implementable_debit`
  - `train_distribution_entry_bid_ask_width`
  - `train_distribution_entry_quote_size_or_liquidity`
  - `train_distribution_cost_adjusted_strike_reachability_target`

## Strike-Reachability Target

For a call debit vertical, the post-entry underlying move must be large enough that the selected long strike is reached or nearly reached and the forced-close spread value can overcome entry implementable debit, bid/ask friction, and $0.64 per-leg fees. Implementable PnL, not mid PnL, governs the target.

| Date | Entry | Close | Long strike | Required move | Realized move | Shortfall | Implementable PnL |
|:--|--:|--:|--:|--:|--:|--:|--:|
| 2025-02-11 | 603.52 | 604.93 | 605.00 | 1.48 | 1.41 | 0.07 | -26.56 |
| 2025-05-05 | 563.12 | 564.38 | 565.00 | 1.88 | 1.26 | 0.62 | -32.56 |

## Train-Only Surrogate Trials

| Trial | Retained train days | Avg implementable PnL | Loss rate | Selected for trading |
|:--|--:|--:|--:|:--:|
| `train_baseline_non_risk` | 30 | 19.306667 | 0.633333 | False |
| `train_followthrough_ge_0` | 17 | 61.616471 | 0.352941 | False |
| `train_followthrough_ge_0.001` | 16 | 67.44 | 0.3125 | False |
| `train_followthrough_ge_0.002` | 15 | 73.706667 | 0.266667 | False |
| `train_followthrough_ge_0.003` | 13 | 86.132308 | 0.230769 | False |
| `train_followthrough_ge_0.005` | 8 | 131.815 | 0.0 | False |

## Decision

- Next safe action: Pre-register H-A2.63 targeted data/regime expansion plan for breakeven-aware ORB evidence. The plan must name the minimum option-chain fields and windows needed to compute entry strike mapping, entry implementable debit, bid/ask width, liquidity, forced-close value, regime labels, and MinTRL/PSR coverage before any paid download or OOS rule evaluation.
- This diagnostic does not approve paid data by itself. The next artifact must specify the data fields, windows, regimes, and cost gate.

## Guardrails

- No network, paid data, new provider, broker request, IBKR request, GDELT retry, or LLM call was used.
- No OOS tuning, OOS-selected filter, exact replay expansion, E2 claim, paper trading, operational validation, or real-money trading is allowed.
