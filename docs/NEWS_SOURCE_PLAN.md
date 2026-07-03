# News Source Plan

## Purpose

Experiment 7 and the macro/news filters need a timestamp-safe archive of market headlines. This plan selects source candidates and validation rules. It does not import real news yet and must not unblock strategy integration by itself.

## Source Decision

Primary archive candidate:

- `GDELT` via the DOC API/index.
- Reason: broad historical news index, free/no-key access, suitable for timestamp-windowed headline snapshots before SPY 0DTE decision time.
- Project role: primary candidate for real news archive snapshots.

Supplement candidates:

- `Alpha Vantage NEWS_SENTIMENT`: optional market-news supplement. It requires an API key and is deferred until explicitly approved.
- `NewsAPI /everything`: fallback paid/archive candidate. Archive depth depends on plan, so it is deferred.
- `SEC Newsroom`: official regulatory supplement only. It is useful for SEC/market-structure context, not broad market sentiment.

The machine-readable plan is `tests\fixtures\news_sources_v1.json` and is validated by:

```powershell
python scripts\validate_news_sources.py
```

## Required Topics

The first archive shape must cover these Exp07 risk topics:

- `market_panic`
- `systemic_banking_stress`
- `war_escalation`
- `index_halt_circuit_breaker`
- `macro_policy_risk`

This is intentionally narrower than all market news. The goal is to provide the guarded policy and LLM prompt input with event-risk context, not to create a general news sentiment product.

## Timestamp Discipline

Every normalized `news_item` must preserve:

- `decision_time_et`
- `published_at_et`
- `fetched_at_et`
- `source_name`
- `headline`
- `url`
- `provider`

For historical strategy replay:

- `published_at_et` must be less than or equal to the strategy `decision_time_et`.
- The raw snapshot must be saved before any strategy use.
- For live replay tests, `fetched_at_et` must also be less than or equal to `decision_time_et`.
- Deduplicate by `provider + url`.

This protects against lookahead leakage from articles discovered or revised after the decision timestamp.

## Query Shape

The initial GDELT query windows should be anchored around the strategy decision time in ET and converted to UTC for requests. Candidate query groups:

- Market panic: `market panic OR selloff OR risk-off OR liquidity`
- Systemic banking stress: `banking crisis OR funding stress OR bank run OR emergency lending`
- War escalation: `war escalation OR missile strike OR invasion OR geopolitical risk`
- Index halt/circuit breaker: `circuit breaker OR limit down OR trading halt OR futures halt`
- Macro policy risk: `Federal Reserve OR Powell OR inflation data OR jobs report OR Treasury yields`

Do not tune query wording on OOS strategy outcomes. Query refinements should be reviewed as data-quality changes, not performance optimization.

## Current Status

Done:

- Source selection v1 exists.
- Validation enforces HTTPS URLs, source roles, access status, archive status, required topics, and anti-leakage rules.
- Deferred key-required providers cannot become the primary source accidentally.
- Offline snapshot importer skeleton exists at `scripts\import_news_snapshots.py`.
- Fixture GDELT-like snapshot exists at `tests\fixtures\news_snapshots\gdelt_news_sample.csv`.
- GDELT capture script exists at `scripts\capture_gdelt_news_snapshots.py`. It defaults to dry-run request planning and only fetches live data when `--execute` is passed.
- Candidate-day GDELT capture command planner exists at `scripts\plan_gdelt_news_capture_commands.py`; it writes a no-network retry plan from existing pilot candidate-ready days.
- Multi-snapshot GDELT directory importer exists at `scripts\import_gdelt_news_capture_directory.py`; it combines captured per-day CSV files and reuses the single-snapshot importer validation.
- Coverage auditor exists at `scripts\audit_news_coverage.py`. It checks canonical real news archive coverage by topic across reference, train, and OOS windows and writes `reports\news_coverage_audit.*`.

Still pending:

- Successful real GDELT snapshot capture. A small manual probe on 2026-06-30 returned HTTP 429, so live capture should be retried later and treated as an external availability issue.
- Passing coverage audit with real article counts by date/topic. Current audit is `blocked` because no canonical real news archive exists at `data\normalized\spy_0dte\news\news_item.jsonl`.
- Strategy ablation using the real news archive.

## Verification

```powershell
python scripts\validate_news_sources.py
python scripts\capture_gdelt_news_snapshots.py --decision-time-et 2024-01-03T09:30:00-05:00 --max-records 5
python scripts\plan_gdelt_news_capture_commands.py
python scripts\import_gdelt_news_capture_directory.py --input-dir tests\fixtures\news_snapshots --pattern gdelt_news_sample.csv --output-root build\news_gdelt_capture_import
python scripts\audit_news_coverage.py
python scripts\import_news_snapshots.py --output-root build\news_fixture
python -m unittest tests.test_capture_gdelt_news_snapshots
python -m unittest tests.test_validate_news_sources
python -m unittest tests.test_import_news_snapshots
python -m unittest tests.test_import_gdelt_news_capture_directory
python -m unittest tests.test_audit_news_coverage
python scripts\run_fixture_pipeline.py
```
