# Exp07 Real News Case Plan

- Status: `blocked`
- Collection status: `ready_to_collect`
- Candidate days: `71`
- Captured candidate days: `0`
- Retry pressure: `cooldown_recommended`
- Next unattempted trade date: `2023-04-14`

## Blockers

- `requires_real_news_archive`
- `requires_real_timestamp_clean_news_cases`

## Required Case Groups

- `normal_quiet_day`
- `scheduled_macro_day`
- `large_intraday_move_day`
- `volatility_spike_day`
- `geopolitical_shock_or_war_risk_day`
- `banking_or_liquidity_stress_day`
- `index_etf_futures_disruption_day`
- `false_alarm_day`

## Prompt Template Families

| Family | Purpose | Failure Mode |
|:--|:--|:--|
| `role_only_analyst` | Test whether a simple expert role can interpret real pre-entry news without policy scaffolding. | Overconfident or vague rationale. |
| `structured_json_classifier` | Test parser stability and consistent decision fields. | Becomes a hidden keyword checklist instead of contextual interpretation. |
| `few_shot_real_news_examples` | Test whether real examples improve ambiguous classification. | Overfits to the chosen examples. |
| `evidence_first_rubric` | Require concrete input evidence before risk classification. | May miss latent risk not explicit in headlines. |
| `scenario_branching_prompt` | Compare benign, base, and stress interpretations before deciding. | Higher cost and more verbose outputs. |
| `self_consistency_ensemble` | Measure agreement across repeated calls or prompt variants. | Higher cost and slower decision path. |

## Required News Fields

- `published_at`
- `fetched_at`
- `source`
- `url`
- `headline`
- `decision_time_et`

## Candidate Queue

| Trade Date | Decision Time | Split | Capture Status |
|:--|:--|:--|:--|
| `2023-04-03` | `2023-04-03T09:30:00-04:00` | `in_sample` | `blocked` |
| `2023-04-13` | `2023-04-13T09:30:00-04:00` | `in_sample` | `blocked` |
| `2023-04-14` | `2023-04-14T09:30:00-04:00` | `in_sample` | `not_attempted` |
| `2023-04-17` | `2023-04-17T09:30:00-04:00` | `in_sample` | `not_attempted` |
| `2023-04-20` | `2023-04-20T09:30:00-04:00` | `in_sample` | `not_attempted` |
| `2023-04-27` | `2023-04-27T09:30:00-04:00` | `in_sample` | `not_attempted` |
| `2023-04-28` | `2023-04-28T09:30:00-04:00` | `in_sample` | `not_attempted` |
| `2023-05-31` | `2023-05-31T09:30:00-04:00` | `in_sample` | `not_attempted` |
| `2023-06-01` | `2023-06-01T09:30:00-04:00` | `in_sample` | `not_attempted` |
| `2023-06-02` | `2023-06-02T09:30:00-04:00` | `in_sample` | `not_attempted` |
| `2023-06-13` | `2023-06-13T09:30:00-04:00` | `in_sample` | `not_attempted` |
| `2023-06-16` | `2023-06-16T09:30:00-04:00` | `in_sample` | `not_attempted` |
| `2023-06-23` | `2023-06-23T09:30:00-04:00` | `in_sample` | `not_attempted` |
| `2023-06-26` | `2023-06-26T09:30:00-04:00` | `in_sample` | `not_attempted` |
| `2023-06-27` | `2023-06-27T09:30:00-04:00` | `in_sample` | `not_attempted` |
| `2023-07-03` | `2023-07-03T09:30:00-04:00` | `in_sample` | `not_attempted` |
| `2023-07-13` | `2023-07-13T09:30:00-04:00` | `in_sample` | `not_attempted` |
| `2023-07-18` | `2023-07-18T09:30:00-04:00` | `in_sample` | `not_attempted` |
| `2023-07-25` | `2023-07-25T09:30:00-04:00` | `in_sample` | `not_attempted` |
| `2023-07-28` | `2023-07-28T09:30:00-04:00` | `in_sample` | `not_attempted` |
| `2023-08-01` | `2023-08-01T09:30:00-04:00` | `in_sample` | `not_attempted` |
| `2023-08-02` | `2023-08-02T09:30:00-04:00` | `in_sample` | `not_attempted` |
| `2023-08-10` | `2023-08-10T09:30:00-04:00` | `in_sample` | `not_attempted` |
| `2023-08-11` | `2023-08-11T09:30:00-04:00` | `in_sample` | `not_attempted` |
| `2023-08-21` | `2023-08-21T09:30:00-04:00` | `in_sample` | `not_attempted` |
| `2023-08-28` | `2023-08-28T09:30:00-04:00` | `in_sample` | `not_attempted` |
| `2023-09-01` | `2023-09-01T09:30:00-04:00` | `in_sample` | `blocked` |
| `2023-09-07` | `2023-09-07T09:30:00-04:00` | `in_sample` | `blocked` |
| `2023-10-02` | `2023-10-02T09:30:00-04:00` | `in_sample` | `blocked` |
| `2023-10-05` | `2023-10-05T09:30:00-04:00` | `in_sample` | `not_attempted` |
| `2023-10-23` | `2023-10-23T09:30:00-04:00` | `in_sample` | `not_attempted` |
| `2023-10-25` | `2023-10-25T09:30:00-04:00` | `in_sample` | `not_attempted` |
| `2023-10-27` | `2023-10-27T09:30:00-04:00` | `in_sample` | `not_attempted` |
| `2023-10-31` | `2023-10-31T09:30:00-04:00` | `in_sample` | `not_attempted` |
| `2023-11-09` | `2023-11-09T09:30:00-05:00` | `in_sample` | `not_attempted` |
| `2023-11-10` | `2023-11-10T09:30:00-05:00` | `in_sample` | `not_attempted` |
| `2023-11-13` | `2023-11-13T09:30:00-05:00` | `in_sample` | `not_attempted` |
| `2023-11-20` | `2023-11-20T09:30:00-05:00` | `in_sample` | `not_attempted` |
| `2023-11-27` | `2023-11-27T09:30:00-05:00` | `in_sample` | `not_attempted` |
| `2023-11-30` | `2023-11-30T09:30:00-05:00` | `in_sample` | `not_attempted` |
| `2023-12-06` | `2023-12-06T09:30:00-05:00` | `in_sample` | `not_attempted` |
| `2023-12-12` | `2023-12-12T09:30:00-05:00` | `in_sample` | `not_attempted` |
| `2024-01-05` | `2024-01-05T09:30:00-05:00` | `oos` | `not_attempted` |
| `2024-01-08` | `2024-01-08T09:30:00-05:00` | `oos` | `not_attempted` |
| `2024-01-10` | `2024-01-10T09:30:00-05:00` | `oos` | `not_attempted` |
| `2024-01-11` | `2024-01-11T09:30:00-05:00` | `oos` | `not_attempted` |
| `2024-01-29` | `2024-01-29T09:30:00-05:00` | `oos` | `not_attempted` |
| `2024-01-30` | `2024-01-30T09:30:00-05:00` | `oos` | `not_attempted` |
| `2024-02-13` | `2024-02-13T09:30:00-05:00` | `oos` | `not_attempted` |
| `2024-02-14` | `2024-02-14T09:30:00-05:00` | `oos` | `not_attempted` |
| `2024-02-27` | `2024-02-27T09:30:00-05:00` | `oos` | `not_attempted` |
| `2024-03-06` | `2024-03-06T09:30:00-05:00` | `oos` | `not_attempted` |
| `2024-03-07` | `2024-03-07T09:30:00-05:00` | `oos` | `not_attempted` |
| `2024-03-12` | `2024-03-12T09:30:00-04:00` | `oos` | `not_attempted` |
| `2024-03-20` | `2024-03-20T09:30:00-04:00` | `oos` | `not_attempted` |
| `2024-04-02` | `2024-04-02T09:30:00-04:00` | `oos` | `not_attempted` |
| `2024-04-08` | `2024-04-08T09:30:00-04:00` | `oos` | `not_attempted` |
| `2024-04-10` | `2024-04-10T09:30:00-04:00` | `oos` | `not_attempted` |
| `2024-04-16` | `2024-04-16T09:30:00-04:00` | `oos` | `not_attempted` |
| `2024-04-18` | `2024-04-18T09:30:00-04:00` | `oos` | `not_attempted` |
| `2024-05-02` | `2024-05-02T09:30:00-04:00` | `oos` | `not_attempted` |
| `2024-05-03` | `2024-05-03T09:30:00-04:00` | `oos` | `not_attempted` |
| `2024-05-15` | `2024-05-15T09:30:00-04:00` | `oos` | `not_attempted` |
| `2024-05-20` | `2024-05-20T09:30:00-04:00` | `oos` | `not_attempted` |
| `2024-05-30` | `2024-05-30T09:30:00-04:00` | `oos` | `not_attempted` |
| `2024-05-31` | `2024-05-31T09:30:00-04:00` | `oos` | `not_attempted` |
| `2024-06-13` | `2024-06-13T09:30:00-04:00` | `oos` | `not_attempted` |
| `2024-06-18` | `2024-06-18T09:30:00-04:00` | `oos` | `not_attempted` |
| `2024-06-21` | `2024-06-21T09:30:00-04:00` | `oos` | `not_attempted` |
| `2024-06-27` | `2024-06-27T09:30:00-04:00` | `oos` | `not_attempted` |
| `2024-06-28` | `2024-06-28T09:30:00-04:00` | `oos` | `not_attempted` |

## Next Step

Pause live GDELT retries, then capture one candidate day at a time after 429 pressure clears.
