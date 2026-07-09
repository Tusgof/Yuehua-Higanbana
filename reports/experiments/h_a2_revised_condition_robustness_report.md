# H-A2 Revised Condition Robustness Report

- Status: `complete`
- Conclusion: `ยังสรุปไม่ได้`
- Evidence tier: `E1`
- Locked threshold: `0.001`
- Threshold search used: `False`
- OOS tuning used: `False`

## Core Counts

| Metric | Value |
|:--|--:|
| Baseline OOS non-risk trades | 34 |
| Retained OOS trades | 13 |
| Skipped OOS trades | 21 |
| Retention rate | 0.382353 |

## Robustness Checks

| Check | Result |
|:--|:--|
| Threshold provenance | `True` |
| Big-day dependency | `survives_basic_trim_but_underpowered` |
| Concentration | `not_single_bucket_dominated` |
| Retained minus skipped avg PnL | `106.556776` |
| Sample adequacy | `diagnostic_underpowered` |

## Decision

- Decision: `run_locked_condition_robustness_followup_or_exact_replay_when_bars_clear`
- Next safe action: Keep H-A2 active as E1 prioritization evidence. The next safe step is either exact replay after the 2022 SPY bar blocker clears, or a separately pre-registered local follow-up that does not change threshold 0.001.

## Guardrails

- No network, paid data, broker request, IBKR request, GDELT live retry, or LLM call was used.
- No threshold search or OOS tuning was used.
- No paper trading, operational validation, real-money launch, exact 2022 ORB replay, or E2 claim is allowed.
