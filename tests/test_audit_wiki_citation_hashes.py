from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lib.environment import wiki_root
from scripts.audit_wiki_citation_hashes import audit_wiki_citation_hashes
from tests.tiers import state_audit


class AuditWikiCitationHashesTests(unittest.TestCase):
    def test_reports_missing_hash_for_existing_wiki_reference(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            experiments = root / "experiments"
            wiki = root / "wiki"
            experiments.mkdir()
            wiki.joinpath("concepts").mkdir(parents=True)
            wiki_file = wiki / "concepts" / "minimum-track-record-length.md"
            wiki_file.write_text("MinTRL", encoding="utf-8")
            experiments.joinpath("sample.json").write_text(
                json.dumps({"basis": "wiki/concepts/minimum-track-record-length.md"}),
                encoding="utf-8",
            )
            with patch("scripts.audit_wiki_citation_hashes.PROJECT_ROOT", root):
                report = audit_wiki_citation_hashes(experiments, root / "report.json", wiki_base=wiki)

        self.assertEqual("pass_with_missing_hashes", report["status"])
        self.assertEqual(1, report["hash_missing_count"])

    def test_accepts_recorded_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            experiments = root / "experiments"
            wiki = root / "wiki"
            experiments.mkdir()
            wiki.joinpath("concepts").mkdir(parents=True)
            relative = "concepts/probabilistic-sharpe-ratio.md"
            text = "PSR"
            wiki.joinpath(relative).write_text(text, encoding="utf-8")
            digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
            experiments.joinpath("sample.json").write_text(
                json.dumps(
                    {
                        "basis": "wiki/concepts/probabilistic-sharpe-ratio.md",
                        "wiki_citation_hashes": {relative: digest},
                    }
                ),
                encoding="utf-8",
            )
            with patch("scripts.audit_wiki_citation_hashes.PROJECT_ROOT", root):
                report = audit_wiki_citation_hashes(experiments, root / "report.json", wiki_base=wiki)

        self.assertEqual("pass_with_missing_hashes", report["status"])
        self.assertEqual(1, report["hash_recorded_count"])
        self.assertEqual(0, report["hash_missing_count"])

    def test_active_registry_binds_artifact_and_wiki_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            experiments = root / "experiments"
            wiki = root / "wiki"
            experiments.mkdir()
            wiki.joinpath("concepts").mkdir(parents=True)
            relative = "concepts/minimum-track-record-length.md"
            wiki_file = wiki / relative
            wiki_file.write_text("MinTRL", encoding="utf-8")
            artifact = experiments / "active.json"
            artifact.write_text(
                json.dumps({"basis": "${HIGANBANA_WIKI_ROOT}/concepts/minimum-track-record-length.md"}),
                encoding="utf-8",
            )
            registry = experiments / "active_wiki_citation_hashes.json"
            registry.write_text(
                json.dumps(
                    {
                        "preregistrations": [
                            {
                                "artifact_path": "experiments/active.json",
                                "artifact_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                                "wiki_citation_hashes": {
                                    relative: hashlib.sha256(wiki_file.read_bytes()).hexdigest(),
                                },
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            with patch("scripts.audit_wiki_citation_hashes.PROJECT_ROOT", root):
                report = audit_wiki_citation_hashes(
                    experiments,
                    root / "report.json",
                    wiki_base=wiki,
                    active_registry_path=registry,
                )

        self.assertEqual("pass", report["status"], report["blockers"])
        self.assertEqual(1, report["hash_recorded_count"])

    def test_active_registry_blocks_wiki_hash_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            experiments = root / "experiments"
            wiki = root / "wiki"
            experiments.mkdir()
            wiki.joinpath("concepts").mkdir(parents=True)
            relative = "concepts/minimum-track-record-length.md"
            wiki.joinpath(relative).write_text("changed", encoding="utf-8")
            artifact = experiments / "active.json"
            artifact.write_text(json.dumps({"basis": f"wiki/{relative}"}), encoding="utf-8")
            registry = experiments / "active_wiki_citation_hashes.json"
            registry.write_text(
                json.dumps(
                    {
                        "preregistrations": [
                            {
                                "artifact_path": "experiments/active.json",
                                "artifact_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                                "wiki_citation_hashes": {relative: "0" * 64},
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            with patch("scripts.audit_wiki_citation_hashes.PROJECT_ROOT", root):
                report = audit_wiki_citation_hashes(
                    experiments,
                    root / "report.json",
                    wiki_base=wiki,
                    active_registry_path=registry,
                )

        self.assertEqual("blocked", report["status"])
        self.assertIn(
            "wiki_sha256_mismatch:experiments/active.json:concepts/minimum-track-record-length.md",
            report["blockers"],
        )

    @state_audit(("HIGANBANA_WIKI_ROOT", wiki_root()))
    def test_current_active_registry_passes(self) -> None:
        report = audit_wiki_citation_hashes(write_report=False)

        self.assertEqual("pass", report["status"], report["blockers"])
        self.assertEqual(2, report["active_preregistration_count"])
        self.assertEqual(9, report["hash_recorded_count"])


if __name__ == "__main__":
    unittest.main()
