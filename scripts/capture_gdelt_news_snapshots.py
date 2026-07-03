from __future__ import annotations

import argparse
import csv
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_PLAN_PATH = PROJECT_ROOT / "tests" / "fixtures" / "news_sources_v1.json"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "spy_0dte" / "news" / "gdelt_snapshot.csv"
DEFAULT_STATUS_OUTPUT_PATH = PROJECT_ROOT / "reports" / "news_gdelt_capture_status.json"

TOPIC_QUERIES = {
    "market_panic": "market panic OR selloff OR risk-off OR liquidity",
    "systemic_banking_stress": "banking crisis OR funding stress OR bank run OR emergency lending",
    "war_escalation": "war escalation OR missile strike OR invasion OR geopolitical risk",
    "index_halt_circuit_breaker": "circuit breaker OR limit down OR trading halt OR futures halt",
    "macro_policy_risk": "Federal Reserve OR Powell OR inflation data OR jobs report OR Treasury yields",
}


class GdeltCaptureError(ValueError):
    pass


def build_capture_plan(
    decision_time_et: str,
    lookback_hours: int,
    source_plan_path: Path = DEFAULT_SOURCE_PLAN_PATH,
    max_records: int = 25,
) -> dict[str, Any]:
    source_plan = _load_source_plan(source_plan_path)
    source = _primary_source(source_plan)
    decision_time = _parse_timestamp(decision_time_et)
    end_utc = decision_time.astimezone(timezone.utc)
    start_utc = end_utc - timedelta(hours=lookback_hours)
    topics = source_plan["minimum_required_topics"]
    requests = [
        {
            "source_id": source["source_id"],
            "provider": source["provider"],
            "topic": topic,
            "query": TOPIC_QUERIES[topic],
            "decision_time_et": decision_time.isoformat(timespec="seconds"),
            "start_utc": _gdelt_datetime(start_utc),
            "end_utc": _gdelt_datetime(end_utc),
            "url": _build_url(source["api_url_template"], TOPIC_QUERIES[topic], start_utc, end_utc, max_records),
        }
        for topic in topics
    ]
    return {
        "mode": "dry_run",
        "decision_time_et": decision_time.isoformat(timespec="seconds"),
        "lookback_hours": lookback_hours,
        "source_plan": str(source_plan_path),
        "requests": requests,
    }


def capture_snapshot(
    decision_time_et: str,
    output_path: Path = DEFAULT_OUTPUT_PATH,
    source_plan_path: Path = DEFAULT_SOURCE_PLAN_PATH,
    lookback_hours: int = 24,
    max_records: int = 25,
    execute: bool = False,
) -> dict[str, Any]:
    plan = build_capture_plan(decision_time_et, lookback_hours, source_plan_path, max_records)
    if not execute:
        return plan

    rows: list[dict[str, str]] = []
    for request in plan["requests"]:
        payload = _fetch_json(request["url"])
        rows.extend(parse_artlist_response(payload, request))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    _write_rows(output_path, rows)
    return {
        "mode": "execute",
        "output_path": str(output_path),
        "row_count": len(rows),
        "decision_time_et": plan["decision_time_et"],
        "topics": sorted({row["topic"] for row in rows}),
    }


def parse_artlist_response(payload: dict[str, Any], request: dict[str, str]) -> list[dict[str, str]]:
    articles = payload.get("articles")
    if not isinstance(articles, list):
        raise GdeltCaptureError("GDELT response missing articles array")
    rows: list[dict[str, str]] = []
    seen_urls: set[str] = set()
    for article in articles:
        if not isinstance(article, dict):
            continue
        url = str(article.get("url", "")).strip()
        title = str(article.get("title", "")).strip()
        seendate = str(article.get("seendate", "")).strip()
        if not url.startswith("https://") or not title or not seendate:
            continue
        if url in seen_urls:
            continue
        seen_urls.add(url)
        timestamp = _parse_gdelt_seendate(seendate)
        rows.append(
            {
                "source_id": request["source_id"],
                "topic": request["topic"],
                "decision_time_et": request["decision_time_et"],
                "fetched_at_utc": timestamp,
                "published_at_utc": timestamp,
                "source_name": str(article.get("domain") or article.get("sourceCountry") or request["provider"]),
                "headline": title,
                "url": url,
            }
        )
    return rows


def _fetch_json(url: str) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            raise GdeltCaptureError("GDELT returned 429 Too Many Requests; retry later and keep using cached/offline snapshots") from exc
        raise GdeltCaptureError(f"GDELT request failed with HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise GdeltCaptureError(f"GDELT request failed: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise GdeltCaptureError("GDELT returned a non-JSON response") from exc
    if not isinstance(payload, dict):
        raise GdeltCaptureError("GDELT returned a non-object JSON response")
    return payload


def _primary_source(source_plan: dict[str, Any]) -> dict[str, Any]:
    primary_id = source_plan["primary_source_id"]
    for source in source_plan["sources"]:
        if source["source_id"] == primary_id:
            return source
    raise GdeltCaptureError(f"primary source {primary_id!r} not found")


def _build_url(template: str, query: str, start_utc: datetime, end_utc: datetime, max_records: int) -> str:
    base = template.format(
        query=urllib.parse.quote(query),
        start_utc=_gdelt_datetime(start_utc),
        end_utc=_gdelt_datetime(end_utc),
    )
    separator = "&" if "?" in base else "?"
    return f"{base}{separator}maxrecords={max_records}"


def _parse_timestamp(value: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise GdeltCaptureError("decision_time_et must include timezone")
    return parsed


def _parse_gdelt_seendate(value: str) -> str:
    try:
        parsed = datetime.strptime(value, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise GdeltCaptureError(f"invalid GDELT seendate {value!r}") from exc
    return parsed.isoformat(timespec="seconds").replace("+00:00", "Z")


def _gdelt_datetime(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y%m%d%H%M%S")


def _load_source_plan(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_rows(output_path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "source_id",
        "topic",
        "decision_time_et",
        "fetched_at_utc",
        "published_at_utc",
        "source_name",
        "headline",
        "url",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_status(path: Path, result: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Capture GDELT DOC API news snapshots for later offline import.")
    parser.add_argument("--decision-time-et", required=True, help="Decision timestamp with ET offset, e.g. 2024-01-03T09:30:00-05:00")
    parser.add_argument("--lookback-hours", type=int, default=24)
    parser.add_argument("--max-records", type=int, default=25)
    parser.add_argument("--source-plan-path", type=Path, default=DEFAULT_SOURCE_PLAN_PATH)
    parser.add_argument("--output-path", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--status-output-path", type=Path, default=DEFAULT_STATUS_OUTPUT_PATH)
    parser.add_argument("--execute", action="store_true", help="Fetch live GDELT data. Omit for dry-run request plan.")
    args = parser.parse_args(argv)

    try:
        result = capture_snapshot(
            decision_time_et=args.decision_time_et,
            output_path=args.output_path,
            source_plan_path=args.source_plan_path,
            lookback_hours=args.lookback_hours,
            max_records=args.max_records,
            execute=args.execute,
        )
        result["status"] = "captured" if args.execute else "planned"
    except GdeltCaptureError as exc:
        result = {
            "mode": "execute" if args.execute else "dry_run",
            "status": "blocked",
            "blockers": ["gdelt_capture_unavailable"],
            "error": str(exc),
            "decision_time_et": args.decision_time_et,
            "lookback_hours": args.lookback_hours,
            "max_records": args.max_records,
            "output_path": str(args.output_path),
            "source_plan_path": str(args.source_plan_path),
        }
        _write_status(args.status_output_path, result)
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), file=sys.stderr)
        return 2

    if args.execute:
        _write_status(args.status_output_path, result)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
