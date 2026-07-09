from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "run_gdelt_doc_api_enrichment_scaffold.py"


def load_scaffold():
    spec = importlib.util.spec_from_file_location("run_gdelt_doc_api_enrichment_scaffold", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load GDELT DOC API enrichment scaffold module")
    module = importlib.util.module_from_spec(spec)
    sys.modules["run_gdelt_doc_api_enrichment_scaffold"] = module
    spec.loader.exec_module(module)
    return module


class RunGdeltDocApiEnrichmentScaffoldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.scaffold = load_scaffold()

    def test_scaffold_selects_doc_api_path_and_preserves_real_archive_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            probe_path = root / "probe.json"
            note_path = root / "decision.md"
            snapshot_path = root / "snapshot.csv"
            import_root = root / "imported"
            probe_path.write_text(
                json.dumps(
                    {
                        "status": "blocked_requires_enrichment_or_policy",
                        "blockers": ["gkg_has_no_verified_headline_field"],
                        "selected_file": {"decision_time_et": "2024-01-29T09:30:00-05:00"},
                    }
                ),
                encoding="utf-8",
            )
            note_path.write_text("# Decision\n", encoding="utf-8")

            result = self.scaffold.run_scaffold(
                probe_report_path=probe_path,
                decision_note_path=note_path,
                output_root=root / "out",
                snapshot_path=snapshot_path,
                import_output_root=import_root,
            )

        self.assertEqual("scaffold_pass_real_archive_blocked", result["status"])
        self.assertEqual("gdelt_doc_api_topic_requery_after_cooldown", result["selected_path"])
        self.assertEqual(0, result["network_calls"])
        self.assertEqual(0.0, result["paid_cost_usd"])
        self.assertTrue(result["not_research_evidence"])
        self.assertIn("requires_real_news_archive", result["remaining_blockers"])
        self.assertEqual(5, result["snapshot_row_count"])
        self.assertEqual(5, result["import_result"]["record_count"])
        self.assertIn("headline_from_title", result["doc_api_fields_proven_by_scaffold"])

    def test_main_writes_json_and_markdown_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            probe_path = root / "probe.json"
            note_path = root / "decision.md"
            json_output = root / "report.json"
            md_output = root / "report.md"
            probe_path.write_text(
                json.dumps(
                    {
                        "status": "blocked_requires_enrichment_or_policy",
                        "blockers": ["gkg_publication_time_is_surrogate_not_exact"],
                        "selected_file": {"decision_time_et": "2024-01-29T09:30:00-05:00"},
                    }
                ),
                encoding="utf-8",
            )
            note_path.write_text("# Decision\n", encoding="utf-8")

            returncode = self.scaffold.main(
                [
                    "--probe-report-path",
                    str(probe_path),
                    "--decision-note-path",
                    str(note_path),
                    "--output-root",
                    str(root / "out"),
                    "--snapshot-path",
                    str(root / "snapshot.csv"),
                    "--import-output-root",
                    str(root / "imported"),
                    "--json-output",
                    str(json_output),
                    "--report-output",
                    str(md_output),
                ]
            )

            result = json.loads(json_output.read_text(encoding="utf-8"))
            report = md_output.read_text(encoding="utf-8")

        self.assertEqual(0, returncode)
        self.assertEqual("scaffold_pass_real_archive_blocked", result["status"])
        self.assertIn("GDELT DOC API Enrichment Scaffold", report)
        self.assertIn("It does not prove real historical news availability", report)

    def test_scaffold_rejects_unblocked_gkg_probe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            probe_path = root / "probe.json"
            note_path = root / "decision.md"
            probe_path.write_text(json.dumps({"status": "pass"}), encoding="utf-8")
            note_path.write_text("# Decision\n", encoding="utf-8")

            with self.assertRaisesRegex(self.scaffold.GdeltScaffoldError, "must be blocked"):
                self.scaffold.run_scaffold(
                    probe_report_path=probe_path,
                    decision_note_path=note_path,
                    output_root=root / "out",
                    snapshot_path=root / "snapshot.csv",
                    import_output_root=root / "imported",
                )


if __name__ == "__main__":
    unittest.main()
