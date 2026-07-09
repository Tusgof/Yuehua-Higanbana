# H-A2 Exact-Data Prioritization Decision

## Status

- **Date**: 2026-07-05
- **Track**: H-A2 Macro-Conditioned ORB Edge
- **Evidence tier**: E0 decision/control artifact
- **Decision**: H-A2.13 is strong enough to justify a separate narrow exact-data plan, but it does not approve IBKR requests, paid data, a new provider, paper trading, operational validation, or an edge claim.

## Question

Does the directionally coherent H-A2.13 proxy evidence justify a separate narrowly scoped exact-data plan, or should H-A2 be narrowed further before any data-source work?

## Decision

The selected path is:

`draft_narrow_exact_2022_underlying_bar_plan`

This means the next H-A2 artifact may plan how to obtain/import/validate the 2022-10 SPY underlying bars needed for an exact stress rerun against the already-downloaded 2022-10 option quotes.

This decision does not execute that plan.

## Why This Is Not A Data Chase

The hypothesis comes first:

H-A2 asks whether the ORB strategy behaves differently under macro/VIX risk labels. SPY 1-minute bars are only a method for testing exact ORB timing and fill-path claims.

H-A2.13 showed directional coherence:

| Evidence | Result |
|:--|--:|
| Proxy measured days | 444 |
| Daily rows | 463 |
| Trial count | 7 |
| Existing trade days | 90 |
| Combined-risk trade days | 26 |
| Non-risk trade days | 64 |
| Combined-risk avg implementable PnL | -10.56 |
| Non-risk avg implementable PnL | 12.815 |
| Risk minus non-risk avg PnL | -23.375 |

The lower-resolution proxy and existing exact-quote trade outcomes both point in the same direction: risk-labeled macro/VIX days underperform non-risk days.

That is not enough for acceptance. It is enough to justify a narrow exact-data plan because the next exact question is now named:

Can an exact 2022-10 stress rerun falsify or strengthen the H-A2 mechanism under the same non-risk/risk split observed in H-A2.13?

## Resolution Boundary

SPY 1-minute bars are required for:

- exact 2022-10 ORB entry timing,
- breakout ordering,
- stop/target path reconstruction,
- timestamp-aligned option fill timing,
- acceptance-grade exact stress rerun.

SPY 1-minute bars are not required for:

- mechanism proxy review,
- coarse stress/regime review,
- prioritization decisions,
- deciding whether a narrow source plan is worth drafting.

## What Is Allowed Next

A separate H-A2 exact 2022 underlying-bar acquisition/import plan may be drafted.

That plan must:

- state the H-A2 hypothesis first,
- name the exact inference gap,
- limit the first scope to 2022-10 underlying bars before any 2022-09 option-data work,
- explain why 1-minute bars are required for the exact rerun,
- preserve no order transmission,
- preserve no paper trading,
- require coverage, timestamp, and import validation before rerun,
- require user approval for any new provider or paid source,
- avoid treating H-A2.13 as E2 evidence.

## What Is Still Forbidden

This decision does not allow:

- IBKR historical-bar requests,
- paid data,
- a new data provider,
- LLM calls,
- strategy PnL in this artifact,
- paper trading,
- operational validation,
- real-money trading,
- an H-A2 edge claim,
- exact 2022-10 ORB claims.

## Rejected Paths

| Path | Reason |
|:--|:--|
| Request IBKR bars now | H-A2.13 justifies planning, not execution. IBKR remains externally blocked unless local TWS/Gateway is listening and a separate data-only probe plan passes. |
| Buy a new provider now | Any new provider or paid source requires explicit user approval and cost/source policy. Current headroom is only 5.010294 USD. |
| Narrow H-A2 without an exact plan | The proxy evidence is directionally coherent enough to justify a narrow exact-data plan before narrowing the hypothesis further. |
| Paper trading or operational validation | No strategy hypothesis has E2 acceptance. H-A2.13 and this decision are not acceptance-grade evidence. |

## Verification

```powershell
python scripts\validate_h_a2_exact_data_prioritization_decision.py
python -m unittest tests.test_validate_h_a2_exact_data_prioritization_decision
```
