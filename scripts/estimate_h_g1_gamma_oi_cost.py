from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_PATH = PROJECT_ROOT / "experiments" / "h_g1_gamma_regime_date_set_preregistration.json"
DEFAULT_JSON_REPORT = PROJECT_ROOT / "reports" / "data_cost" / "h_g1_gamma_oi_12_date_cost_estimate.json"
DEFAULT_MD_REPORT = PROJECT_ROOT / "reports" / "data_cost" / "h_g1_gamma_oi_12_date_cost_estimate.md"
DEFAULT_DATASET = "OPRA.PILLAR"
DEFAULT_SCHEMA = "statistics"
DEFAULT_SYMBOL = "SPY.OPT"
DEFAULT_STYPE_IN = "parent"
DEFAULT_API_KEY_ENV = "DATABENTO_API_KEY"
DATABENTO_API_KEY_ENV_ALIASES = ("DATABENTO_SPY0DTE_API",)


@dataclass(frozen=True)
class OiCostRequest:
    date: str
    dataset: str
    symbols: list[str]
    schema: str
    stype_in: str
    start: str
    end: str
    window: str
    note: str


def build_full_day_requests(
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    dataset: str = DEFAULT_DATASET,
    schema: str = DEFAULT_SCHEMA,
    symbol: str = DEFAULT_SYMBOL,
    stype_in: str = DEFAULT_STYPE_IN,
) -> tuple[dict[str, Any], list[OiCostRequest], list[dict[str, Any]]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    requests: list[OiCostRequest] = []
    existing: list[dict[str, Any]] = []
    for item in manifest.get("selected_dates", []):
        status = item.get("opra_oi_status")
        if status == "existing_probe":
            existing.append({"date": item.get("date"), "opra_oi_status": status})
            continue
        if status != "needs_metadata_cost_check":
            continue
        target_date = _parse_date(item["date"])
        next_date = target_date + timedelta(days=1)
        requests.append(
            OiCostRequest(
                date=item["date"],
                dataset=dataset,
                symbols=[symbol],
                schema=schema,
                stype_in=stype_in,
                start=_utc_midnight(target_date),
                end=_utc_midnight(next_date),
                window=f"{item['date']}_full_utc_day_statistics",
                note=(
                    "Full UTC day OPRA statistics request. Prior probe found intraday windows can show "
                    "$0.0 while full-day records carry the usable open-interest payload."
                ),
            )
        )
    return manifest, requests, existing


def estimate_live_cost(
    requests: list[OiCostRequest],
    api_key_env: str = DEFAULT_API_KEY_ENV,
    cost_provider: Callable[[OiCostRequest], float] | None = None,
) -> dict[str, Any]:
    provider = cost_provider or _databento_cost_provider(api_key_env)
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    total = 0.0
    for request in requests:
        row = asdict(request)
        try:
            cost = round(float(provider(request)), 6)
            row["estimated_cost_usd"] = cost
            total += cost
        except Exception as exc:
            row["estimated_cost_usd"] = None
            row["error"] = str(exc)
            errors.append({"date": request.date, "window": request.window, "error": str(exc)})
        rows.append(row)
    return {
        "mode": "live_metadata_cost_no_download",
        "download_performed": False,
        "live_request_count": len(requests),
        "total_estimated_cost_usd": round(total, 6),
        "requests": rows,
        "errors": errors,
    }


def build_result(
    manifest: dict[str, Any],
    requests: list[OiCostRequest],
    existing_probe_dates: list[dict[str, Any]],
    cost_result: dict[str, Any] | None,
    manifest_validation: dict[str, Any],
    paid_cost_audit: dict[str, Any],
) -> dict[str, Any]:
    cost_guard = {
        "status": paid_cost_audit.get("status"),
        "basis": paid_cost_audit.get("cost_guard_basis"),
        "used_usd": paid_cost_audit.get("cost_guard_used_usd"),
        "stop_threshold_usd": paid_cost_audit.get("stop_threshold_usd"),
        "remaining_before_stop_usd": paid_cost_audit.get("remaining_before_stop_usd"),
    }
    total_estimate = None if cost_result is None else cost_result.get("total_estimated_cost_usd")
    projected_usage = None
    if isinstance(total_estimate, int | float) and isinstance(cost_guard["used_usd"], int | float):
        projected_usage = round(float(cost_guard["used_usd"]) + float(total_estimate), 6)

    blockers: list[str] = []
    if manifest_validation.get("status") != "pass":
        blockers.append("manifest_validation_not_pass")
    if paid_cost_audit.get("status") != "pass":
        blockers.append("paid_cost_audit_not_pass")
    if cost_result is None:
        blockers.append("requires_live_metadata_cost")
    else:
        if cost_result.get("errors"):
            blockers.append("metadata_cost_errors_present")
        remaining = cost_guard.get("remaining_before_stop_usd")
        if isinstance(total_estimate, int | float) and isinstance(remaining, int | float) and total_estimate > remaining:
            blockers.append("estimated_cost_exceeds_remaining_headroom")

    decision = {
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "download_allowed_under_current_guard": not blockers,
        "reason": _decision_reason(blockers, total_estimate, cost_guard.get("remaining_before_stop_usd")),
    }

    return {
        "schema_version": "h_g1_gamma_oi_cost_estimate_v1",
        "hypothesis_id": manifest.get("hypothesis_id"),
        "mode": "dry_run_no_download" if cost_result is None else cost_result.get("mode"),
        "download_performed": False,
        "manifest_schema_version": manifest.get("schema_version"),
        "manifest_validation": manifest_validation,
        "existing_probe_dates": existing_probe_dates,
        "missing_oi_date_count": len(requests),
        "planned_requests": [asdict(request) for request in requests],
        "cost_result": cost_result,
        "cost_guard": cost_guard,
        "projected_usage_if_downloaded_usd": projected_usage,
        "decision": decision,
    }


def render_markdown(result: dict[str, Any]) -> str:
    decision = result["decision"]
    cost_guard = result["cost_guard"]
    cost_result = result.get("cost_result") or {}
    total_estimate = cost_result.get("total_estimated_cost_usd")
    lines = [
        "# H-G1 Gamma/OI Cost Gate",
        "",
        f"- **Hypothesis**: `{result.get('hypothesis_id')}`",
        f"- **Mode**: `{result.get('mode')}`",
        f"- **Download performed**: `{result.get('download_performed')}`",
        f"- **Missing OI dates estimated**: {result.get('missing_oi_date_count')}",
        f"- **Existing probe dates**: {', '.join(item['date'] for item in result.get('existing_probe_dates', [])) or '-'}",
        f"- **Total estimated cost**: `{total_estimate if total_estimate is not None else 'not_available'}`",
        f"- **Cost guard used**: `${cost_guard.get('used_usd')}` / `${cost_guard.get('stop_threshold_usd')}`",
        f"- **Remaining before stop**: `${cost_guard.get('remaining_before_stop_usd')}`",
        f"- **Projected usage if downloaded**: `${result.get('projected_usage_if_downloaded_usd')}`",
        f"- **Decision**: `{decision['status']}`",
        f"- **Download allowed under current guard**: `{decision['download_allowed_under_current_guard']}`",
        f"- **Reason**: {decision['reason']}",
        "",
        "## Planned Full-Day Requests",
        "",
        "| Date | Window | Start | End | Cost |",
        "|:--|:--|:--|:--|--:|",
    ]
    cost_by_window = {
        item["window"]: item.get("estimated_cost_usd")
        for item in cost_result.get("requests", [])
        if isinstance(item, dict)
    }
    for request in result["planned_requests"]:
        cost = cost_by_window.get(request["window"], "")
        lines.append(f"| `{request['date']}` | `{request['window']}` | `{request['start']}` | `{request['end']}` | `{cost}` |")
    if decision["blockers"]:
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- `{blocker}`" for blocker in decision["blockers"])
    lines.extend(
        [
            "",
            "## Guardrail",
            "",
            "This report is a metadata cost gate only. It must not be treated as a Databento download, an OI coverage pass, or a gamma strategy result.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_outputs(result: dict[str, Any], json_report: Path, md_report: Path) -> None:
    json_report.parent.mkdir(parents=True, exist_ok=True)
    json_report.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_report.parent.mkdir(parents=True, exist_ok=True)
    md_report.write_text(render_markdown(result), encoding="utf-8")


def _decision_reason(blockers: list[str], total_estimate: Any, remaining: Any) -> str:
    if not blockers:
        return f"Estimated H-G1 OI cost ${total_estimate} fits within remaining headroom ${remaining}."
    if "requires_live_metadata_cost" in blockers:
        return "Dry-run only; run with --live before any H-G1 OI download."
    if "estimated_cost_exceeds_remaining_headroom" in blockers:
        return f"Estimated H-G1 OI cost ${total_estimate} exceeds remaining headroom ${remaining}."
    return "One or more validation or metadata-cost blockers must be resolved before download."


def _databento_cost_provider(api_key_env: str) -> Callable[[OiCostRequest], float]:
    api_key = _databento_api_key_from_env(api_key_env)
    if not api_key:
        raise RuntimeError(f"missing Databento API key environment variable: {_databento_env_names(api_key_env)}")
    try:
        import databento as db  # type: ignore
    except ImportError as exc:
        raise RuntimeError("missing Python package: databento") from exc

    client = db.Historical(api_key)

    def provider(request: OiCostRequest) -> float:
        return float(
            client.metadata.get_cost(
                dataset=request.dataset,
                symbols=request.symbols,
                schema=request.schema,
                stype_in=request.stype_in,
                start=request.start,
                end=request.end,
            )
        )

    return provider


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


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _utc_midnight(value: date) -> str:
    return datetime(value.year, value.month, value.day, tzinfo=timezone.utc).isoformat()


def _load_manifest_validation(manifest_path: Path) -> dict[str, Any]:
    import importlib.util

    script_path = PROJECT_ROOT / "scripts" / "validate_h_g1_regime_date_set.py"
    spec = importlib.util.spec_from_file_location("validate_h_g1_regime_date_set", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load H-G1 date-set validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.validate_h_g1_regime_date_set(manifest_path)


def _load_paid_cost_audit() -> dict[str, Any]:
    import importlib.util

    script_path = PROJECT_ROOT / "scripts" / "audit_paid_costs.py"
    spec = importlib.util.spec_from_file_location("audit_paid_costs", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load paid cost auditor")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.audit_paid_costs()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Estimate H-G1 OPRA statistics/OI full-day cost before any download.")
    parser.add_argument("--manifest-path", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--json-report", type=Path, default=DEFAULT_JSON_REPORT)
    parser.add_argument("--md-report", type=Path, default=DEFAULT_MD_REPORT)
    parser.add_argument("--api-key-env", default=DEFAULT_API_KEY_ENV)
    parser.add_argument("--live", action="store_true", help="Call Databento metadata.get_cost. No download is performed.")
    args = parser.parse_args(argv)

    manifest, requests, existing = build_full_day_requests(args.manifest_path)
    validation = _load_manifest_validation(args.manifest_path)
    audit = _load_paid_cost_audit()
    cost_result = estimate_live_cost(requests, args.api_key_env) if args.live else None
    result = build_result(manifest, requests, existing, cost_result, validation, audit)
    write_outputs(result, args.json_report, args.md_report)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["decision"]["status"] == "pass" or not args.live else 1


if __name__ == "__main__":
    raise SystemExit(main())
