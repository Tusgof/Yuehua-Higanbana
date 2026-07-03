from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COST_REPORT = PROJECT_ROOT / "reports" / "data_cost" / "h_g1_gamma_oi_12_date_cost_estimate.json"
DEFAULT_RAW_ROOT = PROJECT_ROOT / "data" / "raw" / "spy_0dte" / "databento" / "h_g1_gamma_oi_12_date"
DEFAULT_JSON_REPORT = PROJECT_ROOT / "reports" / "data_cost" / "h_g1_gamma_oi_download_result.json"
DEFAULT_MD_REPORT = PROJECT_ROOT / "reports" / "data_cost" / "h_g1_gamma_oi_download_result.md"
DEFAULT_API_KEY_ENV = "DATABENTO_API_KEY"
DATABENTO_API_KEY_ENV_ALIASES = ("DATABENTO_SPY0DTE_API",)


def build_download_plan(cost_report_path: Path = DEFAULT_COST_REPORT, raw_root: Path = DEFAULT_RAW_ROOT) -> dict[str, Any]:
    cost_report = json.loads(cost_report_path.read_text(encoding="utf-8"))
    cost_result = cost_report.get("cost_result") or {}
    requests = []
    for item in cost_result.get("requests", []):
        date = item["date"]
        requests.append(
            {
                **item,
                "raw_path": str(raw_root / f"{date}_full_utc_day_statistics.dbn.zst"),
            }
        )
    return {
        "mode": "download_plan",
        "hypothesis_id": cost_report.get("hypothesis_id"),
        "source_cost_report": _relative(cost_report_path),
        "cost_gate_decision": cost_report.get("decision"),
        "cost_guard": cost_report.get("cost_guard"),
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
            errors.append({"date": request.get("date", ""), "error": str(exc)})
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
        "schema_version": "h_g1_gamma_oi_download_result_v1",
        "mode": "download_complete" if execution is not None and status == "pass" else "download_plan",
        "status": status,
        "hypothesis_id": plan.get("hypothesis_id"),
        "scenario": "h_g1_gamma_oi_12_date",
        "download_performed": execution is not None,
        "source_cost_report": plan.get("source_cost_report"),
        "total_estimated_cost_usd": plan.get("total_estimated_cost_usd"),
        "cost_gate_decision": plan.get("cost_gate_decision"),
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
    }


def render_markdown(result: dict[str, Any]) -> str:
    audit = result["paid_cost_audit_before_download"]
    execution = result.get("execution") or {}
    lines = [
        "# H-G1 Gamma/OI Download Result",
        "",
        f"- **Status**: `{result['status']}`",
        f"- **Mode**: `{result['mode']}`",
        f"- **Hypothesis**: `{result.get('hypothesis_id')}`",
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
        "| Date | Source | Bytes | SHA-256 | Path |",
        "|:--|:--|--:|:--|:--|",
    ]
    for row in execution.get("downloads", []):
        lines.append(
            f"| `{row.get('date')}` | `{row.get('source')}` | {row.get('bytes', 0)} | `{row.get('sha256', '')}` | `{row.get('raw_path', '')}` |"
        )
    if result["blockers"]:
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- `{blocker}`" for blocker in result["blockers"])
    lines.extend(
        [
            "",
            "## Guardrail",
            "",
            "This is a controlled OPRA statistics/OI data acquisition record only. It is not a gamma proxy validation pass.",
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
    decision = plan.get("cost_gate_decision") or {}
    if decision.get("status") != "pass" or decision.get("download_allowed_under_current_guard") is not True:
        blockers.append("cost_gate_not_pass")
    if paid_cost_audit.get("status") != "pass":
        blockers.append("paid_cost_audit_not_pass")
    estimate = plan.get("total_estimated_cost_usd")
    remaining = paid_cost_audit.get("remaining_before_stop_usd")
    if isinstance(estimate, int | float) and isinstance(remaining, int | float) and estimate > remaining:
        blockers.append("estimated_cost_exceeds_remaining_headroom")
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


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Download H-G1 OPRA statistics/OI files only after the cost gate passes.")
    parser.add_argument("--cost-report", type=Path, default=DEFAULT_COST_REPORT)
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    parser.add_argument("--json-report", type=Path, default=DEFAULT_JSON_REPORT)
    parser.add_argument("--md-report", type=Path, default=DEFAULT_MD_REPORT)
    parser.add_argument("--api-key-env", default=DEFAULT_API_KEY_ENV)
    parser.add_argument("--execute", action="store_true", help="Download missing raw files. Default writes a blocked plan only.")
    args = parser.parse_args(argv)

    plan = build_download_plan(args.cost_report, args.raw_root)
    audit = _load_paid_cost_audit()
    execution = execute_downloads(plan, args.api_key_env) if args.execute else None
    result = build_result(plan, audit, execution)
    write_outputs(result, args.json_report, args.md_report)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" or not args.execute else 1


if __name__ == "__main__":
    raise SystemExit(main())
