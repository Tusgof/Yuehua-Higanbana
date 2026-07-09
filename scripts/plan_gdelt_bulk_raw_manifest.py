from __future__ import annotations

import argparse
import json
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COMMAND_PLAN_PATH = PROJECT_ROOT / "reports" / "news_gdelt_capture_command_plan.json"
DEFAULT_JSON_OUTPUT = PROJECT_ROOT / "reports" / "news_gdelt_bulk_raw_manifest.json"
DEFAULT_REPORT_OUTPUT = PROJECT_ROOT / "reports" / "news_gdelt_bulk_raw_manifest.md"
DEFAULT_MASTER_FILE_LIST_URL = "http://data.gdeltproject.org/gdeltv2/masterfilelist.txt"
FAMILY_TEMPLATES = {
    "gkg": "{stamp}.gkg.csv.zip",
    "mentions": "{stamp}.mentions.CSV.zip",
    "export": "{stamp}.export.CSV.zip",
}


class GdeltBulkRawManifestError(ValueError):
    pass


def plan_bulk_raw_manifest(
    command_plan_path: Path = DEFAULT_COMMAND_PLAN_PATH,
    master_file_list_path: Path | None = None,
    master_file_list_url: str = DEFAULT_MASTER_FILE_LIST_URL,
    lookback_hours: int | None = None,
    families: list[str] | None = None,
    max_candidate_days: int | None = None,
) -> dict[str, Any]:
    if lookback_hours is not None and lookback_hours <= 0:
        raise GdeltBulkRawManifestError("lookback_hours must be positive")
    selected_families = families or ["gkg", "mentions", "export"]
    unknown = sorted(set(selected_families).difference(FAMILY_TEMPLATES))
    if unknown:
        raise GdeltBulkRawManifestError(f"unknown GDELT file families: {unknown}")

    command_plan = _load_json(command_plan_path)
    commands = _select_commands(command_plan, max_candidate_days)
    effective_lookback_hours = int(lookback_hours or command_plan.get("lookback_hours") or 24)
    expected = _build_expected_files(commands, selected_families, effective_lookback_hours)
    wanted_basenames = {item["basename"] for item in expected}
    matched_by_basename = _scan_master_file_list(wanted_basenames, master_file_list_path, master_file_list_url)

    manifest_items = []
    for item in expected:
        match = matched_by_basename.get(item["basename"])
        manifest_items.append(
            {
                **item,
                "available_in_master_file_list": match is not None,
                "source_url": match.get("url") if match else None,
                "compressed_bytes": match.get("compressed_bytes") if match else None,
                "master_hash": match.get("master_hash") if match else None,
                "download_status": "not_downloaded_metadata_only",
            }
        )

    by_family = _summarize_by_family(manifest_items)
    missing_items = [item for item in manifest_items if not item["available_in_master_file_list"]]
    status = "ready_for_one_file_probe" if by_family.get("gkg", {}).get("matched_file_count", 0) > 0 else "blocked"
    blockers = [] if status == "ready_for_one_file_probe" else ["requires_gdelt_bulk_gkg_master_matches"]
    return {
        "plan_version": "gdelt-bulk-raw-manifest-v1",
        "mode": "metadata_only_no_raw_download",
        "status": status,
        "blockers": blockers,
        "command_plan_path": str(command_plan_path),
        "master_file_list_source": str(master_file_list_path) if master_file_list_path else master_file_list_url,
        "candidate_day_count": len(commands),
        "lookback_hours": effective_lookback_hours,
        "file_families": selected_families,
        "expected_file_count": len(manifest_items),
        "matched_file_count": sum(1 for item in manifest_items if item["available_in_master_file_list"]),
        "missing_file_count": len(missing_items),
        "estimated_total_compressed_bytes": sum(int(item["compressed_bytes"] or 0) for item in manifest_items),
        "by_family": by_family,
        "timestamp_policy": {
            "decision_time_source": "reports\\news_gdelt_capture_command_plan.json commands[].decision_time_et",
            "window": "GDELT 15-minute file stamps from decision_time - lookback_hours through decision_time",
            "publication_timestamp_status": "not_validated",
            "seen_timestamp_status": "candidate_only",
            "anti_leakage_requirement": "future parser must map raw timestamps into published_at/fetched_at or an honest surrogate before canonical import",
        },
        "parser_blockers": [
            "select and validate GKG columns for source/headline/url/timestamps",
            "distinguish exact publication time from GDELT seen/index time",
            "pre-register topic matching before OOS strategy use",
            "convert one small probe file to the existing offline news snapshot CSV shape before canonical import",
        ],
        "next_step": _next_step(status),
        "missing_manifest_items": missing_items[:50],
        "manifest_items": manifest_items,
    }


def write_reports(result: dict[str, Any], json_output: Path = DEFAULT_JSON_OUTPUT, report_output: Path = DEFAULT_REPORT_OUTPUT) -> None:
    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# GDELT Bulk Raw Manifest Probe",
        "",
        f"- Mode: `{result['mode']}`",
        f"- Status: `{result['status']}`",
        f"- Candidate days: `{result['candidate_day_count']}`",
        f"- Lookback hours: `{result['lookback_hours']}`",
        f"- Expected files: `{result['expected_file_count']}`",
        f"- Matched files: `{result['matched_file_count']}`",
        f"- Missing files: `{result['missing_file_count']}`",
        f"- Estimated compressed bytes: `{result['estimated_total_compressed_bytes']}`",
        f"- Master file list source: `{result['master_file_list_source']}`",
        "",
        "## Family Summary",
        "",
        "| Family | Expected | Matched | Estimated Bytes |",
        "|:--|--:|--:|--:|",
    ]
    for family, summary in result["by_family"].items():
        lines.append(
            f"| {family} | {summary['expected_file_count']} | {summary['matched_file_count']} | {summary['estimated_compressed_bytes']} |"
        )

    lines.extend(["", "## Blockers", ""])
    blockers = result.get("blockers") or []
    lines.extend([f"- `{blocker}`" for blocker in blockers] if blockers else ["- None for metadata planning. Real news remains blocked until parser/import audit passes."])

    lines.extend(["", "## Parser Blockers", ""])
    lines.extend(f"- {blocker}" for blocker in result["parser_blockers"])
    lines.extend(["", "## Timestamp Policy", ""])
    for key, value in result["timestamp_policy"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Next Step", "", result["next_step"], "", "## Sample Manifest Items", ""])
    for item in result["manifest_items"][:20]:
        lines.append(
            f"- `{item['trade_date']}` `{item['family']}` `{item['basename']}` "
            f"matched=`{item['available_in_master_file_list']}` bytes=`{item['compressed_bytes']}`"
        )
    missing_items = result.get("missing_manifest_items") or []
    if missing_items:
        lines.extend(["", "## Missing Manifest Items", ""])
        for item in missing_items[:20]:
            lines.append(f"- `{item['trade_date']}` `{item['family']}` `{item['basename']}`")
    report_output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise GdeltBulkRawManifestError(f"{path} must contain a JSON object")
    return payload


def _select_commands(command_plan: dict[str, Any], max_candidate_days: int | None) -> list[dict[str, Any]]:
    commands = command_plan.get("commands")
    if not isinstance(commands, list) or not commands:
        raise GdeltBulkRawManifestError("command plan missing commands array")
    selected = [command for command in commands if isinstance(command, dict)]
    if max_candidate_days is not None:
        if max_candidate_days <= 0:
            raise GdeltBulkRawManifestError("max_candidate_days must be positive")
        selected = selected[:max_candidate_days]
    return selected


def _build_expected_files(commands: list[dict[str, Any]], families: list[str], lookback_hours: int) -> list[dict[str, Any]]:
    expected: list[dict[str, Any]] = []
    for command in commands:
        trade_date = str(command.get("trade_date") or "")
        decision_time = _parse_timestamp(str(command.get("decision_time_et") or ""))
        for stamp in _gdelt_stamps(decision_time, lookback_hours):
            for family in families:
                basename = FAMILY_TEMPLATES[family].format(stamp=stamp)
                expected.append(
                    {
                        "trade_date": trade_date,
                        "decision_time_et": decision_time.isoformat(timespec="seconds"),
                        "gdelt_file_timestamp_utc": stamp,
                        "family": family,
                        "basename": basename,
                    }
                )
    return expected


def _parse_timestamp(value: str) -> datetime:
    if not value:
        raise GdeltBulkRawManifestError("decision_time_et is required")
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise GdeltBulkRawManifestError("decision_time_et must include timezone")
    return parsed


def _gdelt_stamps(decision_time: datetime, lookback_hours: int) -> list[str]:
    end = _floor_15m(decision_time.astimezone(timezone.utc))
    start = _floor_15m(end - timedelta(hours=lookback_hours))
    stamps = []
    current = start
    while current <= end:
        stamps.append(current.strftime("%Y%m%d%H%M%S"))
        current += timedelta(minutes=15)
    return stamps


def _floor_15m(value: datetime) -> datetime:
    return value.replace(minute=(value.minute // 15) * 15, second=0, microsecond=0)


def _scan_master_file_list(
    wanted_basenames: set[str],
    master_file_list_path: Path | None,
    master_file_list_url: str,
) -> dict[str, dict[str, Any]]:
    matches: dict[str, dict[str, Any]] = {}
    for line in _iter_master_lines(master_file_list_path, master_file_list_url):
        parsed = _parse_master_line(line)
        if not parsed:
            continue
        basename = Path(parsed["url"]).name
        if basename in wanted_basenames:
            matches[basename] = parsed
            if len(matches) == len(wanted_basenames):
                break
    return matches


def _iter_master_lines(master_file_list_path: Path | None, master_file_list_url: str) -> Iterable[str]:
    if master_file_list_path:
        yield from master_file_list_path.read_text(encoding="utf-8").splitlines()
        return
    with urllib.request.urlopen(master_file_list_url, timeout=60) as response:
        for raw_line in response:
            yield raw_line.decode("utf-8", errors="replace").strip()


def _parse_master_line(line: str) -> dict[str, Any] | None:
    parts = line.split()
    if len(parts) < 3:
        return None
    try:
        compressed_bytes = int(parts[0])
    except ValueError:
        return None
    return {"compressed_bytes": compressed_bytes, "master_hash": parts[1], "url": parts[-1]}


def _summarize_by_family(items: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    summary: dict[str, dict[str, int]] = {}
    for item in items:
        family = item["family"]
        bucket = summary.setdefault(family, {"expected_file_count": 0, "matched_file_count": 0, "estimated_compressed_bytes": 0})
        bucket["expected_file_count"] += 1
        if item["available_in_master_file_list"]:
            bucket["matched_file_count"] += 1
            bucket["estimated_compressed_bytes"] += int(item["compressed_bytes"] or 0)
    return dict(sorted(summary.items()))


def _next_step(status: str) -> str:
    if status != "ready_for_one_file_probe":
        return "Fix the master-file-list mapping before any raw-file download."
    return (
        "Select one small GKG file from this manifest for a controlled parser probe. "
        "Do not download broad raw archives or run LLM research until the probe maps timestamps/source/headline/url into canonical news_item fields."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan a metadata-only GDELT bulk raw-file manifest without downloading raw archive files.")
    parser.add_argument("--command-plan-path", type=Path, default=DEFAULT_COMMAND_PLAN_PATH)
    parser.add_argument("--master-file-list-path", type=Path)
    parser.add_argument("--master-file-list-url", default=DEFAULT_MASTER_FILE_LIST_URL)
    parser.add_argument("--lookback-hours", type=int)
    parser.add_argument("--family", action="append", dest="families", choices=sorted(FAMILY_TEMPLATES))
    parser.add_argument("--max-candidate-days", type=int)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    args = parser.parse_args(argv)

    result = plan_bulk_raw_manifest(
        command_plan_path=args.command_plan_path,
        master_file_list_path=args.master_file_list_path,
        master_file_list_url=args.master_file_list_url,
        lookback_hours=args.lookback_hours,
        families=args.families,
        max_candidate_days=args.max_candidate_days,
    )
    write_reports(result, args.json_output, args.report_output)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
