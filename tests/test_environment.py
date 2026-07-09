from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lib import environment


class EnvironmentTests(unittest.TestCase):
    def test_environment_variable_overrides_default(self) -> None:
        expected = Path(tempfile.gettempdir()) / "higanbana-data-root"
        with patch.dict(os.environ, {"HIGANBANA_DATA_ROOT": str(expected)}, clear=False):
            self.assertEqual(expected.resolve(), environment.data_root())

    def test_machine_config_is_used_when_environment_is_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "machine.json"
            expected = Path(tmp) / "wiki"
            config_path.write_text(json.dumps({"wiki_root": str(expected)}), encoding="utf-8")
            with patch.object(environment, "MACHINE_CONFIG_PATH", config_path):
                with patch.dict(os.environ, {}, clear=True):
                    self.assertEqual(expected.resolve(), environment.wiki_root())

    def test_wiki_token_resolves_under_configured_root(self) -> None:
        root = Path(tempfile.gettempdir()) / "higanbana-wiki-root"
        with patch.dict(os.environ, {"HIGANBANA_WIKI_ROOT": str(root)}, clear=False):
            actual = environment.resolve_configured_path(
                "${HIGANBANA_WIKI_ROOT}/concepts/minimum-track-record-length.md"
            )
        self.assertEqual(root.resolve() / "concepts" / "minimum-track-record-length.md", actual)

    def test_tokens_expand_inside_json_text(self) -> None:
        root = Path(tempfile.gettempdir()) / "higanbana-wiki-root"
        with patch.dict(os.environ, {"HIGANBANA_WIKI_ROOT": str(root)}, clear=False):
            actual = environment.expand_configured_tokens(
                '{"path":"${HIGANBANA_WIKI_ROOT}/concepts/example.md"}'
            )
        self.assertIn(f'{root.resolve().as_posix()}/concepts/example.md', actual)

    def test_interpreter_metadata_is_uniform_and_nonempty(self) -> None:
        metadata = environment.interpreter_metadata()
        self.assertEqual(
            {"python_executable", "python_implementation", "python_version"},
            set(metadata),
        )
        self.assertTrue(all(metadata.values()))
