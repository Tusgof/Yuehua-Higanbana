from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "audit_databento_cache.py"


def load_auditor():
    spec = importlib.util.spec_from_file_location("audit_databento_cache", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load Databento cache auditor")
    module = importlib.util.module_from_spec(spec)
    sys.modules["audit_databento_cache"] = module
    spec.loader.exec_module(module)
    return module


class DatabentoCacheAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.auditor = load_auditor()

    def test_audit_reports_present_and_missing_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            present_path = root / "raw" / "present.dbn.zst"
            missing_path = root / "raw" / "missing.dbn.zst"
            present_path.parent.mkdir(parents=True)
            present_path.write_bytes(b"present-cache")
            plan_path = root / "plan.json"
            plan_path.write_text(
                json.dumps(
                    {
                        "scenario": "one_month_pilot",
                        "items": [
                            {"window": "present", "output_path": str(present_path), "estimated_cost_usd": 0.01},
                            {"window": "missing", "output_path": str(missing_path), "estimated_cost_usd": 0.02},
                        ],
                    }
                ),
                encoding="utf-8",
            )

            audit = self.auditor.audit_cache(plan_path)

            self.assertEqual("one_month_pilot", audit["scenario"])
            self.assertEqual(2, audit["planned_request_count"])
            self.assertEqual(1, audit["present_count"])
            self.assertEqual(1, audit["missing_count"])
            self.assertEqual(0, audit["invalid_count"])
            self.assertFalse(audit["all_present"])
            self.assertEqual(len(b"present-cache"), audit["total_present_bytes"])
            self.assertIsNotNone(audit["items"][0]["sha256"])
            self.assertIsNone(audit["items"][1]["sha256"])

    def test_markdown_states_offline_only_rule(self) -> None:
        markdown = self.auditor.render_markdown(
            {
                "created_at_utc": "2026-06-29T00:00:00+00:00",
                "source_plan": "plan.json",
                "scenario": "one_month_pilot",
                "planned_request_count": 0,
                "present_count": 0,
                "missing_count": 0,
                "invalid_count": 0,
                "total_present_bytes": 0,
                "all_present": False,
                "items": [],
            }
        )
        self.assertIn("offline-only", markdown)
        self.assertIn("does not call Databento", markdown)


if __name__ == "__main__":
    unittest.main()
