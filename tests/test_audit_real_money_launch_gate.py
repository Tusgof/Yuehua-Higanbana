from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "audit_real_money_launch_gate.py"


def load_audit_module():
    spec = importlib.util.spec_from_file_location("audit_real_money_launch_gate", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load launch gate audit module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RealMoneyLaunchGateAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.audit = load_audit_module()

    def test_current_project_launch_gate_is_blocked(self) -> None:
        result = self.audit.audit_real_money_launch_gate()

        self.assertEqual("blocked", result["status"])
        self.assertFalse(result["real_money_allowed"])
        self.assertIn("research_acceptance_real_money_not_allowed", result["blockers"])
        self.assertIn("ibkr_transmit_disabled", result["blockers"])
        self.assertIn("kill_switch_enabled", result["blockers"])
        self.assertIn("checklist_missing:user_real_money_approval_recorded", result["blockers"])

    def test_gate_passes_only_when_every_required_input_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            acceptance = write_json(root / "acceptance.json", {"status": "approved_for_operational_validation", "real_money_allowed": True})
            checklist = write_json(
                root / "checklist.json",
                {
                    "research_acceptance_passed": True,
                    "options_permission_approved": True,
                    "cash_account_constraints_documented": True,
                    "defined_risk_only_confirmed": True,
                    "user_real_money_approval_recorded": True,
                    "kill_switch_tested": True,
                    "forced_close_tested": True,
                    "backup_close_order_plan_tested": True,
                    "first_live_max_risk_usd": 20.0,
                },
            )
            ibkr = write_json(
                root / "ibkr.json",
                {
                    "mode": "live",
                    "transmit_enabled": True,
                    "options_permission_confirmed": True,
                    "account_type": "cash",
                    "forced_close_time_et": "15:45:00",
                },
            )
            kill_switch = write_json(root / "kill_switch.json", {"enabled": False})

            result = self.audit.audit_real_money_launch_gate(
                acceptance_path=acceptance,
                checklist_path=checklist,
                ibkr_config_path=ibkr,
                kill_switch_path=kill_switch,
            )

        self.assertEqual("pass", result["status"])
        self.assertTrue(result["real_money_allowed"])
        self.assertEqual([], result["blockers"])

    def test_main_writes_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "launch_gate.json"
            report = Path(tmp) / "launch_gate.md"

            returncode = self.audit.main(["--json-output", str(output), "--report-output", str(report)])

            self.assertEqual(0, returncode)
            result = json.loads(output.read_text(encoding="utf-8"))
            markdown = report.read_text(encoding="utf-8")
            self.assertEqual("blocked", result["status"])
            self.assertIn("Real-Money Launch Gate Audit", markdown)
            self.assertIn("Blockers", markdown)


def write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


if __name__ == "__main__":
    unittest.main()
