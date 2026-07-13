# Research Readiness Audit

- Status: `blocked`
- Blocker count: 23

## Environment

| Variable | Process env | User env | Machine env |
|:--|:--:|:--:|:--:|
| `DATABENTO_API_KEY` | False | False | False |
| `DATABENTO_SPY0DTE_API` | True | True | False |
| `DATABENTO_API_MO` | True | True | False |
| `DATABENTO_API_AI` | True | True | False |
| `HIGANBANA_OPENROUTER_API` | True | True | False |

## Checks

| Check | Status | Details | Blockers |
|:--|:--|:--|:--|
| macro_calendar | `pass` | - | - |
| vix_vxv | `pass` | - | - |
| news | `blocked` | - | `requires_news_archive_start_by_2022_05_11`, `requires_news_topic_coverage_2022`, `requires_news_topic_coverage_2023`, `requires_news_topic_coverage_2024`, `requires_news_topic_coverage_2025`, `requires_news_topic_coverage_2026`, `requires_news_window_coverage_oos`, `requires_news_window_coverage_reference_pre_break`, `requires_news_window_coverage_train`, `requires_real_news_archive` |
| gdelt_capture_status | `blocked` | files `6`<br>status counts `blocked=6` | `gdelt_capture_not_captured:2023-04-03`, `gdelt_capture_not_captured:2023-04-13`, `gdelt_capture_not_captured:2023-04-14`, `gdelt_capture_not_captured:2023-09-01`, `gdelt_capture_not_captured:2023-09-07`, `gdelt_capture_not_captured:2023-10-02`, `gdelt_capture_unavailable` |
| gdelt_command_plan | `blocked` | retry pressure `cooldown_recommended`<br>next retry `2023-04-17` | `gdelt_retry_cooldown_recommended` |
| paid_cost | `pass` | known cost `$196.358053`<br>guard used `$120.494368`<br>basis `user_reported_actual_usage`<br>remaining `$4.505632` | - |
| research_logs | `pass` | - | - |
| strategy_data | `blocked` | closed trades `90`<br>candidate days `93` | `requires_mintrl_psr_sample_adequacy` |
| new_script_lib_usage | `pass` | new scripts bypassing lib `0` | - |
| exp07_prompt_redesign | `blocked` | - | `requires_real_timestamp_clean_news_cases_for_exp07_prompt_research` |
| exp07_real_news_case_plan | `blocked` | candidate days `71` | `requires_real_news_archive`, `requires_real_timestamp_clean_news_cases` |
| exp07_acceptance | `blocked` | - | `requires_real_strategy_backtest_ablation`, `requires_real_news_archive`, `requires_wider_spy_0dte_data` |
| exp07_strategy_ablation | `blocked` | - | `requires_mintrl_psr_sample_adequacy`, `requires_real_news_archive`, `requires_wider_spy_0dte_data` |
| aug_2023_databento | `ready_for_live_cost_estimate` | requests `322` | - |
| opra_statistics_oi_probe | `pass` | full-day records `541311`<br>intraday records `0`<br>open interest records `180279` | - |
| openrouter_llm | `available` | - | - |

## Next Safe Actions

- H-A2 is formally restricted to prior-close VIX <25 after two independent stress-silence windows (Aug 2024 and Oct 2022); VIX >=25 is blocked/out-of-scope and must not be treated as profitability evidence. The Section 5 fresh OOS 2025-2026 cost plan is ready for user review: 20 untouched dates across prior-VIX <15 and 15-25 buckets, base projection $10.957555, and user-approval ceiling $12.601188. No metadata call or purchase occurred. Next action is user approval or rejection of that ceiling. After approval, refresh live metadata cost and the selected-key guard; stop if the live estimate exceeds the approved ceiling. Do not approve E2, paper trading, operational validation, or real-money trading from this plan.
- News-Unblock priority is now to evaluate alternative timestamp-clean real-news source paths instead of waiting only on GDELT. Use `reports\news_gdelt_doc_api_enrichment_scaffold.md` as the current GDELT scaffold reference, but next write a source-decision artifact comparing feasible real headline/body, publication timestamp, fetch/availability timestamp, licensing, parser/import, and decision-time discipline paths before any live LLM research. Keep GKG as candidate index only; do not broad-download GKG or run LLM research yet.
- Pause additional live GDELT `--execute` retries until HTTP 429 pressure clears; monitor the command plan before retrying one candidate day.
- Do not run another synthetic Exp07 prompt matrix as research; build real timestamp-clean news cases first.
- Use `reports\experiments\exp07_real_news_case_plan.md` as the collection plan before any Exp07 prompt-family run.
- H-G1.24a no-paid local-cache overlap scan is complete and blocked: no additional baseline trade dates have local quote, local SPY bar, and local OI files beyond the current 2-date gamma intersection. H-G1 remains parked; do not run a metadata cost check, paid data download, new gamma ablation, strategy use, paper trading, or true net-gamma claim from this scan. Active edge work should prefer News-Unblock N.7 or H-A2 once their external blockers clear.
