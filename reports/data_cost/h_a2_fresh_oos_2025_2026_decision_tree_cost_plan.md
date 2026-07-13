# H-A2 Fresh OOS 2025-2026 Decision-Tree Cost Plan

- Status: `awaiting_user_approval`
- Mode: `plan_only_no_network_no_purchase`
- Hypothesis: `H-A2`
- Proposed approval ceiling: `$12.601188`
- Purchase performed: `false`

## Why This Block Exists

The Aug 2024 and Oct 2022 stress windows both produced zero H-A2 candidates. That evidence supports a formal restriction: H-A2 is evaluated only when prior-close VIX is below 25 and there is no high-importance macro event. It does not support buying more high-VIX months to validate the current rule.

The next missing evidence is fresh OOS data that was not used in the original M5.5 search or later rule diagnostics. The proposed block covers both in-scope volatility buckets:

| Window | VIX bucket | Dates | High-macro dates | Existing raw cache |
|:--|:--|--:|--:|--:|
| 2025 low-VIX OOS | prior VIX `< 15` | 10 | 0 | 0 |
| 2026 normal-VIX OOS | prior VIX `15-25` | 10 | 0 | 0 |

The exact dates are recorded in the JSON artifact. Date selection uses only locally archived VIX and macro labels, not strategy outcomes.

## Section 5 Decision Tree

1. **Q0 passes**: the named gap is H-A2 fresh OOS search decontamination inside the formal VIX `< 25` scope.
2. **Q1 does not fill the gap**: none of the 20 target dates has matching raw option data in the local cache.
3. **Q2 is conditional**: this is a bounded candidate-density pilot below the `$15` cheap-falsification ceiling. It does not promise enough trades to reach MinTRL.
4. **Q3 does not approve E2 validation**: MinTRL against the full null set is unresolved, so this block cannot be called acceptance-grade evidence by itself.
5. **Q4 is not applicable**: no new field or provider is introduced.

## Cost Projection

The projection uses two prior 10-date control-pack estimates totaling `$10.957555`, or `$0.54787775` per date. No live metadata API call was made in this session.

| Component | Projected cost |
|:--|--:|
| Base projection, 20 dates | `$10.957555` |
| 15% contingency | `$1.643633` |
| **User approval ceiling** | **`$12.601188`** |

Selected key for a later approved action: `DATABENTO_API_MO`. Projected MO usage at the ceiling is `$18.000101`, and projected combined MO/AI usage is `$23.558743`, both below their guards.

## Purchase Gate

This artifact does not authorize a purchase. The user must approve the `$12.601188` ceiling first. After approval, refresh the live metadata estimate and selected-key cost guard. Stop if the live estimate exceeds the approved ceiling.

After importing all 20 dates, report candidate density by VIX bucket and cost per candidate. There is no automatic expansion. Fewer than 2 candidates, or a worse MinTRL cost projection, returns H-A2 to hypothesis revision.

This plan does not approve E2, paper trading, operational validation, real-money trading, or any extrapolation to prior-close VIX `>= 25`.
