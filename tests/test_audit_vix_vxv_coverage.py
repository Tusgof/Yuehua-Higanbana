from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "audit_vix_vxv_coverage.py"


def load_auditor():
    spec = importlib.util.spec_from_file_location("audit_vix_vxv_coverage", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load VIX/VXV coverage auditor")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AuditVixVxvCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.auditor = load_auditor()

    def test_audit_passes_when_required_windows_have_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vix_vxv.jsonl"
            rows = [
                {"record_type": "vix_vxv", "date": "2022-01-03", "vix_close": 20.0, "vxv_close": 22.0},
                {"record_type": "vix_vxv", "date": "2022-05-11", "vix_close": 20.0, "vxv_close": 22.0},
                {"record_type": "vix_vxv", "date": "2023-01-03", "vix_close": 20.0, "vxv_close": 22.0},
                {"record_type": "vix_vxv", "date": "2024-01-03", "vix_close": 20.0, "vxv_close": 22.0},
                {"record_type": "vix_vxv", "date": "2025-01-03", "vix_close": 20.0, "vxv_close": 22.0},
                {"record_type": "vix_vxv", "date": "2026-06-29", "vix_close": 20.0, "vxv_close": 22.0},
            ]
            path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

            result = self.auditor.audit_vix_vxv_coverage(path, as_of_date=date(2026, 6, 30))

            self.assertEqual("pass", result["status"])
            self.assertEqual([], result["blockers"])

    def test_audit_blocks_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self.auditor.audit_vix_vxv_coverage(Path(tmp) / "missing.jsonl", as_of_date=date(2026, 6, 30))

            self.assertEqual("blocked", result["status"])
            self.assertIn("requires_real_vix_vxv_archive", result["blockers"])


if __name__ == "__main__":
    unittest.main()
