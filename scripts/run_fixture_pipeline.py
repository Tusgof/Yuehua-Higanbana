from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_step(name: str, args: list[str]) -> dict[str, object]:
    env = os.environ.copy()
    if name == "unit_tests":
        env["SPY0DTE_FIXTURE_PIPELINE_CHILD"] = "1"
    completed = subprocess.run(
        [sys.executable, *args],
        cwd=PROJECT_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "name": name,
        "command": " ".join([Path(sys.executable).name, *args]),
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def main() -> int:
    steps = [
        ("validate_m2_contracts", ["scripts/validate_m2_contracts.py"]),
        ("validate_exp07_policy_cases", ["scripts/validate_exp07_policy_cases.py"]),
        ("evaluate_exp07_acceptance", ["scripts/evaluate_exp07_acceptance.py"]),
        ("validate_exp07_strategy_ablation_plan", ["scripts/validate_exp07_strategy_ablation_plan.py"]),
        ("run_exp07_strategy_ablation_status", ["scripts/run_exp07_strategy_ablation.py"]),
        ("validate_m3_experiment_guardrails", ["scripts/validate_m3_experiment_guardrails.py"]),
        ("audit_m3_backtest_reporting_hardening", ["scripts/audit_m3_backtest_reporting_hardening.py"]),
        ("validate_macro_calendar_sources", ["scripts/validate_macro_calendar_sources.py"]),
        (
            "macro_calendar_capture_dry_run",
            [
                "scripts/capture_macro_calendar_snapshots.py",
                "--as-of-date",
                "2024-01-03",
            ],
        ),
        (
            "convert_macro_calendar_capture_check",
            [
                "scripts/convert_macro_calendar_capture.py",
                "--capture-root",
                "data/raw/spy_0dte/macro_calendar/2026-06-30",
                "--output-path",
                "build/macro_calendar_capture_convert/official_macro_calendar_2026-06-30.csv",
            ],
        ),
        (
            "import_converted_macro_calendar_capture",
            [
                "scripts/import_macro_calendar_snapshots.py",
                "--snapshot-path",
                "build/macro_calendar_capture_convert/official_macro_calendar_2026-06-30.csv",
                "--output-root",
                "build/macro_calendar_capture_import",
            ],
        ),
        ("audit_macro_calendar_coverage", ["scripts/audit_macro_calendar_coverage.py"]),
        (
            "plan_macro_calendar_capture_commands",
            [
                "scripts/plan_macro_calendar_capture_commands.py",
                "--start-year",
                "2022",
                "--end-year",
                "2025",
            ],
        ),
        (
            "audit_macro_calendar_raw_archive",
            [
                "scripts/audit_macro_calendar_raw_archive.py",
                "--start-year",
                "2022",
                "--end-year",
                "2025",
            ],
        ),
        (
            "vix_vxv_capture_dry_run",
            [
                "scripts/capture_vix_vxv_cboe.py",
                "--as-of-date",
                "2026-06-30",
            ],
        ),
        (
            "import_vix_vxv_cboe",
            [
                "scripts/import_vix_vxv_cboe.py",
                "--capture-root",
                "data/raw/spy_0dte/vix_vxv/2026-06-30",
                "--start-date",
                "2022-01-01",
                "--end-date",
                "2026-06-30",
            ],
        ),
        (
            "audit_vix_vxv_coverage",
            [
                "scripts/audit_vix_vxv_coverage.py",
                "--as-of-date",
                "2026-06-30",
            ],
        ),
        ("validate_news_sources", ["scripts/validate_news_sources.py"]),
        (
            "gdelt_news_capture_dry_run",
            [
                "scripts/capture_gdelt_news_snapshots.py",
                "--decision-time-et",
                "2024-01-03T09:30:00-05:00",
                "--max-records",
                "5",
            ],
        ),
        ("plan_gdelt_news_capture_commands", ["scripts/plan_gdelt_news_capture_commands.py"]),
        ("plan_exp07_real_news_cases", ["scripts/plan_exp07_real_news_cases.py"]),
        ("validate_exp07_real_news_case_plan", ["scripts/validate_exp07_real_news_case_plan.py"]),
        ("audit_news_coverage", ["scripts/audit_news_coverage.py"]),
        ("audit_paid_costs", ["scripts/audit_paid_costs.py"]),
        ("audit_strategy_data_readiness", ["scripts/audit_strategy_data_readiness.py"]),
        ("validate_hypothesis_registry", ["scripts/validate_hypothesis_registry.py"]),
        ("validate_evidence_tiers", ["scripts/validate_evidence_tiers.py"]),
        ("validate_h_g1_regime_date_set", ["scripts/validate_h_g1_regime_date_set.py"]),
        ("audit_research_readiness", ["scripts/audit_research_readiness.py"]),
        ("audit_research_logs", ["scripts/audit_research_logs.py"]),
        (
            "import_macro_calendar_snapshot_fixture",
            [
                "scripts/import_macro_calendar_snapshots.py",
                "--output-root",
                "build/macro_calendar_fixture",
            ],
        ),
        (
            "import_news_snapshot_fixture",
            [
                "scripts/import_news_snapshots.py",
                "--output-root",
                "build/news_fixture",
            ],
        ),
        (
            "import_gdelt_news_capture_directory_fixture",
            [
                "scripts/import_gdelt_news_capture_directory.py",
                "--input-dir",
                "tests/fixtures/news_snapshots",
                "--pattern",
                "gdelt_news_sample.csv",
                "--output-root",
                "build/news_gdelt_capture_import",
            ],
        ),
        ("validate_provider_samples", ["scripts/provider_adapters.py"]),
        (
            "databento_cost_dry_run",
            [
                "scripts/estimate_databento_cost.py",
                "--scenario",
                "one_day_sample",
                "--report-path",
                "reports/data_cost/databento_cost_dry_run.md",
            ],
        ),
        (
            "databento_cache_audit",
            [
                "scripts/audit_databento_cache.py",
                "--plan-path",
                "reports/data_cost/databento_download_plan.json",
                "--report-path",
                "reports/data_cost/databento_cache_audit.md",
                "--json-report-path",
                "reports/data_cost/databento_cache_audit.json",
            ],
        ),
        (
            "import_provider_sample_fixture",
            [
                "scripts/import_provider_sample.py",
                "--provider",
                "optionsdx",
                "--raw-path",
                "tests/fixtures/provider_samples/optionsdx_option_quote_sample.csv",
                "--output-root",
                "build/provider_sample_fixture",
            ],
        ),
        ("import_m3_fixture", ["scripts/import_m3_fixture.py"]),
        ("generate_m6_reports", ["scripts/experiment_runner_m6.py"]),
        ("unit_tests", ["-m", "unittest", "discover", "-s", "tests"]),
    ]
    results = [run_step(name, args) for name, args in steps]
    failed = [result for result in results if result["returncode"] != 0]
    summary = {
        "status": "fail" if failed else "pass",
        "project_root": str(PROJECT_ROOT),
        "steps": results,
        "important_outputs": {
            "final_review": str(PROJECT_ROOT / "reports" / "final_research_review.md"),
            "user_inputs": str(PROJECT_ROOT / "docs" / "NEXT_USER_INPUTS.md"),
            "paid_cost": str(PROJECT_ROOT / "reports" / "data_cost" / "paid_cost_audit.md"),
            "strategy_data_readiness": str(PROJECT_ROOT / "reports" / "strategy_data_readiness_audit.md"),
            "hypothesis_registry": str(PROJECT_ROOT / "reports" / "hypothesis_registry_audit.md"),
            "evidence_tiers": str(PROJECT_ROOT / "reports" / "evidence_tier_audit.md"),
            "h_g1_regime_date_set": str(PROJECT_ROOT / "experiments" / "h_g1_gamma_regime_date_set_preregistration.json"),
            "research_readiness": str(PROJECT_ROOT / "reports" / "research_readiness_audit.md"),
            "research_logs": str(PROJECT_ROOT / "reports" / "research_log_audit.md"),
        },
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
