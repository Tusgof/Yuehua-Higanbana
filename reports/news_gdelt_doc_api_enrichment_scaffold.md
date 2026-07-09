# GDELT DOC API Enrichment Scaffold

- Status: `scaffold_pass_real_archive_blocked`
- Selected path: `gdelt_doc_api_topic_requery_after_cooldown`
- Network calls: `0`
- Paid cost: `$0.0`
- Not research evidence: `True`

## What This Proves

This scaffold proves that the existing GDELT DOC API parser shape can feed the canonical `news_item` importer when `title`, `url`, `domain`, and `seendate` exist.

It does not prove real historical news availability and does not unblock LLM research.

## Preserved GKG Blockers

- `gkg_has_no_verified_headline_field`
- `gkg_publication_time_is_surrogate_not_exact`
- `gkg_topic_mapping_not_pre_registered`

## Rejected Paths

- `url_slug_surrogate_headline`
- `broad_gkg_download_before_enrichment_proof`
- `source_page_title_scrape_without_point_in_time_policy`
- `bigquery_or_paid_news_provider_without_user_approval`
- `live_llm_before_real_timestamp_clean_news_cases`

## Remaining Blockers

- `requires_real_gdelt_doc_api_capture_after_cooldown`
- `requires_real_news_archive`
- `requires_news_coverage_audit_pass`

## Outputs

- Snapshot CSV: `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\build\news_gdelt_doc_api_enrichment_scaffold\gdelt_doc_api_scaffold_snapshot.csv`
- Imported records: `5`
- Normalized output: `D:\Fogust\Workspace\Investment\Project\SPY 0DTE - Higanbana\build\news_gdelt_doc_api_enrichment_scaffold\canonical_import\data\normalized\spy_0dte\news\news_item.jsonl`

## Next Step

News-Unblock priority is now to evaluate alternative timestamp-clean real-news source paths before any live LLM research. Keep this GDELT DOC API scaffold as the current reference path, but do not wait only on GDELT; compare feasible real headline/body, publication timestamp, fetch/availability timestamp, licensing, parser/import, and decision-time discipline paths.
