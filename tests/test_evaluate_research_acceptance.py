from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "evaluate_research_acceptance.py"


def load_evaluator():
    spec = importlib.util.spec_from_file_location("evaluate_research_acceptance", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load research acceptance evaluator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def complete_e2_report() -> dict:
    return {
        "evidence_tier": "E2",
        "no_oos_tuning": True,
        "mintrl": {"status": "pass", "value": 120},
        "psr": {"status": "pass", "value": 0.97},
        "dsr": {"status": "pass", "value": 0.93},
        "search_log": {"trial_count": 4},
        "metrics": {
            "implementable_pnl": 123.45,
            "cost_drag": 12.34,
            "max_drawdown": -0.08,
        },
        "big_day_dependency_result": {"status": "pass"},
        "regime_trade_counts": {"by_volatility_bucket": {"normal": 60, "high": 60}},
        "benchmark_comparison": {
            "benchmark_variant": "same_trade_calendar_spy",
            "max_drawdown_delta": 0.02,
        },
        "adversarial_review": {"status": "completed", "reviewer": "other-model-or-user"},
    }


class ResearchAcceptanceEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.evaluator = load_evaluator()

    def test_current_project_is_blocked_without_e2_hypothesis(self) -> None:
        result = self.evaluator.evaluate_research_acceptance()

        self.assertEqual("blocked", result["status"])
        self.assertFalse(result["operational_validation_allowed"])
        self.assertFalse(result["paper_trading_allowed"])
        self.assertFalse(result["real_money_allowed"])
        self.assertIn("no_strategy_hypothesis_at_e2_or_higher", result["blockers"])
        self.assertIn("research_readiness_blocked", result["blockers"])
        self.assertTrue(any(item.startswith("readiness:requires_mintrl") for item in result["blockers"]))
        self.assertEqual([], result["candidate_hypotheses"])

    def test_e2_active_hypothesis_can_approve_operational_validation_when_audits_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / "registry.json"
            evidence = root / "evidence.json"
            readiness = root / "readiness.json"
            paid_cost = root / "paid_cost.json"
            report = root / "reports" / "x.json"
            report.parent.mkdir()
            report.write_text(json.dumps(complete_e2_report()), encoding="utf-8")
            registry.write_text(
                json.dumps(
                    {
                        "hypotheses": [
                            {
                                "id": "H-X",
                                "family": "test",
                                "status": "active",
                                "evidence": [{"path": str(report), "evidence_tier": "E2"}],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            evidence.write_text(json.dumps({"status": "pass", "summaries": []}), encoding="utf-8")
            readiness.write_text(json.dumps({"status": "pass", "blockers": [], "checks": []}), encoding="utf-8")
            paid_cost.write_text(json.dumps({"status": "pass"}), encoding="utf-8")

            result = self.evaluator.evaluate_research_acceptance(
                registry_path=registry,
                evidence_audit_path=evidence,
                readiness_audit_path=readiness,
                paid_cost_audit_path=paid_cost,
            )

        self.assertEqual("approved_for_operational_validation", result["status"])
        self.assertTrue(result["operational_validation_allowed"])
        self.assertTrue(result["paper_trading_allowed"])
        self.assertFalse(result["real_money_allowed"])
        self.assertEqual([], result["blockers"])
        self.assertEqual("H-X", result["candidate_hypotheses"][0]["id"])

    def test_e2_candidate_missing_acceptance_gate_evidence_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / "registry.json"
            evidence = root / "evidence.json"
            readiness = root / "readiness.json"
            paid_cost = root / "paid_cost.json"
            report = root / "reports" / "x.json"
            report.parent.mkdir()
            report.write_text(json.dumps({"evidence_tier": "E2", "status": "complete"}), encoding="utf-8")
            registry.write_text(
                json.dumps(
                    {
                        "hypotheses": [
                            {
                                "id": "H-X",
                                "family": "test",
                                "status": "active",
                                "evidence": [{"path": str(report), "evidence_tier": "E2"}],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            evidence.write_text(json.dumps({"status": "pass", "summaries": []}), encoding="utf-8")
            readiness.write_text(json.dumps({"status": "pass", "blockers": [], "checks": []}), encoding="utf-8")
            paid_cost.write_text(json.dumps({"status": "pass"}), encoding="utf-8")

            result = self.evaluator.evaluate_research_acceptance(
                registry_path=registry,
                evidence_audit_path=evidence,
                readiness_audit_path=readiness,
                paid_cost_audit_path=paid_cost,
            )

        self.assertEqual("blocked", result["status"])
        self.assertFalse(result["operational_validation_allowed"])
        self.assertIn("candidate:H-X:mintrl_psr_dsr_handling", result["blockers"])
        self.assertIn("candidate:H-X:big_day_dependency_survival", result["blockers"])
        self.assertIn("candidate:H-X:adversarial_review_completed", result["blockers"])
        self.assertEqual("H-X", result["candidate_gate_results"][0]["hypothesis_id"])

    def test_e2_candidate_with_nonhard_readiness_blocker_is_scope_restricted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / "registry.json"
            evidence = root / "evidence.json"
            readiness = root / "readiness.json"
            paid_cost = root / "paid_cost.json"
            report = root / "reports" / "x.json"
            report.parent.mkdir()
            report.write_text(json.dumps(complete_e2_report()), encoding="utf-8")
            registry.write_text(
                json.dumps(
                    {
                        "hypotheses": [
                            {
                                "id": "H-X",
                                "family": "test",
                                "status": "active",
                                "evidence": [{"path": str(report), "evidence_tier": "E2"}],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            evidence.write_text(json.dumps({"status": "pass", "summaries": []}), encoding="utf-8")
            readiness.write_text(json.dumps({"status": "blocked", "blockers": ["research_log_worktree_not_clean"], "checks": []}), encoding="utf-8")
            paid_cost.write_text(json.dumps({"status": "pass"}), encoding="utf-8")

            result = self.evaluator.evaluate_research_acceptance(
                registry_path=registry,
                evidence_audit_path=evidence,
                readiness_audit_path=readiness,
                paid_cost_audit_path=paid_cost,
            )

        self.assertEqual("scope_restricted", result["status"])
        self.assertTrue(result["operational_validation_allowed"])
        self.assertTrue(result["paper_trading_allowed"])
        self.assertFalse(result["real_money_allowed"])
        self.assertEqual([], result["blockers"])

    def test_main_writes_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "acceptance.json"
            report = Path(tmp) / "acceptance.md"

            returncode = self.evaluator.main(["--json-output", str(output), "--report-output", str(report)])

            self.assertEqual(0, returncode)
            result = json.loads(output.read_text(encoding="utf-8"))
            markdown = report.read_text(encoding="utf-8")
            self.assertIn(result["status"], {"blocked", "scope_restricted", "approved_for_operational_validation"})
            self.assertIn("Research Acceptance Evaluation", markdown)
            self.assertIn("Gate Requirements", markdown)


if __name__ == "__main__":
    unittest.main()
