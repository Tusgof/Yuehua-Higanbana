from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COST_REPORT = PROJECT_ROOT / "reports" / "data_cost" / "databento_cost_plan.json"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "data" / "raw" / "spy_0dte" / "databento"
DEFAULT_PLAN_PATH = PROJECT_ROOT / "reports" / "data_cost" / "databento_download_plan.json"
DEFAULT_API_KEY_ENV = "DATABENTO_API_KEY"
DATABENTO_API_KEY_ENV_ALIASES = ("DATABENTO_SPY0DTE_API", "DATABENTO_API_MO", "DATABENTO_API_AI")


def build_download_plan(
    cost_report_path: Path = DEFAULT_COST_REPORT,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    max_download_requests: int = 100,
    allow_review_decision: bool = False,
    approval_note: str | None = None,
) -> dict[str, Any]:
    report = json.loads(cost_report_path.read_text(encoding="utf-8"))
    validate_cost_report_for_download(
        report,
        max_download_requests=max_download_requests,
        allow_review_decision=allow_review_decision,
    )

    scenario = _single_scenario(report)
    output_dir = output_root / scenario
    items: list[dict[str, Any]] = []
    for request in report["requests"]:
        if request.get("estimated_cost_usd") is None:
            continue
        filename = f"{request['window']}.dbn.zst"
        items.append(
            {
                "dataset": request["dataset"],
                "symbols": request["symbols"],
                "schema": request["schema"],
                "stype_in": request["stype_in"],
                "start": request["start"],
                "end": request["end"],
                "window": request["window"],
                "estimated_cost_usd": request["estimated_cost_usd"],
                "output_path": str(output_dir / filename),
            }
        )

    return {
        "mode": "download_plan",
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_cost_report": str(cost_report_path),
        "scenario": scenario,
        "decision": report["decision"],
        "approval_note": approval_note if allow_review_decision else None,
        "total_estimated_cost_usd": report["total_estimated_cost_usd"],
        "request_count": len(items),
        "items": items,
    }


def validate_cost_report_for_download(
    report: dict[str, Any],
    max_download_requests: int = 100,
    allow_review_decision: bool = False,
) -> None:
    decision = report.get("decision", {})
    allowed_statuses = {"pass", "review"} if allow_review_decision else {"pass"}
    if decision.get("status") not in allowed_statuses:
        raise ValueError(f"cost report decision must be pass, got {decision.get('status')!r}")
    if decision.get("status") == "review" and not allow_review_decision:
        raise ValueError("review decision requires explicit approval")
    if report.get("errors"):
        raise ValueError("cost report contains errors; review coverage before download")
    request_count = len([row for row in report.get("requests", []) if row.get("estimated_cost_usd") is not None])
    if request_count > max_download_requests:
        raise ValueError(
            f"refusing {request_count} download requests; increase --max-download-requests above {max_download_requests} if approved"
        )


def execute_download_plan(
    plan: dict[str, Any],
    api_key_env: str = DEFAULT_API_KEY_ENV,
    per_request_retries: int = 0,
    retry_sleep_seconds: float = 10.0,
) -> dict[str, Any]:
    api_key = _databento_api_key_from_env(api_key_env)
    if not api_key:
        raise RuntimeError(f"missing Databento API key environment variable: {_databento_env_names(api_key_env)}")
    import databento as db  # type: ignore

    client = db.Historical(api_key)
    downloaded: list[dict[str, Any]] = []
    for item in plan["items"]:
        output_path = Path(item["output_path"])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        source = "cache"
        if output_path.exists() and output_path.stat().st_size == 0:
            output_path.unlink()
        if not output_path.exists():
            temp_path = output_path.with_name(f"{output_path.name}.download")
            _download_with_retries(client, item, temp_path, per_request_retries, retry_sleep_seconds)
            temp_path.replace(output_path)
            source = "downloaded"
        downloaded.append(
            {
                "window": item["window"],
                "output_path": str(output_path),
                "source": source,
                "sha256": _sha256(output_path),
                "bytes": output_path.stat().st_size,
            }
        )
    result = dict(plan)
    result["mode"] = "download_complete"
    result["downloaded"] = downloaded
    return result


def _databento_api_key_from_env(api_key_env: str = DEFAULT_API_KEY_ENV) -> str | None:
    api_key = os.environ.get(api_key_env)
    if api_key or api_key_env != DEFAULT_API_KEY_ENV:
        return api_key
    for alias in DATABENTO_API_KEY_ENV_ALIASES:
        api_key = os.environ.get(alias)
        if api_key:
            return api_key
    return None


def _databento_env_names(api_key_env: str = DEFAULT_API_KEY_ENV) -> str:
    if api_key_env != DEFAULT_API_KEY_ENV:
        return api_key_env
    return " or ".join((DEFAULT_API_KEY_ENV, *DATABENTO_API_KEY_ENV_ALIASES))


def write_plan(plan: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _download_range(client: Any, item: dict[str, Any], temp_path: Path) -> None:
    client.timeseries.get_range(
        dataset=item["dataset"],
        symbols=item["symbols"],
        schema=item["schema"],
        stype_in=item["stype_in"],
        start=item["start"],
        end=item["end"],
        path=temp_path,
    )


def _download_with_retries(
    client: Any,
    item: dict[str, Any],
    temp_path: Path,
    per_request_retries: int,
    retry_sleep_seconds: float,
) -> None:
    attempts = max(0, per_request_retries) + 1
    for attempt in range(attempts):
        if temp_path.exists():
            temp_path.unlink()
        try:
            _download_range(client, item, temp_path)
            return
        except FileExistsError:
            if temp_path.exists():
                temp_path.unlink()
            _download_range(client, item, temp_path)
            return
        except Exception:
            if temp_path.exists():
                temp_path.unlink()
            if attempt + 1 >= attempts:
                raise
            if retry_sleep_seconds > 0:
                time.sleep(retry_sleep_seconds)


def _single_scenario(report: dict[str, Any]) -> str:
    scenarios = report.get("summary", {}).get("scenarios", {})
    if len(scenarios) != 1:
        raise ValueError("download requires a cost report with exactly one scenario")
    return next(iter(scenarios))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan or execute a gated Databento data download.")
    parser.add_argument("--cost-report", type=Path, default=DEFAULT_COST_REPORT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--plan-path", type=Path, default=DEFAULT_PLAN_PATH)
    parser.add_argument("--api-key-env", default=DEFAULT_API_KEY_ENV)
    parser.add_argument("--max-download-requests", default=100, type=int)
    parser.add_argument("--allow-review-decision", action="store_true")
    parser.add_argument("--approval-note")
    parser.add_argument("--per-request-retries", type=int, default=0)
    parser.add_argument("--retry-sleep-seconds", type=float, default=10.0)
    parser.add_argument("--execute", action="store_true", help="Actually download data. Default only writes a plan.")
    args = parser.parse_args()

    plan = build_download_plan(
        args.cost_report,
        args.output_root,
        args.max_download_requests,
        allow_review_decision=args.allow_review_decision,
        approval_note=args.approval_note,
    )
    result = (
        execute_download_plan(
            plan,
            args.api_key_env,
            per_request_retries=args.per_request_retries,
            retry_sleep_seconds=args.retry_sleep_seconds,
        )
        if args.execute
        else plan
    )
    write_plan(result, args.plan_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
