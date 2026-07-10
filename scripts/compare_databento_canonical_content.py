from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.environment import data_root, interpreter_metadata
from lib.integrity import dbn_record_body_hashes, dbn_section_hashes, sha256_file


DATA_ROOT = data_root()
DEFAULT_JSON_OUTPUT = PROJECT_ROOT / "reports" / "diagnostics" / "databento_integrity_canonical_comparison_2024_06_13.json"
DEFAULT_MD_OUTPUT = PROJECT_ROOT / "reports" / "diagnostics" / "databento_integrity_canonical_comparison_2024_06_13.md"
TARGETS = (
    {
        "window": "2024-06-13_exit_check_1430",
        "current": "raw/spy_0dte/databento/oos_2024_06_intraday_exit_30m_chunk2/2024-06-13_exit_check_1430.dbn.zst",
        "fresh": "raw/spy_0dte/databento/_integrity_requarantine_2024_06_13/2024-06-13_exit_check_1430.dbn.zst",
    },
    {
        "window": "2024-06-13_exit_check_1500",
        "current": "raw/spy_0dte/databento/oos_2024_06_intraday_exit_30m_chunk2/2024-06-13_exit_check_1500.dbn.zst",
        "fresh": "raw/spy_0dte/databento/_integrity_requarantine_2024_06_13/2024-06-13_exit_check_1500.dbn.zst",
    },
)


def decompressed_dbn_hashes(path: Path) -> dict[str, Any]:
    return dbn_record_body_hashes(path)


def canonical_record_lines(path: Path) -> tuple[list[str], Counter[str], list[str]]:
    try:
        import databento as db  # type: ignore
    except ModuleNotFoundError as exc:
        raise RuntimeError("Databento is required for canonical DBN record comparison.") from exc

    frame = db.DBNStore.from_file(path).to_df()
    columns = sorted(str(column) for column in frame.columns)
    records: list[str] = []
    record_types: Counter[str] = Counter()
    for ts_recv, row in frame.iterrows():
        record = {"ts_recv": _canonical_scalar(ts_recv)}
        for column in columns:
            value = row[column]
            record[column] = _canonical_scalar(value)
        record_types[str(record.get("rtype"))] += 1
        records.append(json.dumps(record, ensure_ascii=True, separators=(",", ":"), sort_keys=True))
    return sorted(records), record_types, columns


def canonical_record_export(path: Path) -> dict[str, Any]:
    records, record_types, columns = canonical_record_lines(path)
    digest = hashlib.sha256()
    for record in records:
        digest.update(record.encode("ascii"))
        digest.update(b"\n")
    return {
        "record_count": len(records),
        "record_type_counts": dict(sorted(record_types.items())),
        "columns": columns,
        "sha256": digest.hexdigest(),
        "records": records,
    }


def compare_target(current_path: Path, fresh_path: Path) -> dict[str, Any]:
    current_export = canonical_record_export(current_path)
    fresh_export = canonical_record_export(fresh_path)
    current_body = decompressed_dbn_hashes(current_path)
    fresh_body = decompressed_dbn_hashes(fresh_path)
    body_equal = current_body["sha256"] == fresh_body["sha256"]
    canonical_equal = current_export["sha256"] == fresh_export["sha256"]
    content_verified = body_equal and canonical_equal
    result = {
        "current": {
            "path": _relative(current_path),
            "container_sha256": sha256_file(current_path),
            "decompressed_dbn_body": current_body,
            "canonical_record_export": _public_export(current_export),
        },
        "fresh_quarantine": {
            "path": _relative(fresh_path),
            "container_sha256": sha256_file(fresh_path),
            "decompressed_dbn_body": fresh_body,
            "canonical_record_export": _public_export(fresh_export),
        },
        "decompressed_body_equal": body_equal,
        "canonical_record_export_equal": canonical_equal,
        "content_verified": content_verified,
        "disposition": "content_verified_envelope_variance" if content_verified else "re_escalated_canonical_content_difference",
    }
    if not content_verified:
        result["record_level_diff"] = _record_level_diff(current_export, fresh_export)
    return result


def compare_all() -> dict[str, Any]:
    rows = []
    for target in TARGETS:
        row = compare_target(DATA_ROOT / target["current"], DATA_ROOT / target["fresh"])
        row["window"] = target["window"]
        rows.append(row)
    content_verified = all(row["content_verified"] for row in rows)
    return {
        "schema_version": "databento-canonical-content-comparison-v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "content_verified_envelope_variance" if content_verified else "re_escalated",
        "methodology": {
            "decompressed_dbn_body": "SHA-256 of zstd-decompressed DBN record bytes after the metadata header. Metadata header SHA-256 is recorded separately as envelope evidence.",
            "canonical_record_export": "SHA-256 of sorted JSONL records from DBNStore.to_df(), with sorted columns, ts_recv included, deterministic scalar normalization, and an ASCII JSON encoding.",
            "resolution_rule": "Both hashes must match for every target before classifying a mismatch as envelope variance.",
        },
        "rows": rows,
        "interpreter": interpreter_metadata(),
    }


def _canonical_scalar(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, bool | int | str):
        return value
    if isinstance(value, bytes):
        return {"bytes_hex": value.hex()}
    if isinstance(value, float):
        if math.isnan(value):
            return "NaN"
        if math.isinf(value):
            return "Infinity" if value > 0 else "-Infinity"
        return format(value, ".17g")
    item = getattr(value, "item", None)
    if callable(item):
        try:
            return _canonical_scalar(item())
        except ValueError:
            return "NaN"
    return str(value)


def _public_export(export: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in export.items() if key != "records"}


def _record_level_diff(current: dict[str, Any], fresh: dict[str, Any]) -> dict[str, Any]:
    current_records = current["records"]
    fresh_records = fresh["records"]
    first_divergence: dict[str, Any] | None = None
    for index, (current_record, fresh_record) in enumerate(zip(current_records, fresh_records)):
        if current_record != fresh_record:
            first_divergence = {
                "sorted_index": index,
                "current_record": json.loads(current_record),
                "fresh_record": json.loads(fresh_record),
            }
            break
    if first_divergence is None and len(current_records) != len(fresh_records):
        index = min(len(current_records), len(fresh_records))
        first_divergence = {
            "sorted_index": index,
            "current_record": json.loads(current_records[index]) if index < len(current_records) else None,
            "fresh_record": json.loads(fresh_records[index]) if index < len(fresh_records) else None,
        }
    return {
        "record_count_current": len(current_records),
        "record_count_fresh": len(fresh_records),
        "record_type_counts_current": current["record_type_counts"],
        "record_type_counts_fresh": fresh["record_type_counts"],
        "first_divergent_record": first_divergence,
    }


def _relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path)


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Databento Canonical Content Comparison - 2024-06-13",
        "",
        f"- **Status**: `{result['status']}`",
        "- **Rule**: both decompressed-body and canonical-record-export hashes must match.",
        "",
        "| Window | Body equal | Canonical records equal | Disposition |",
        "|:--|:--:|:--:|:--|",
    ]
    for row in result["rows"]:
        lines.append(
            f"| `{row['window']}` | `{row['decompressed_body_equal']}` | "
            f"`{row['canonical_record_export_equal']}` | `{row['disposition']}` |"
        )
    lines.extend(["", "## Hashes", ""])
    for row in result["rows"]:
        lines.extend(
            [
                f"### `{row['window']}`",
                f"- Current container/body/canonical: `{row['current']['container_sha256']}` / `{row['current']['decompressed_dbn_body']['sha256']}` / `{row['current']['canonical_record_export']['sha256']}`",
                f"- Fresh container/body/canonical: `{row['fresh_quarantine']['container_sha256']}` / `{row['fresh_quarantine']['decompressed_dbn_body']['sha256']}` / `{row['fresh_quarantine']['canonical_record_export']['sha256']}`",
                "",
            ]
        )
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare Databento container and canonical DBN content hashes.")
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--md-output", type=Path, default=DEFAULT_MD_OUTPUT)
    args = parser.parse_args()
    result = compare_all()
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.md_output.parent.mkdir(parents=True, exist_ok=True)
    args.md_output.write_text(render_markdown(result), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "content_verified_envelope_variance" else 1


if __name__ == "__main__":
    raise SystemExit(main())
