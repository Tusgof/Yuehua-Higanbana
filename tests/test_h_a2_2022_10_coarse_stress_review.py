from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from lib.environment import data_root
from tests.tiers import state_audit

from scripts.run_h_a2_2022_10_coarse_stress_review import run_h_a2_2022_10_coarse_stress_review
from scripts.validate_h_a2_2022_10_coarse_stress_review import validate_h_a2_2022_10_coarse_stress_review


@state_audit(("HIGANBANA_DATA_ROOT", data_root()))
class HA2202210CoarseStressReviewTests(unittest.TestCase):
    def test_temp_report_runs_and_validates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_json = Path(tmp) / "review.json"
            output_md = Path(tmp) / "review.md"
            report = run_h_a2_2022_10_coarse_stress_review(output_json_path=output_json, output_md_path=output_md)
            self.assertEqual("continue_exact_rerun_research", report["status"])
            result = validate_h_a2_2022_10_coarse_stress_review(output_json)
        self.assertEqual("pass", result["status"], result["blockers"])
        self.assertEqual(21, result["trading_day_count"])
        self.assertIs(False, result["paper_trading_allowed"])

    def test_rejects_paper_trading_or_strategy_pnl_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_json = Path(tmp) / "review.json"
            output_md = Path(tmp) / "review.md"
            run_h_a2_2022_10_coarse_stress_review(output_json_path=output_json, output_md_path=output_md)
            data = json.loads(output_json.read_text(encoding="utf-8"))
            data["paper_trading_allowed"] = True
            data["strategy_pnl_used"] = True
            output_json.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            result = validate_h_a2_2022_10_coarse_stress_review(output_json)
        self.assertEqual("blocked", result["status"])
        self.assertIn("paper_trading_allowed_must_be_false", result["blockers"])
        self.assertIn("strategy_pnl_used_must_be_false", result["blockers"])

    def test_rejects_missing_research_log_requirement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_json = Path(tmp) / "review.json"
            output_md = Path(tmp) / "review.md"
            run_h_a2_2022_10_coarse_stress_review(output_json_path=output_json, output_md_path=output_md)
            data = json.loads(output_json.read_text(encoding="utf-8"))
            data["research_log_required"] = False
            output_json.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            result = validate_h_a2_2022_10_coarse_stress_review(output_json)
        self.assertEqual("blocked", result["status"])
        self.assertIn("research_log_required_must_be_true", result["blockers"])


if __name__ == "__main__":
    unittest.main()
