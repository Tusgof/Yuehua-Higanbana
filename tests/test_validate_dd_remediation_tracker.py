from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "validate_dd_remediation_tracker.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_dd_remediation_tracker", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load DD remediation tracker validator")
    module = importlib.util.module_from_spec(spec)
    sys.modules["validate_dd_remediation_tracker"] = module
    spec.loader.exec_module(module)
    return module


class ValidateDdRemediationTrackerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_validator()

    def test_current_tracker_is_valid_shape(self) -> None:
        result = self.validator.validate_tracker()
        self.assertEqual("pass", result["status"], result["blockers"])

    def test_done_claim_without_artifact_fails(self) -> None:
        payload = {
            "schema_version": "dd_remediation_tracker_v1",
            "updated": "2026-07-10",
            "workstreams": [
                _entry("WS1"),
                {
                    "id": "WS2",
                    "title": "Golden-number statistics anchors",
                    "status": "done",
                    "required_artifacts": [{"path": "tests/definitely_missing_statistics_golden.py", "must": "exist"}],
                    "user_actions_pending": [],
                    "evidence": [],
                    "updated": "2026-07-10",
                },
                _entry("WS3"),
                _entry("WS4"),
                _entry("WS5"),
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            tracker = Path(tmp) / "tracker.json"
            tracker.write_text(json.dumps(payload), encoding="utf-8")
            result = self.validator.validate_tracker(tracker)
        self.assertEqual("fail", result["status"])
        self.assertIn("WS2:missing_artifact:tests/definitely_missing_statistics_golden.py", result["blockers"])

    def test_done_hermetic_test_file_runs_without_tier_recursion(self) -> None:
        blockers = self.validator._validate_done_artifact(
            "WS2",
            "tests/test_statistics_golden.py",
            "pass_in_hermetic_tier",
            run_expensive=False,
        )
        self.assertEqual([], blockers)


def _entry(ws_id: str) -> dict[str, object]:
    return {
        "id": ws_id,
        "title": ws_id,
        "status": "not_started",
        "required_artifacts": [],
        "user_actions_pending": [],
        "evidence": [],
        "updated": "2026-07-10",
    }


if __name__ == "__main__":
    unittest.main()
