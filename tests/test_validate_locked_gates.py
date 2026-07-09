from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.validate_locked_gates import validate_locked_gates


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class ValidateLockedGatesTests(unittest.TestCase):
    def test_current_manifest_passes(self) -> None:
        result = validate_locked_gates()
        self.assertEqual("pass", result["status"], result["blockers"])
        self.assertGreaterEqual(result["entry_count"], 1)

    def test_rejects_hash_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            experiments = root / "experiments"
            scripts = root / "scripts"
            experiments.mkdir()
            scripts.mkdir()
            artifact = experiments / "gate.json"
            validator = scripts / "validate_gate.py"
            artifact.write_text('{"status":"locked"}', encoding="utf-8")
            validator.write_text("print('ok')\n", encoding="utf-8")
            manifest = experiments / "locked_gates.jsonl"
            manifest.write_text(
                json.dumps(
                    {
                        "gate_id": "test_gate",
                        "artifact_path": "experiments/gate.json",
                        "artifact_sha256": _sha256('{"status":"locked"}'),
                        "validator_path": "scripts/validate_gate.py",
                        "validator_sha256": "wrong",
                        "human_approval": "unit-test",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            with patch("scripts.validate_locked_gates.PROJECT_ROOT", root):
                result = validate_locked_gates(manifest)

        self.assertEqual("blocked", result["status"])
        self.assertIn("validator_hash_mismatch:test_gate:scripts/validate_gate.py", result["blockers"])


if __name__ == "__main__":
    unittest.main()
