from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from capture_gdelt_news_snapshots import TOPIC_QUERIES, build_capture_plan, parse_artlist_response
from import_news_snapshots import import_news_snapshot


DEFAULT_PROBE_REPORT = PROJECT_ROOT / "reports" / "news_gdelt_gkg_one_file_parser_probe.json"
DEFAULT_DECISION_NOTE = PROJECT_ROOT / "docs" / "GDELT_GKG_ENRICHMENT_DECISION_NOTE.md"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "build" / "news_gdelt_doc_api_enrichment_scaffold"
DEFAULT_SNAPSHOT_PATH = DEFAULT_OUTPUT_ROOT / "gdelt_doc_api_scaffold_snapshot.csv"
DEFAULT_IMPORT_OUTPUT_ROOT = DEFAULT_OUTPUT_ROOT / "canonical_import"
DEFAULT_JSON_OUTPUT = PROJECT_ROOT / "reports" / "news_gdelt_doc_api_enrichment_scaffold.json"
DEFAULT_REPORT_OUTPUT = PROJECT_ROOT / "reports" / "news_gdelt_doc_api_enrichment_scaffold.md"

FIELDNAMES = [
    "source_id",
    "topic",
    "decision_time_et",
    "fetched_at_utc",
    "published_at_utc",
    "source_name",
    "headline",
    "url",
]


class GdeltScaffoldError(ValueError):
    pass


def run_scaffold(
    probe_report_path: Path = DEFAULT_PROBE_REPORT,
    decision_note_path: Path = DEFAULT_DECISION_NOTE,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    snapshot_path: Path = DEFAULT_SNAPSHOT_PATH,
    import_output_root: Path = DEFAULT_IMPORT_OUTPUT_ROOT,
) -> dict[str, Any]:
    probe = _load_json(probe_report_path)
    if probe.get("status") != "blocked_requires_enrichment_or_policy":
        raise GdeltScaffoldError("GKG one-file probe must be blocked before this scaffold is meaningful")
    if not decision_note_path.exists():
        raise GdeltScaffoldError("GKG enrichment decision note is required")

    selected_file = probe.get("selected_file", {})
    decision_time_et = str(selected_file.get("decision_time_et") or "2024-01-29T09:30:00-05:00")
    plan = build_capture_plan(decision_time_et, lookback_hours=24, max_records=1)
    rows = _build_scaffold_rows(plan)

    output_root.mkdir(parents=True, exist_ok=True)
    _write_snapshot(snapshot_path, rows)
    import_result = import_news_snapshot(snapshot_path=snapshot_path, output_root=import_output_root)

    result = {
        "status": "scaffold_pass_real_archive_blocked",
        "scaffold_version": "gdelt-doc-api-enrichment-scaffold-v1",
        "selected_path": "gdelt_doc_api_topic_requery_after_cooldown",
        "not_research_evidence": True,
        "network_calls": 0,
        "paid_cost_usd": 0.0,
        "decision_time_et": decision_time_et,
        "gkg_probe_report": str(probe_report_path),
        "decision_note": str(decision_note_path),
        "gkg_blockers_preserved": list(probe.get("blockers", [])),
        "doc_api_fields_proven_by_scaffold": [
            "headline_from_title",
            "url_from_article_url",
            "source_name_from_domain",
            "published_at_utc_from_seendate",
            "fetched_at_utc_from_seendate",
            "topic_from_pre_registered_project_query",
        ],
        "timestamp_policy": "For DOC API captures, seendate is treated as the replay-visible timestamp and must be <= decision_time_et. This scaffold proves importer compatibility only; real research still requires archived live capture rows.",
        "rejected_paths": [
            "url_slug_surrogate_headline",
            "broad_gkg_download_before_enrichment_proof",
            "source_page_title_scrape_without_point_in_time_policy",
            "bigquery_or_paid_news_provider_without_user_approval",
            "live_llm_before_real_timestamp_clean_news_cases",
        ],
        "snapshot_path": str(snapshot_path),
        "snapshot_row_count": len(rows),
        "topics": sorted({row["topic"] for row in rows}),
        "import_result": import_result,
        "remaining_blockers": [
            "requires_real_gdelt_doc_api_capture_after_cooldown",
            "requires_real_news_archive",
            "requires_news_coverage_audit_pass",
        ],
        "next_step": "News-Unblock priority is now to evaluate alternative timestamp-clean real-news source paths before any live LLM research. Keep this GDELT DOC API scaffold as the current reference path, but do not wait only on GDELT; compare feasible real headline/body, publication timestamp, fetch/availability timestamp, licensing, parser/import, and decision-time discipline paths.",
    }
    return result


def write_outputs(result: dict[str, Any], json_output: Path = DEFAULT_JSON_OUTPUT, report_output: Path = DEFAULT_REPORT_OUTPUT) -> None:
    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# GDELT DOC API Enrichment Scaffold",
        "",
        f"- Status: `{result['status']}`",
        f"- Selected path: `{result['selected_path']}`",
        f"- Network calls: `{result['network_calls']}`",
        f"- Paid cost: `${result['paid_cost_usd']}`",
        f"- Not research evidence: `{result['not_research_evidence']}`",
        "",
        "## What This Proves",
        "",
        "This scaffold proves that the existing GDELT DOC API parser shape can feed the canonical `news_item` importer when `title`, `url`, `domain`, and `seendate` exist.",
        "",
        "It does not prove real historical news availability and does not unblock LLM research.",
        "",
        "## Preserved GKG Blockers",
        "",
    ]
    for blocker in result["gkg_blockers_preserved"]:
        lines.append(f"- `{blocker}`")

    lines.extend(["", "## Rejected Paths", ""])
    for path in result["rejected_paths"]:
        lines.append(f"- `{path}`")

    lines.extend(["", "## Remaining Blockers", ""])
    for blocker in result["remaining_blockers"]:
        lines.append(f"- `{blocker}`")

    lines.extend(
        [
            "",
            "## Outputs",
            "",
            f"- Snapshot CSV: `{result['snapshot_path']}`",
            f"- Imported records: `{result['import_result']['record_count']}`",
            f"- Normalized output: `{result['import_result']['normalized_path']}`",
            "",
            "## Next Step",
            "",
            result["next_step"],
        ]
    )
    report_output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _build_scaffold_rows(plan: dict[str, Any]) -> list[dict[str, str]]:
    decision_time = datetime.fromisoformat(plan["decision_time_et"])
    rows: list[dict[str, str]] = []
    for index, request in enumerate(plan["requests"]):
        seen = decision_time.astimezone(timezone.utc) - timedelta(minutes=30 + index)
        payload = {
            "articles": [
                {
                    "url": f"https://example.com/higanbana-gdelt-scaffold/{request['topic']}",
                    "title": f"Higanbana scaffold headline for {request['topic'].replace('_', ' ')}",
                    "seendate": seen.strftime("%Y%m%d%H%M%S"),
                    "domain": "example.com",
                }
            ]
        }
        rows.extend(parse_artlist_response(payload, request))
    return rows


def _write_snapshot(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise GdeltScaffoldError(f"required file does not exist: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a no-network DOC API enrichment scaffold proof for the news unblock track.")
    parser.add_argument("--probe-report-path", type=Path, default=DEFAULT_PROBE_REPORT)
    parser.add_argument("--decision-note-path", type=Path, default=DEFAULT_DECISION_NOTE)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--snapshot-path", type=Path, default=DEFAULT_SNAPSHOT_PATH)
    parser.add_argument("--import-output-root", type=Path, default=DEFAULT_IMPORT_OUTPUT_ROOT)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    args = parser.parse_args(argv)

    result = run_scaffold(
        probe_report_path=args.probe_report_path,
        decision_note_path=args.decision_note_path,
        output_root=args.output_root,
        snapshot_path=args.snapshot_path,
        import_output_root=args.import_output_root,
    )
    write_outputs(result, args.json_output, args.report_output)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
