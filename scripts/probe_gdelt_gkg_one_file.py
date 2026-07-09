from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_PATH = PROJECT_ROOT / "reports" / "news_gdelt_bulk_raw_manifest.json"
DEFAULT_RAW_DIR = PROJECT_ROOT / "data" / "raw" / "spy_0dte" / "news" / "gdelt_bulk_probe"
DEFAULT_JSON_OUTPUT = PROJECT_ROOT / "reports" / "news_gdelt_gkg_one_file_parser_probe.json"
DEFAULT_REPORT_OUTPUT = PROJECT_ROOT / "reports" / "news_gdelt_gkg_one_file_parser_probe.md"

GKG_COLUMNS = [
    "gkg_record_id",
    "date",
    "source_collection_identifier",
    "source_common_name",
    "document_identifier",
    "counts",
    "v2_counts",
    "themes",
    "v2_themes",
    "locations",
    "v2_locations",
    "persons",
    "v2_persons",
    "organizations",
    "v2_organizations",
    "v2_tone",
    "dates",
    "gcam",
    "sharing_image",
    "related_images",
    "social_image_embeds",
    "social_video_embeds",
    "quotations",
    "all_names",
    "amounts",
    "translation_info",
    "extras",
]


class GdeltGkgProbeError(ValueError):
    pass


def probe_gdelt_gkg_one_file(
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    raw_dir: Path = DEFAULT_RAW_DIR,
    json_output: Path = DEFAULT_JSON_OUTPUT,
    report_output: Path = DEFAULT_REPORT_OUTPUT,
    max_rows: int | None = None,
) -> dict[str, Any]:
    manifest = _load_json(manifest_path)
    item = _select_smallest_gkg_item(manifest)
    raw_zip_path = _ensure_zip(item, raw_dir)
    parsed = _parse_gkg_zip(raw_zip_path, max_rows=max_rows)
    result = _build_probe_result(manifest_path, item, raw_zip_path, parsed)
    write_reports(result, json_output, report_output)
    return result


def write_reports(result: dict[str, Any], json_output: Path = DEFAULT_JSON_OUTPUT, report_output: Path = DEFAULT_REPORT_OUTPUT) -> None:
    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# GDELT GKG One-File Parser Probe",
        "",
        f"- Status: `{result['status']}`",
        f"- Selected file: `{result['selected_file']['basename']}`",
        f"- Trade date: `{result['selected_file']['trade_date']}`",
        f"- Decision time ET: `{result['selected_file']['decision_time_et']}`",
        f"- Raw ZIP path: `{result['raw_zip_path']}`",
        f"- Raw ZIP SHA256: `{result['raw_zip_sha256']}`",
        f"- Parsed rows: `{result['row_count']}`",
        f"- HTTPS URL rows: `{result['https_url_count']}`",
        f"- Non-empty source rows: `{result['non_empty_source_count']}`",
        "",
        "## Field Mapping",
        "",
        "| Canonical field | Status | Source | Note |",
        "|:--|:--|:--|:--|",
    ]
    for field, mapping in result["field_mapping"].items():
        lines.append(f"| `{field}` | `{mapping['status']}` | `{mapping['source']}` | {mapping['note']} |")

    lines.extend(["", "## Blockers", ""])
    blockers = result.get("blockers") or []
    lines.extend([f"- `{blocker}`" for blocker in blockers] if blockers else ["- None."])

    lines.extend(["", "## Sample Rows", ""])
    for row in result["sample_rows"]:
        lines.append(f"- `{row['source_name']}` `{row['gkg_timestamp_utc']}` `{row['url']}`")

    lines.extend(["", "## Next Step", "", result["next_step"]])
    report_output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _build_probe_result(manifest_path: Path, item: dict[str, Any], raw_zip_path: Path, parsed: dict[str, Any]) -> dict[str, Any]:
    blockers = []
    if parsed["row_count"] == 0:
        blockers.append("gkg_file_has_no_rows")
    if parsed["non_empty_source_count"] == 0:
        blockers.append("gkg_source_name_not_mapped")
    if parsed["https_url_count"] == 0:
        blockers.append("gkg_https_url_not_mapped")

    # GKG DATE is a GDELT observation/file timestamp. It is useful for anti-leakage
    # ordering, but it does not prove exact article publication time.
    timestamp_status = "surrogate_only" if parsed["row_count"] else "blocked"
    headline_status = "blocked"
    topic_status = "blocked"
    blockers.extend(
        [
            "gkg_has_no_verified_headline_field",
            "gkg_publication_time_is_surrogate_not_exact",
            "gkg_topic_mapping_not_pre_registered",
        ]
    )

    status = "blocked_requires_enrichment_or_policy"
    return {
        "probe_version": "gdelt-gkg-one-file-parser-probe-v1",
        "mode": "one_file_controlled_probe",
        "status": status,
        "blockers": sorted(set(blockers)),
        "manifest_path": str(manifest_path),
        "selected_file": {
            "trade_date": item["trade_date"],
            "decision_time_et": item["decision_time_et"],
            "gdelt_file_timestamp_utc": item["gdelt_file_timestamp_utc"],
            "basename": item["basename"],
            "source_url": item["source_url"],
            "compressed_bytes": item["compressed_bytes"],
        },
        "raw_zip_path": str(raw_zip_path),
        "raw_zip_sha256": _sha256(raw_zip_path),
        "inner_filename": parsed["inner_filename"],
        "row_count": parsed["row_count"],
        "column_count_histogram": parsed["column_count_histogram"],
        "https_url_count": parsed["https_url_count"],
        "non_empty_source_count": parsed["non_empty_source_count"],
        "url_slug_surrogate_count": parsed["url_slug_surrogate_count"],
        "field_mapping": {
            "decision_time_et": {
                "status": "pass",
                "source": "manifest item decision_time_et",
                "note": "Decision timestamp comes from the pre-existing candidate-day command plan.",
            },
            "fetched_at_et": {
                "status": timestamp_status,
                "source": "GKG DATE / file timestamp",
                "note": "Usable only as GDELT seen/index time, not as exact fetch replay time.",
            },
            "published_at_et": {
                "status": timestamp_status,
                "source": "GKG DATE / file timestamp",
                "note": "Publication time is not proven by this field.",
            },
            "source_name": {
                "status": "pass" if parsed["non_empty_source_count"] else "blocked",
                "source": "source_common_name",
                "note": "Maps to the canonical source name when non-empty.",
            },
            "url": {
                "status": "pass" if parsed["https_url_count"] else "blocked",
                "source": "document_identifier",
                "note": "Canonical importer currently accepts HTTPS URLs.",
            },
            "headline": {
                "status": headline_status,
                "source": "not present as verified GKG column",
                "note": "URL slug can be a diagnostic surrogate only; do not import it as a real headline.",
            },
            "topic": {
                "status": topic_status,
                "source": "themes/v2_themes",
                "note": "Project topic mapping must be pre-registered before canonical import.",
            },
        },
        "sample_rows": parsed["sample_rows"],
        "next_step": (
            "Do not broad-download GKG files yet. Decide whether to enrich this one-file GKG probe through a source page/title fetch, "
            "a GDELT DOC API join, or another timestamp-clean news source; then rerun canonical import/audit only if verified headlines and timestamp policy pass."
        ),
    }


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise GdeltGkgProbeError(f"{path} must contain a JSON object")
    return payload


def _select_smallest_gkg_item(manifest: dict[str, Any]) -> dict[str, Any]:
    items = [
        item
        for item in manifest.get("manifest_items", [])
        if item.get("family") == "gkg" and item.get("available_in_master_file_list") and item.get("compressed_bytes") and item.get("source_url")
    ]
    if not items:
        raise GdeltGkgProbeError("manifest has no available GKG items")
    return sorted(items, key=lambda item: int(item["compressed_bytes"]))[0]


def _ensure_zip(item: dict[str, Any], raw_dir: Path) -> Path:
    raw_dir.mkdir(parents=True, exist_ok=True)
    target = raw_dir / item["basename"]
    if target.exists() and target.stat().st_size > 0:
        return target

    source_url = str(item["source_url"])
    parsed = urllib.parse.urlparse(source_url)
    if parsed.scheme == "file":
        source_path = Path(urllib.request.url2pathname(parsed.path))
        shutil.copyfile(source_path, target)
        return target

    with urllib.request.urlopen(source_url, timeout=60) as response:
        target.write_bytes(response.read())
    return target


def _parse_gkg_zip(path: Path, max_rows: int | None = None) -> dict[str, Any]:
    if max_rows is not None and max_rows <= 0:
        raise GdeltGkgProbeError("max_rows must be positive")

    row_count = 0
    https_url_count = 0
    non_empty_source_count = 0
    url_slug_surrogate_count = 0
    column_count_histogram: dict[str, int] = {}
    sample_rows: list[dict[str, str]] = []

    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if not names:
            raise GdeltGkgProbeError(f"{path} contains no files")
        inner_filename = names[0]
        with archive.open(inner_filename) as raw:
            wrapper = (line.decode("utf-8", errors="replace") for line in raw)
            reader = csv.reader(wrapper, delimiter="\t")
            for row in reader:
                if max_rows is not None and row_count >= max_rows:
                    break
                row_count += 1
                column_count_histogram[str(len(row))] = column_count_histogram.get(str(len(row)), 0) + 1
                record = _row_to_record(row)
                source_name = record.get("source_common_name", "").strip()
                url = record.get("document_identifier", "").strip()
                if source_name:
                    non_empty_source_count += 1
                if url.startswith("https://"):
                    https_url_count += 1
                if _url_slug_surrogate(url):
                    url_slug_surrogate_count += 1
                if len(sample_rows) < 10:
                    sample_rows.append(
                        {
                            "gkg_record_id": record.get("gkg_record_id", ""),
                            "gkg_timestamp_utc": _format_gkg_timestamp(record.get("date", "")),
                            "source_name": source_name,
                            "url": url,
                            "url_slug_surrogate": _url_slug_surrogate(url),
                        }
                    )

    return {
        "inner_filename": inner_filename,
        "row_count": row_count,
        "column_count_histogram": dict(sorted(column_count_histogram.items())),
        "https_url_count": https_url_count,
        "non_empty_source_count": non_empty_source_count,
        "url_slug_surrogate_count": url_slug_surrogate_count,
        "sample_rows": sample_rows,
    }


def _row_to_record(row: list[str]) -> dict[str, str]:
    values = row[: len(GKG_COLUMNS)] + [""] * max(0, len(GKG_COLUMNS) - len(row))
    return dict(zip(GKG_COLUMNS, values))


def _format_gkg_timestamp(value: str) -> str:
    try:
        parsed = datetime.strptime(value, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return value
    return parsed.isoformat(timespec="seconds").replace("+00:00", "Z")


def _url_slug_surrogate(url: str) -> str:
    path = urllib.parse.urlparse(url).path.strip("/")
    if not path:
        return ""
    slug = path.split("/")[-1]
    slug = slug.rsplit(".", 1)[0]
    cleaned = " ".join(part for part in slug.replace("-", " ").replace("_", " ").split() if part)
    return cleaned[:160]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a controlled one-file parser probe for GDELT GKG raw archives.")
    parser.add_argument("--manifest-path", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    parser.add_argument("--max-rows", type=int)
    args = parser.parse_args(argv)

    result = probe_gdelt_gkg_one_file(
        manifest_path=args.manifest_path,
        raw_dir=args.raw_dir,
        json_output=args.json_output,
        report_output=args.report_output,
        max_rows=args.max_rows,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
