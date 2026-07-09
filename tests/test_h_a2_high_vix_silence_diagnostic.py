from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

from lib.environment import data_root
from tests.tiers import state_audit


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "run_h_a2_high_vix_silence_diagnostic.py"


def load_module():
    spec = importlib.util.spec_from_file_location("run_h_a2_high_vix_silence_diagnostic", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load H-A2 high-VIX diagnostic module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@state_audit(("HIGANBANA_DATA_ROOT", data_root()))
class HA2HighVixSilenceDiagnosticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()

    def test_aug_2024_high_vix_window_is_orb_silence_not_missing_label(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = self.module.run_diagnostic(
                summary_path=root / "summary.json",
                report_path=root / "report.md",
            )

        self.assertEqual("complete", result["status"])
        self.assertEqual("H-A2", result["hypothesis_id"])
        self.assertEqual("E1", result["evidence_tier"])
        self.assertFalse(result["research_log_required"])
        self.assertTrue(result["no_new_paid_data"])
        self.assertEqual("genuine_orb_silence_during_high_vix_window", result["diagnostic_result"])
        self.assertEqual([], result["date_sets"]["missing_vix_dates"])
        self.assertEqual([], result["date_sets"]["missing_market_data_on_high_vix_dates"])
        self.assertIn("2024-08-05", result["date_sets"]["same_day_high_vix_dates"])
        self.assertIn("2024-08-06", result["date_sets"]["prior_high_vix_dates"])
        self.assertEqual(0, result["counts"]["candidate_ready_on_same_day_high_vix"])
        self.assertEqual(0, result["counts"]["candidate_ready_on_prior_high_vix"])
        self.assertEqual(["2024-08-12", "2024-08-28"], result["date_sets"]["candidate_ready_dates"])
        self.assertTrue(result["interpretation"]["orb_silence_during_high_vix"])
        self.assertFalse(result["interpretation"]["labeling_gap"])


if __name__ == "__main__":
    unittest.main()
