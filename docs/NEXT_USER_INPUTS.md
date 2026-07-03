# NEXT_USER_INPUTS.md

## Current State

The non-interactive implementation pass is complete through the fixture/simulation scaffold:

- Data source audit and canonical contracts exist.
- Synthetic raw fixture imports into normalized JSONL.
- Registry manifest flow records provider, coverage, schema version, and raw hash.
- ORB, capped-risk spread construction, filters, NOVI proxy, and DeepSeek/OpenRouter dry-run contracts exist.
- Fixture backtest engine supports fills, exits, sizing, benchmark, and append-only JSONL.
- Experiment manifests, fixture report generation, charts, and acceptance gate exist.
- IBKR operational bridge is dry-run only and blocks live transmit by default.
- Provider sample spec, synthetic OptionsDX-like/ThetaData-like adapter templates, a provider sample import command, and a Databento cost-estimator report exist for validating the first real data path.
- User-approved one-month Databento pilot is downloaded, cache-audited, inspected, and normalized to canonical 0DTE option quotes.
- SPY underlying 1-minute bar cost plan exists for the same Jan 2024 pilot window; estimated Databento cost is about `$0.006720364094`.
- Jan 2024 SPY underlying 1-minute bars are downloaded/cached and normalized to canonical `spy_bar` JSONL: 10,738 records from 2024-01-02 through 2024-01-31.
- Jan 2024 pilot adapter joined SPY bars with 0DTE option quotes and found 6 Sub-System A candidate-ready days out of 21 dates.
- Jan 2024 pilot PnL ran on those candidates: 4 closed forced-1545 trades, 2 skipped for missing close quotes, pilot-only total net PnL `$270.00` before commission sensitivity.
- Jan 2024 pilot sensitivity ran 10 scenarios; worst strict full-spread stress result was `$242.00` net PnL and the pilot status is `healthy_enough_for_wider_data_pilot`.
- User approved continuing low-cost Databento research downloads without per-run approval inside the already estimated SPY-only scope.
- OpenRouter/DeepSeek adapter uses env var `HIGANBANA_OPENROUTER_API` and model id `deepseek/deepseek-v4-flash`; it now reads the Windows user env when a fresh process env does not contain the key, without printing the secret. Controlled Exp07 v12 still rejects raw LLM gate usage and only marks the guarded policy candidate as passing the prompt-matrix criteria. New live prompt runs preserve token usage and USD cost metadata when OpenRouter returns it.
- Macro calendar source selection v1 exists in `docs\MACRO_CALENDAR_SOURCE_PLAN.md`, with official/free sources selected. The 2022-2026 official-source backfill has been captured, converted, imported to canonical `macro_event` JSONL, and passes the macro coverage audit for required event-type presence across reference, train, OOS, and each year from 2022 through 2026.
- VIX/VXV source selection now uses official Cboe public CSVs: VIX history plus VIX3M history mapped into the project `vxv_close` field. The 2022-2026 capture is imported to canonical `vix_vxv` JSONL and passes `scripts\audit_vix_vxv_coverage.py`.
- News source selection v1 exists in `docs\NEWS_SOURCE_PLAN.md`, with GDELT selected as the primary free archive candidate and key-required Alpha Vantage/NewsAPI deferred. A GDELT capture dry-run tool, candidate-day command planner, single-snapshot importer, directory importer, and news coverage auditor exist, but successful real GDELT snapshot capture/archive is still pending after small 2026-06-30 probes returned HTTP 429. The latest per-day live capture status is stored under `reports\news_gdelt_capture_status`; `reports\news_gdelt_capture_status\2023-04-03.json`, `reports\news_gdelt_capture_status\2023-09-01.json`, `reports\news_gdelt_capture_status\2023-09-07.json`, and `reports\news_gdelt_capture_status\2023-10-02.json` are all `blocked` with blocker `gdelt_capture_unavailable`. The no-network retry plan is stored at `reports\news_gdelt_capture_command_plan.md` with 71 candidate-day commands, currently reports `blocked=4` daily statuses, points to `2023-04-13` as the next unattempted retry date, and marks `retry_pressure.status` as `cooldown_recommended` until HTTP 429 pressure clears. The directory importer summary is stored at `reports\news_gdelt_capture_directory_import_summary.md` from fixture data. The coverage audit is `blocked` because no canonical real news archive exists yet.
- Exp07 guarded-policy strategy ablation design v1 exists in `docs\EXP07_STRATEGY_ABLATION_PLAN.md`, and the status runner writes a blocked readiness artifact; real ablation remains blocked until wider data, real news archive, and `N >= 500` trade sample size exist. The current ablation status reads `reports\strategy_data_readiness_audit.json`, records 11,593,672 quote rows and 68 closed trades as bid/ask evidence, and no longer reports `requires_bid_ask_quotes` as an active ablation blocker. The corrected Exp07 prompt path now has a no-network real-news case collection plan at `reports\experiments\exp07_real_news_case_plan.md`; it lists required real-news fields, eight case groups, six prompt-template families, and 71 candidate days, but remains blocked because no candidate day has a successful real-news capture yet.
- A read-only paid-cost auditor exists at `scripts\audit_paid_costs.py`. It writes `reports\data_cost\paid_cost_audit.*` and currently reports `pass`: known committed Databento/OpenRouter estimated cost is `$107.437757` for traceability, user-reported provider actual usage is `$49.37`, and the current guard leaves `$75.63` before the `$125` stop threshold. Existing historical OpenRouter/DeepSeek live prompt summaries remain unpriced because they do not record `openrouter_actual_cost_usd`; future live summaries can be counted when that field is present.
- A read-only strategy-data readiness auditor exists at `scripts\audit_strategy_data_readiness.py`. It writes `reports\strategy_data_readiness_audit.*` and currently reports `blocked`: Mar-Dec 2023 in-sample plus Jan-Jun 2024 OOS pilot artifacts contain 11,593,672 option quote rows, 166,287 SPY bar rows, 71 candidate days, and 68 closed trades, which is still far below the `N >= 500` research target.
- A read-only research-log auditor exists at `scripts\audit_research_logs.py`. It writes `reports\research_log_audit.*` and currently reports `pass`: no experiment summary artifact is explicitly marked with `research_log_required=true`, so no new Thai research log is required. The audit still verifies the `research_log` Git remote and confirms local HEAD matches the Yuehua Research Log remote HEAD. Legacy Exp07 synthetic/prompt-matrix summaries are infrastructure evidence only and are not treated as completed experiments requiring new logs.
- A read-only aggregate readiness auditor exists at `scripts\audit_research_readiness.py`. It writes `reports\research_readiness_audit.*` and currently reports `blocked`: macro, VIX/VXV, paid-cost, and research-log audits pass; OpenRouter env is configured in the current process and Windows user scope; Databento is available through process/user `DATABENTO_SPY0DTE_API` even though `DATABENTO_API_KEY` is absent; per-day GDELT capture status is still `blocked` from HTTP 429 with four blocked daily status files; the GDELT command-plan check is also `blocked` with `gdelt_retry_cooldown_recommended`; strategy-data readiness has only 68 closed trades versus N >= 500; real news archive is missing; Exp07 real-news case plan has 71 candidate days and 0 captured candidates; and Exp07 strategy integration still lacks wider data/news/sample-size evidence.

This is not evidence of trading edge. The generated report is intentionally labeled `ยังสรุปไม่ได้` because the data is synthetic and N is far below 500 trades.

Research conclusion labels remain: `ผ่าน`, `ไม่ผ่าน`, `ยังสรุปไม่ได้`.

## User Inputs Required To Continue With Real Research

| Input | Why It Is Needed | Acceptable Next Action |
|:--|:--|:--|
| Wider historical SPY 0DTE options bid/ask data | The one-month pilot is available, but real research needs longer train/OOS coverage and N >= 500 where possible | Continue Databento cost-logged downloads inside the estimated SPY-only scope, provide another data source, or keep work scoped to the one-month pilot |
| Preferred provider choice/sample | M3 provider-specific importer cannot be trusted without source format | Use `docs/PROVIDER_SAMPLE_SPEC.md`; choose OptionsDX if coverage is enough, otherwise ThetaData is the recommended first subscription candidate |
| Databento API key/account | Wider live cost estimates/downloads require Databento account access, though dry-run request plans work without it | Use `DATABENTO_API_KEY` or the project alias `DATABENTO_SPY0DTE_API` in process or Windows user env, then run a live cost estimate before any new download |
| Databento/OpenRouter budget override | Default Databento gate blocks estimates at $25+ and flags $5+ for review | Continue within the already-scoped SPY-only plan while cumulative paid cost remains below `$125`; current user-reported actual usage is `$49.37`, with `$75.63` room left and `$107.437757` known committed estimate retained for audit traceability |
| Paid-cost stop threshold | User approved already-scoped Databento/OpenRouter work below `$125`, but runaway requests must still be prevented | Stop and ask if cumulative estimated/actual paid cost reaches `$125`, changes provider, changes symbol universe beyond SPY, or moves into broker/order-transmission work |
| IBKR options permission status | Paper/live operational validation depends on account capability | Confirm whether permission is approved; if not, use paper session only |
| IBKR paper session details | Actual paper order-ticket validation requires a live local session/API setup | Provide connection method later; no credentials should be stored in repo |
| Email alert settings | Real email alert send needs SMTP/API settings and recipient | Provide SMTP/API approach or keep dry-run email payloads |
| Real-money launch approval | Live trading must remain blocked until explicit approval | Complete `config/real_money_launch_checklist.example.json` only after research pass |

## Safe Next Work Without These Inputs

- Plan and cost-check the next wider Databento SPY-only coverage pull under the `$125` stop threshold.
- Re-run `python scripts\audit_paid_costs.py` before additional paid pulls to confirm remaining budget room.
- Use the updated OpenRouter prompt runner for any future live prompt experiment so `openrouter_actual_cost_usd`, costed assessment count, and token totals are captured when available.
- Run the same normalization, adapter, PnL, and sensitivity checks on the wider window after data is cached.
- Re-run `python scripts\audit_strategy_data_readiness.py` after each wider-data pilot to verify actual quote rows, SPY bar rows, candidate days, and closed-trade count.
- Use `reports\experiments\exp07_real_news_case_plan.md` to guide real-news case collection before any Exp07 prompt-family run.
- Confirm provider-specific importer mapping after a real sample file is supplied.
- Use the completed official macro-calendar archive as a strategy filter input after the wider SPY 0DTE dataset is available.
- Use the completed Cboe VIX/VIX3M canonical archive as the VIX/VXV regime input after the wider SPY 0DTE dataset is available.
- Retry real GDELT news snapshot capture later, after the HTTP 429 pressure clears; use `reports\news_gdelt_capture_command_plan.md` and check `reports\news_gdelt_capture_status` for per-day live attempt results.
- Capture real GDELT news snapshots using the selected source plan, then import the captured CSV directory with `scripts\import_gdelt_news_capture_directory.py --output-root .`.
- Expand synthetic fixture coverage for edge cases.
- Add more report formatting and metric tests.
- Prepare documentation for environment variables and local run commands.
- Re-run `python scripts\audit_research_readiness.py` after setting env vars, after new data imports, or after paid-cost audit changes to confirm which blockers changed.

## Blocked Work

- Statistically meaningful real historical experiment results beyond the pilot window.
- OOS acceptance decision.
- Raw DeepSeek/OpenRouter LLM gate usage in strategy research or live paths; Exp07 v12 raw LLM gate failed, and guarded-policy strategy integration still needs ablation plus real macro/news data.
- Exp07 prompt-family research on synthetic/policy fixtures; real timestamp-clean news cases are required first.
- Real guarded-policy strategy ablation conclusions until wider SPY 0DTE data, real news archive, and `N >= 500` trade sample size exist.
- News filtering on real data until GDELT or another approved source is archived with real snapshots, imported, and passing the news coverage audit.
- IBKR paper/live connection.
- Backup GTT/GTD order verification.
- Real email delivery.
- Any real-money launch.
