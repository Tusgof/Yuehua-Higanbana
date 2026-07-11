from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from lib.io import load_json
from scripts.audit_helper_drift import audit_helper_drift
from tests.tiers import state_audit


class AuditHelperDriftTests(unittest.TestCase):
    def test_detects_divergent_helper_body(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_root = root / "scripts"
            script_root.mkdir()
            script_root.joinpath("a.py").write_text(
                "def _load_json(path):\n"
                "    return {'path': str(path)}\n",
                encoding="utf-8",
            )
            script_root.joinpath("b.py").write_text(
                "def _load_json(path):\n"
                "    return {'other': str(path)}\n",
                encoding="utf-8",
            )

            report = audit_helper_drift(script_root, root / "report.json")

        load_json_report = next(item for item in report["helper_reports"] if item["helper_name"] == "_load_json")
        self.assertEqual("pass_with_findings", report["status"])
        self.assertEqual(2, load_json_report["occurrence_count"])
        self.assertEqual(2, load_json_report["variant_count"])
        self.assertEqual(1, report["total_divergent_files"])

    def test_writes_report_without_autofix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_root = root / "scripts"
            script_root.mkdir()
            script_root.joinpath("a.py").write_text(
                "def _relative(path):\n"
                "    return str(path)\n",
                encoding="utf-8",
            )
            output = root / "reports" / "helper_drift.json"

            report = audit_helper_drift(script_root, output)
            saved = load_json(output)

        self.assertEqual("pass", report["status"])
        self.assertFalse(saved["auto_fix_applied"])
        self.assertEqual("helper_drift_audit", saved["audit_id"])

    @state_audit()
    def test_current_scripts_are_measured_without_autofix(self) -> None:
        report = audit_helper_drift(write_report=False)

        self.assertIn(report["status"], {"pass", "pass_with_findings"})
        self.assertFalse(report["auto_fix_applied"])
        self.assertGreater(sum(item["occurrence_count"] for item in report["helper_reports"]), 0)


if __name__ == "__main__":
    unittest.main()
