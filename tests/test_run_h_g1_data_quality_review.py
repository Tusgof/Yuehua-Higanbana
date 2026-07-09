from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "run_h_g1_data_quality_review.py"


def load_module():
    spec = importlib.util.spec_from_file_location("run_h_g1_data_quality_review", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load H-G1 data-quality review module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class H_G1DataQualityReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()

    def test_issue_class_detects_manifest_cache_mismatch(self) -> None:
        issue = self.module._issue_class("present", baseline_bar_rows=0, underlying_join_count=0, diagnostic_item={})

        self.assertEqual("manifest_cache_mismatch_missing_spy_bars", issue)

    def test_run_review_writes_no_purchase_review_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bar_path = root / "bars.jsonl"
            quote_path = root / "quotes.jsonl"
            bar_path.write_text(json.dumps({"timestamp_et": "2024-01-03T09:35:00-05:00"}) + "\n", encoding="utf-8")
            quote_path.write_text(json.dumps({"quote_timestamp_et": "2024-01-03T09:35:00-05:00"}) + "\n", encoding="utf-8")
            manifest_path = root / "manifest.json"
            baseline_path = root / "baseline.json"
            enrichment_path = root / "enrichment.json"
            diagnostic_path = root / "diagnostic.json"
            json_output = root / "review.json"
            report_output = root / "review.md"

            manifest_path.write_text(
                json.dumps(
                    {
                        "selected_dates": [
                            {"date": "2023-03-13", "split": "in_sample", "volatility_bucket": "high", "high_importance_macro": False, "local_spy_bar_cache_status": "present"},
                            {"date": "2024-01-03", "split": "oos", "volatility_bucket": "low", "high_importance_macro": True, "local_spy_bar_cache_status": "present"},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            baseline_path.write_text(
                json.dumps({"datasets": [{"bar_path": str(bar_path), "quote_path": str(quote_path)}]}),
                encoding="utf-8",
            )
            enrichment_path.write_text(
                json.dumps(
                    {
                        "date_summaries": [
                            {"date": "2023-03-13", "bar_rows": 0, "quote_snapshot_rows": 10, "underlying_join_count": 0, "open_interest_join_count": 10, "computed_greeks_count": 0},
                            {"date": "2024-01-03", "bar_rows": 1, "quote_snapshot_rows": 10, "underlying_join_count": 10, "open_interest_join_count": 10, "computed_greeks_count": 5},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            diagnostic_path.write_text(
                json.dumps(
                    {
                        "per_date": {
                            "2023-03-13": {"required_bucket_blockers": ["atm_missing"]},
                            "2024-01-03": {"required_bucket_blockers": ["otm_put_computed_rate_below_60pct"]},
                        }
                    }
                ),
                encoding="utf-8",
            )

            result = self.module.run_review(manifest_path, baseline_path, enrichment_path, diagnostic_path)
            self.module.write_outputs(result, json_output, report_output)
            json_exists = json_output.exists()
            report_text = report_output.read_text(encoding="utf-8")

        self.assertEqual("complete_no_purchase_review", result["status"])
        self.assertEqual(1, result["summary"]["manifest_spy_bar_mismatch_count"])
        self.assertEqual(1, result["summary"]["bucket_failure_after_underlying_date_count"])
        self.assertTrue(json_exists)
        self.assertIn("H-G1 Data Quality Review", report_text)


if __name__ == "__main__":
    unittest.main()
