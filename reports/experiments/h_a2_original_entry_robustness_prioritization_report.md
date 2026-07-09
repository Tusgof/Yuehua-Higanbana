# H-A2 Original-Entry Robustness And Prioritization Report

- Status: `complete`
- Conclusion: `ยังสรุปไม่ได้`
- Evidence tier: `E1`
- Decision: `prioritize_independent_validation_plan_under_e1`

## Locked Rule

- Candidate decision time ET: `09:35:00`
- Threshold: `0.001`
- Features: `clean_macro_vix_condition`, `proxy_5m_followthrough`
- Forbidden components stayed unused: 15-minute conflict, delayed-entry quote/fill, new OOS-selected filter.

## Sample

| Group | Train | OOS |
|:--|--:|--:|
| Baseline non-risk | 30 | 34 |
| Retained | 16 | 14 |
| Skipped | 14 | 20 |

## Robustness Checks

- Leave-one-out min avg PnL: `63.209231`
- Largest retained day share: `0.151153`
- Big-day status: `pass_directional_but_underpowered`
- Largest calendar/regime bucket share: `0.5`
- Concentration status: `concentrated_underpowered`
- Retained minus skipped avg PnL: `106.0`
- Skip-cost status: `directionally_useful_but_sample_reducing`

## Decision

- Next safe action: Pre-register an independent validation-data plan or no-paid validation feasibility plan before any paid data, IBKR request, exact replay, paper trading, or E2 claim.
- Claims stay capped at E1. This does not approve paid data, exact replay, IBKR request, LLM call, paper trading, operational validation, or real-money trading.
