from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NEWS_PATH = PROJECT_ROOT / "data" / "normalized" / "spy_0dte" / "news" / "news_item.jsonl"
DEFAULT_SOURCE_PLAN_PATH = PROJECT_ROOT / "tests" / "fixtures" / "news_sources_v1.json"
DEFAULT_JSON_OUTPUT = PROJECT_ROOT / "reports" / "news_coverage_audit.json"
DEFAULT_REPORT_OUTPUT = PROJECT_ROOT / "reports" / "news_coverage_audit.md"

REQUIRED_WINDOWS = {
    "reference_pre_break": ("2019-01-01", "2022-05-10"),
    "train": ("2022-05-11", "2023-12-31"),
    "oos": ("2024-01-01", date.today().isoformat()),
}


class NewsCoverageError(ValueError):
    pass


def audit_news_coverage(
    news_path: Path = DEFAULT_NEWS_PATH,
    source_plan_path: Path = DEFAULT_SOURCE_PLAN_PATH,
) -> dict[str, Any]:
    required_topics = _load_required_topics(source_plan_path)
    records = _load_news_items(news_path)
    published_dates = [_published_date(record) for record in records]
    coverage_start = min(published_dates).isoformat() if published_dates else None
    coverage_end = max(published_dates).isoformat() if published_dates else None

    by_year: dict[int, set[str]] = defaultdict(set)
    by_window: dict[str, set[str]] = {name: set() for name in REQUIRED_WINDOWS}
    for record, published_date in zip(records, published_dates):
        topic = record["topic"]
        by_year[published_date.year].add(topic)
        for name, (start, end) in REQUIRED_WINDOWS.items():
            if date.fromisoformat(start) <= published_date <= date.fromisoformat(end):
                by_window[name].add(topic)

    target_years = list(range(2022, date.today().year + 1))
    year_results = []
    for year in target_years:
        present = sorted(by_year.get(year, set()))
        missing = sorted(set(required_topics).difference(present))
        year_results.append({"year": year, "present_topics": present, "missing_topics": missing})

    window_results = []
    for name, (start, end) in REQUIRED_WINDOWS.items():
        present = sorted(by_window[name])
        missing = sorted(set(required_topics).difference(present))
        window_results.append(
            {
                "window": name,
                "start": start,
                "end": end,
                "present_topics": present,
                "missing_topics": missing,
            }
        )

    all_missing = sorted({topic for item in year_results + window_results for topic in item["missing_topics"]})
    status = "pass" if records and not all_missing and coverage_start and coverage_start <= "2022-05-11" else "blocked"
    return {
        "status": status,
        "news_path": str(news_path),
        "record_count": len(records),
        "coverage_start": coverage_start,
        "coverage_end": coverage_end,
        "required_topics": required_topics,
        "years": year_results,
        "windows": window_results,
        "blockers": _blockers(status, records, coverage_start, year_results, window_results),
    }


def write_reports(result: dict[str, Any], json_output: Path = DEFAULT_JSON_OUTPUT, report_output: Path = DEFAULT_REPORT_OUTPUT) -> None:
    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# News Coverage Audit",
        "",
        f"- Status: `{result['status']}`",
        f"- Record count: {result['record_count']}",
        f"- Coverage start: `{result['coverage_start']}`",
        f"- Coverage end: `{result['coverage_end']}`",
        "",
        "## Blockers",
        "",
    ]
    for blocker in result["blockers"]:
        lines.append(f"- `{blocker}`")
    lines.extend(["", "## Year Coverage", "", "| Year | Present | Missing |", "|:--|:--|:--|"])
    for item in result["years"]:
        lines.append(f"| {item['year']} | {', '.join(item['present_topics']) or '-'} | {', '.join(item['missing_topics']) or '-'} |")
    lines.extend(["", "## Window Coverage", "", "| Window | Start | End | Missing |", "|:--|:--|:--|:--|"])
    for item in result["windows"]:
        lines.append(f"| {item['window']} | {item['start']} | {item['end']} | {', '.join(item['missing_topics']) or '-'} |")
    report_output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _load_required_topics(path: Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    topics = payload.get("minimum_required_topics")
    if not isinstance(topics, list) or not topics:
        raise NewsCoverageError("minimum_required_topics must be a non-empty array")
    return [str(topic) for topic in topics]


def _load_news_items(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            record = json.loads(line)
            if record.get("record_type") == "news_item" and record.get("provider") != "synthetic":
                records.append(record)
    return records


def _published_date(record: dict[str, Any]) -> date:
    timestamp = str(record.get("published_at_et", ""))
    if not timestamp:
        raise NewsCoverageError("news_item missing published_at_et")
    return datetime.fromisoformat(timestamp).date()


def _blockers(
    status: str,
    records: list[dict[str, Any]],
    coverage_start: str | None,
    years: list[dict[str, Any]],
    windows: list[dict[str, Any]],
) -> list[str]:
    blockers: set[str] = set()
    if status == "pass":
        return []
    if not records:
        blockers.add("requires_real_news_archive")
    if not coverage_start or coverage_start > "2022-05-11":
        blockers.add("requires_news_archive_start_by_2022_05_11")
    for item in years:
        if item["missing_topics"]:
            blockers.add(f"requires_news_topic_coverage_{item['year']}")
    for item in windows:
        if item["missing_topics"]:
            blockers.add(f"requires_news_window_coverage_{item['window']}")
    return sorted(blockers)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit canonical news archive coverage for Higanbana train/OOS windows.")
    parser.add_argument("--news-path", type=Path, default=DEFAULT_NEWS_PATH)
    parser.add_argument("--source-plan-path", type=Path, default=DEFAULT_SOURCE_PLAN_PATH)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    args = parser.parse_args(argv)

    result = audit_news_coverage(args.news_path, args.source_plan_path)
    write_reports(result, args.json_output, args.report_output)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
