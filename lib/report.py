from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from lib.environment import interpreter_metadata
from lib.io import write_json


def render_markdown_report(title: str, sections: Iterable[tuple[str, str]]) -> str:
    lines = [f"# {title}", ""]
    for heading, body in sections:
        lines.extend([f"## {heading}", "", body.rstrip(), ""])
    return "\n".join(lines)


def write_report_pair(payload: dict[str, Any], json_path: Path, markdown_path: Path, markdown: str) -> dict[str, Any]:
    stored = {**payload}
    stored.setdefault("interpreter", interpreter_metadata())
    write_json(json_path, stored)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(markdown.rstrip() + "\n", encoding="utf-8")
    return stored
