from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_PATH = PROJECT_ROOT / "experiments" / "experiment_manifests.json"
DEFAULT_GUARDRAIL_PATH = PROJECT_ROOT / "experiments" / "m3_experiment_guardrails.json"
DEFAULT_JSON_OUTPUT = PROJECT_ROOT / "reports" / "m3_experiment_guardrails_audit.json"
DEFAULT_REPORT_OUTPUT = PROJECT_ROOT / "reports" / "m3_experiment_guardrails_audit.md"

ALLOWED_SPLIT_METHODS = {"chronological", "expanding_window", "rolling_window", "purged_embargoed"}
FORBIDDEN_SPLIT_METHODS = {"random", "shuffle", "shuffled", "kfold", "k-fold", "random_kfold", "random-k-fold"}
EXPECTED_TRAIN_START = "2022-05-11"
EXPECTED_TRAIN_END = "2023-12-31"
EXPECTED_OOS_START = "2024-01-01"


def validate_guardrails(
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    guardrail_path: Path = DEFAULT_GUARDRAIL_PATH,
) -> dict[str, Any]:
    manifests = _load_json(manifest_path)
    guardrails = _load_json(guardrail_path)
    manifest_ids = [manifest.get("experiment_id") for manifest in manifests]
    guardrail_ids = set(guardrails.get("experiments", {}))
    blockers: list[str] = []
    warnings: list[str] = []
    experiments: list[dict[str, Any]] = []

    if len(manifest_ids) != len(set(manifest_ids)):
        blockers.append("duplicate_experiment_id_in_manifest")

    for experiment_id in sorted(guardrail_ids - set(manifest_ids)):
        blockers.append(f"guardrail_without_manifest:{experiment_id}")
    for experiment_id in sorted(set(manifest_ids) - guardrail_ids):
        blockers.append(f"manifest_without_guardrail:{experiment_id}")

    for manifest in manifests:
        experiment_id = str(manifest.get("experiment_id"))
        guardrail = guardrails.get("experiments", {}).get(experiment_id, {})
        merged = _merge_default_policies(guardrails.get("defaults", {}), guardrail)
        experiment_blockers, experiment_warnings = _validate_experiment(manifest, merged)
        blockers.extend(f"{experiment_id}:{item}" for item in experiment_blockers)
        warnings.extend(f"{experiment_id}:{item}" for item in experiment_warnings)
        experiments.append(
            {
                "experiment_id": experiment_id,
                "requires_search_log_policy": bool(guardrail.get("requires_search_log_policy")),
                "requires_strike_mapping_policy": bool(guardrail.get("requires_strike_mapping_policy")),
                "validation_policy": merged.get("validation_policy"),
                "search_log_policy": merged.get("search_log_policy") if guardrail.get("requires_search_log_policy") else None,
                "strike_mapping_policy": merged.get("strike_mapping_policy") if guardrail.get("requires_strike_mapping_policy") else None,
                "blockers": experiment_blockers,
                "warnings": experiment_warnings,
            }
        )

    return {
        "status": "blocked" if blockers else "pass",
        "blockers": blockers,
        "warnings": warnings,
        "manifest_path": str(manifest_path),
        "guardrail_path": str(guardrail_path),
        "experiment_count": len(manifests),
        "experiments": experiments,
    }


def write_reports(
    result: dict[str, Any],
    json_output: Path = DEFAULT_JSON_OUTPUT,
    report_output: Path = DEFAULT_REPORT_OUTPUT,
) -> None:
    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# M3 Experiment Guardrails Audit",
        "",
        f"- Status: `{result['status']}`",
        f"- Blocker count: {len(result['blockers'])}",
        f"- Warning count: {len(result['warnings'])}",
        f"- Experiment count: {result['experiment_count']}",
        f"- Manifest: `{result['manifest_path']}`",
        f"- Guardrails: `{result['guardrail_path']}`",
        "",
        "## Experiments",
        "",
        "| Experiment | Search log policy | Strike mapping | Split method | Blockers |",
        "|:--|:--:|:--:|:--|:--|",
    ]
    for item in result["experiments"]:
        validation_policy = item.get("validation_policy") or {}
        blockers = ", ".join(item["blockers"]) if item["blockers"] else "None"
        lines.append(
            "| `{experiment_id}` | {search} | {strike} | `{split}` | {blockers} |".format(
                experiment_id=item["experiment_id"],
                search=item["requires_search_log_policy"],
                strike=item["requires_strike_mapping_policy"],
                split=validation_policy.get("split_method"),
                blockers=blockers,
            )
        )

    lines.extend(["", "## Blockers", ""])
    if result["blockers"]:
        lines.extend(f"- `{blocker}`" for blocker in result["blockers"])
    else:
        lines.append("- None")

    lines.extend(["", "## Warnings", ""])
    if result["warnings"]:
        lines.extend(f"- `{warning}`" for warning in result["warnings"])
    else:
        lines.append("- None")

    report_output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _validate_experiment(manifest: dict[str, Any], guardrail: dict[str, Any]) -> tuple[list[str], list[str]]:
    blockers: list[str] = []
    warnings: list[str] = []
    blockers.extend(_validate_windows(manifest))
    blockers.extend(_validate_validation_policy(guardrail.get("validation_policy", {})))

    if guardrail.get("requires_search_log_policy") is True:
        blockers.extend(_validate_search_log_policy(guardrail.get("search_log_policy", {}), str(manifest.get("experiment_id"))))
    elif _has_search_like_metrics(manifest):
        warnings.append("search_like_metrics_without_required_search_policy")

    if guardrail.get("requires_strike_mapping_policy") is True:
        blockers.extend(_validate_strike_mapping_policy(guardrail.get("strike_mapping_policy", {})))

    return blockers, warnings


def _validate_windows(manifest: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    data_window = manifest.get("data_window", {})
    train_window = manifest.get("train_window", {})
    oos_window = manifest.get("oos_window", {})
    try:
        data_start = date.fromisoformat(data_window["start"])
        data_end = date.fromisoformat(data_window["end"])
        train_start = date.fromisoformat(train_window["start"])
        train_end = date.fromisoformat(train_window["end"])
        oos_start = date.fromisoformat(oos_window["start"])
        oos_end = date.fromisoformat(oos_window["end"])
    except (KeyError, TypeError, ValueError) as exc:
        return [f"invalid_window_dates:{type(exc).__name__}"]

    if not data_start <= train_start <= train_end < oos_start <= oos_end <= data_end:
        blockers.append("non_chronological_windows")
    if train_window.get("start") != EXPECTED_TRAIN_START:
        blockers.append(f"unexpected_train_start:{train_window.get('start')}")
    if train_window.get("end") != EXPECTED_TRAIN_END:
        blockers.append(f"unexpected_train_end:{train_window.get('end')}")
    if oos_window.get("start") != EXPECTED_OOS_START:
        blockers.append(f"unexpected_oos_start:{oos_window.get('start')}")
    if manifest.get("parameters_locked_before_oos") is not True:
        blockers.append("parameters_not_locked_before_oos")
    return blockers


def _validate_validation_policy(policy: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    split_method = str(policy.get("split_method", "")).lower()
    allowed = set(policy.get("allowed_split_methods") or ALLOWED_SPLIT_METHODS)
    if split_method in FORBIDDEN_SPLIT_METHODS:
        blockers.append(f"forbidden_split_method:{split_method}")
    if split_method not in allowed or split_method not in ALLOWED_SPLIT_METHODS:
        blockers.append(f"unsupported_split_method:{split_method}")
    for key in ("forbid_random_split", "forbid_oos_tuning", "fit_only_before_decision_timestamp"):
        if policy.get(key) is not True:
            blockers.append(f"validation_policy.{key}_must_be_true")
    return blockers


def _validate_search_log_policy(policy: dict[str, Any], experiment_id: str) -> list[str]:
    blockers: list[str] = []
    for key in (
        "trial_count_required",
        "parameter_grid_required",
        "record_all_trials_required",
        "dsr_required_if_selecting_best_sharpe",
        "dsr_blocker_allowed_if_search_log_incomplete",
    ):
        if policy.get(key) is not True:
            blockers.append(f"search_log_policy.{key}_must_be_true")
    path_template = policy.get("search_log_path_template")
    if not isinstance(path_template, str) or "{experiment_id}" not in path_template:
        blockers.append("search_log_policy.search_log_path_template_missing_experiment_id")
    else:
        rendered = path_template.format(experiment_id=experiment_id)
        if not rendered.startswith("reports/experiments/search_logs/") or not rendered.endswith(".jsonl"):
            blockers.append("search_log_policy.search_log_path_template_invalid_location")
    return blockers


def _validate_strike_mapping_policy(policy: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if policy.get("method") != "nearest_discrete_strike_rounding":
        blockers.append(f"strike_mapping_policy.unsupported_method:{policy.get('method')}")
    if not policy.get("tie_breaker"):
        blockers.append("strike_mapping_policy.tie_breaker_required")
    if policy.get("interpolation_allowed_for_research_only") is not False:
        blockers.append("strike_mapping_policy.interpolation_must_not_be_default")
    if policy.get("disclose_in_report") is not True:
        blockers.append("strike_mapping_policy.disclose_in_report_must_be_true")
    return blockers


def _has_search_like_metrics(manifest: dict[str, Any]) -> bool:
    metrics = {str(metric) for metric in manifest.get("metrics", [])}
    return bool(metrics & {"sharpe", "sortino", "cost_drag", "win_rate", "expected_value", "premium_yield"})


def _merge_default_policies(defaults: dict[str, Any], guardrail: dict[str, Any]) -> dict[str, Any]:
    merged = json.loads(json.dumps(defaults))
    for key, value in guardrail.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key].update(value)
        else:
            merged[key] = value
    return merged


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate M3 experiment guardrails for search logs, chronological split, and strike mapping.")
    parser.add_argument("--manifest-path", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--guardrail-path", type=Path, default=DEFAULT_GUARDRAIL_PATH)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    args = parser.parse_args(argv)

    result = validate_guardrails(args.manifest_path, args.guardrail_path)
    write_reports(result, args.json_output, args.report_output)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
