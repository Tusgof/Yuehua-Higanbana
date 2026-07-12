from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


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

    def test_standalone_tracker_passes_with_expensive_check_unverified(self) -> None:
        result = self.validator.validate_tracker()
        self.assertEqual("pass", result["status"], result["blockers"])
        self.assertEqual([], result["blockers"])
        self.assertEqual(
            [
                {
                    "workstream": "WS1",
                    "path": "scripts/run_test_tier.py",
                    "must": "pass_hermetic_tier",
                    "reason": "expensive_check_not_run",
                }
            ],
            result["unverified"],
        )
        self.assertNotIn(
            {"workstream": "WS1", "path": "scripts/run_test_tier.py", "must": "pass_hermetic_tier"},
            result["done_artifacts_checked"],
        )

    def test_expensive_check_failure_is_still_a_blocker_when_requested(self) -> None:
        completed = type("Completed", (), {"returncode": 1})()
        with patch.object(self.validator.subprocess, "run", return_value=completed):
            blockers = self.validator._validate_done_artifact(
                "WS1",
                "scripts/run_test_tier.py",
                "pass_hermetic_tier",
                run_expensive=True,
            )
        self.assertEqual(["WS1:hermetic_tier_failed:scripts/run_test_tier.py"], blockers)

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

    def test_retention_policy_false_cannot_support_done_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            policy = root / "docs" / "REPORT_RETENTION_POLICY_PROPOSAL.md"
            policy.parent.mkdir()
            policy.write_text("- **User-approved**: `false`\n", encoding="utf-8")
            with patch.object(self.validator, "PROJECT_ROOT", root):
                blockers = self.validator._validate_done_artifact(
                    "WS5",
                    "docs/REPORT_RETENTION_POLICY_PROPOSAL.md",
                    "retention_policy_user_approved",
                    run_expensive=False,
                )

        self.assertEqual(
            ["WS5:retention_policy_not_user_approved:docs/REPORT_RETENTION_POLICY_PROPOSAL.md"],
            blockers,
        )


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
