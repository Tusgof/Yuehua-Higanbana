from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DECISION_PATH = PROJECT_ROOT / "experiments" / "h_a2_normal_control_paid_download_decision.json"
DEFAULT_ESTIMATE_PATH = (
    PROJECT_ROOT / "reports" / "data_cost" / "h_a2_normal_control_low_normal_vix_control_pack_cost_estimate.json"
)
DEFAULT_RAW_ROOT = (
    PROJECT_ROOT / "data" / "raw" / "spy_0dte" / "databento" / "h_a2_normal_control_low_normal_vix_control_pack"
)
DEFAULT_JSON_REPORT = (
    PROJECT_ROOT
    / "reports"
    / "data_cost"
    / "databento_download_result_h_a2_normal_control_low_normal_vix_control_pack.json"
)
DEFAULT_MD_REPORT = (
    PROJECT_ROOT
    / "reports"
    / "data_cost"
    / "databento_download_result_h_a2_normal_control_low_normal_vix_control_pack.md"
)
DEFAULT_API_KEY_ENV = "DATABENTO_API_MO"


def build_download_plan(
    decision_path: Path = DEFAULT_DECISION_PATH,
    estimate_path: Path = DEFAULT_ESTIMATE_PATH,
    raw_root: Path = DEFAULT_RAW_ROOT,
) -> dict[str, Any]:
    decision = _load_json(decision_path)
    estimate = _load_json(estimate_path)
    batch_id = (decision.get("selected_batch") or {}).get("batch_id")
    scenario = "h_a2_normal_control_low_normal_vix_control_pack"
    if batch_id and batch_id != "low_normal_vix_control_pack":
        scenario = f"h_a2_{batch_id}"
    cost_result = estimate.get("cost_result") or {}
    requests = []
    for item in cost_result.get("requests", []):
        window = item["window"]
        requests.append({**item, "raw_path": str(raw_root / f"{window}.dbn.zst")})
    return {
        "mode": "download_plan",
        "hypothesis_id": "H-A2",
        "scenario": scenario,
        "source_decision": _relative(decision_path),
        "source_cost_report": _relative(estimate_path),
        "download_decision": decision.get("decision"),
        "selected_batch": decision.get("selected_batch"),
        "locked_signal_under_validation": decision.get("locked_signal_under_validation"),
        "cost_guard": decision.get("cost_guard"),
        "approved_download_scope": decision.get("approved_download_scope"),
        "planned_required_request_count": (decision.get("approved_download_scope") or {}).get(
            "planned_required_request_count"
        ),
        "metadata_grouped_request_count": (decision.get("approved_download_scope") or {}).get(
            "metadata_grouped_request_count"
        ),
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
    schema_version = "h_a2_normal_control_download_result_v1"
    if plan.get("scenario") == "h_a2_post_stress_normalization_control_pack":
        schema_version = "h_a2_post_stress_normalization_control_download_result_v1"
    return {
        "schema_version": schema_version,
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
        "approved_download_scope": plan.get("approved_download_scope"),
        "total_estimated_cost_usd": plan.get("total_estimated_cost_usd"),
        "cost_guard": plan.get("cost_guard"),
        "paid_cost_audit_before_download": {
            "status": paid_cost_audit.get("status"),
            "cost_guard_basis": paid_cost_audit.get("cost_guard_basis"),
            "cost_guard_used_usd": paid_cost_audit.get("cost_guard_used_usd"),
            "remaining_before_stop_usd": paid_cost_audit.get("remaining_before_stop_usd"),
        },
        "planned_required_request_count": plan.get("planned_required_request_count"),
        "metadata_grouped_request_count": plan.get("metadata_grouped_request_count"),
        "request_count": plan.get("request_count"),
        "requests": plan.get("requests"),
        "execution": execution,
        "blockers": blockers,
        "allowed_claims": [
            "H-A2 raw data was downloaded or cache-confirmed for the approved dates only.",
            "The download preserves the locked 09:35-only H-A2 signal and threshold 0.001.",
            "The download is data acquisition only and does not validate H-A2 edge.",
        ],
        "forbidden_claims": [
            "Do not claim H-A2 edge is validated.",
            "Do not claim E2 acceptance-grade evidence.",
            "Do not approve paper trading.",
            "Do not run exact replay directly from this download result.",
            "Do not change threshold 0.001 or add an OOS-selected filter.",
        ],
    }


def render_markdown(result: dict[str, Any]) -> str:
    audit = result["paid_cost_audit_before_download"]
    execution = result.get("execution") or {}
    lines = [
        "# H-A2 Databento Download Result",
        "",
        f"- **Status**: `{result['status']}`",
        f"- **Mode**: `{result['mode']}`",
        f"- **Hypothesis**: `{result.get('hypothesis_id')}`",
        f"- **Scenario**: `{result.get('scenario')}`",
        f"- **Download performed**: `{result.get('download_performed')}`",
        f"- **Grouped request count**: {result.get('request_count')}",
        f"- **Planned required windows**: {result.get('planned_required_request_count')}",
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
            "This is controlled normal/control data acquisition only. It is not an H-A2 edge-validation result, not exact replay, and not paper-trading approval.",
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
    batch_id = (plan.get("selected_batch") or {}).get("batch_id")
    expected_scenario = "h_a2_normal_control_low_normal_vix_control_pack"
    if batch_id and batch_id != "low_normal_vix_control_pack":
        expected_scenario = f"h_a2_{batch_id}"
    expected_decision = f"approve_{batch_id}_download_after_paid_cost_audit_pass"
    expected_cost = (plan.get("cost_guard") or {}).get("estimated_download_cost_usd")
    expected_key_env = (plan.get("cost_guard") or {}).get("selected_key_env")

    if not batch_id:
        blockers.append("selected_batch_id_required")
    if plan.get("download_decision") != expected_decision:
        blockers.append("download_decision_not_approved")
    if plan.get("scenario") != expected_scenario:
        blockers.append("scenario_must_match_selected_batch")
    if plan.get("planned_required_request_count") != 150:
        blockers.append("planned_required_request_count_must_be_150")
    if plan.get("metadata_grouped_request_count") != 20 or plan.get("request_count") != 20:
        blockers.append("grouped_request_count_must_be_20")
    if _round6(plan.get("total_estimated_cost_usd")) != _round6(expected_cost):
        blockers.append("estimated_cost_mismatch")
    if paid_cost_audit.get("status") != "pass":
        blockers.append("paid_cost_audit_not_pass")

    guard = plan.get("cost_guard") or {}
    if guard.get("basis") != "selected_key_mo_ai_pool":
        blockers.append("cost_guard_basis_must_be_selected_key_mo_ai_pool")
    scope = plan.get("approved_download_scope") or {}
    if not expected_key_env or scope.get("selected_key_env") != expected_key_env:
        blockers.append("selected_key_env_must_match_cost_guard")
    if float(guard.get("projected_selected_key_usage_if_downloaded_usd", 999999)) >= float(
        guard.get("selected_key_cap_usd", 0)
    ):
        blockers.append("projected_selected_key_usage_must_remain_below_cap")
    if float(guard.get("projected_mo_ai_pool_usage_if_downloaded_usd", 999999)) >= float(
        guard.get("mo_ai_combined_pool_cap_usd", 0)
    ):
        blockers.append("projected_mo_ai_pool_usage_must_remain_below_cap")

    allowed_dates = set((plan.get("selected_batch") or {}).get("dates") or [])
    request_dates = {row.get("date") for row in plan.get("requests", [])}
    if request_dates != allowed_dates or len(allowed_dates) != 10:
        blockers.append("request_dates_must_match_approved_dates")
    return blockers


def _databento_downloader(api_key_env: str) -> Callable[[dict[str, Any]], dict[str, Any]]:
    api_key = os.environ.get(api_key_env)
    if not api_key:
        raise RuntimeError(f"missing Databento API key environment variable: {api_key_env}")
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
        return {**request, "source": source, "bytes": raw_path.stat().st_size, "sha256": _sha256(raw_path)}

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
    parser = argparse.ArgumentParser(description="Download H-A2 normal/control Databento data after decision gates pass.")
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
