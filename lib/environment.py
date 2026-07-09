from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MACHINE_CONFIG_PATH = PROJECT_ROOT / "config" / "machine.json"


def _machine_config(path: Path | None = None) -> dict[str, Any]:
    path = path or MACHINE_CONFIG_PATH
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"machine config must be a JSON object: {path}")
    return payload


def _configured_path(env_name: str, config_key: str, default: Path | None) -> Path | None:
    raw = os.environ.get(env_name)
    if raw is None:
        raw = _machine_config().get(config_key)
    if raw in (None, ""):
        return default.resolve() if default is not None else None
    return Path(os.path.expandvars(os.path.expanduser(str(raw)))).resolve()


def data_root() -> Path:
    resolved = _configured_path("HIGANBANA_DATA_ROOT", "data_root", PROJECT_ROOT / "data")
    assert resolved is not None
    return resolved


def wiki_root() -> Path:
    workspace_default = PROJECT_ROOT.parents[2] / "LLM Wiki" / "LLM Wiki" / "wiki"
    resolved = _configured_path("HIGANBANA_WIKI_ROOT", "wiki_root", workspace_default)
    assert resolved is not None
    return resolved


def ibkr_python() -> Path | None:
    return _configured_path("HIGANBANA_IBKR_PYTHON", "ibkr_python", None)


def resolve_configured_path(value: str | Path) -> Path:
    text = str(value)
    replacements = {
        "${HIGANBANA_DATA_ROOT}": data_root(),
        "${HIGANBANA_WIKI_ROOT}": wiki_root(),
        "${HIGANBANA_IBKR_PYTHON}": ibkr_python(),
    }
    for token, root in replacements.items():
        if text == token:
            if root is None:
                raise ValueError(f"{token} is not configured")
            return root
        prefix = f"{token}/"
        if text.startswith(prefix):
            if root is None:
                raise ValueError(f"{token} is not configured")
            return root.joinpath(*Path(text[len(prefix) :]).parts)
    return Path(text)


def expand_configured_tokens(text: str) -> str:
    replacements = {
        "${HIGANBANA_DATA_ROOT}": data_root(),
        "${HIGANBANA_WIKI_ROOT}": wiki_root(),
        "${HIGANBANA_IBKR_PYTHON}": ibkr_python(),
    }
    expanded = text
    for token, root in replacements.items():
        if token in expanded:
            if root is None:
                raise ValueError(f"{token} is not configured")
            expanded = expanded.replace(token, root.as_posix())
    return expanded


def interpreter_metadata() -> dict[str, str]:
    return {
        "python_executable": sys.executable,
        "python_implementation": sys.implementation.name,
        "python_version": sys.version.split()[0],
    }
