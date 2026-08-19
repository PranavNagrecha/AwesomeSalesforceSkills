#!/usr/bin/env python3
"""Launch the SfSkills MCP server from a Cursor plugin install."""

from __future__ import annotations

import json
import os
import runpy
import sys
from pathlib import Path


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    pointer = here.parent.parent / "repo-root.json"
    if pointer.is_file():
        raw = json.loads(pointer.read_text(encoding="utf-8"))
        path = Path(raw["repo_root"])
        if (path / "mcp" / "sfskills-mcp" / "src").is_dir():
            return path
    for parent in here.parents:
        if (parent / "mcp" / "sfskills-mcp" / "src" / "sfskills_mcp").is_dir():
            return parent
    raise SystemExit(
        "Cannot locate SfSkills checkout. Re-run "
        "python3 scripts/install_cursor_plugin.py --link"
    )


def main() -> None:
    root = _repo_root()
    src = root / "mcp" / "sfskills-mcp" / "src"
    os.environ.setdefault("SFSKILLS_REPO_ROOT", str(root))
    sys.path.insert(0, str(src))
    sys.path.insert(0, str(root))
    runpy.run_module("sfskills_mcp", run_name="__main__")


if __name__ == "__main__":
    main()
