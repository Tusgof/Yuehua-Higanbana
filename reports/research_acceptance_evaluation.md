# Research Acceptance Evaluation

- Status: `blocked`
- Operational validation allowed: `False`
- Paper trading allowed: `False`
- Real money allowed: `False`
- Candidate hypotheses: 0

## Hypotheses

| ID | Status | Max tier | E2+ candidate | Evidence paths |
|:--|:--|:--|:--|--:|
| `H-A1` | `falsified-as-stated` | `E1` | `False` | 2 |
| `H-A2` | `active` | `E1` | `False` | 29 |
| `H-B1` | `falsified` | `E1` | `False` | 1 |
| `H-B2` | `parked` | `E1` | `False` | 2 |
| `H-G1` | `parked` | `E1` | `False` | 23 |
| `H-L1` | `active_blocked` | `E1` | `False` | 4 |
| `H-L2` | `proposed` | `E0` | `False` | 1 |
| `H-L3` | `active_blocked` | `E0` | `False` | 1 |

## Blockers

- `no_strategy_hypothesis_at_e2_or_higher`
- `readiness:gdelt_capture_not_captured:2023-04-03`
- `readiness:gdelt_capture_not_captured:2023-04-13`
- `readiness:gdelt_capture_not_captured:2023-04-14`
- `readiness:gdelt_capture_not_captured:2023-09-01`
- `readiness:gdelt_capture_not_captured:2023-09-07`
- `readiness:gdelt_capture_not_captured:2023-10-02`
- `readiness:gdelt_capture_unavailable`
- `readiness:gdelt_retry_cooldown_recommended`
- `readiness:requires_mintrl_psr_sample_adequacy`
- `readiness:requires_news_archive_start_by_2022_05_11`
- `readiness:requires_news_topic_coverage_2022`
- `readiness:requires_news_topic_coverage_2023`
- `readiness:requires_news_topic_coverage_2024`
- `readiness:requires_news_topic_coverage_2025`
- `readiness:requires_news_topic_coverage_2026`
- `readiness:requires_news_window_coverage_oos`
- `readiness:requires_news_window_coverage_reference_pre_break`
- `readiness:requires_news_window_coverage_train`
- `readiness:requires_real_news_archive`
- `readiness:requires_real_strategy_backtest_ablation`
- `readiness:requires_real_timestamp_clean_news_cases`
- `readiness:requires_real_timestamp_clean_news_cases_for_exp07_prompt_research`
- `readiness:requires_wider_spy_0dte_data`
- `research_readiness_blocked`

## Gate Requirements

- `registered_hypothesis_at_e2_or_higher`
- `chronological_validation_without_oos_tuning`
- `mintrl_psr_dsr_handling`
- `implementable_pnl_with_cost_drag`
- `big_day_dependency_survival`
- `regime_coverage_or_explicit_scope_restriction`
- `benchmark_and_drawdown_comparison`
- `paid_cost_guard_pass`

## Candidate Gate Results

- none
