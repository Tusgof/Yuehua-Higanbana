# RUNBOOK.md

## Purpose

This runbook explains how to operate the current fixture/simulation scaffold and what must happen before real SPY 0DTE research or broker validation can begin.

## Current Safe Command

Run the local fixture pipeline:

```powershell
python scripts\run_fixture_pipeline.py
```

Expected result:

- M2 contract fixture validates.
- M3 synthetic raw file imports into normalized JSONL.
- M6 generates 10 fixture experiment reports plus `reports/final_research_review.md`.
- Unit tests pass.
- Final research gate remains `blocked` because fixture data is not real trading evidence.

For current real-research readiness, run the aggregate read-only audit:

```powershell
python scripts\audit_research_readiness.py
```

Expected current result:

- Macro calendar coverage is `pass`.
- VIX/VXV coverage is `pass`.
- Paid-cost audit is `pass`; when `reports/data_cost/user_reported_actual_usage.json` exists, the stop guard uses that provider actual usage while retaining known committed estimated cost for traceability.
- Research-log audit is `pass`.
- OpenRouter user env is available.
- Readiness remains `blocked` until real GDELT/news archive and wider SPY 0DTE trade sample evidence exist. Databento is available through the project alias `DATABENTO_SPY0DTE_API` even when `DATABENTO_API_KEY` is absent.

## Verification Commands

```powershell
python scripts\validate_m2_contracts.py
python scripts\provider_adapters.py
python scripts\estimate_databento_cost.py --scenario one_day_sample --report-path reports\data_cost\databento_cost_dry_run.md
python scripts\project_databento_cost.py --source reports\data_cost\databento_cost_plan.json --report-path reports\data_cost\databento_cost_projection.md --json-report-path reports\data_cost\databento_cost_projection.json
python scripts\download_databento_data.py --cost-report reports\data_cost\databento_cost_plan.json --plan-path reports\data_cost\databento_download_plan.json
python scripts\audit_databento_cache.py --plan-path reports\data_cost\databento_download_plan.json --report-path reports\data_cost\databento_cache_audit.md --json-report-path reports\data_cost\databento_cache_audit.json
python scripts\inspect_databento_raw.py --raw-root data\raw\spy_0dte\databento\one_month_pilot --report-path reports\data_cost\databento_raw_inspection.md --json-report-path reports\data_cost\databento_raw_inspection.json
python scripts\normalize_databento_options.py --raw-root data\raw\spy_0dte\databento\one_month_pilot --output-path data\normalized\spy_0dte\databento\one_month_pilot\option_quote.jsonl --summary-path reports\data_cost\databento_normalization_summary.json
python scripts\plan_databento_spy_bars.py --live-cost --api-key-env DATABENTO_API_KEY --plan-path reports\data_cost\databento_spy_bars_plan.json --report-path reports\data_cost\databento_spy_bars_plan.md
python scripts\validate_macro_calendar_sources.py
python scripts\capture_macro_calendar_snapshots.py --as-of-date 2024-01-03
python scripts\capture_macro_calendar_snapshots.py --as-of-date 2026-06-30 --execute
python scripts\convert_macro_calendar_capture.py --capture-root data\raw\spy_0dte\macro_calendar\2026-06-30
python scripts\import_macro_calendar_snapshots.py --snapshot-path data\raw\spy_0dte\macro_calendar\official_macro_calendar_2022_2026_backfill.csv --output-root .
python scripts\audit_macro_calendar_raw_archive.py --start-year 2022 --end-year 2026 --current-as-of-date 2026-06-30
python scripts\audit_macro_calendar_coverage.py
python scripts\capture_vix_vxv_cboe.py --as-of-date 2026-06-30
python scripts\capture_vix_vxv_cboe.py --as-of-date 2026-06-30 --execute
python scripts\import_vix_vxv_cboe.py --capture-root data\raw\spy_0dte\vix_vxv\2026-06-30 --start-date 2022-01-01 --end-date 2026-06-30
python scripts\audit_vix_vxv_coverage.py --as-of-date 2026-06-30
python scripts\validate_news_sources.py
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2024-01-03T09:30:00-05:00 --max-records 5
python scripts\plan_gdelt_news_capture_commands.py
python scripts\import_gdelt_news_capture_directory.py --input-dir tests\fixtures\news_snapshots --pattern gdelt_news_sample.csv --output-root build\news_gdelt_capture_import
python scripts\audit_news_coverage.py
python scripts\audit_paid_costs.py
python scripts\audit_strategy_data_readiness.py
python scripts\audit_research_readiness.py
python scripts\import_macro_calendar_snapshots.py --output-root build\macro_calendar_fixture
python scripts\import_news_snapshots.py --output-root build\news_fixture
python scripts\validate_exp07_strategy_ablation_plan.py
python scripts\run_exp07_strategy_ablation.py
python scripts\estimate_databento_cost.py --scenario all
python scripts\import_provider_sample.py --provider optionsdx --raw-path tests\fixtures\provider_samples\optionsdx_option_quote_sample.csv --output-root build\provider_sample_fixture
python scripts\import_m3_fixture.py
python scripts\experiment_runner_m6.py
python -m unittest discover -s tests
```

## Important Outputs

| Output | Path | Meaning |
|:--|:--|:--|
| Data source audit | `docs/DATA_SOURCE_AUDIT.md` | Provider recommendation and blocked paid-data decisions |
| Provider sample spec | `docs/PROVIDER_SAMPLE_SPEC.md` | Exact sample fields needed before provider-specific import can be trusted |
| User input list | `docs/NEXT_USER_INPUTS.md` | Exact inputs needed before real research/execution |
| Registry | `data/registry/datasets.jsonl` | Provider, coverage, schema, and raw hash records |
| Experiment reports | `reports/experiments/*.md` | Fixture reports for all 10 experiments |
| Final review | `reports/final_research_review.md` | Fixture final review; gate must remain blocked |
| Databento cache audit | `reports/data_cost/databento_cache_audit.md` | Offline check of present/missing raw Databento files |
| Databento raw inspection | `reports/data_cost/databento_raw_inspection.md` | Offline summary of readable DBN rows, bid/ask rows, symbols, expirations, and strikes |
| Databento normalized quotes | `data/normalized/spy_0dte/databento/one_month_pilot/option_quote.jsonl` | Canonical 0DTE-only option quotes filtered from the parent SPY option chain |
| Databento SPY bars plan | `reports/data_cost/databento_spy_bars_plan.md` | Cost plan for SPY 1-minute underlying bars needed by ORB logic |
| Macro calendar source plan | `docs/MACRO_CALENDAR_SOURCE_PLAN.md` | Official/free macro source list and offline snapshot importer contract |
| Macro calendar capture dry-run | `scripts/capture_macro_calendar_snapshots.py` | Builds raw official-source archive paths without network unless `--execute` is passed |
| Macro calendar raw capture manifests | `data/raw/spy_0dte/macro_calendar/YYYY-12-31/capture_manifest.json` and `data/raw/spy_0dte/macro_calendar/2026-06-30/capture_manifest.json` | Raw official-source capture manifests with bytes and SHA-256 hashes |
| Macro calendar converted backfill | `data/raw/spy_0dte/macro_calendar/official_macro_calendar_2022_2026_backfill.csv` | Importer-ready CSV converted from official-source raw archives |
| Macro calendar normalized archive | `data/normalized/spy_0dte/macro_calendar/macro_event.jsonl` | Canonical macro events from the 2022-2026 official-source backfill |
| Macro calendar coverage audit | `reports/macro_calendar_coverage_audit.md` | Reference/train/OOS required event-type coverage audit; current status should be `pass` |
| VIX/VXV raw capture | `data/raw/spy_0dte/vix_vxv/2026-06-30/capture_manifest.json` | Official Cboe VIX and VIX3M CSV capture manifest |
| VIX/VXV normalized archive | `data/normalized/spy_0dte/vix_vxv/vix_vxv.jsonl` | Canonical daily close VIX/VXV records from Cboe VIX/VIX3M |
| VIX/VXV coverage audit | `reports/vix_vxv_coverage_audit.md` | Reference/train/OOS VIX/VXV daily close coverage audit; current status should be `pass` |
| News source plan | `docs/NEWS_SOURCE_PLAN.md` | GDELT-first news archive source selection and timestamp anti-leakage contract |
| GDELT capture dry-run | `scripts/capture_gdelt_news_snapshots.py` | Builds timestamp-safe GDELT request windows without network unless `--execute` is passed |
| GDELT candidate-day command plan | `reports/news_gdelt_capture_command_plan.md` | No-network retry plan generated from candidate-ready pilot days |
| GDELT directory import summary | `reports/news_gdelt_capture_directory_import_summary.md` | Offline combined-import summary for captured GDELT CSV files; fixture output is not real research evidence |
| GDELT per-day live capture status | `reports/news_gdelt_capture_status/*.json` | Structured per-day results from live GDELT capture attempts; current status is expected to include `blocked` while HTTP 429 persists |
| News coverage audit | `reports/news_coverage_audit.md` | Train/OOS news-topic coverage audit; expected `blocked` until real GDELT/news archive coverage is complete |
| Paid cost audit | `reports/data_cost/paid_cost_audit.md` | Read-only cumulative paid-cost status for Databento and cost-recorded OpenRouter summaries; the current stop guard should remain below the `$125` threshold |
| Strategy data readiness audit | `reports/strategy_data_readiness_audit.md` | Read-only summary of existing real Databento pilot artifacts; currently blocked because only 68 closed trades exist versus the N >= 500 target |
| Research readiness audit | `reports/research_readiness_audit.md` | Read-only aggregate blocker state for env, macro, VIX/VXV, news, Exp07, and Aug 2023 Databento readiness |
| Macro calendar fixture import | `build/macro_calendar_fixture/data/normalized/spy_0dte/macro_calendar/macro_event.jsonl` | Canonical macro-event rows from the offline fixture snapshot; not real research evidence |
| News fixture import | `build/news_fixture/data/normalized/spy_0dte/news/news_item.jsonl` | Canonical news-item rows from the offline fixture snapshot; not real research evidence |
| Exp07 ablation plan | `docs/EXP07_STRATEGY_ABLATION_PLAN.md` | Locked baseline-vs-guarded strategy ablation design; not a completed ablation result |
| Exp07 ablation status | `reports/experiments/exp07_strategy_ablation_status.md` | Blocked readiness artifact for the locked ablation plan; not a completed ablation result |
| IBKR example config | `config/ibkr.example.json` | Safe non-transmit paper-mode defaults |
| Launch checklist | `config/real_money_launch_checklist.example.json` | Must remain incomplete until research passes |

## Environment Setup

Use `.env.example` only as a template. Real API keys and credentials must stay outside project files.

Allowed environment variable pattern:

```powershell
$env:HIGANBANA_OPENROUTER_API = "<local secret>"
$env:DATABENTO_API_KEY = "<local secret>"
# Or use the project-local Databento alias:
$env:DATABENTO_SPY0DTE_API = "<local secret>"
```

The target LLM path is DeepSeek via OpenRouter, with DeepSeek V4 flash thinking as the preferred primary model using model id `deepseek/deepseek-v4-flash`. Live LLM gate decisions remain blocked from strategy/live use until controlled prompt experiments and strategy ablation pass. New live OpenRouter prompt summaries record token usage and USD cost only when the provider response includes those fields; old live summaries without cost fields remain unpriced and must not be backfilled with guessed prices.

On Windows, `scripts\openrouter_deepseek_adapter.py` reads `HIGANBANA_OPENROUTER_API` from the current process env first and then from the user env. Databento helpers read `DATABENTO_API_KEY` first and then the project-local alias `DATABENTO_SPY0DTE_API`. Status output only reports whether keys are configured; it must never print secret values.

For bounded Exp07 prompt checks, start with a subset before any full matrix:

```powershell
python scripts\run_exp07_prompt_experiment.py --live --case-id quiet_vix18_normal_term_structure --prompt-variant A --summary-path reports\experiments\exp07_prompt_v13_smoke_summary.json
python scripts\audit_paid_costs.py
```

Treat subset results as OpenRouter wiring and prompt-parse evidence only. Do not use them as strategy evidence.

Do not write real secrets into:

- `PROJECT_BRAIN.md`
- `IMPLEMENT_PLAN.md`
- `config/*.json`
- `.env.example`
- test fixtures

## Provider Decision Procedure

1. Start with `docs/DATA_SOURCE_AUDIT.md`.
2. Use `docs/PROVIDER_SAMPLE_SPEC.md` to request a small real sample with 9:35 AM, 10:00 AM, and 3:45 PM ET bid/ask quotes.
3. If a sample file is available, place it under `data/raw/spy_0dte/` and map it through a provider-specific adapter.
4. If no sample exists, choose whether to approve a paid provider.
5. Preferred path:
   - OptionsDX if it covers the required 2022-2026 SPY 0DTE snapshots.
   - ThetaData if OptionsDX cannot cover OOS 2024-current or API access is more useful.
   - Cboe DataShop only if cheaper sources fail.

Current adapter templates are synthetic only:

```powershell
python scripts\provider_adapters.py
```

These templates validate the canonical mapping shape. They do not prove that a real provider export uses the same columns.

To import a provider sample into canonical JSONL plus registry manifest:

```powershell
python scripts\import_provider_sample.py --provider optionsdx --raw-path data\raw\spy_0dte\<sample>.csv
```

Supported template providers are `optionsdx` and `thetadata`. Confirm the mapping against a real provider sample before using outputs for research.

## Databento Cost Estimation

Dry-run request plan without an API key:

```powershell
python scripts\estimate_databento_cost.py --scenario one_day_sample
python scripts\estimate_databento_cost.py --scenario one_month_pilot
python scripts\estimate_databento_cost.py --scenario oos_2024_2025
python scripts\estimate_databento_cost.py --scenario all
```

Write a Markdown decision artifact:

```powershell
python scripts\estimate_databento_cost.py --scenario one_day_sample --report-path reports\data_cost\databento_cost_plan.md
```

Live cost estimate after setting the key locally:

```powershell
$env:DATABENTO_API_KEY = "<local secret>"
python scripts\estimate_databento_cost.py --scenario one_day_sample --live
```

The default request uses `OPRA.PILLAR`, `cbbo-1m`, `SPY.OPT`, and `stype_in=parent`. Treat this as an upper-bound estimate because parent symbology can include more contracts than same-day 0DTE only.

Cost decision defaults:

- Below `$5`: `pass`
- `$5` to below `$25`: `review`
- `$25` or higher: `block`

Override only when the user explicitly accepts a different budget:

```powershell
python scripts\estimate_databento_cost.py --scenario one_day_sample --live --review-cost-usd 10 --block-cost-usd 50
```

Safety rule:

- Start live cost checks with `one_day_sample`.
- Run `python scripts\audit_paid_costs.py` before further already-scoped paid pulls and keep the current stop-guard usage below the `$125` threshold. If `reports/data_cost/user_reported_actual_usage.json` exists, that user-reported provider actual usage is the guard basis; otherwise the auditor uses known committed estimated cost.
- For OpenRouter/DeepSeek, rely on `openrouter_actual_cost_usd` in live prompt summaries when present. Do not infer USD cost from token counts unless a provider-priced artifact records the cost.
- Do not run `full_research --live` until the one-day and one-month estimates look safe.
- The script refuses more than 100 live cost calls by default. Increase `--max-live-requests` only after reviewing the dry-run request count.
- Low-cost Databento pulls inside the already estimated SPY-only research scope may proceed after cost logging.
- Stop and ask before downloading if the request uses a new paid provider, changes the symbol universe beyond SPY, or exceeds the $125 stop threshold.
- Do not download data when the report decision is `block` unless the user explicitly approves a higher cap.

Projection from an accepted live report:

```powershell
python scripts\project_databento_cost.py --source reports\data_cost\databento_cost_plan.json --report-path reports\data_cost\databento_cost_projection.md --json-report-path reports\data_cost\databento_cost_projection.json
```

Projection is not a Databento quote. Use it to decide whether a wider live `get_cost` run is worth doing.

Download plan without downloading data:

```powershell
python scripts\download_databento_data.py --cost-report reports\data_cost\databento_cost_plan.json --plan-path reports\data_cost\databento_download_plan.json
```

Actual download uses `--execute` and reuses cache when files already exist:

```powershell
$env:DATABENTO_API_KEY = "<local secret>"
python scripts\download_databento_data.py --cost-report reports\data_cost\databento_cost_plan.json --plan-path reports\data_cost\databento_download_result.json --execute
```

The download script refuses reports that are not `pass`, contain errors, or exceed `--max-download-requests`.

Download/cache policy:

- A Databento request can create a billable data pull; estimate/log cost first and stay inside the approved SPY-only research scope.
- Downloaded `.dbn.zst` files are treated as raw immutable cache under `data/raw/spy_0dte/databento/<scenario>/`.
- If a planned output file already exists, the script reuses the local file and records its hash instead of downloading that window again.
- Backtests and experiment sweeps should read from local raw/normalized files. They should not call Databento directly.
- Re-query Databento only for missing windows, changed schema/granularity, changed symbol universe, or an explicit approved refresh.

Audit local cache without calling Databento:

```powershell
python scripts\audit_databento_cache.py --plan-path reports\data_cost\databento_download_plan.json --report-path reports\data_cost\databento_cache_audit.md --json-report-path reports\data_cost\databento_cache_audit.json
```

Before approved download, the audit should show missing windows. After approved download, it should show present files with bytes and SHA-256 hashes.

Inspect local DBN files without calling Databento:

```powershell
python scripts\inspect_databento_raw.py --raw-root data\raw\spy_0dte\databento\one_month_pilot --report-path reports\data_cost\databento_raw_inspection.md --json-report-path reports\data_cost\databento_raw_inspection.json
```

Normalize the one-month pilot to canonical 0DTE `option_quote` JSONL:

```powershell
python scripts\normalize_databento_options.py --raw-root data\raw\spy_0dte\databento\one_month_pilot --output-path data\normalized\spy_0dte\databento\one_month_pilot\option_quote.jsonl --summary-path reports\data_cost\databento_normalization_summary.json
```

Important: `SPY.OPT` parent symbology includes many expirations, not only 0DTE. The normalizer filters to expiration date equal to the trade date and keeps only usable positive bid/ask quotes.

Plan SPY underlying 1-minute bars for ORB logic:

```powershell
$env:DATABENTO_API_KEY = "<local secret>"
python scripts\plan_databento_spy_bars.py --live-cost --api-key-env DATABENTO_API_KEY --plan-path reports\data_cost\databento_spy_bars_plan.json --report-path reports\data_cost\databento_spy_bars_plan.md
```

Download SPY-bar cache after a pass-status plan:

```powershell
$env:DATABENTO_API_KEY = "<local secret>"
python scripts\plan_databento_spy_bars.py --execute --api-key-env DATABENTO_API_KEY --plan-path reports\data_cost\databento_spy_bars_download_result.json --report-path reports\data_cost\databento_spy_bars_download_result.md
```

Normalize SPY bars to canonical `spy_bar` JSONL:

```powershell
python scripts\normalize_databento_spy_bars.py --raw-path data\raw\spy_0dte\databento\spy_bars\jan_2024_spy_ohlcv_1m.dbn.zst --output-path data\normalized\spy_0dte\databento\one_month_pilot\spy_bar.jsonl --summary-path reports\data_cost\databento_spy_bars_normalization_summary.json
```

Join the normalized Jan 2024 pilot data and check ORB candidate availability:

```powershell
python scripts\run_jan2024_pilot_adapter.py
```

This adapter only checks data readiness and Sub-System A candidate construction. It does not produce PnL or evidence of edge.

Run pilot-only PnL on candidate-ready days:

```powershell
python scripts\run_jan2024_pilot_pnl.py
```

This report is still below research acceptance quality. It uses one month of data, skips days with missing close quotes, and defaults commission to `0.0` so broker fees are not guessed.

Run pilot sensitivity scenarios for commission, fill stress, and close-quote handling:

```powershell
python scripts\run_jan2024_pilot_sensitivity.py
```

The sensitivity report can justify whether to buy/download a wider Databento pilot. It must not be used as strategy acceptance because the sample is far below N >= 500.

Audit current real strategy-data coverage without live API calls:

```powershell
python scripts\audit_strategy_data_readiness.py
```

The current audit reads Mar-Dec 2023 in-sample plus Jan-Jun 2024 OOS pilot artifacts. It should remain `blocked` until the closed-trade count reaches the N >= 500 research target.

## Real Research Gate

Do not treat any fixture report as evidence of edge.

Research can move from scaffold to real experiment only when:

- Historical SPY 0DTE bid/ask option data exists.
- Entry and exit timestamps are covered.
- OOS window is untouched.
- Trade count can approach the N >= 500 target or the report explicitly says evidence is insufficient.

## Operational Gate

Do not enable IBKR live transmit until:

- Research acceptance passes.
- Options permission is approved.
- Cash-account constraints are documented.
- Kill switch and forced close are tested.
- User real-money approval is recorded.

Entry market orders remain prohibited.
