from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.audit_new_script_lib_usage import audit_new_script_lib_usage


class AuditNewScriptLibUsageTests(unittest.TestCase):
    def test_current_registry_passes(self) -> None:
        result = audit_new_script_lib_usage()
        self.assertEqual("pass", result["status"], result["blockers"])
        self.assertEqual(0, result["bypassing_lib_count"])

    def test_blocks_registered_script_without_lib_import(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scripts = root / "scripts"
            config_dir = root / "config"
            scripts.mkdir()
            config_dir.mkdir()
            scripts.joinpath("bad.py").write_text("import json\nprint(json.dumps({}))\n", encoding="utf-8")
            config = config_dir / "new_code_scripts.json"
            config.write_text(json.dumps({"scripts": ["scripts/bad.py"]}), encoding="utf-8")
            with patch("scripts.audit_new_script_lib_usage.PROJECT_ROOT", root):
                result = audit_new_script_lib_usage(config, root / "report.json")

        self.assertEqual("blocked", result["status"])
        self.assertEqual(1, result["bypassing_lib_count"])
        self.assertIn("blocked_no_lib_import:scripts/bad.py", result["blockers"])


if __name__ == "__main__":
    unittest.main()
