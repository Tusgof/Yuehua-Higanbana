from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any
from datetime import date


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ESTIMATOR_PATH = PROJECT_ROOT / "scripts" / "estimate_databento_cost.py"
DEFAULT_SOURCE = PROJECT_ROOT / "reports" / "data_cost" / "databento_cost_plan.json"
DEFAULT_REPORT = PROJECT_ROOT / "reports" / "data_cost" / "databento_cost_projection.md"


def load_estimator():
    spec = importlib.util.spec_from_file_location("estimate_databento_cost", ESTIMATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load Databento estimator")
    module = importlib.util.module_from_spec(spec)
    sys.modules["estimate_databento_cost"] = module
    spec.loader.exec_module(module)
    return module


def project_costs(
    source_path: Path = DEFAULT_SOURCE,
    target_scenario: str | None = None,
    target_start_date: date | None = None,
    target_end_date: date | None = None,
    target_window_profile: str = "entry_close",
    target_scenario_label: str | None = None,
) -> dict[str, Any]:
    source = json.loads(source_path.read_text(encoding="utf-8"))
    successful_costs = [
        float(row["estimated_cost_usd"])
        for row in source.get("requests", [])
        if row.get("estimated_cost_usd") is not None
    ]
    if not successful_costs:
        raise ValueError(f"{source_path} has no successful live cost estimates")

    average_cost = sum(successful_costs) / len(successful_costs)
    estimator = load_estimator()
    projections: dict[str, Any] = {}
    scenarios = [target_scenario] if target_scenario else estimator.SCENARIOS
    for scenario in scenarios:
        requests = estimator.build_cost_requests(
            scenario,
            start_date=target_start_date,
            end_date=target_end_date,
            window_profile=target_window_profile,
            scenario_label=target_scenario_label,
        )
        projection_key = target_scenario_label or scenario
        projected_cost = average_cost * len(requests)
        projections[projection_key] = {
            "request_count": len(requests),
            "projected_cost_usd": round(projected_cost, 6),
        }

    return {
        "source_path": str(source_path),
        "source_mode": source.get("mode"),
        "source_scenario": _source_scenario(source),
        "source_total_estimated_cost_usd": source.get("total_estimated_cost_usd"),
        "source_successful_request_count": len(successful_costs),
        "source_error_count": len(source.get("errors", [])),
        "average_cost_per_window_usd": round(average_cost, 8),
        "projections": projections,
    }


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Databento Cost Projection",
        "",
        f"- **Source report**: `{result['source_path']}`",
        f"- **Source scenario**: `{result['source_scenario']}`",
        f"- **Source mode**: `{result['source_mode']}`",
        f"- **Source successful request count**: {result['source_successful_request_count']}",
        f"- **Source error count**: {result['source_error_count']}",
        f"- **Average cost per research window**: `${result['average_cost_per_window_usd']}`",
        "",
        "## Projection",
        "",
        "| Scenario | Requests | Projected Cost USD |",
        "|:--|--:|--:|",
    ]
    for scenario, data in result["projections"].items():
        lines.append(f"| `{scenario}` | {data['request_count']} | `${data['projected_cost_usd']}` |")
    lines.extend(
        [
            "",
            "## Use Rule",
            "",
            "- This is a projection from live one-month cost estimates, not a Databento quote.",
            "- Run live `get_cost` for the next wider scenario only after reviewing this projection.",
            "- Do not download data until the live cost report for that exact scope is accepted.",
            "",
        ]
    )
    return "\n".join(lines)


def _source_scenario(source: dict[str, Any]) -> str:
    scenarios = source.get("summary", {}).get("scenarios", {})
    if len(scenarios) == 1:
        return next(iter(scenarios))
    return ",".join(sorted(scenarios)) if scenarios else "unknown"


def main() -> int:
    parser = argparse.ArgumentParser(description="Project Databento costs from a live cost estimate report.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--target-scenario", choices=["one_day_sample", "one_month_pilot", "oos_2024_2025", "full_research"])
    parser.add_argument("--target-scenario-label")
    parser.add_argument("--target-start-date", type=date.fromisoformat)
    parser.add_argument("--target-end-date", type=date.fromisoformat)
    parser.add_argument("--target-window-profile", choices=["entry_close", "intraday_exit_30m"], default="entry_close")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--json-report-path", type=Path)
    args = parser.parse_args()

    result = project_costs(
        args.source,
        target_scenario=args.target_scenario,
        target_start_date=args.target_start_date,
        target_end_date=args.target_end_date,
        target_window_profile=args.target_window_profile,
        target_scenario_label=args.target_scenario_label,
    )
    args.report_path.parent.mkdir(parents=True, exist_ok=True)
    args.report_path.write_text(render_markdown(result), encoding="utf-8")
    if args.json_report_path:
        args.json_report_path.parent.mkdir(parents=True, exist_ok=True)
        args.json_report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
