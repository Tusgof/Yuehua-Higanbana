from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "report_project_state.py"


def load_reporter():
    spec = importlib.util.spec_from_file_location("report_project_state", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load project-state reporter")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReportProjectStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.reporter = load_reporter()

    def test_current_project_state_contains_required_sections(self) -> None:
        state = self.reporter.build_project_state()

        self.assertIn(state["status"], {"pass", "blocked", "warning"})
        self.assertEqual(8, len(state["hypotheses"]))
        self.assertIn("remaining_before_stop_usd", state["paid_cost"])
        self.assertIn("next_safe_actions", state["readiness"])
        self.assertIn("gdelt_command_plan_status", state["news_gdelt"])

    def test_markdown_render_includes_key_headings(self) -> None:
        state = self.reporter.build_project_state()
        markdown = self.reporter.render_markdown(state)

        self.assertIn("# Higanbana Project State", markdown)
        self.assertIn("## Hypotheses", markdown)
        self.assertIn("## Next Safe Actions", markdown)

    def test_cli_json_mode_is_read_only_and_parseable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = write_fixture_audits(root)

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--json",
                    "--hypothesis-audit-path",
                    str(paths["hypothesis"]),
                    "--evidence-audit-path",
                    str(paths["evidence"]),
                    "--readiness-audit-path",
                    str(paths["readiness"]),
                    "--paid-cost-audit-path",
                    str(paths["paid_cost"]),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            state = json.loads(completed.stdout)

        self.assertEqual("blocked", state["status"])
        self.assertEqual("H-X1", state["hypotheses"][0]["id"])
        self.assertEqual(20.0, state["paid_cost"]["remaining_before_stop_usd"])


def write_fixture_audits(root: Path) -> dict[str, Path]:
    hypothesis = root / "hypothesis.json"
    evidence = root / "evidence.json"
    readiness = root / "readiness.json"
    paid_cost = root / "paid_cost.json"

    hypothesis.write_text(
        json.dumps(
            {
                "status": "pass",
                "hypotheses": [
                    {
                        "id": "H-X1",
                        "family": "subsystem_a",
                        "status": "active",
                        "evidence_tiers": ["E1"],
                        "blockers": [],
                        "warnings": [],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    evidence.write_text(
        json.dumps({"status": "pass", "summary_count": 1, "blockers": [], "warnings": ["legacy"], "strict_missing_metadata": False}),
        encoding="utf-8",
    )
    readiness.write_text(
        json.dumps(
            {
                "status": "blocked",
                "blockers": ["requires_real_news_archive"],
                "next_safe_actions": ["Collect real timestamp-clean news cases."],
                "checks": [
                    {"name": "news", "status": "blocked"},
                    {"name": "gdelt_capture_status", "status": "blocked", "status_counts": {"blocked": 1}},
                    {
                        "name": "gdelt_command_plan",
                        "status": "blocked",
                        "retry_pressure_status": "cooldown_recommended",
                        "not_attempted_count": 2,
                        "next_unattempted_trade_date": "2023-04-14",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    paid_cost.write_text(
        json.dumps(
            {
                "status": "pass",
                "cost_guard_basis": "user_reported_actual_usage",
                "cost_guard_used_usd": 105.0,
                "stop_threshold_usd": 125.0,
                "remaining_before_stop_usd": 20.0,
                "budget_policy": {"cap_extension_method": "real_payment_on_existing_databento_account_only"},
            }
        ),
        encoding="utf-8",
    )
    return {"hypothesis": hypothesis, "evidence": evidence, "readiness": readiness, "paid_cost": paid_cost}


if __name__ == "__main__":
    unittest.main()
