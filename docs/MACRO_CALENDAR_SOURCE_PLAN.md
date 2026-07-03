# Macro Calendar Source Plan

## Purpose

This plan selects official macro-calendar sources for the Higanbana event filter without adding a new paid provider.

The machine-readable source plan is `tests/fixtures/macro_calendar_sources_v1.json`. The validator is `scripts/validate_macro_calendar_sources.py`.

The capture planner is `scripts/capture_macro_calendar_snapshots.py`. It builds a dry-run archive plan by default and only fetches official source pages when `--execute` is passed. Executed captures write raw source files plus `capture_manifest.json`.

The offline importer is `scripts/import_macro_calendar_snapshots.py`. It reads saved CSV snapshots, normalizes them to canonical `macro_event` JSONL, writes a registry manifest with raw SHA-256, and rejects snapshots that do not cover the required event types.

The coverage auditor is `scripts/audit_macro_calendar_coverage.py`. It checks canonical macro events against the reference, train, and OOS windows. The current official-source 2022-2026 canonical import passes this audit.

## Local Research Rationale

The local LLM Wiki says 0DTE regime filtering should skip major scheduled macro-event days, including FOMC, CPI, NFP, and Fed Chair speech days. It also frames macro releases as exogenous features that can create lookahead or instability if handled loosely.

For this project, macro calendar data is a blocking input for:

- deterministic no-trade filters,
- LLM prompt context,
- future strategy backtest ablation,
- avoiding OOS leakage by preserving source timestamps.

## Selected Sources

| Event Group | Primary Source | Why |
|:--|:--|:--|
| FOMC decisions and minutes | Federal Reserve FOMC calendar | Official calendar and meeting materials. FOMC statements/minutes are listed with release times around 2:00 PM ET. |
| CPI, NFP, PPI, JOLTS | BLS yearly release schedule | Official BLS calendar. The annual `schedule/YYYY/home.htm` pages state release times in Eastern Time and avoid current-page contamination during backfill. |
| PCE | BEA Personal Income and Outlays release pages | Official BEA release pages contain the embargo/release timestamp and avoid relying on a current-only schedule page for historical backfill. |
| ISM Manufacturing and Services PMI | ISM release calendar | Official ISM calendar. Manufacturing PMI is first business day at 10:00 AM ET; Services PMI is third business day at 10:00 AM ET. |
| Retail sales | U.S. Census Bureau MARTS release-date Excel | Official Advance Monthly Retail Sales release-date workbook. |

Trading Economics remains deferred because it is a paid consolidated API and would need explicit user approval.

## Normalized Event Contract

Each imported event must map to the existing `macro_event` schema:

- `record_type`: `macro_event`
- `schema_version`: `m2.0`
- `event_id`: stable source-derived id
- `event_type`: one of the planned event types
- `event_timestamp_et`: release timestamp in ET
- `importance`: `high`, `medium`, or `low`
- `provider`: source organization
- `source`: source URL or archived raw file path

Minimum required event types for the next importer:

- `FOMC_DECISION`
- `FOMC_MINUTES`
- `CPI`
- `NFP`
- `PCE`
- `JOLTS`
- `ISM_MANUFACTURING`
- `ISM_SERVICES`
- `RETAIL_SALES`

## Implementation Notes

- Preserve the raw source snapshot and raw hash before normalization.
- Treat all scheduled release timestamps as ET.
- For source pages that list revised government-shutdown dates, preserve the observed source timestamp and do not backfill from assumptions.
- Use official sources first. Do not use Trading Economics or another paid calendar without explicit approval.
- Capture raw official source pages before converting them into importer CSV shape.
- The source-specific converter turns raw HTML/JSON/XLS captures into the importer snapshot shape before normalization.
- BLS historical backfill now uses `https://www.bls.gov/schedule/{year}/home.htm` through `source_url_template`; the converter supports the BLS yearly list view and ignores similarly named state/special releases.
- BEA PCE historical backfill uses `capture_mode: bea_pce_release_pages`, storing official release pages in a raw JSON archive and parsing the BEA embargo timestamp.
- Census retail historical backfill uses `https://www.census.gov/retail/marts/www/MARTSreleasedates.xls` with `output_extension: xls`.
- Canonical import of the 2022-2026 official-source backfill is complete: `data\raw\spy_0dte\macro_calendar\official_macro_calendar_2022_2026_backfill.csv` imported to `data\normalized\spy_0dte\macro_calendar\macro_event.jsonl` with 481 events.
- The current coverage audit passes for required event-type presence across reference, train, OOS, and each year from 2022 through 2026. Note that the `reference_pre_break` check confirms required event-type presence inside the window; it does not claim full 2019-2021 continuity.

## Verification

```powershell
python scripts\validate_macro_calendar_sources.py
python scripts\capture_macro_calendar_snapshots.py --as-of-date 2024-01-03
python scripts\capture_macro_calendar_snapshots.py --as-of-date 2026-06-30 --execute
python scripts\convert_macro_calendar_capture.py --capture-root data\raw\spy_0dte\macro_calendar\2026-06-30
python scripts\import_macro_calendar_snapshots.py --output-root build\macro_calendar_fixture
python scripts\import_macro_calendar_snapshots.py --snapshot-path data\raw\spy_0dte\macro_calendar\official_macro_calendar_2022_2026_backfill.csv --output-root .
python scripts\audit_macro_calendar_raw_archive.py --start-year 2022 --end-year 2026 --current-as-of-date 2026-06-30
python scripts\audit_macro_calendar_coverage.py
python -m unittest tests.test_validate_macro_calendar_sources tests.test_capture_macro_calendar_snapshots tests.test_convert_macro_calendar_capture tests.test_import_macro_calendar_snapshots tests.test_audit_macro_calendar_coverage
```

## Source Links

- Federal Reserve FOMC calendar: https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm
- Federal Reserve RSS/calendar index: https://www.federalreserve.gov/feeds/feeds.htm
- BLS release schedule: https://www.bls.gov/schedule/
- BLS yearly release schedule example: https://www.bls.gov/schedule/2024/home.htm
- BEA news archive: https://www.bea.gov/news/archive
- ISM PMI release calendar: https://www.ismworld.org/supply-management-news-and-reports/reports/rob-report-calendar/
- Census MARTS release dates: https://www.census.gov/retail/marts/www/MARTSreleasedates.xls
