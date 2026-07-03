from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from import_news_snapshots import DEFAULT_SOURCE_PLAN_PATH, NewsImportError, import_news_snapshot


DEFAULT_INPUT_DIR = PROJECT_ROOT / "data" / "raw" / "spy_0dte" / "news" / "gdelt"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "build" / "news_gdelt_capture_import"
DEFAULT_COMBINED_SNAPSHOT_PATH = DEFAULT_OUTPUT_ROOT / "gdelt_news_combined.csv"
DEFAULT_SUMMARY_PATH = PROJECT_ROOT / "reports" / "news_gdelt_capture_directory_import_summary.json"
DEFAULT_REPORT_PATH = PROJECT_ROOT / "reports" / "news_gdelt_capture_directory_import_summary.md"

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


class GdeltNewsDirectoryImportError(ValueError):
    pass


def import_capture_directory(
    input_dir: Path = DEFAULT_INPUT_DIR,
    source_plan_path: Path = DEFAULT_SOURCE_PLAN_PATH,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    combined_snapshot_path: Path = DEFAULT_COMBINED_SNAPSHOT_PATH,
    summary_path: Path = DEFAULT_SUMMARY_PATH,
    report_path: Path = DEFAULT_REPORT_PATH,
    pattern: str = "*.csv",
) -> dict[str, Any]:
    snapshot_paths = _find_snapshot_paths(input_dir, pattern)
    combined = combine_snapshot_files(snapshot_paths, combined_snapshot_path)
    import_result = import_news_snapshot(combined_snapshot_path, source_plan_path, output_root)
    result = {
        "mode": "offline_directory_import",
        "input_dir": str(input_dir),
        "pattern": pattern,
        "snapshot_count": len(snapshot_paths),
        "source_snapshots": [str(path) for path in snapshot_paths],
        "combined_snapshot_path": str(combined_snapshot_path),
        "combined_row_count": combined["row_count"],
        "record_count": import_result["record_count"],
        "topics": import_result["topics"],
        "normalized_path": import_result["normalized_path"],
        "registry_path": import_result["registry_path"],
        "manifest": import_result["manifest"],
        "note": "Offline import only. This does not fetch GDELT and does not prove news coverage until audit_news_coverage.py passes against the target output root.",
    }
    write_reports(result, summary_path, report_path)
    return result


def combine_snapshot_files(snapshot_paths: list[Path], combined_snapshot_path: Path) -> dict[str, Any]:
    rows: list[dict[str, str]] = []
    for path in snapshot_paths:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            missing_columns = set(FIELDNAMES).difference(reader.fieldnames or [])
            if missing_columns:
                raise GdeltNewsDirectoryImportError(f"{path} missing columns: {sorted(missing_columns)}")
            for row in reader:
                rows.append({field: (row.get(field) or "").strip() for field in FIELDNAMES})
    if not rows:
        raise GdeltNewsDirectoryImportError("no rows found in GDELT capture snapshots")

    rows.sort(key=lambda row: (row["decision_time_et"], row["topic"], row["published_at_utc"], row["url"]))
    combined_snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    with combined_snapshot_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    return {"row_count": len(rows), "path": str(combined_snapshot_path)}


def write_reports(result: dict[str, Any], summary_path: Path = DEFAULT_SUMMARY_PATH, report_path: Path = DEFAULT_REPORT_PATH) -> None:
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# GDELT News Capture Directory Import Summary",
        "",
        f"- Mode: `{result['mode']}`",
        f"- Snapshot count: `{result['snapshot_count']}`",
        f"- Combined rows: `{result['combined_row_count']}`",
        f"- Imported records: `{result['record_count']}`",
        f"- Combined snapshot: `{result['combined_snapshot_path']}`",
        f"- Normalized output: `{result['normalized_path']}`",
        f"- Registry output: `{result['registry_path']}`",
        "",
        "## Topics",
        "",
    ]
    lines.extend(f"- `{topic}`" for topic in result["topics"])
    lines.extend(["", "## Note", "", str(result["note"])])
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _find_snapshot_paths(input_dir: Path, pattern: str) -> list[Path]:
    if not input_dir.exists():
        raise GdeltNewsDirectoryImportError(f"input directory does not exist: {input_dir}")
    paths = sorted(path for path in input_dir.glob(pattern) if path.is_file())
    if not paths:
        raise GdeltNewsDirectoryImportError(f"no GDELT snapshot files found under {input_dir} with pattern {pattern!r}")
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Combine and import multiple offline GDELT capture CSV files.")
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--pattern", default="*.csv")
    parser.add_argument("--source-plan-path", type=Path, default=DEFAULT_SOURCE_PLAN_PATH)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--combined-snapshot-path", type=Path, default=DEFAULT_COMBINED_SNAPSHOT_PATH)
    parser.add_argument("--summary-path", type=Path, default=DEFAULT_SUMMARY_PATH)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT_PATH)
    args = parser.parse_args(argv)

    try:
        result = import_capture_directory(
            input_dir=args.input_dir,
            source_plan_path=args.source_plan_path,
            output_root=args.output_root,
            combined_snapshot_path=args.combined_snapshot_path,
            summary_path=args.summary_path,
            report_path=args.report_path,
            pattern=args.pattern,
        )
    except (GdeltNewsDirectoryImportError, NewsImportError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
