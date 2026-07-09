from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "select_h_g1_manifest_v3_replacement.py"


def load_selector():
    spec = importlib.util.spec_from_file_location("select_h_g1_manifest_v3_replacement", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load H-G1 v3 selector")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class H_G1ManifestV3SelectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.selector = load_selector()

    def test_selector_chooses_2023_09_13_from_locked_rules(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = root / "manifest.json"
            report_json = root / "selection.json"
            report_md = root / "selection.md"

            report = self.selector.build_manifest_v3(
                output_manifest_path=manifest_path,
                output_report_json=report_json,
                output_report_md=report_md,
            )

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual("pass", report["status"])
        self.assertFalse(report["network_used"])
        self.assertFalse(report["paid_data_used"])
        self.assertEqual("2023-09-13", report["selected_replacement_date"])
        self.assertEqual("2023-09-13", report["candidate_ranking_table"][0]["date"])
        self.assertIn("computed gamma proxy", report["forbidden_selection_inputs_not_used"])
        self.assertIn("strategy PnL", report["forbidden_selection_inputs_not_used"])
        self.assertNotIn("2023-07-12", {item["date"] for item in manifest["selected_dates"]})
        self.assertEqual(1, sum(item["opra_oi_status"] == "needs_metadata_cost_check" for item in manifest["selected_dates"]))


if __name__ == "__main__":
    unittest.main()
