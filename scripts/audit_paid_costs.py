from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_COST_ROOT = PROJECT_ROOT / "reports" / "data_cost"
DEFAULT_EXPERIMENT_ROOT = PROJECT_ROOT / "reports" / "experiments"
DEFAULT_JSON_OUTPUT = PROJECT_ROOT / "reports" / "data_cost" / "paid_cost_audit.json"
DEFAULT_REPORT_OUTPUT = PROJECT_ROOT / "reports" / "data_cost" / "paid_cost_audit.md"
DEFAULT_USER_REPORTED_USAGE_PATH = PROJECT_ROOT / "reports" / "data_cost" / "user_reported_actual_usage.json"
DEFAULT_STOP_THRESHOLD_USD = 125.0
BUDGET_POLICY = {
    "cap_extension_method": "real_payment_on_existing_databento_account_only",
    "approved_databento_key_envs": [
        "DATABENTO_API_KEY",
        "DATABENTO_SPY0DTE_API",
        "DATABENTO_API_MO",
        "DATABENTO_API_AI",
        "DATABENTO_API_01",
    ],
    "per_key_caps_usd": {
        "DATABENTO_API_MO": 100.0,
        "DATABENTO_API_AI": 100.0,
        "DATABENTO_API_01": 50.0,
    },
    "combined_pool_caps_usd": {
        "DATABENTO_API_MO+DATABENTO_API_AI": 200.0,
    },
    "prohibited": ["multi_account_signup_credit_harvesting"],
    "per_key_ledger": {
        "DATABENTO_API_01": {
            "account_provenance": "primary_existing_databento_account",
            "authorization_limit_usd": 50.0,
            "known_committed_estimated_usage_usd": 0.0,
        }
    },
    "notes": (
        "The user added Databento env keys DATABENTO_API_MO and DATABENTO_API_AI as one approved $200 research pool, "
        "while each individual key remains capped at $100. Never store key values. "
        "A paid action must estimate/log cost first and must not exceed the selected key cap or combined pool cap. "
        "DATABENTO_API_01 is a user-authorized $50 key on the primary existing Databento account. "
        "Opening extra accounts or using other identities to harvest duplicate signup credits remains prohibited."
    ),
}


def audit_paid_costs(
    data_cost_root: Path = DEFAULT_DATA_COST_ROOT,
    stop_threshold_usd: float = DEFAULT_STOP_THRESHOLD_USD,
    experiment_root: Path = DEFAULT_EXPERIMENT_ROOT,
    user_reported_usage_path: Path | None = None,
) -> dict[str, Any]:
    usage_path = user_reported_usage_path or data_cost_root / "user_reported_actual_usage.json"
    committed, committed_source_reports = _load_committed_databento_costs(data_cost_root)
    openrouter_committed, openrouter_unpriced = _load_openrouter_costs(experiment_root)
    committed.extend(openrouter_committed)
    committed = sorted(committed, key=lambda item: (item["provider"], item["item_id"]))
    estimated_only = _load_live_estimates_without_download(data_cost_root, committed, committed_source_reports)
    committed_total = round(sum(item["estimated_cost_usd"] for item in committed), 6)
    user_reported_usage = _load_user_reported_usage(usage_path)
    cost_guard_used = user_reported_usage["actual_usage_usd"] if user_reported_usage else committed_total
    cost_guard_basis = "user_reported_actual_usage" if user_reported_usage else "known_committed_estimated_cost"
    remaining = round(stop_threshold_usd - cost_guard_used, 6)
    status = "blocked" if remaining <= 0 else "pass"
    reconciliation = _build_cost_guard_reconciliation(
        stop_threshold_usd=stop_threshold_usd,
        committed_total=committed_total,
        user_reported_usage=user_reported_usage,
        estimated_only=estimated_only,
    )
    budget_policy = json.loads(json.dumps(BUDGET_POLICY))
    for key_env, ledger in budget_policy.get("per_key_ledger", {}).items():
        ledger["known_committed_estimated_usage_usd"] = round(
            sum(
                float(item["estimated_cost_usd"])
                for item in committed
                if item.get("provider") == "Databento" and item.get("selected_key_env") == key_env
            ),
            6,
        )

    return {
        "status": status,
        "stop_threshold_usd": stop_threshold_usd,
        "known_committed_estimated_cost_usd": committed_total,
        "user_reported_actual_usage": user_reported_usage,
        "cost_guard_basis": cost_guard_basis,
        "cost_guard_used_usd": round(float(cost_guard_used), 6),
        "remaining_before_stop_usd": remaining,
        "committed_items": committed,
        "estimated_only_items": estimated_only,
        "cost_guard_reconciliation": reconciliation,
        "budget_policy": budget_policy,
        "unpriced_items": openrouter_unpriced,
        "blockers": [] if status == "pass" else ["paid_cost_stop_threshold_reached"],
    }


def write_reports(result: dict[str, Any], json_output: Path = DEFAULT_JSON_OUTPUT, report_output: Path = DEFAULT_REPORT_OUTPUT) -> None:
    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Paid Cost Audit",
        "",
        f"- Status: `{result['status']}`",
        f"- Stop threshold: `${result['stop_threshold_usd']}`",
        f"- Known committed estimated cost: `${result['known_committed_estimated_cost_usd']}`",
        f"- Cost guard basis: `{result['cost_guard_basis']}`",
        f"- Cost guard used: `${result['cost_guard_used_usd']}`",
        f"- Remaining before stop: `${result['remaining_before_stop_usd']}`",
        "",
        "## Cost Guard Reconciliation",
        "",
    ]
    reconciliation = result["cost_guard_reconciliation"]
    actual_basis = reconciliation["actual_usage_basis"]
    conservative_basis = reconciliation["known_committed_estimate_basis"]
    estimated_risk = reconciliation["estimated_only_risk"]
    lines.extend(
        [
            f"- Actual-usage basis status: `{actual_basis['status']}`; used `${actual_basis['used_usd']}`; remaining `${actual_basis['remaining_usd']}`",
            f"- Conservative known-estimate basis status: `{conservative_basis['status']}`; used `${conservative_basis['used_usd']}`; remaining `${conservative_basis['remaining_usd']}`",
            f"- Estimated-only total not yet committed: `${estimated_risk['estimated_only_total_usd']}`",
            f"- Single estimated-only items that would reach stop if committed: `{estimated_risk['single_item_threshold_breach_count']}`",
            "",
        ]
    )
    if estimated_risk["single_item_threshold_breaches"]:
        lines.extend(["| Item | Cost | Projected Conservative Total | Source |", "|:--|--:|--:|:--|"])
        for item in estimated_risk["single_item_threshold_breaches"]:
            lines.append(
                f"| `{item['item_id']}` | `${item['estimated_cost_usd']}` | `${item['projected_known_estimated_cost_usd']}` | `{item['source_path']}` |"
            )
        lines.append("")

    lines.extend([
        "## Budget Policy",
        "",
        f"- Cap extension method: `{result['budget_policy']['cap_extension_method']}`",
        f"- Approved Databento key envs: `{', '.join(result['budget_policy']['approved_databento_key_envs'])}`",
        f"- Per-key caps: `{json.dumps(result['budget_policy']['per_key_caps_usd'], sort_keys=True)}`",
        f"- Per-key ledger: `{json.dumps(result['budget_policy']['per_key_ledger'], sort_keys=True)}`",
        f"- Prohibited: `{', '.join(result['budget_policy']['prohibited'])}`",
        f"- Notes: {result['budget_policy']['notes']}",
        "",
        "## User-Reported Actual Usage",
        "",
    ])
    if result.get("user_reported_actual_usage"):
        usage = result["user_reported_actual_usage"]
        lines.extend(
            [
                f"- Actual usage: `${usage['actual_usage_usd']}`",
                f"- Reported at UTC: `{usage.get('reported_at_utc')}`",
                f"- Source: `{usage.get('source')}`",
                f"- Notes: {usage.get('notes', '-')}",
                "",
            ]
        )
    else:
        lines.extend(["- None recorded.", ""])

    lines.extend([
        "## Committed Databento Items",
        "",
        "| Item | Cost | Source |",
        "|:--|--:|:--|",
    ])
    for item in result["committed_items"]:
        lines.append(f"| `{item['item_id']}` | `${item['estimated_cost_usd']}` | `{item['source_path']}` |")

    lines.extend(["", "## Live Estimates Without Completed Download", "", "| Item | Cost | Source |", "|:--|--:|:--|"])
    for item in result["estimated_only_items"]:
        lines.append(f"| `{item['item_id']}` | `${item['estimated_cost_usd']}` | `{item['source_path']}` |")
    if not result["estimated_only_items"]:
        lines.append("| - | - | - |")

    lines.extend(["", "## Unpriced Items", ""])
    for item in result["unpriced_items"]:
        source = f" Source: `{item['source_path']}`." if item.get("source_path") else ""
        lines.append(f"- {item['provider']}: {item['reason']}{source}")

    report_output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _load_committed_databento_costs(root: Path) -> tuple[list[dict[str, Any]], set[str]]:
    items: list[dict[str, Any]] = []
    source_reports: set[str] = set()
    for path in sorted(root.glob("databento_download_result*.json")):
        payload = _load_json(path)
        if payload.get("mode") != "download_complete":
            continue
        source_report = payload.get("source_cost_report")
        if isinstance(source_report, str) and source_report:
            source_reports.add(_normalized_relative(source_report))
        cost = _cost_from_payload(payload)
        if cost is None:
            continue
        items.append(
            {
                "item_id": _item_id(payload, path),
                "provider": "Databento",
                "estimated_cost_usd": cost,
                "mode": payload.get("mode"),
                "scenario": payload.get("scenario"),
                "selected_key_env": _selected_key_env(payload),
                "source_path": _relative(path),
            }
        )
    for path in sorted(root.glob("databento_spy_bars_download_result*.json")):
        payload = _load_json(path)
        if payload.get("mode") != "download_complete":
            continue
        request = payload.get("request", {})
        cost = request.get("estimated_cost_usd") if isinstance(request, dict) else None
        if not isinstance(cost, int | float):
            continue
        items.append(
            {
                "item_id": _item_id(payload, path),
                "provider": "Databento",
                "estimated_cost_usd": round(float(cost), 6),
                "mode": payload.get("mode"),
                "scenario": payload.get("scenario"),
                "source_path": _relative(path),
            }
        )
    for path in sorted(root.glob("databento_opra_statistics_oi_download_probe*.json")):
        payload = _load_json(path)
        if payload.get("mode") != "opra_statistics_oi_download_probe" or payload.get("status") != "pass":
            continue
        plan = payload.get("plan", {})
        cost = plan.get("estimated_cost_usd") if isinstance(plan, dict) else None
        if not isinstance(cost, int | float):
            continue
        window = plan.get("window") if isinstance(plan, dict) else None
        items.append(
            {
                "item_id": f"opra_statistics_oi_probe:{window or path.stem}",
                "provider": "Databento",
                "estimated_cost_usd": round(float(cost), 6),
                "mode": payload.get("mode"),
                "scenario": "opra_statistics_oi_probe",
                "source_path": _relative(path),
            }
        )
    for path in sorted(root.glob("h_g1_gamma_oi_download_result*.json")):
        payload = _load_json(path)
        if payload.get("mode") != "download_complete" or payload.get("status") != "pass":
            continue
        cost = _cost_from_payload(payload)
        if cost is None:
            continue
        scenario = payload.get("scenario") or path.stem
        items.append(
            {
                "item_id": str(scenario),
                "provider": "Databento",
                "estimated_cost_usd": cost,
                "mode": payload.get("mode"),
                "scenario": scenario,
                "source_path": _relative(path),
            }
        )
    return sorted(items, key=lambda item: item["item_id"]), source_reports


def _load_live_estimates_without_download(
    root: Path,
    committed: list[dict[str, Any]],
    committed_source_reports: set[str],
) -> list[dict[str, Any]]:
    committed_ids = {item["item_id"] for item in committed}
    estimates: list[dict[str, Any]] = []
    for path in sorted(root.glob("databento_cost*.json")):
        relative_path = _relative(path)
        if _normalized_relative(relative_path) in committed_source_reports:
            continue
        payload = _load_json(path)
        if payload.get("mode") != "live":
            continue
        cost = _cost_from_payload(payload)
        if cost is None:
            continue
        item_id = _item_id(payload, path)
        if item_id in committed_ids:
            continue
        estimates.append(
            {
                "item_id": item_id,
                "provider": "Databento",
                "estimated_cost_usd": cost,
                "mode": payload.get("mode"),
                "scenario": payload.get("scenario"),
                "source_path": _relative(path),
            }
        )
    for path in sorted(root.glob("databento_spy_bars_plan*.json")):
        payload = _load_json(path)
        if payload.get("mode") != "plan":
            continue
        cost = _cost_from_payload(payload)
        if cost is None:
            continue
        item_id = _item_id(payload, path)
        if item_id in committed_ids:
            continue
        estimates.append(
            {
                "item_id": item_id,
                "provider": "Databento",
                "estimated_cost_usd": cost,
                "mode": payload.get("mode"),
                "scenario": payload.get("scenario"),
                "source_path": _relative(path),
            }
        )
    for path in sorted(root.glob("h_a2_independent_validation_paid_cost_estimate*.json")):
        relative_path = _relative(path)
        if _normalized_relative(relative_path) in committed_source_reports:
            continue
        payload = _load_json(path)
        if payload.get("mode") != "live_metadata_cost_no_download":
            continue
        cost = _cost_from_payload(payload)
        if cost is None:
            cost_result = payload.get("cost_result")
            cost = _cost_from_payload(cost_result) if isinstance(cost_result, dict) else None
        if cost is None:
            continue
        batch_id = payload.get("batch_id") or path.stem
        item_id = f"h_a2_independent_validation:{batch_id}"
        if item_id in committed_ids:
            continue
        estimates.append(
            {
                "item_id": item_id,
                "provider": "Databento",
                "estimated_cost_usd": cost,
                "mode": payload.get("mode"),
                "scenario": payload.get("experiment_id"),
                "source_path": relative_path,
            }
        )
    return sorted(estimates, key=lambda item: item["item_id"])


def _build_cost_guard_reconciliation(
    stop_threshold_usd: float,
    committed_total: float,
    user_reported_usage: dict[str, Any] | None,
    estimated_only: list[dict[str, Any]],
) -> dict[str, Any]:
    actual_used = user_reported_usage["actual_usage_usd"] if user_reported_usage else None
    actual_remaining = round(stop_threshold_usd - actual_used, 6) if actual_used is not None else None
    conservative_remaining = round(stop_threshold_usd - committed_total, 6)
    estimated_total = round(sum(item["estimated_cost_usd"] for item in estimated_only), 6)
    threshold_breaches = []
    for item in estimated_only:
        projected_total = round(committed_total + item["estimated_cost_usd"], 6)
        if projected_total >= stop_threshold_usd:
            threshold_breaches.append(
                {
                    "item_id": item["item_id"],
                    "estimated_cost_usd": item["estimated_cost_usd"],
                    "projected_known_estimated_cost_usd": projected_total,
                    "source_path": item["source_path"],
                }
            )
    threshold_breaches = sorted(
        threshold_breaches,
        key=lambda item: (item["projected_known_estimated_cost_usd"], item["item_id"]),
        reverse=True,
    )
    return {
        "stop_threshold_usd": stop_threshold_usd,
        "actual_usage_basis": {
            "status": "not_recorded" if actual_used is None else ("blocked" if actual_remaining <= 0 else "pass"),
            "used_usd": actual_used,
            "remaining_usd": actual_remaining,
        },
        "known_committed_estimate_basis": {
            "status": "blocked" if conservative_remaining <= 0 else "pass",
            "used_usd": committed_total,
            "remaining_usd": conservative_remaining,
        },
        "estimated_only_risk": {
            "estimated_only_total_usd": estimated_total,
            "would_exceed_stop_threshold_if_all_estimates_committed": round(committed_total + estimated_total, 6) >= stop_threshold_usd,
            "single_item_threshold_breach_count": len(threshold_breaches),
            "single_item_threshold_breaches": threshold_breaches,
        },
    }


def _load_openrouter_costs(root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    items: list[dict[str, Any]] = []
    unpriced: list[dict[str, Any]] = []
    if not root.exists():
        return items, unpriced
    for path in sorted(root.glob("exp07_prompt*summary*.json")):
        payload = _load_json(path)
        if payload.get("mode") != "live_openrouter":
            continue
        cost = payload.get("openrouter_actual_cost_usd")
        if isinstance(cost, int | float):
            items.append(
                {
                    "item_id": path.stem,
                    "provider": "OpenRouter/DeepSeek",
                    "estimated_cost_usd": round(float(cost), 6),
                    "mode": payload.get("mode"),
                    "scenario": "exp07_prompt_matrix",
                    "assessment_count": payload.get("assessment_count"),
                    "costed_assessment_count": payload.get("openrouter_costed_assessment_count"),
                    "source_path": _relative(path),
                }
            )
        else:
            unpriced.append(
                {
                    "provider": "OpenRouter/DeepSeek",
                    "source_path": _relative(path),
                    "reason": "Live prompt summary does not record `openrouter_actual_cost_usd`; do not include guessed costs in the committed total.",
                }
            )
    if not items and not unpriced:
        unpriced.append(
            {
                "provider": "OpenRouter/DeepSeek",
                "reason": "No live prompt cost artifact found; do not include guessed costs in the committed total.",
            }
        )
    return items, unpriced


def _load_user_reported_usage(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = _load_json(path)
    actual_usage = payload.get("actual_usage_usd")
    if not isinstance(actual_usage, int | float):
        return None
    return {
        "actual_usage_usd": round(float(actual_usage), 6),
        "reported_at_utc": payload.get("reported_at_utc"),
        "source": payload.get("source"),
        "notes": payload.get("notes"),
        "source_path": _relative(path),
    }


def _item_id(payload: dict[str, Any], path: Path) -> str:
    if "spy_bars" in path.stem:
        return f"spy_bars:{_spy_bars_suffix(path.stem)}"
    scenario = payload.get("scenario")
    if isinstance(scenario, str) and scenario:
        suffix = path.stem.removeprefix("databento_download_result_").removeprefix("databento_cost_")
        return f"{scenario}:{suffix}"
    return path.stem


def _spy_bars_suffix(stem: str) -> str:
    for prefix in ("databento_spy_bars_download_result_", "databento_spy_bars_plan_"):
        if stem.startswith(prefix):
            return stem.removeprefix(prefix)
    if stem in {"databento_spy_bars_download_result", "databento_spy_bars_plan"}:
        return "default"
    return stem


def _selected_key_env(payload: dict[str, Any]) -> str | None:
    direct = payload.get("selected_key_env")
    if isinstance(direct, str) and direct:
        return direct
    for container_name in ("cost_guard", "approved_download_scope", "selected_key_policy"):
        container = payload.get(container_name)
        if isinstance(container, dict):
            value = container.get("selected_key_env")
            if isinstance(value, str) and value:
                return value
    return None


def _cost_from_payload(payload: dict[str, Any]) -> float | None:
    cost = payload.get("total_estimated_cost_usd")
    if isinstance(cost, int | float):
        return round(float(cost), 6)
    request = payload.get("request")
    if isinstance(request, dict) and isinstance(request.get("estimated_cost_usd"), int | float):
        return round(float(request["estimated_cost_usd"]), 6)
    return None


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _normalized_relative(path: str) -> str:
    return path.replace("/", "\\").lstrip(".\\")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit known committed paid research/API costs without live provider calls.")
    parser.add_argument("--data-cost-root", type=Path, default=DEFAULT_DATA_COST_ROOT)
    parser.add_argument("--experiment-root", type=Path, default=DEFAULT_EXPERIMENT_ROOT)
    parser.add_argument("--user-reported-usage-path", type=Path, default=None)
    parser.add_argument("--stop-threshold-usd", type=float, default=DEFAULT_STOP_THRESHOLD_USD)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    args = parser.parse_args(argv)

    result = audit_paid_costs(args.data_cost_root, args.stop_threshold_usd, args.experiment_root, args.user_reported_usage_path)
    write_reports(result, args.json_output, args.report_output)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
