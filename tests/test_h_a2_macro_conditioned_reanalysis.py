from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "run_h_a2_macro_conditioned_reanalysis.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("run_h_a2_macro_conditioned_reanalysis", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load H-A2 re-analysis runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HA2MacroConditionedReanalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = load_runner()

    def test_current_reanalysis_is_e1_and_not_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary_path = Path(tmp) / "summary.json"
            report_path = Path(tmp) / "report.md"

            result = self.runner.run_reanalysis(summary_path=summary_path, report_path=report_path)

        self.assertEqual("H-A2", result["hypothesis_id"])
        self.assertEqual("E1", result["evidence_tier"])
        self.assertEqual("ยังสรุปไม่ได้", result["conclusion"])
        self.assertIn("inherited_9_trial_search_contamination", result["tier_blockers"])
        self.assertEqual(9, result["search_contamination"]["inherited_trial_count"])
        self.assertTrue(result["no_new_paid_data"])
        self.assertTrue(result["research_log_required"])
        self.assertEqual("higanbana-macro-conditioned-orb-reanalysis", result["research_log_slug"])

    def test_outputs_are_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary_path = Path(tmp) / "summary.json"
            report_path = Path(tmp) / "report.md"

            self.runner.run_reanalysis(summary_path=summary_path, report_path=report_path)
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            report = report_path.read_text(encoding="utf-8")

        self.assertEqual("experiment_summary", summary["record_type"])
        self.assertIn("H-A2 Macro-Conditioned ORB Re-Analysis", report)
        self.assertIn("Search Contamination And DSR", report)


if __name__ == "__main__":
    unittest.main()
