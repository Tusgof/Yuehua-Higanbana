# H-A2 Decision After Two Exact Replays

## Status
- **Hypothesis**: H-A2
- **Evidence tier**: E0
- **Status**: decision complete
- **Created**: 2026-07-08
- **Controlling JSON**: `experiments/h_a2_post_two_exact_replay_decision.json`

## Why This Exists
H-A2 now has two bounded exact replay results:

| Date | Direction | Mid PnL | Implementable PnL | Cost drag |
|:--|:--|--:|--:|--:|
| `2025-02-11` | call | `-22.00` | `-26.56` | `4.56` |
| `2025-05-05` | call | `-28.00` | `-32.56` | `4.56` |

Both trades lost money after implementable costs. This is still too small to falsify the broader H-A2 family, but it is enough to stop blind expansion of the same locked condition.

## Decision
The next H-A2 step is:

`revise_h_a2_mechanism_before_more_sample_expansion`

The next artifact should define the market mechanism first: what condition should make ORB debit spreads work, what evidence would falsify that condition, and what sample/regime expansion is justified by that logic.

## What This Does Not Permit
- No new paid data.
- No exact replay expansion.
- No threshold search.
- No OOS-selected filter.
- No IBKR request.
- No LLM call.
- No GDELT retry.
- No paper trading, operational validation, real-money trading, or E2 claim.

## Verification
Run:

```powershell
python scripts\validate_h_a2_post_two_exact_replay_decision.py
python -m unittest tests.test_validate_h_a2_post_two_exact_replay_decision
```
