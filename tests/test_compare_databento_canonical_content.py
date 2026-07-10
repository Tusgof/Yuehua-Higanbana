from __future__ import annotations

import hashlib
import importlib.util
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "compare_databento_canonical_content.py"


def load_module():
    spec = importlib.util.spec_from_file_location("compare_databento_canonical_content", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load canonical content comparator")
    module = importlib.util.module_from_spec(spec)
    sys.modules["compare_databento_canonical_content"] = module
    spec.loader.exec_module(module)
    return module


class CanonicalContentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.comparator = load_module()

    def test_scalar_normalization_is_deterministic(self) -> None:
        self.assertEqual("1.25", self.comparator._canonical_scalar(1.25))
        self.assertEqual("NaN", self.comparator._canonical_scalar(float("nan")))
        self.assertEqual({"bytes_hex": "00ff"}, self.comparator._canonical_scalar(b"\x00\xff"))

    def test_record_level_diff_reports_first_sorted_difference(self) -> None:
        current = {"records": ['{"a":1}', '{"a":3}'], "record_type_counts": {"193": 2}}
        fresh = {"records": ['{"a":1}', '{"a":4}'], "record_type_counts": {"193": 2}}
        diff = self.comparator._record_level_diff(current, fresh)
        self.assertEqual(1, diff["first_divergent_record"]["sorted_index"])
        self.assertEqual({"a": 3}, diff["first_divergent_record"]["current_record"])
        self.assertEqual({"a": 4}, diff["first_divergent_record"]["fresh_record"])

    def test_dbn_section_hashes_exclude_metadata_header(self) -> None:
        metadata = b"metadata"
        body = b"market-record-body"
        stream = b"DBN\x03" + len(metadata).to_bytes(4, byteorder="little") + metadata + body
        from lib.integrity import dbn_section_hashes

        result = dbn_section_hashes(stream)
        self.assertEqual(len(metadata) + 8, result["metadata_header_bytes"])
        self.assertEqual(len(body), result["bytes"])
        self.assertEqual(
            hashlib.sha256(body).hexdigest(),
            result["sha256"],
        )

    def test_markdown_renderer_has_one_terminal_newline(self) -> None:
        rendered = self.comparator.render_markdown({"status": "pass", "rows": []})
        self.assertTrue(rendered.endswith("\n"))
        self.assertFalse(rendered.endswith("\n\n"))


if __name__ == "__main__":
    unittest.main()
