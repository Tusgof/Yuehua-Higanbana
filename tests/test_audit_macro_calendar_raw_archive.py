from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "audit_macro_calendar_raw_archive.py"


def load_auditor():
    spec = importlib.util.spec_from_file_location("audit_macro_calendar_raw_archive", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load macro calendar raw archive auditor")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AuditMacroCalendarRawArchiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.auditor = load_auditor()

    def test_reports_blocked_when_manifest_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self.auditor.audit_raw_archive(raw_root=Path(tmp), start_year=2022, end_year=2022)

            self.assertEqual("blocked", result["status"])
            self.assertEqual([2022], result["blocked_years"])
            self.assertEqual(0, result["years"][0]["present_count"])
            self.assertEqual(5, len(result["years"][0]["missing_sources"]))

    def test_passes_when_all_sources_match_manifest_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raw_root = Path(tmp)
            as_of_root = raw_root / "2022-12-31"
            as_of_root.mkdir()
            source_ids = [
                "federal_reserve_fomc_calendar",
                "bls_release_calendar",
                "bea_release_schedule",
                "ism_pmi_release_calendar",
                "census_retail_release_schedule",
            ]
            captured = []
            for source_id in source_ids:
                output_path = as_of_root / f"{source_id}.html"
                payload = f"<html>{source_id}</html>".encode("utf-8")
                output_path.write_bytes(payload)
                captured.append(
                    {
                        "source_id": source_id,
                        "provider": source_id,
                        "source_url": "https://example.test",
                        "output_path": str(output_path),
                        "bytes": len(payload),
                        "sha256": hashlib.sha256(payload).hexdigest(),
                    }
                )
            (as_of_root / "capture_manifest.json").write_text(
                json.dumps({"as_of_date": "2022-12-31", "captured": captured}, indent=2),
                encoding="utf-8",
            )

            result = self.auditor.audit_raw_archive(raw_root=raw_root, start_year=2022, end_year=2022)

            self.assertEqual("pass", result["status"])
            self.assertEqual([], result["blocked_years"])
            self.assertEqual(5, result["years"][0]["present_count"])

    def test_current_year_uses_current_as_of_date(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raw_root = Path(tmp)
            as_of_root = raw_root / "2026-06-30"
            as_of_root.mkdir()
            source_ids = [
                "federal_reserve_fomc_calendar",
                "bls_release_calendar",
                "bea_release_schedule",
                "ism_pmi_release_calendar",
                "census_retail_release_schedule",
            ]
            captured = []
            for source_id in source_ids:
                output_path = as_of_root / f"{source_id}.html"
                payload = f"<html>{source_id}</html>".encode("utf-8")
                output_path.write_bytes(payload)
                captured.append(
                    {
                        "source_id": source_id,
                        "output_path": str(output_path),
                        "bytes": len(payload),
                        "sha256": hashlib.sha256(payload).hexdigest(),
                    }
                )
            (as_of_root / "capture_manifest.json").write_text(
                json.dumps({"as_of_date": "2026-06-30", "captured": captured}, indent=2),
                encoding="utf-8",
            )

            result = self.auditor.audit_raw_archive(
                raw_root=raw_root,
                start_year=2026,
                end_year=2026,
                current_as_of_date=date(2026, 6, 30),
            )

            self.assertEqual("pass", result["status"])
            self.assertEqual("2026-06-30", result["years"][0]["as_of_date"])

    def test_detects_hash_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raw_root = Path(tmp)
            as_of_root = raw_root / "2022-12-31"
            as_of_root.mkdir()
            output_path = as_of_root / "federal_reserve_fomc_calendar.html"
            output_path.write_text("changed", encoding="utf-8")
            (as_of_root / "capture_manifest.json").write_text(
                json.dumps(
                    {
                        "as_of_date": "2022-12-31",
                        "captured": [
                            {
                                "source_id": "federal_reserve_fomc_calendar",
                                "output_path": str(output_path),
                                "bytes": len("changed"),
                                "sha256": "not-the-real-hash",
                            }
                        ],
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            result = self.auditor.audit_raw_archive(raw_root=raw_root, start_year=2022, end_year=2022)
            source = result["years"][0]["sources"][0]

            self.assertEqual("sha256_mismatch", source["status"])


if __name__ == "__main__":
    unittest.main()
