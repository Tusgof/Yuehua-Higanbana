from __future__ import annotations

import tempfile
import unittest
import os
from pathlib import Path
from unittest.mock import patch

from tests.tiers import state_audit


class TestTierTests(unittest.TestCase):
    def test_state_audit_marks_test_class(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            existing = Path(tmp)

            with patch.dict(os.environ, {"HIGANBANA_TEST_TIER": ""}):
                @state_audit(("fixture", existing))
                class StateTest(unittest.TestCase):
                    def test_example(self) -> None:
                        pass

        self.assertEqual("state-audit", StateTest.higanbana_test_tier)
        self.assertFalse(getattr(StateTest, "__unittest_skip__", False))

    def test_missing_state_root_skips_with_named_input(self) -> None:
        missing = Path(tempfile.gettempdir()) / "higanbana-definitely-missing-root"

        with patch.dict(os.environ, {"HIGANBANA_TEST_TIER": ""}):
            @state_audit(("HIGANBANA_DATA_ROOT", missing))
            class StateTest(unittest.TestCase):
                def test_example(self) -> None:
                    pass

        self.assertTrue(StateTest.__unittest_skip__)
        self.assertIn("HIGANBANA_DATA_ROOT", StateTest.__unittest_skip_why__)
