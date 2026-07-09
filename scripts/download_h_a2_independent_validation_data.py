from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DECISION_PATH = PROJECT_ROOT / "experiments" / "h_a2_independent_validation_paid_download_decision.json"
DEFAULT_ESTIMATE_PATH = PROJECT_ROOT / "reports" / "data_cost" / "h_a2_independent_validation_paid_cost_estimate.json"
DEFAULT_RAW_ROOT = PROJECT_ROOT / "data" / "raw" / "spy_0dte" / "databento" / "h_a2_independent_validation_2025_04_08"
DEFAULT_JSON_REPORT = PROJECT_ROOT / "reports" / "data_cost" / "databento_download_result_h_a2_independent_validation_2025_04_08.json"
DEFAULT_MD_REPORT = PROJECT_ROOT / "reports" / "data_cost" / "databento_download_result_h_a2_independent_validation_2025_04_08.md"
DEFAULT_API_KEY_ENV = "DATABENTO_API_KEY"
DATABENTO_API_KEY_ENV_ALIASES = ("DATABENTO_SPY0DTE_API", "DATABENTO_API_MO", "DATABENTO_API_AI")


def build_download_plan(
    decision_path: Path = DEFAULT_DECISION_PATH,
    estimate_path: Path = DEFAULT_ESTIMATE_PATH,
    raw_root: Path = DEFAULT_RAW_ROOT,
) -> dict[str, Any]:
    decision = _load_json(decision_path)
    estimate = _load_json(estimate_path)
    cost_result = estimate.get("cost_result") or {}
    requests = []
    for item in cost_result.get("requests", []):
        window = item["window"]
        requests.append(
            {
                **item,
                "raw_path": str(raw_root / f"{window}.dbn.zst"),
            }
        )
    return {
        "mode": "download_plan",
        "hypothesis_id": "H-A2",
        "scenario": "h_a2_independent_validation_2025_04_08",
        "source_decision": _relative(decision_path),
        "source_cost_report": _relative(estimate_path),
        "download_decision": decision.get("decision"),
        "selected_batch": decision.get("selected_batch"),
        "locked_signal_under_validation": decision.get("locked_signal_under_validation"),
        "cost_guard": decision.get("cost_guard"),
        "total_estimated_cost_usd": cost_result.get("total_estimated_cost_usd"),
        "request_count": len(requests),
        "requests": requests,
    }


def execute_downloads(
    plan: dict[str, Any],
    api_key_env: str = DEFAULT_API_KEY_ENV,
    downloader: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    download_one = downloader or _databento_downloader(api_key_env)
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for request in plan["requests"]:
        try:
            rows.append(download_one(request))
        except Exception as exc:
            rows.append({**request, "source": "error", "error": str(exc)})
            errors.append({"window": request.get("window", ""), "error": str(exc)})
    return {
        "downloads": rows,
        "errors": errors,
        "downloaded_count": sum(1 for row in rows if row.get("source") == "downloaded"),
        "cache_count": sum(1 for row in rows if row.get("source") == "cache"),
        "total_bytes": sum(int(row.get("bytes", 0) or 0) for row in rows),
    }


def build_result(plan: dict[str, Any], paid_cost_audit: dict[str, Any], execution: dict[str, Any] | None) -> dict[str, Any]:
    blockers = _preflight_blockers(plan, paid_cost_audit)
    if execution is None:
        blockers.append("requires_execute")
    elif execution.get("errors"):
        blockers.append("download_errors_present")
    elif any(int(row.get("bytes", 0) or 0) <= 0 for row in execution.get("downloads", [])):
        blockers.append("empty_download_file_present")

    status = "pass" if not blockers else "blocked"
    return {
        "schema_version": "h_a2_independent_validation_download_result_v1",
        "mode": "download_complete" if execution is not None and status == "pass" else "download_plan",
        "status": status,
        "hypothesis_id": plan.get("hypothesis_id"),
        "scenario": plan.get("scenario"),
        "download_performed": execution is not None,
        "source_decision": plan.get("source_decision"),
        "source_cost_report": plan.get("source_cost_report"),
        "download_decision": plan.get("download_decision"),
        "selected_batch": plan.get("selected_batch"),
        "locked_signal_under_validation": plan.get("locked_signal_under_validation"),
        "total_estimated_cost_usd": plan.get("total_estimated_cost_usd"),
        "cost_guard": plan.get("cost_guard"),
        "paid_cost_audit_before_download": {
            "status": paid_cost_audit.get("status"),
            "cost_guard_basis": paid_cost_audit.get("cost_guard_basis"),
            "cost_guard_used_usd": paid_cost_audit.get("cost_guard_used_usd"),
            "remaining_before_stop_usd": paid_cost_audit.get("remaining_before_stop_usd"),
        },
        "request_count": plan.get("request_count"),
        "requests": plan.get("requests"),
        "execution": execution,
        "blockers": blockers,
        "allowed_claims": [
            "One-day H-A2 independent-validation raw data was downloaded or cache-confirmed.",
            "The download preserves the locked 09:35-only H-A2 signal and threshold 0.001.",
            "The download is data acquisition only and does not validate H-A2 edge."
        ],
        "forbidden_claims": [
            "Do not claim H-A2 edge is validated.",
            "Do not claim E2 acceptance-grade evidence.",
            "Do not approve paper trading.",
            "Do not run exact replay directly from this download result.",
            "Do not change threshold 0.001 or add an OOS-selected filter."
        ],
    }


def render_markdown(result: dict[str, Any]) -> str:
    audit = result["paid_cost_audit_before_download"]
    execution = result.get("execution") or {}
    lines = [
        "# H-A2 Independent Validation Download Result",
        "",
        f"- **Status**: `{result['status']}`",
        f"- **Mode**: `{result['mode']}`",
        f"- **Hypothesis**: `{result.get('hypothesis_id')}`",
        f"- **Scenario**: `{result.get('scenario')}`",
        f"- **Download performed**: `{result.get('download_performed')}`",
        f"- **Request count**: {result.get('request_count')}",
        f"- **Estimated committed cost**: `${result.get('total_estimated_cost_usd')}`",
        f"- **Audit before download**: `{audit.get('status')}`, used `${audit.get('cost_guard_used_usd')}`, remaining `${audit.get('remaining_before_stop_usd')}`",
        f"- **Downloaded files**: {execution.get('downloaded_count', 0)}",
        f"- **Cache files**: {execution.get('cache_count', 0)}",
        f"- **Total bytes**: {execution.get('total_bytes', 0)}",
        "",
        "## Files",
        "",
        "| Window | Source | Bytes | SHA-256 | Path |",
        "|:--|:--|--:|:--|:--|",
    ]
    for row in execution.get("downloads", []):
        lines.append(
            f"| `{row.get('window')}` | `{row.get('source')}` | {row.get('bytes', 0)} | `{row.get('sha256', '')}` | `{row.get('raw_path', '')}` |"
        )
    if result["blockers"]:
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- `{blocker}`" for blocker in result["blockers"])
    lines.extend(
        [
            "",
            "## Guardrail",
            "",
            "This is a controlled one-day data acquisition record only. It is not an H-A2 edge-validation result, not exact replay, and not paper-trading approval.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_outputs(result: dict[str, Any], json_report: Path, md_report: Path) -> None:
    json_report.parent.mkdir(parents=True, exist_ok=True)
    json_report.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_report.parent.mkdir(parents=True, exist_ok=True)
    md_report.write_text(render_markdown(result), encoding="utf-8")


def _preflight_blockers(plan: dict[str, Any], paid_cost_audit: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if plan.get("download_decision") != "approve_sample_cost_probe_high_vix_one_day_download_after_paid_cost_audit_pass":
        blockers.append("download_decision_not_approved")
    if plan.get("scenario") != "h_a2_independent_validation_2025_04_08":
        blockers.append("scenario_must_be_h_a2_independent_validation_2025_04_08")
    if plan.get("request_count") != 15:
        blockers.append("request_count_must_be_15")
    if _round6(plan.get("total_estimated_cost_usd")) != 0.504662:
        blockers.append("estimated_cost_mismatch")
    if paid_cost_audit.get("status") != "pass":
        blockers.append("paid_cost_audit_not_pass")
    estimate = plan.get("total_estimated_cost_usd")
    remaining = paid_cost_audit.get("remaining_before_stop_usd")
    if isinstance(estimate, int | float) and isinstance(remaining, int | float) and estimate > remaining:
        blockers.append("estimated_cost_exceeds_remaining_headroom")
    guard = plan.get("cost_guard") or {}
    if float(guard.get("projected_used_after_download_usd", 999999)) >= float(guard.get("stop_threshold_usd", 0)):
        blockers.append("projected_usage_must_remain_below_stop_threshold")
    return blockers


def _databento_downloader(api_key_env: str) -> Callable[[dict[str, Any]], dict[str, Any]]:
    api_key = _databento_api_key_from_env(api_key_env)
    if not api_key:
        raise RuntimeError(f"missing Databento API key environment variable: {_databento_env_names(api_key_env)}")
    try:
        import databento as db  # type: ignore
    except ImportError as exc:
        raise RuntimeError("missing Python package: databento") from exc

    client = db.Historical(api_key)

    def download_one(request: dict[str, Any]) -> dict[str, Any]:
        raw_path = Path(request["raw_path"])
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        source = "cache"
        if raw_path.exists() and raw_path.stat().st_size == 0:
            raw_path.unlink()
        if not raw_path.exists():
            temp_path = raw_path.with_name(f"{raw_path.name}.download")
            if temp_path.exists():
                temp_path.unlink()
            client.timeseries.get_range(
                dataset=request["dataset"],
                symbols=request["symbols"],
                schema=request["schema"],
                stype_in=request["stype_in"],
                start=request["start"],
                end=request["end"],
                path=temp_path,
            )
            temp_path.replace(raw_path)
            source = "downloaded"
        return {
            **request,
            "source": source,
            "bytes": raw_path.stat().st_size,
            "sha256": _sha256(raw_path),
        }

    return download_one


def _load_paid_cost_audit() -> dict[str, Any]:
    import importlib.util

    script_path = PROJECT_ROOT / "scripts" / "audit_paid_costs.py"
    spec = importlib.util.spec_from_file_location("audit_paid_costs", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load paid cost auditor")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.audit_paid_costs()


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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _round6(value: Any) -> float | None:
    if value is None:
        return None
    return round(float(value), 6)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Download one-day H-A2 independent-validation Databento data after decision gates pass.")
    parser.add_argument("--decision-path", type=Path, default=DEFAULT_DECISION_PATH)
    parser.add_argument("--estimate-path", type=Path, default=DEFAULT_ESTIMATE_PATH)
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    parser.add_argument("--json-report", type=Path, default=DEFAULT_JSON_REPORT)
    parser.add_argument("--md-report", type=Path, default=DEFAULT_MD_REPORT)
    parser.add_argument("--api-key-env", default=DEFAULT_API_KEY_ENV)
    parser.add_argument("--execute", action="store_true", help="Download missing raw files. Default writes a blocked plan only.")
    args = parser.parse_args(argv)

    plan = build_download_plan(args.decision_path, args.estimate_path, args.raw_root)
    audit = _load_paid_cost_audit()
    execution = execute_downloads(plan, args.api_key_env) if args.execute else None
    result = build_result(plan, audit, execution)
    write_outputs(result, args.json_report, args.md_report)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" or not args.execute else 1


if __name__ == "__main__":
    raise SystemExit(main())
