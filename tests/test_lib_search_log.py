from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from lib.io import load_jsonl
from lib.search_log import write_search_log


class SearchLogTests(unittest.TestCase):
    def test_writes_sorted_jsonl_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "search_log.jsonl"
            written = write_search_log(path, [{"trial_index": 1, "z": 1, "a": 2}])
            rows = load_jsonl(path)

        self.assertEqual(1, written)
        self.assertEqual([{"a": 2, "trial_index": 1, "z": 1}], rows)
