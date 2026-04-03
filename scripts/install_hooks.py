#!/usr/bin/env python3
"""Install repo-local git hooks for validation and sync."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    git_dir = ROOT / ".git"
    if not git_dir.exists():
        print("No .git directory found. Install hooks manually once this repo is initialized as a git repository.")
        print("Suggested command:")
        print("  git config core.hooksPath .githooks")
        return 0

    subprocess.run(["git", "config", "core.hooksPath", ".githooks"], cwd=ROOT, check=True)
    print("Configured git hooks to use .githooks/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
