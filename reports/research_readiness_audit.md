# Research Readiness Audit

- Status: `blocked`
- Blocker count: 22

## Environment

| Variable | Process env | User env | Machine env |
|:--|:--:|:--:|:--:|
| `DATABENTO_API_KEY` | False | False | False |
| `DATABENTO_SPY0DTE_API` | True | True | False |
| `HIGANBANA_OPENROUTER_API` | True | True | False |

## Checks

| Check | Status | Details | Blockers |
|:--|:--|:--|:--|
| macro_calendar | `pass` | - | - |
| vix_vxv | `pass` | - | - |
| news | `blocked` | - | `requires_news_archive_start_by_2022_05_11`, `requires_news_topic_coverage_2022`, `requires_news_topic_coverage_2023`, `requires_news_topic_coverage_2024`, `requires_news_topic_coverage_2025`, `requires_news_topic_coverage_2026`, `requires_news_window_coverage_oos`, `requires_news_window_coverage_reference_pre_break`, `requires_news_window_coverage_train`, `requires_real_news_archive` |
| gdelt_capture_status | `blocked` | files `5`<br>status counts `blocked=5` | `gdelt_capture_not_captured:2023-04-03`, `gdelt_capture_not_captured:2023-04-13`, `gdelt_capture_not_captured:2023-09-01`, `gdelt_capture_not_captured:2023-09-07`, `gdelt_capture_not_captured:2023-10-02`, `gdelt_capture_unavailable` |
| gdelt_command_plan | `blocked` | retry pressure `cooldown_recommended`<br>next retry `2023-04-14` | `gdelt_retry_cooldown_recommended` |
| paid_cost | `pass` | known cost `$173.988357`<br>guard used `$109.082227`<br>basis `user_reported_actual_usage`<br>remaining `$15.917773` | - |
| research_logs | `pass` | - | - |
| strategy_data | `blocked` | closed trades `90`<br>candidate days `93` | `requires_mintrl_psr_sample_adequacy` |
| exp07_prompt_redesign | `blocked` | - | `requires_real_timestamp_clean_news_cases_for_exp07_prompt_research` |
| exp07_real_news_case_plan | `blocked` | candidate days `71` | `requires_real_news_archive`, `requires_real_timestamp_clean_news_cases` |
| exp07_acceptance | `blocked` | - | `requires_real_strategy_backtest_ablation`, `requires_real_news_archive`, `requires_wider_spy_0dte_data` |
| exp07_strategy_ablation | `blocked` | - | `requires_mintrl_psr_sample_adequacy`, `requires_real_news_archive`, `requires_wider_spy_0dte_data` |
| aug_2023_databento | `ready_for_live_cost_estimate` | requests `322` | - |
| opra_statistics_oi_probe | `pass` | full-day records `541311`<br>intraday records `0`<br>open interest records `180279` | - |
| openrouter_llm | `available` | - | - |

## Next Safe Actions

- Pause additional live GDELT `--execute` retries until HTTP 429 pressure clears; monitor the command plan before retrying one candidate day.
- Do not run another synthetic Exp07 prompt matrix as research; build real timestamp-clean news cases first.
- Use `reports\experiments\exp07_real_news_case_plan.md` as the collection plan before any Exp07 prompt-family run.
- Before any further broad Databento download, use `reports\risk_first_data_audit.md`, `reports\greeks_oi_enrichment_probe_report.md`, `docs\GAMMA_AGGREGATION_VALIDATION_POLICY.md`, and `reports\diagnostics\gamma_aggregation_diagnostic_summary.json` as the pre-purchase checkpoint: expand the pre-registered H-G1 gamma/OI regime date set, choose missing-regime H-A2 stress/pre-break coverage, or revise toward a higher-density strategy hypothesis; then re-run paid-cost/readiness audits and confirm actual provider usage remains below the stop threshold.
