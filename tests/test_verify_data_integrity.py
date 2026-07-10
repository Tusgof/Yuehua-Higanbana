from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.verify_data_integrity import verify_data_integrity


class VerifyDataIntegrityTests(unittest.TestCase):
    def test_registered_paid_file_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_root = root / "data"
            raw_path = data_root / "raw" / "spy_0dte" / "databento" / "sample.dbn.zst"
            raw_path.parent.mkdir(parents=True)
            raw_path.write_bytes(b"paid-data")
            digest = hashlib.sha256(b"paid-data").hexdigest()
            registry = data_root / "registry" / "datasets.jsonl"
            registry.parent.mkdir(parents=True)
            registry.write_text(
                json.dumps(
                    {
                        "provider": "Databento",
                        "dataset_id": "sample",
                        "source_url": "data/raw/spy_0dte/databento/sample.dbn.zst",
                        "raw_sha256": digest,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            report_root = root / "reports"
            report_root.mkdir()

            result = verify_data_integrity(registry, report_root, data_root)

        self.assertEqual("pass", result["status"])
        self.assertEqual("pass", result["registry_checks"][0]["status"])

    def test_unregistered_download_artifact_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_root = root / "data"
            registry = data_root / "registry" / "datasets.jsonl"
            registry.parent.mkdir(parents=True)
            registry.write_text("", encoding="utf-8")
            raw_path = data_root / "raw" / "spy_0dte" / "databento" / "orphan.dbn.zst"
            raw_path.parent.mkdir(parents=True)
            raw_path.write_bytes(b"orphan")
            report_root = root / "reports" / "data_cost"
            report_root.mkdir(parents=True)
            report_root.joinpath("download.json").write_text(
                json.dumps(
                    {
                        "output_path": "data/raw/spy_0dte/databento/orphan.dbn.zst",
                        "sha256": hashlib.sha256(b"orphan").hexdigest(),
                    }
                ),
                encoding="utf-8",
            )

            result = verify_data_integrity(registry, report_root, data_root)

        self.assertEqual("blocked", result["status"])
        self.assertEqual(1, result["uncovered_download_artifact_count"])

    def test_supplemental_registry_backfills_download_report_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_root = root / "data"
            registry = data_root / "registry" / "datasets.jsonl"
            registry.parent.mkdir(parents=True)
            registry.write_text("", encoding="utf-8")
            raw_path = data_root / "raw" / "spy_0dte" / "databento" / "orphan.dbn.zst"
            raw_path.parent.mkdir(parents=True)
            raw_path.write_bytes(b"orphan")
            report_root = root / "reports" / "data_cost"
            report_root.mkdir(parents=True)
            report_root.joinpath("download.json").write_text(
                json.dumps(
                    {
                        "output_path": "data/raw/spy_0dte/databento/orphan.dbn.zst",
                        "sha256": hashlib.sha256(b"orphan").hexdigest(),
                    }
                ),
                encoding="utf-8",
            )
            supplemental = registry.parent / "paid_artifact_checksums.jsonl"

            with patch(
                "scripts.verify_data_integrity.dbn_record_body_hashes",
                return_value={"sha256": "canonical-content", "bytes": 7},
            ):
                result = verify_data_integrity(
                    registry,
                    report_root,
                    data_root,
                    supplemental_registry_path=supplemental,
                    write_supplemental_registry=True,
                )

        self.assertEqual("pass", result["status"])
        self.assertEqual(1, result["supplemental_registry_count"])
        self.assertEqual("pass", result["supplemental_checks"][0]["status"])
        self.assertEqual(1, result["canonical_backfill"]["canonical_backfilled"])

    def test_canonical_content_accepts_container_envelope_variance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_root = root / "data"
            registry = data_root / "registry" / "datasets.jsonl"
            registry.parent.mkdir(parents=True)
            registry.write_text("", encoding="utf-8")
            raw_path = data_root / "raw" / "spy_0dte" / "databento" / "sample.dbn.zst"
            raw_path.parent.mkdir(parents=True)
            raw_path.write_bytes(b"different-container")
            supplemental = registry.parent / "paid_artifact_checksums.jsonl"
            supplemental.write_text(
                json.dumps(
                    {
                        "path": raw_path.relative_to(data_root).as_posix(),
                        "sha256": hashlib.sha256(b"historical-container").hexdigest(),
                        "canonical_content_sha256": "canonical-content",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            report_root = root / "reports"
            report_root.mkdir()

            with patch(
                "scripts.verify_data_integrity.dbn_record_body_hashes",
                return_value={"sha256": "canonical-content"},
            ):
                result = verify_data_integrity(
                    registry,
                    report_root,
                    data_root,
                    supplemental_registry_path=supplemental,
                )

        self.assertEqual("pass", result["status"])
        self.assertEqual("content_verified_envelope_variance", result["supplemental_checks"][0]["status"])
