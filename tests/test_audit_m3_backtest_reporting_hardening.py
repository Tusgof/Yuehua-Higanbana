from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "audit_m3_backtest_reporting_hardening.py"


def load_auditor():
    spec = importlib.util.spec_from_file_location("audit_m3_backtest_reporting_hardening", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load M3 hardening auditor")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AuditM3BacktestReportingHardeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.auditor = load_auditor()

    def test_current_artifacts_pass(self) -> None:
        result = self.auditor.audit_hardening()

        self.assertEqual("pass", result["status"])
        self.assertEqual([], result["blockers"])

    def test_blocks_missing_pnl_model_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_valid_case(Path(tmp))
            pnl_summary = json.loads(paths["pnl_summary"].read_text(encoding="utf-8"))
            del pnl_summary["total_implementable_pnl"]
            paths["pnl_summary"].write_text(json.dumps(pnl_summary), encoding="utf-8")

            result = self.audit_paths(paths)

        self.assertEqual("blocked", result["status"])
        self.assertIn("pnl_model.missing:total_implementable_pnl", result["blockers"])

    def test_blocks_search_log_line_count_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_valid_case(Path(tmp))
            lines = paths["search_log"].read_text(encoding="utf-8").splitlines()
            paths["search_log"].write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")

            result = self.audit_paths(paths)

        self.assertEqual("blocked", result["status"])
        self.assertIn("search_log.line_count_mismatch:1!=2", result["blockers"])

    def test_blocks_guardrail_audit_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_valid_case(Path(tmp))
            guardrail = json.loads(paths["guardrail_audit"].read_text(encoding="utf-8"))
            guardrail["status"] = "blocked"
            guardrail["blockers"] = ["fixture_blocker"]
            paths["guardrail_audit"].write_text(json.dumps(guardrail), encoding="utf-8")

            result = self.audit_paths(paths)

        self.assertEqual("blocked", result["status"])
        self.assertIn("guardrail_audit.unexpected_status:blocked", result["blockers"])
        self.assertIn("guardrail_audit.has_blockers", result["blockers"])

    def audit_paths(self, paths: dict[str, Path]) -> dict[str, object]:
        return self.auditor.audit_hardening(
            paths["pnl_summary"],
            paths["pnl_report"],
            paths["sensitivity_summary"],
            paths["sensitivity_report"],
            paths["search_log"],
            paths["guardrail_audit"],
        )


def write_valid_case(root: Path) -> dict[str, Path]:
    paths = {
        "pnl_summary": root / "pnl_summary.json",
        "pnl_report": root / "pnl_report.md",
        "sensitivity_summary": root / "sensitivity_summary.json",
        "sensitivity_report": root / "sensitivity_report.md",
        "search_log": root / "search_log.jsonl",
        "guardrail_audit": root / "guardrail_audit.json",
    }
    paths["pnl_summary"].write_text(json.dumps(valid_pnl_summary()), encoding="utf-8")
    paths["pnl_report"].write_text(
        "implementable_pnl mid_pnl cost drag under-sampled underpowered big-day",
        encoding="utf-8",
    )
    paths["sensitivity_summary"].write_text(json.dumps(valid_sensitivity_summary()), encoding="utf-8")
    paths["sensitivity_report"].write_text("search log DSR trial parameter", encoding="utf-8")
    paths["search_log"].write_text(
        "\n".join(json.dumps(record) for record in valid_search_records()) + "\n",
        encoding="utf-8",
    )
    paths["guardrail_audit"].write_text(
        json.dumps({"status": "pass", "blockers": [], "experiment_count": 10}),
        encoding="utf-8",
    )
    return paths


def valid_pnl_summary() -> dict[str, object]:
    return {
        "total_mid_pnl": 10.0,
        "total_implementable_pnl": 8.0,
        "total_cost_drag": 2.0,
        "fee_per_contract": 0.64,
        "fill_model": "half_spread",
        "pnl_model": {
            "mid_pnl": "Entry and exit at mid price.",
            "implementable_pnl": "Bid/ask and fees.",
        },
        "sample_adequacy": {
            "closed_trades": 2,
            "labels": ["under-sampled", "underpowered"],
            "mintrl_status": "pending_return_distribution",
            "psr_status": "pending_return_distribution",
            "power_note": "Diagnostic only.",
        },
        "big_day_dependency": {
            "method": "remove_top_and_bottom_5pct_by_implementable_pnl",
            "original_closed_trades": 2,
            "removed_trade_count": 2,
            "retained_closed_trades": 0,
            "retained_total_implementable_pnl": 0.0,
            "status": "pass",
        },
    }


def valid_sensitivity_summary() -> dict[str, object]:
    return {
        "scenario_count": 2,
        "scenarios": [{"trial_index": 1}, {"trial_index": 2}],
        "parameter_grid": {"fill_model": ["mid", "half_spread"]},
        "search_log": {"all_trials_recorded": True, "trial_count": 2},
        "selection_rule": {"acceptance_use": "diagnostic_only_not_oos_tuning"},
        "dsr_assessment": {
            "status": "blocked",
            "reason": "Under-sampled diagnostic.",
            "trial_count": 2,
            "required_before_acceptance": ["full return distribution"],
        },
    }


def valid_search_records() -> list[dict[str, object]]:
    return [
        {
            "record_type": "parameter_search_trial",
            "trial_index": 1,
            "parameters": {"fill_model": "mid"},
            "metrics": {"total_net_pnl": 10.0},
        },
        {
            "record_type": "parameter_search_trial",
            "trial_index": 2,
            "parameters": {"fill_model": "half_spread"},
            "metrics": {"total_net_pnl": 8.0},
        },
    ]


if __name__ == "__main__":
    unittest.main()
