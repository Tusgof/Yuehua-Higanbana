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

    def test_accepts_human_reviewed_supersession(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, manifest, artifact, validator = _gate_paths(Path(tmp))
            initial = _entry("gate-v1", artifact, validator)
            artifact.write_text('{"status":"revised"}', encoding="utf-8")
            validator.write_text("print('revised')\n", encoding="utf-8")
            replacement = _entry("gate-v2", artifact, validator)
            replacement.update(
                {
                    "supersedes_gate_id": "gate-v1",
                    "human_approval": "User approved a documented revision.",
                    "reviewed_by": "Fable 5",
                }
            )
            manifest.write_text(
                "\n".join(json.dumps(entry) for entry in [initial, replacement]) + "\n",
                encoding="utf-8",
            )
            with patch("scripts.validate_locked_gates.PROJECT_ROOT", root):
                result = validate_locked_gates(manifest)

        self.assertEqual("pass", result["status"], result["blockers"])
        self.assertEqual("superseded", result["checked"][0]["status"])
        self.assertEqual("gate-v2", result["checked"][0]["superseded_by"])

    def test_rejects_supersession_without_human_approval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, manifest, artifact, validator = _gate_paths(Path(tmp))
            initial = _entry("gate-v1", artifact, validator)
            artifact.write_text('{"status":"revised"}', encoding="utf-8")
            validator.write_text("print('revised')\n", encoding="utf-8")
            replacement = _entry("gate-v2", artifact, validator)
            replacement.update({"supersedes_gate_id": "gate-v1", "human_approval": "", "reviewed_by": "Fable 5"})
            manifest.write_text(
                "\n".join(json.dumps(entry) for entry in [initial, replacement]) + "\n",
                encoding="utf-8",
            )
            with patch("scripts.validate_locked_gates.PROJECT_ROOT", root):
                result = validate_locked_gates(manifest)

        self.assertEqual("blocked", result["status"])
        self.assertIn("missing_human_approval:gate-v2", result["blockers"])

    def test_rejects_supersession_without_reviewer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root, manifest, artifact, validator = _gate_paths(Path(tmp))
            initial = _entry("gate-v1", artifact, validator)
            artifact.write_text('{"status":"revised"}', encoding="utf-8")
            validator.write_text("print('revised')\n", encoding="utf-8")
            replacement = _entry("gate-v2", artifact, validator)
            replacement.update({"supersedes_gate_id": "gate-v1", "human_approval": "User approved a documented revision."})
            manifest.write_text(
                "\n".join(json.dumps(entry) for entry in [initial, replacement]) + "\n",
                encoding="utf-8",
            )
            with patch("scripts.validate_locked_gates.PROJECT_ROOT", root):
                result = validate_locked_gates(manifest)

        self.assertEqual("blocked", result["status"])
        self.assertIn("missing_reviewer:gate-v2", result["blockers"])


def _gate_paths(root: Path) -> tuple[Path, Path, Path, Path]:
    experiments = root / "experiments"
    scripts = root / "scripts"
    experiments.mkdir()
    scripts.mkdir()
    artifact = experiments / "gate.json"
    validator = scripts / "validate_gate.py"
    artifact.write_text('{"status":"locked"}', encoding="utf-8")
    validator.write_text("print('ok')\n", encoding="utf-8")
    return root, experiments / "locked_gates.jsonl", artifact, validator


def _entry(gate_id: str, artifact: Path, validator: Path) -> dict[str, str]:
    return {
        "gate_id": gate_id,
        "artifact_path": "experiments/gate.json",
        "artifact_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
        "validator_path": "scripts/validate_gate.py",
        "validator_sha256": hashlib.sha256(validator.read_bytes()).hexdigest(),
        "human_approval": "Initial human approval.",
    }


if __name__ == "__main__":
    unittest.main()
