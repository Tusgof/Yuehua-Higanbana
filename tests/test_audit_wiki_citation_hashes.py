from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.audit_wiki_citation_hashes import audit_wiki_citation_hashes


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


if __name__ == "__main__":
    unittest.main()
