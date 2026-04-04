#!/usr/bin/env python3
"""Composite API Patterns — legacy entrypoint.

This script is retained for backward compatibility with the scaffolded name.
The primary checker is check_composite_api.py in the same directory.

Usage:
    python3 check_composite_api_patterns.py [--manifest-dir PATH]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Composite API Patterns configuration for common issues. "
            "Delegates to check_composite_api.py with the same directory."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory to scan (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    checker = Path(__file__).parent / "check_composite_api.py"
    result = subprocess.run(
        [sys.executable, str(checker), "--project-dir", args.manifest_dir],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    if result.returncode != 0:
        print("ERROR: check_composite_api.py reported issues — see output above.")
        sys.exit(1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
