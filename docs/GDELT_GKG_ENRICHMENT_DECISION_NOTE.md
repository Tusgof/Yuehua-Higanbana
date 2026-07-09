# GDELT GKG Enrichment Decision Note

## Purpose
Decide what to do after the controlled one-file GKG parser probe in `reports\news_gdelt_gkg_one_file_parser_probe.md`.

This note is not a research result and does not unblock LLM experiments. It only prevents the project from treating GKG raw files as canonical news records before the required fields are actually proven.

## Evidence
- Probe file: `20240128221500.gkg.csv.zip`
- Probe mode: one-file controlled probe only
- Parsed rows: `605`
- HTTPS URL rows: `598`
- Non-empty source rows: `605`
- Canonical field mapping:
  - `decision_time_et`: pass from manifest command plan
  - `source_name`: pass from `source_common_name`
  - `url`: pass for HTTPS `document_identifier`
  - `fetched_at_et`: surrogate only from GKG file/index timestamp
  - `published_at_et`: surrogate only from GKG file/index timestamp
  - `headline`: blocked; no verified headline field in the parsed GKG rows
  - `topic`: blocked until project topic mapping from GKG themes is pre-registered

## Decision
GKG raw files are not sufficient by themselves for canonical `news_item` import.

Use GKG as a candidate URL/source/timestamp index only. Do not import URL slugs as headlines, and do not claim exact publication time from the GKG file timestamp.

## Approved Next Path
1. Keep GDELT DOC API as the primary canonical capture path after cooldown because it already maps to the current snapshot importer shape: title/headline, URL, domain, and `seendate`.
2. Use the one-file GKG probe to design a narrow enrichment path only if it can produce verified headlines and a defensible timestamp policy.
3. Before any broad GKG download, run a small enrichment proof that turns one GKG file into a canonical-style snapshot and then passes the existing import and news coverage audits on a staging output root.

## Rejected Or Deferred Paths
- Reject URL slug as headline for research evidence. It is a diagnostic surrogate only.
- Reject broad GKG archive download until headline, timestamp, and topic mapping are proven.
- Defer source-page title scraping. It is not point-in-time clean unless the archive/fetch timestamp policy is solved first.
- Defer BigQuery or any paid news provider until the user explicitly approves a provider change.
- Keep live LLM research blocked until real timestamp-clean news cases exist.

## Next Verification Target
The next implementation step should create a narrow GKG enrichment proof or DOC API cooldown retry plan that verifies all of:
- verified headline source,
- defensible `published_at_et` / `fetched_at_et` policy,
- pre-registered topic mapping,
- canonical `news_item` import on a staging output root,
- `python scripts\audit_news_coverage.py` remains honest about real archive coverage.
