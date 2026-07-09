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
| exp07_prompt_redesign | `blocked` | - | `requires_real_timestamp_clean_news_cases_for_exp07_prompt_research` |
| exp07_real_news_case_plan | `blocked` | candidate days `71` | `requires_real_news_archive`, `requires_real_timestamp_clean_news_cases` |
| exp07_acceptance | `blocked` | - | `requires_real_strategy_backtest_ablation`, `requires_real_news_archive`, `requires_wider_spy_0dte_data` |
| exp07_strategy_ablation | `blocked` | - | `requires_mintrl_psr_sample_adequacy`, `requires_real_news_archive`, `requires_wider_spy_0dte_data` |
| aug_2023_databento | `ready_for_live_cost_estimate` | requests `322` | - |
| opra_statistics_oi_probe | `pass` | full-day records `541311`<br>intraday records `0`<br>open interest records `180279` | - |
| openrouter_llm | `available` | - | - |

## Next Safe Actions

- H-A2.63 targeted data/regime expansion plan is pre-registered as E0 control evidence after H-A2.62. It converts the blocker from vague sample-size shortage into specific target sets ['train_candidate_geometry_backfill', 'normal_control_geometry_pack', 'stress_regime_geometry_pack', 'oos_locked_rule_evaluation_pack']: train candidate geometry backfill first, normal/control geometry pack, stress-regime geometry pack, and future OOS locked-rule evaluation pack. Next safe H-A2 work is H-A2.64: h_a2_targeted_geometry_cache_inventory_and_cost_estimate as cache inventory plus metadata/cost estimate only. Required missing fields include entry strike mapping, entry implementable debit, bid/ask width, quote size/liquidity, forced-close value, regime labels, and MinTRL/PSR coverage. Do not download data yet, do not broad-buy calendar data, do not run OOS rule evaluation, do not select thresholds, do not call LLMs/GDELT, do not request broker/order work, do not approve paper trading, operational validation, real-money trading, or claim E2 from H-A2.63.
- News-Unblock priority is now to evaluate alternative timestamp-clean real-news source paths instead of waiting only on GDELT. Use `reports\news_gdelt_doc_api_enrichment_scaffold.md` as the current GDELT scaffold reference, but next write a source-decision artifact comparing feasible real headline/body, publication timestamp, fetch/availability timestamp, licensing, parser/import, and decision-time discipline paths before any live LLM research. Keep GKG as candidate index only; do not broad-download GKG or run LLM research yet.
- Pause additional live GDELT `--execute` retries until HTTP 429 pressure clears; monitor the command plan before retrying one candidate day.
- Do not run another synthetic Exp07 prompt matrix as research; build real timestamp-clean news cases first.
- Use `reports\experiments\exp07_real_news_case_plan.md` as the collection plan before any Exp07 prompt-family run.
- H-A2.17 IBKR readiness gate rerun is complete and externally blocked: Python clients are available (`ib_insync, ibapi`), but no local IBKR API port is listening on 7497/7496/4002/4001. No historical data was requested, no order was transmitted, no paid data was used, and no new provider was introduced. Next start local TWS/Gateway with API enabled and confirm market-data permission, then rerun the readiness probe. If local IBKR cannot be made available, stop for clear user direction before Alpaca or any new paid provider. Do not treat fixture bars as real data, rerun exact H-A2 stress diagnostics, approve paper trading, or claim H-A2 edge from H-A2.16/H-A2.17.
- H-G1.24a no-paid local-cache overlap scan is complete and blocked: no additional baseline trade dates have local quote, local SPY bar, and local OI files beyond the current 2-date gamma intersection. H-G1 remains parked; do not run a metadata cost check, paid data download, new gamma ablation, strategy use, paper trading, or true net-gamma claim from this scan. Active edge work should prefer News-Unblock N.7 or H-A2 once their external blockers clear.
