# M6 News Source Decision Note

## Status
- **Date**: 2026-07-02
- **Milestone**: M6 Real News And LLM Prompt/Gate Research
- **Decision**: Keep GDELT as the free primary candidate, but do not continue rapid live retries while HTTP 429 pressure persists.
- **Conclusion**: M6.1 remains blocked until a real timestamp-clean news archive exists.

## Evidence
- `reports\news_gdelt_capture_command_plan.json` now records 71 candidate-day capture commands.
- Five per-day GDELT capture attempts are blocked:
  - `2023-04-03`
  - `2023-04-13`
  - `2023-09-01`
  - `2023-09-07`
  - `2023-10-02`
- Latest retry on `2023-04-13` returned `429 Too Many Requests`.
- `reports\news_coverage_audit.json` reports 0 canonical news records.
- `scripts\audit_research_readiness.py` remains blocked on `requires_real_news_archive`, `requires_real_timestamp_clean_news_cases`, and `gdelt_retry_cooldown_recommended`.

## Methodology Constraint
Local LLM Wiki guidance treats news and LLM inputs as high leakage-risk external features:
- `llm-training-data-contamination.md`: historical LLM tests must assume event memorization risk unless model checkpoint, timestamps, retrieval window, and entity handling are documented.
- `lookahead-leakage.md`: features must be available at the decision timestamp.
- `exogenous-features.md`: external data must align with availability and revision timing.

Therefore, synthetic prompt cases or post-event summaries must not be counted as M6 research evidence.

## Next Safe Actions
1. Pause additional live GDELT `--execute` retries until retry pressure clears.
2. Before changing provider or using a paid news source, ask for explicit user approval because that is a new provider/source decision.
3. Prefer a timestamp-clean offline archive path if available: raw records must include `published_at`, `fetched_at`, source, URL/headline/body where available, `decision_time_et`, and raw provenance. Canonical `news_item` imports now preserve `decision_time_et` and reject records where `published_at_et` or `fetched_at_et` is after the decision time.
4. Do not run DeepSeek/OpenRouter prompt-family research until at least one real timestamp-clean case set is imported and audited.

## Verification
- `python scripts\plan_gdelt_news_capture_commands.py`
- `python scripts\audit_news_coverage.py`
- `python scripts\audit_research_readiness.py`
