from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.validate_governance_epochs import validate_governance_epochs


class GovernanceEpochValidationTests(unittest.TestCase):
    def test_current_manifest_passes(self) -> None:
        result = validate_governance_epochs()
        self.assertEqual("pass", result["status"], result["blockers"])
        self.assertGreaterEqual(result["epoch_count"], 4)

    def test_blocks_missing_evidence_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / "config"
            config.mkdir()
            manifest = config / "governance_epochs.json"
            manifest.write_text(
                json.dumps(
                    {
                        "epochs": [
                            {
                                "epoch_id": "technical-dd-remediation-2026-07-09",
                                "date": "2026-07-09",
                                "status": "active",
                                "kind": "technical_due_diligence",
                                "description": "test",
                                "evidence_paths": ["missing.md"],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            with patch("scripts.validate_governance_epochs.PROJECT_ROOT", root):
                result = validate_governance_epochs(manifest, root / "report.json")

        self.assertEqual("blocked", result["status"])
        self.assertIn("technical-dd-remediation-2026-07-09:missing_evidence_path:missing.md", result["blockers"])

    def test_blocks_invalid_governance_tag_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / "config"
            config.mkdir()
            evidence = root / "evidence.md"
            evidence.write_text("evidence", encoding="utf-8")
            manifest = config / "governance_epochs.json"
            manifest.write_text(
                json.dumps(
                    {
                        "epochs": [
                            {
                                "epoch_id": "technical-dd-remediation-2026-07-09",
                                "date": "2026-07-09",
                                "status": "active",
                                "kind": "technical_due_diligence",
                                "description": "test",
                                "git_tag": "Invalid Tag",
                                "evidence_paths": ["evidence.md"],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            with patch("scripts.validate_governance_epochs.PROJECT_ROOT", root):
                result = validate_governance_epochs(manifest, root / "report.json")

        self.assertEqual("blocked", result["status"])
        self.assertIn(
            "technical-dd-remediation-2026-07-09:git_tag must be a valid lowercase tag name",
            result["blockers"],
        )


if __name__ == "__main__":
    unittest.main()
