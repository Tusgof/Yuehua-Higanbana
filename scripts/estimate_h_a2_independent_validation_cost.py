from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from datetime import date, datetime, time
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PREREG_PATH = PROJECT_ROOT / "experiments" / "h_a2_independent_validation_paid_cost_plan_preregistration.json"
NORMAL_CONTROL_DECISION_PATH = PROJECT_ROOT / "experiments" / "h_a2_normal_control_sample_decision.json"
DEFAULT_PLAN_JSON = PROJECT_ROOT / "reports" / "data_cost" / "h_a2_independent_validation_paid_cost_plan.json"
DEFAULT_PLAN_MD = PROJECT_ROOT / "reports" / "data_cost" / "h_a2_independent_validation_paid_cost_plan.md"
DEFAULT_LIVE_JSON = PROJECT_ROOT / "reports" / "data_cost" / "h_a2_independent_validation_paid_cost_estimate.json"
DEFAULT_LIVE_MD = PROJECT_ROOT / "reports" / "data_cost" / "h_a2_independent_validation_paid_cost_estimate.md"
DEFAULT_BATCH_ID = "sample_cost_probe_high_vix_one_day"
DEFAULT_API_KEY_ENV = "DATABENTO_API_KEY"
DATABENTO_API_KEY_ENV_ALIASES = ("DATABENTO_SPY0DTE_API", "DATABENTO_API_MO", "DATABENTO_API_AI")
ET = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")


@dataclass(frozen=True)
class CostRequest:
    batch_id: str
    date: str
    field_group: str
    dataset: str
    symbols: list[str]
    schema: str
    stype_in: str
    start: str
    end: str
    window: str
    note: str


def build_batch_requests(
    prereg_path: Path = DEFAULT_PREREG_PATH,
    batch_id: str = DEFAULT_BATCH_ID,
) -> tuple[dict[str, Any], dict[str, Any], list[CostRequest]]:
    prereg = _load_json(prereg_path)
    batch = _find_batch(prereg, batch_id)
    dates = _batch_dates(batch)
    requests: list[CostRequest] = []
    for value in dates:
        target_date = date.fromisoformat(value)
        requests.extend(_option_requests(batch_id, target_date))
        requests.append(_underlying_request(batch_id, target_date))
    return prereg, batch, requests


def estimate_live_cost(
    requests: list[CostRequest],
    api_key_env: str = DEFAULT_API_KEY_ENV,
    cost_provider: Callable[[CostRequest], float] | None = None,
    group_requests: bool = False,
) -> dict[str, Any]:
    cost_requests = _group_requests_for_metadata_cost(requests) if group_requests else requests
    provider = cost_provider or _databento_cost_provider(api_key_env)
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    total = 0.0
    for request in cost_requests:
        row = asdict(request)
        try:
            cost = round(float(provider(request)), 6)
            row["estimated_cost_usd"] = cost
            total += cost
        except Exception as exc:
            row["estimated_cost_usd"] = None
            row["error"] = str(exc)
            errors.append({"window": request.window, "error": str(exc)})
        rows.append(row)
    return {
        "mode": "live_metadata_cost_no_download_grouped_conservative" if group_requests else "live_metadata_cost_no_download",
        "download_performed": False,
        "planned_request_count": len(requests),
        "live_request_count": len(cost_requests),
        "grouped_from_request_count": len(requests) if group_requests else None,
        "total_estimated_cost_usd": round(total, 6),
        "requests": rows,
        "errors": errors,
    }


def build_result(
    prereg: dict[str, Any],
    batch: dict[str, Any],
    requests: list[CostRequest],
    cost_result: dict[str, Any] | None,
    prereg_validation: dict[str, Any],
    paid_cost_audit: dict[str, Any],
    selected_key_env: str = DEFAULT_API_KEY_ENV,
) -> dict[str, Any]:
    selected_key_cap = _selected_key_cap(paid_cost_audit, selected_key_env, prereg)
    combined_pool_cap = _combined_pool_cap(paid_cost_audit)
    uses_mo_ai_pool = selected_key_env in {"DATABENTO_API_MO", "DATABENTO_API_AI"}
    cost_guard = {
        "status": paid_cost_audit.get("status"),
        "basis": paid_cost_audit.get("cost_guard_basis"),
        "used_usd": paid_cost_audit.get("cost_guard_used_usd"),
        "stop_threshold_usd": paid_cost_audit.get("stop_threshold_usd"),
        "remaining_before_stop_usd": paid_cost_audit.get("remaining_before_stop_usd"),
        "active_guard_for_selected_key": "mo_ai_pool" if uses_mo_ai_pool else "legacy_account_guard",
    }
    total_estimate = None if cost_result is None else cost_result.get("total_estimated_cost_usd")
    projected_usage = None
    projected_selected_key_usage = None
    if isinstance(total_estimate, int | float) and isinstance(cost_guard["used_usd"], int | float):
        projected_usage = round(float(cost_guard["used_usd"]) + float(total_estimate), 6)
    if uses_mo_ai_pool and isinstance(total_estimate, int | float):
        projected_selected_key_usage = round(float(total_estimate), 6)

    blockers: list[str] = []
    if prereg_validation.get("status") != "pass":
        blockers.append("preregistration_validation_not_pass")
    if paid_cost_audit.get("status") != "pass":
        blockers.append("paid_cost_audit_not_pass")
    if cost_guard.get("remaining_before_stop_usd") is not None and float(cost_guard["remaining_before_stop_usd"]) <= 0:
        blockers.append("remaining_headroom_not_positive")
    if cost_result is None:
        blockers.append("requires_live_metadata_cost")
    else:
        if cost_result.get("errors"):
            blockers.append("metadata_cost_errors_present")
        remaining = cost_guard.get("remaining_before_stop_usd")
        if (
            not uses_mo_ai_pool
            and isinstance(total_estimate, int | float)
            and isinstance(remaining, int | float)
            and total_estimate > remaining
        ):
            blockers.append("estimated_cost_exceeds_remaining_headroom")
        if isinstance(total_estimate, int | float) and isinstance(selected_key_cap, int | float) and total_estimate > selected_key_cap:
            blockers.append("estimated_cost_exceeds_selected_key_cap")
        if isinstance(total_estimate, int | float) and isinstance(combined_pool_cap, int | float) and total_estimate > combined_pool_cap:
            blockers.append("estimated_cost_exceeds_mo_ai_pool_cap")

    estimate_status = "metadata_estimate_pass_next_download_decision_required" if not blockers else "blocked"
    decision = {
        "status": estimate_status,
        "blockers": blockers,
        "download_allowed_under_current_guard": False,
        "separate_download_decision_required": True,
        "reason": _decision_reason(
            blockers,
            total_estimate,
            {
                "selected_key_cap_usd": selected_key_cap,
                "mo_ai_combined_pool_cap_usd": combined_pool_cap,
            }
            if uses_mo_ai_pool
            else cost_guard.get("remaining_before_stop_usd"),
        ),
    }

    return {
        "schema_version": "h_a2_independent_validation_cost_estimate_v1",
        "hypothesis_id": prereg.get("hypothesis_id"),
        "experiment_id": prereg.get("experiment_id"),
        "evidence_tier": "E0",
        "batch_id": batch.get("batch_id"),
        "batch_role": batch.get("role"),
        "selected_key_env_for_metadata_estimate": selected_key_env,
        "mode": "dry_run_no_download" if cost_result is None else cost_result.get("mode"),
        "download_performed": False,
        "locked_signal_under_validation": prereg.get("locked_signal_under_validation"),
        "preregistration_validation": prereg_validation,
        "batch": batch,
        "planned_request_count": len(requests),
        "planned_requests": [asdict(request) for request in requests],
        "cost_result": cost_result,
        "cost_guard": cost_guard,
        "selected_key_policy": {
            "selected_key_env": selected_key_env,
            "selected_key_cap_usd": selected_key_cap,
            "mo_ai_combined_pool_cap_usd": combined_pool_cap,
            "active_guard": "mo_ai_pool" if uses_mo_ai_pool else "legacy_account_guard",
            "key_value_stored": False,
        },
        "projected_usage_if_downloaded_usd": projected_usage,
        "projected_selected_key_usage_if_downloaded_usd": projected_selected_key_usage,
        "decision": decision,
        "forbidden_next_actions": [
            "paid_download_without_separate_decision_artifact",
            "broad_2025_calendar_estimate",
            "new_paid_provider",
            "threshold_search",
            "new_oos_selected_filter",
            "exact_replay",
            "paper_trading_or_e2_claim",
        ],
    }


def render_markdown(result: dict[str, Any]) -> str:
    decision = result["decision"]
    cost_guard = result["cost_guard"]
    cost_result = result.get("cost_result") or {}
    total_estimate = cost_result.get("total_estimated_cost_usd")
    lines = [
        "# H-A2 Independent Validation Cost Gate",
        "",
        f"- **Hypothesis**: `{result.get('hypothesis_id')}`",
        f"- **Experiment**: `{result.get('experiment_id')}`",
        f"- **Batch**: `{result.get('batch_id')}`",
        f"- **Selected key env**: `{result.get('selected_key_env_for_metadata_estimate')}`",
        f"- **Mode**: `{result.get('mode')}`",
        f"- **Download performed**: `{result.get('download_performed')}`",
        f"- **Planned requests**: `{result.get('planned_request_count')}`",
        f"- **Total estimated cost**: `{total_estimate if total_estimate is not None else 'not_available'}`",
        f"- **Cost guard used**: `${cost_guard.get('used_usd')}` / `${cost_guard.get('stop_threshold_usd')}`",
        f"- **Remaining before stop**: `${cost_guard.get('remaining_before_stop_usd')}`",
        f"- **Projected usage if downloaded**: `${result.get('projected_usage_if_downloaded_usd')}`",
        f"- **Projected selected-key usage if downloaded**: `${result.get('projected_selected_key_usage_if_downloaded_usd')}`",
        f"- **Decision**: `{decision['status']}`",
        f"- **Download allowed under current guard**: `{decision['download_allowed_under_current_guard']}`",
        f"- **Reason**: {decision['reason']}",
        "",
        "## Planned Requests",
        "",
        "| Date | Field | Window | Dataset | Schema | Start | End | Cost |",
        "|:--|:--|:--|:--|:--|:--|:--|--:|",
    ]
    cost_by_window = {
        item["window"]: item.get("estimated_cost_usd")
        for item in cost_result.get("requests", [])
        if isinstance(item, dict)
    }
    for request in result["planned_requests"]:
        cost = cost_by_window.get(request["window"], "")
        lines.append(
            f"| `{request['date']}` | `{request['field_group']}` | `{request['window']}` | "
            f"`{request['dataset']}` | `{request['schema']}` | `{request['start']}` | `{request['end']}` | `{cost}` |"
        )
    if decision["blockers"]:
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- `{blocker}`" for blocker in decision["blockers"])
    lines.extend(
        [
            "",
            "## Guardrail",
            "",
            "This is a metadata cost gate only. It does not download Databento data, add validation PnL days, approve exact replay, or approve paper trading.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_outputs(result: dict[str, Any], json_report: Path, md_report: Path) -> None:
    json_report.parent.mkdir(parents=True, exist_ok=True)
    json_report.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_report.parent.mkdir(parents=True, exist_ok=True)
    md_report.write_text(render_markdown(result), encoding="utf-8")


def _option_requests(batch_id: str, target_date: date) -> list[CostRequest]:
    windows = [
        ("entry_0935", time(9, 30), time(9, 40), "option_entry_quote", "10-minute window around 09:35 ET entry"),
        ("entry_check_1000", time(9, 55), time(10, 5), "option_exit_quotes", "10-minute window around 10:00 ET check"),
        ("exit_check_1030", time(10, 25), time(10, 35), "option_exit_quotes", "10-minute window around 10:30 ET check"),
        ("exit_check_1100", time(10, 55), time(11, 5), "option_exit_quotes", "10-minute window around 11:00 ET check"),
        ("exit_check_1130", time(11, 25), time(11, 35), "option_exit_quotes", "10-minute window around 11:30 ET check"),
        ("exit_check_1200", time(11, 55), time(12, 5), "option_exit_quotes", "10-minute window around 12:00 ET check"),
        ("exit_check_1230", time(12, 25), time(12, 35), "option_exit_quotes", "10-minute window around 12:30 ET check"),
        ("exit_check_1300", time(12, 55), time(13, 5), "option_exit_quotes", "10-minute window around 13:00 ET check"),
        ("exit_check_1330", time(13, 25), time(13, 35), "option_exit_quotes", "10-minute window around 13:30 ET check"),
        ("exit_check_1400", time(13, 55), time(14, 5), "option_exit_quotes", "10-minute window around 14:00 ET check"),
        ("exit_check_1430", time(14, 25), time(14, 35), "option_exit_quotes", "10-minute window around 14:30 ET check"),
        ("exit_check_1500", time(14, 55), time(15, 5), "option_exit_quotes", "10-minute window around 15:00 ET check"),
        ("exit_check_1530", time(15, 25), time(15, 35), "option_exit_quotes", "10-minute window around 15:30 ET check"),
        ("forced_close_1545", time(15, 40), time(15, 50), "option_exit_quotes", "10-minute window around 15:45 ET forced close"),
    ]
    return [
        CostRequest(
            batch_id=batch_id,
            date=target_date.isoformat(),
            field_group=field_group,
            dataset="OPRA.PILLAR",
            symbols=["SPY.OPT"],
            schema="cbbo-1m",
            stype_in="parent",
            start=_et_to_utc_iso(target_date, start_time),
            end=_et_to_utc_iso(target_date, end_time),
            window=f"{target_date.isoformat()}_{name}",
            note=note,
        )
        for name, start_time, end_time, field_group, note in windows
    ]


def _underlying_request(batch_id: str, target_date: date) -> CostRequest:
    return CostRequest(
        batch_id=batch_id,
        date=target_date.isoformat(),
        field_group="spy_underlying_bars",
        dataset="EQUS.MINI",
        symbols=["SPY"],
        schema="ohlcv-1m",
        stype_in="raw_symbol",
        start=_et_to_utc_iso(target_date, time(9, 30)),
        end=_et_to_utc_iso(target_date, time(16, 0)),
        window=f"{target_date.isoformat()}_spy_underlying_full_session",
        note="Full regular-session 1-minute SPY bars for signal reconstruction and context.",
    )


def _group_requests_for_metadata_cost(requests: list[CostRequest]) -> list[CostRequest]:
    grouped: list[CostRequest] = []
    by_date: dict[str, list[CostRequest]] = {}
    for request in requests:
        by_date.setdefault(request.date, []).append(request)
    for date_text in sorted(by_date):
        daily = by_date[date_text]
        option_requests = [request for request in daily if request.dataset == "OPRA.PILLAR"]
        if option_requests:
            first = min(option_requests, key=lambda request: request.start)
            last = max(option_requests, key=lambda request: request.end)
            grouped.append(
                CostRequest(
                    batch_id=first.batch_id,
                    date=date_text,
                    field_group="option_quotes_grouped_conservative",
                    dataset="OPRA.PILLAR",
                    symbols=["SPY.OPT"],
                    schema="cbbo-1m",
                    stype_in="parent",
                    start=first.start,
                    end=last.end,
                    window=f"{date_text}_opra_grouped_0930_1550",
                    note="Conservative metadata-cost estimate covering all required OPRA windows for the day. No download is performed.",
                )
            )
        grouped.extend(request for request in daily if request.dataset != "OPRA.PILLAR")
    return grouped


def _decision_reason(blockers: list[str], total_estimate: Any, remaining: Any) -> str:
    if not blockers:
        if isinstance(remaining, dict):
            return (
                f"Metadata estimate ${total_estimate} fits within selected key cap "
                f"${remaining.get('selected_key_cap_usd')} and MO/AI pool cap "
                f"${remaining.get('mo_ai_combined_pool_cap_usd')}; a separate download decision artifact is still required before any data pull."
            )
        return (
            f"Metadata estimate ${total_estimate} fits within remaining headroom ${remaining}; "
            "a separate download decision artifact is still required before any data pull."
        )
    if "requires_live_metadata_cost" in blockers:
        return "Dry-run only; run with --live before any H-A2 independent-validation download decision."
    if "estimated_cost_exceeds_remaining_headroom" in blockers:
        return f"Estimated H-A2 sample cost ${total_estimate} exceeds remaining headroom ${remaining}."
    if "estimated_cost_exceeds_selected_key_cap" in blockers:
        return f"Estimated H-A2 sample cost ${total_estimate} exceeds the selected Databento key cap."
    if "estimated_cost_exceeds_mo_ai_pool_cap" in blockers:
        return f"Estimated H-A2 sample cost ${total_estimate} exceeds the approved MO/AI combined pool cap."
    return "One or more preregistration, cost-audit, or metadata-cost blockers must be resolved."


def _load_prereg_validation(prereg_path: Path) -> dict[str, Any]:
    import importlib.util

    schema = _load_json(prereg_path).get("schema_version")
    if schema == "h_a2_normal_control_sample_decision_v1":
        script_path = PROJECT_ROOT / "scripts" / "validate_h_a2_normal_control_sample_decision.py"
        function_name = "validate_h_a2_normal_control_sample_decision"
        module_name = "validate_h_a2_normal_control_sample_decision"
    elif schema == "h_a2_post_exact_replay_sample_expansion_decision_v1":
        script_path = PROJECT_ROOT / "scripts" / "validate_h_a2_post_exact_replay_sample_expansion_decision.py"
        function_name = "validate_h_a2_post_exact_replay_sample_expansion_decision"
        module_name = "validate_h_a2_post_exact_replay_sample_expansion_decision"
    else:
        script_path = PROJECT_ROOT / "scripts" / "validate_h_a2_independent_validation_paid_cost_plan_preregistration.py"
        function_name = "validate_h_a2_independent_validation_paid_cost_plan_preregistration"
        module_name = "validate_h_a2_independent_validation_paid_cost_plan_preregistration"
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load H-A2 cost-plan validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, function_name)(prereg_path)


def _selected_key_cap(paid_cost_audit: dict[str, Any], selected_key_env: str, prereg: dict[str, Any]) -> float | None:
    per_key_caps = paid_cost_audit.get("budget_policy", {}).get("per_key_caps_usd", {})
    cap = per_key_caps.get(selected_key_env)
    if isinstance(cap, int | float):
        return float(cap)
    snapshot_cap = prereg.get("budget_policy_snapshot", {}).get("selected_key_cap_usd")
    if isinstance(snapshot_cap, int | float):
        return float(snapshot_cap)
    return None


def _combined_pool_cap(paid_cost_audit: dict[str, Any]) -> float | None:
    cap = paid_cost_audit.get("budget_policy", {}).get("combined_pool_caps_usd", {}).get("DATABENTO_API_MO+DATABENTO_API_AI")
    return float(cap) if isinstance(cap, int | float) else None


def _load_paid_cost_audit() -> dict[str, Any]:
    import importlib.util

    script_path = PROJECT_ROOT / "scripts" / "audit_paid_costs.py"
    spec = importlib.util.spec_from_file_location("audit_paid_costs", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load paid cost auditor")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.audit_paid_costs()


def _databento_cost_provider(api_key_env: str) -> Callable[[CostRequest], float]:
    api_key = _databento_api_key_from_env(api_key_env)
    if not api_key:
        raise RuntimeError(f"missing Databento API key environment variable: {_databento_env_names(api_key_env)}")
    try:
        import databento as db  # type: ignore
    except ImportError as exc:
        raise RuntimeError("missing Python package: databento") from exc

    client = db.Historical(api_key)

    def provider(request: CostRequest) -> float:
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


def _find_batch(prereg: dict[str, Any], batch_id: str) -> dict[str, Any]:
    for batch in prereg.get("candidate_estimate_batches", []):
        if batch.get("batch_id") == batch_id:
            return batch
    raise ValueError(f"unknown batch_id: {batch_id}")


def _batch_dates(batch: dict[str, Any]) -> list[str]:
    if isinstance(batch.get("dates"), list):
        return [str(item) for item in batch["dates"]]
    start = batch.get("period_start")
    end = batch.get("period_end")
    if not isinstance(start, str) or not isinstance(end, str):
        raise ValueError(f"batch has no dates or period range: {batch.get('batch_id')}")
    start_date = date.fromisoformat(start)
    end_date = date.fromisoformat(end)
    days: list[str] = []
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:
            days.append(current.isoformat())
        current = date.fromordinal(current.toordinal() + 1)
    return days


def _et_to_utc_iso(target_date: date, value: time) -> str:
    return datetime.combine(target_date, value, tzinfo=ET).astimezone(UTC).isoformat()


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


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Estimate H-A2 independent-validation Databento metadata cost without download.")
    parser.add_argument("--prereg-path", type=Path, default=DEFAULT_PREREG_PATH)
    parser.add_argument("--batch-id", default=DEFAULT_BATCH_ID)
    parser.add_argument("--json-report", type=Path, default=None)
    parser.add_argument("--md-report", type=Path, default=None)
    parser.add_argument("--api-key-env", default=DEFAULT_API_KEY_ENV)
    parser.add_argument("--live", action="store_true", help="Call Databento metadata.get_cost. No download is performed.")
    parser.add_argument(
        "--group-live-requests",
        action="store_true",
        help="For live metadata estimates, group each day's OPRA windows into one conservative full-window request.",
    )
    args = parser.parse_args(argv)

    json_report = args.json_report or (DEFAULT_LIVE_JSON if args.live else DEFAULT_PLAN_JSON)
    md_report = args.md_report or (DEFAULT_LIVE_MD if args.live else DEFAULT_PLAN_MD)
    prereg, batch, requests = build_batch_requests(args.prereg_path, args.batch_id)
    validation = _load_prereg_validation(args.prereg_path)
    audit = _load_paid_cost_audit()
    cost_result = estimate_live_cost(requests, args.api_key_env, group_requests=args.group_live_requests) if args.live else None
    result = build_result(prereg, batch, requests, cost_result, validation, audit, args.api_key_env)
    write_outputs(result, json_report, md_report)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if args.live and result["decision"]["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
