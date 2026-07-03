from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_PLAN_PATH = PROJECT_ROOT / "tests" / "fixtures" / "macro_calendar_sources_v1.json"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "data" / "raw" / "spy_0dte" / "macro_calendar"


class MacroCalendarCaptureError(ValueError):
    pass


def build_capture_plan(
    as_of_date: str,
    source_plan_path: Path = DEFAULT_SOURCE_PLAN_PATH,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    source_ids: list[str] | None = None,
) -> dict[str, Any]:
    source_plan = _load_source_plan(source_plan_path)
    _validate_as_of_date(as_of_date)
    sources = _filter_sources(source_plan["sources"], source_ids)
    requests = []
    year = datetime.strptime(as_of_date, "%Y-%m-%d").year
    for source in sources:
        source_url = _source_url_for_year(source, year)
        output_path = output_root / as_of_date / f"{_safe_filename(source['source_id'])}.{_output_extension(source)}"
        requests.append(
            {
                "source_id": source["source_id"],
                "provider": source["provider"],
                "source_url": source_url,
                "event_types": source["event_types"],
                "parser_status": source["parser_status"],
                "capture_mode": source.get("capture_mode", "single_url"),
                "as_of_date": as_of_date,
                "output_path": str(output_path),
            }
        )
    return {
        "mode": "dry_run",
        "as_of_date": as_of_date,
        "source_plan": str(source_plan_path),
        "output_root": str(output_root),
        "required_event_types": source_plan["minimum_required_event_types"],
        "source_ids": [source["source_id"] for source in sources],
        "requests": requests,
    }


def capture_snapshots(
    as_of_date: str,
    source_plan_path: Path = DEFAULT_SOURCE_PLAN_PATH,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    execute: bool = False,
    source_ids: list[str] | None = None,
) -> dict[str, Any]:
    plan = build_capture_plan(as_of_date, source_plan_path, output_root, source_ids)
    if not execute:
        return plan

    captured = []
    for request in plan["requests"]:
        if request.get("capture_mode") == "bea_pce_release_pages":
            payload = _fetch_bea_pce_release_pages_bytes(year=datetime.strptime(as_of_date, "%Y-%m-%d").year)
        else:
            payload = _fetch_bytes(request["source_url"])
        output_path = Path(request["output_path"])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(payload)
        captured.append(
            {
                "source_id": request["source_id"],
                "provider": request["provider"],
                "source_url": request["source_url"],
                "output_path": str(output_path),
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )

    result = {
        "mode": "execute",
        "as_of_date": as_of_date,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "captured_count": len(captured),
        "captured": captured,
        "next_step": "Convert archived official snapshots into importer CSV shape, then run import_macro_calendar_snapshots.py.",
    }
    manifest_path = output_root / as_of_date / "capture_manifest.json"
    result = _merge_capture_manifest(manifest_path, result)
    manifest_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result["manifest_path"] = str(manifest_path)
    return result


def _fetch_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "HiganbanaResearchBot/0.1"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        raise MacroCalendarCaptureError(f"macro calendar request failed with HTTP {exc.code}: {url}") from exc
    except urllib.error.URLError as exc:
        raise MacroCalendarCaptureError(f"macro calendar request failed: {exc.reason}") from exc


def _fetch_bea_pce_release_pages_bytes(year: int) -> bytes:
    pages: list[dict[str, Any]] = []
    missing: list[dict[str, str]] = []
    for title, candidates in _bea_pce_release_page_candidates(year):
        fetched = False
        last_error = ""
        for url in candidates:
            try:
                payload = _fetch_bytes(url)
            except MacroCalendarCaptureError as exc:
                last_error = str(exc)
                continue
            pages.append({"title": title, "source_url": url, "content": payload.decode("utf-8", errors="replace")})
            fetched = True
            break
        if not fetched:
            missing.append({"title": title, "source_url": candidates[0], "error": last_error})

    if not pages:
        raise MacroCalendarCaptureError(f"no BEA PCE release pages captured for {year}")
    payload = {
        "source_id": "bea_release_schedule",
        "provider": "BEA",
        "capture_mode": "bea_pce_release_pages",
        "year": year,
        "pages": pages,
        "missing_pages": missing,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")


def _bea_pce_release_page_candidates(year: int) -> list[tuple[str, list[str]]]:
    month_slugs = [
        "january",
        "february",
        "march",
        "april",
        "may",
        "june",
        "july",
        "august",
        "september",
        "october",
        "november",
    ]
    data_months = [("december", year - 1), *[(month, year) for month in month_slugs]]
    candidates = []
    for month, data_year in data_months:
        title = f"Personal Income and Outlays, {month.title()} {data_year}"
        normal_url = f"https://www.bea.gov/news/{year}/personal-income-and-outlays-{month}-{data_year}"
        urls = [normal_url]
        if year == 2022 and month == "august":
            urls.append(f"{normal_url}-and-annual-update")
        candidates.append((title, urls))
    return candidates


def _safe_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._")


def _source_url_for_year(source: dict[str, Any], year: int) -> str:
    template = source.get("source_url_template")
    if isinstance(template, str) and template:
        return template.format(year=year)
    return source["source_url"]


def _output_extension(source: dict[str, Any]) -> str:
    extension = source.get("output_extension")
    if isinstance(extension, str) and extension:
        return _safe_filename(extension.lower())
    return "html"


def _filter_sources(sources: list[dict[str, Any]], source_ids: list[str] | None) -> list[dict[str, Any]]:
    if not source_ids:
        return sources
    requested = set(source_ids)
    selected = [source for source in sources if source["source_id"] in requested]
    found = {source["source_id"] for source in selected}
    missing = sorted(requested.difference(found))
    if missing:
        raise MacroCalendarCaptureError(f"unknown source_id(s): {', '.join(missing)}")
    return selected


def _merge_capture_manifest(manifest_path: Path, result: dict[str, Any]) -> dict[str, Any]:
    if not manifest_path.exists():
        return result
    existing = json.loads(manifest_path.read_text(encoding="utf-8"))
    if existing.get("as_of_date") != result["as_of_date"]:
        raise MacroCalendarCaptureError(f"existing manifest date does not match {result['as_of_date']}")

    captured_by_source = {item["source_id"]: item for item in existing.get("captured", [])}
    for item in result["captured"]:
        captured_by_source[item["source_id"]] = item

    merged = dict(result)
    merged["captured"] = sorted(captured_by_source.values(), key=lambda item: item["source_id"])
    merged["captured_count"] = len(merged["captured"])
    return merged


def _validate_as_of_date(value: str) -> None:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise MacroCalendarCaptureError("as_of_date must use YYYY-MM-DD") from exc


def _load_source_plan(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise MacroCalendarCaptureError(f"{path} must contain a JSON object")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Capture official macro calendar source snapshots for later offline import.")
    parser.add_argument("--as-of-date", required=True, help="Archive date in YYYY-MM-DD format.")
    parser.add_argument("--source-plan-path", type=Path, default=DEFAULT_SOURCE_PLAN_PATH)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--source-id", action="append", dest="source_ids", help="Capture only this source_id. Can be repeated.")
    parser.add_argument("--execute", action="store_true", help="Fetch live official source pages. Omit for dry-run request plan.")
    args = parser.parse_args(argv)

    result = capture_snapshots(
        as_of_date=args.as_of_date,
        source_plan_path=args.source_plan_path,
        output_root=args.output_root,
        execute=args.execute,
        source_ids=args.source_ids,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
