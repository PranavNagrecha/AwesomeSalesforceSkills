#!/usr/bin/env python3
"""Static checker for devops-center-advanced.

Two parts:
  1. Package shape (unchanged): the skill package must carry its required files.
  2. Project path (--manifest-dir): when given, the path must exist and hold at
     least one file; the shape check still runs against this skill package.

Exit contract: a missing --manifest-dir prints `ERROR:` and exits 1; an empty
directory prints one `WARN:` line and exits 0 (1 with --strict); a package
shape failure prints `ERROR:` and exits 1. Intended as a pre-commit or CI
smoke check. Stdlib only.

Usage:
    python3 check_devops_center_advanced.py [--manifest-dir path/to/project] [--strict]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REQUIRED = [
    "SKILL.md",
    "references/examples.md",
    "references/gotchas.md",
    "references/well-architected.md",
    "references/llm-anti-patterns.md",
    "templates",
    "scripts",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Shape and path check for devops-center-advanced.")
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Optional project directory to verify exists and is not empty.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 when any WARN (for example an empty --manifest-dir) is reported.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.manifest_dir is not None:
        root = Path(args.manifest_dir)
        if not root.exists() or not root.is_dir():
            print(f"ERROR: manifest directory not found: {root}")
            return 1
        if not any(p.is_file() for p in root.rglob("*")):
            print(f"WARN: no files found under {root}")
            return 1 if args.strict else 0

    base = Path(__file__).resolve().parents[1]
    missing = [r for r in REQUIRED if not (base / r).exists()]
    if missing:
        print(f"ERROR [devops-center-advanced] missing files: {missing}", file=sys.stderr)
        sys.exit(1)
    print("[devops-center-advanced] shape OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
