from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "validate_evidence_tiers.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_evidence_tiers", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load evidence-tier validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ValidateEvidenceTiersTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_validator()

    def test_current_top_level_summaries_have_no_acceptance_blocker(self) -> None:
        result = self.validator.validate_evidence_tiers()

        self.assertEqual("pass", result["status"])
        self.assertEqual([], result["blockers"])
        self.assertGreater(result["summary_count"], 0)
        self.assertGreaterEqual(len(result["warnings"]), 1)

    def test_rejects_unknown_hypothesis_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_fixture_root(Path(tmp))
            reports_root = root / "reports"
            write_summary(
                reports_root / "experiments" / "unknown_summary.json",
                {"hypothesis_id": "H-MISSING", "evidence_tier": "E1", "tier_blockers": ["sample"]},
            )

            result = self.validator.validate_evidence_tiers(root / "hypothesis_registry.json", reports_root)

        self.assertEqual("blocked", result["status"])
        self.assertTrue(any("unknown_hypothesis_id" in blocker for blocker in result["blockers"]))

    def test_rejects_acceptance_claim_below_e2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_fixture_root(Path(tmp))
            reports_root = root / "reports"
            write_summary(
                reports_root / "experiments" / "accepted_summary.json",
                {
                    "hypothesis_id": "H-X1",
                    "evidence_tier": "E1",
                    "tier_blockers": ["under-sampled"],
                    "conclusion": "ผ่าน",
                },
            )

            result = self.validator.validate_evidence_tiers(root / "hypothesis_registry.json", reports_root)

        self.assertEqual("blocked", result["status"])
        self.assertTrue(any("acceptance_claim_below_E2" in blocker for blocker in result["blockers"]))

    def test_rejects_missing_metadata_for_acceptance_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_fixture_root(Path(tmp))
            reports_root = root / "reports"
            write_summary(reports_root / "experiments" / "missing_metadata_summary.json", {"conclusion": "ผ่าน"})

            result = self.validator.validate_evidence_tiers(root / "hypothesis_registry.json", reports_root)

        self.assertEqual("blocked", result["status"])
        self.assertTrue(any("missing_evidence_metadata" in blocker for blocker in result["blockers"]))

    def test_strict_mode_rejects_missing_metadata_without_acceptance_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_fixture_root(Path(tmp))
            reports_root = root / "reports"
            write_summary(reports_root / "experiments" / "legacy_summary.json", {"conclusion": "ยังสรุปไม่ได้"})

            result = self.validator.validate_evidence_tiers(
                root / "hypothesis_registry.json",
                reports_root,
                strict_missing_metadata=True,
            )

        self.assertEqual("blocked", result["status"])
        self.assertTrue(any("missing_evidence_metadata" in blocker for blocker in result["blockers"]))


def make_fixture_root(root: Path) -> Path:
    (root / "reports" / "experiments").mkdir(parents=True)
    (root / "reports" / "baselines").mkdir(parents=True)
    (root / "reports" / "diagnostics").mkdir(parents=True)
    (root / "hypothesis_registry.json").write_text(
        json.dumps(
            {
                "schema_version": "hypothesis_registry_v1",
                "hypotheses": [
                    {
                        "id": "H-X1",
                        "family": "subsystem_a",
                        "status": "active",
                        "statement": "Fixture.",
                        "economic_rationale": "Fixture.",
                        "testable_predictions": ["Fixture."],
                        "validation_criteria": ["Fixture."],
                        "falsification_criteria": ["Fixture."],
                        "required_data": ["Fixture."],
                        "mintrl_falsify": {"status": "pending"},
                        "evidence": [],
                        "dependencies": [],
                        "decision_log": [{"date": "2026-07-03", "decision": "fixture"}],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return root


def write_summary(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
