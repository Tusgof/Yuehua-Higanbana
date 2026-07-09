# GDELT Bulk Raw Source Decision Note

## Status
- **Date**: 2026-07-03
- **Track**: News-Unblock N.2
- **Decision**: Keep GDELT DOC API as the primary query path, but add GDELT bulk raw files as a free candidate probe path. Do not treat the bulk path as strategy-ready until a manifest, parser, timestamp mapping, and canonical import audit pass.
- **Conclusion**: News remains blocked. This note completes the source evaluation step only; it does not create real timestamp-clean news cases.

## Why This Exists
The current GDELT DOC API path is blocked by HTTP 429 pressure during live historical retries. The project needs a no-cost alternative route before considering any new paid news provider.

Official GDELT documentation says the database is free/open and raw data files can be downloaded, but it also warns that the raw event and graph datasets are large and require technical handling. That makes bulk raw files plausible for offline historical coverage, but risky enough that they need a narrow probe before integration.

## Source Comparison

| Path | Useful For | Strength | Main Risk | Project Decision |
|:--|:--|:--|:--|:--|
| GDELT DOC API / ArticleList | Targeted headline snapshots by topic and time window | Existing capture/import code already matches the project `news_item` shape | Current HTTP 429 pressure; `seendate` is a seen/index timestamp surrogate, not guaranteed article publication time | Keep as primary query path, retry only after cooldown |
| GDELT bulk raw files / GKG-style archives | Offline historical coverage without repeated DOC API requests | Free, open, cacheable, and not dependent on repeated per-topic API calls | Very large files; parser/schema choice not yet locked; may not contain full article body; timestamp fields must be mapped carefully | Approve only a no-download manifest/size probe next |
| GDELT BigQuery | Large-scale search and aggregation | Official GDELT path for large datasets | May require Google Cloud account and query-cost controls; not approved as a paid/new access method | Deferred until explicit user approval |
| New paid news provider | Possible archive fallback | Could provide cleaner article metadata if terms permit | New provider/cost/terms decision; may still fail historical depth | Requires explicit user approval |

## Methodology Constraints
The local LLM Wiki rules still control this track:

- `lookahead-leakage.md`: features must be available at the decision timestamp.
- `exogenous-features.md`: external data adds alignment, availability, revision, and leakage risk.
- `llm-training-data-contamination.md`: historical LLM tests must record source timestamps, retrieval windows, model information, and entity handling.

Therefore, a bulk raw GDELT row is not automatically a valid LLM/news feature. It must first prove:

1. The raw file timestamp can be interpreted without using future information.
2. `published_at` or the closest honest surrogate is less than or equal to `decision_time_et`.
3. `fetched_at` or archive availability is less than or equal to `decision_time_et` for live-replay claims, or clearly labeled as historical archive evidence if not.
4. Headline/source/URL fields are preserved, or the missing fields are declared as blockers.
5. Topic matching is pre-registered and not tuned on OOS strategy results.

## Required Next Implementation
The next safe implementation should be a no-paid, no-article-download planner:

1. Read the GDELT v2 master file list metadata or a cached copy.
2. Map required candidate decision windows to expected bulk raw file URLs.
3. Estimate file counts and likely bytes before any data download.
4. Identify which file family is suitable for project needs:
   - `gkg`: likely best first candidate for article/theme/source metadata.
   - `mentions` and `export`: event-centric supplements, not first-choice headline archive.
5. Write a dry-run manifest report with URLs, timestamps, file family, expected output schema, and blockers.

Only after that manifest passes should the project download one small probe file and convert it into the existing offline snapshot CSV shape used by `scripts\import_news_snapshots.py`.

## Acceptance Criteria For A Future Probe
A future bulk raw probe can remove part of the news blocker only if it produces:

- A raw file manifest with source URL and SHA-256 hash.
- A parser report showing row counts, timestamp fields, source/headline/URL availability, and dropped-row reasons.
- A canonical `news_item.jsonl` import through the existing anti-leakage importer or an equivalent validator.
- A passing or meaningfully improved `python scripts\audit_news_coverage.py` result.
- A clear label distinguishing exact publication timestamps from seen/index timestamps.

## Blockers That Remain
- No real canonical news archive exists yet.
- No GDELT bulk parser has been selected or validated.
- DOC API retries remain on cooldown after HTTP 429 pressure.
- Live DeepSeek/OpenRouter prompt research remains blocked until real timestamp-clean news cases exist.
- Any paid news provider or BigQuery-cost path still requires explicit user approval.

## Verification
This decision note should be verified with:

```powershell
python scripts\validate_news_sources.py
python scripts\audit_news_coverage.py
python scripts\audit_research_readiness.py
```
