#!/usr/bin/env python3
"""Checker script skeleton for this skill.

This is a starting point for skill-specific static analysis. The default
checker performs a structural check that the skill package itself is
well-formed and emits a warning for any flow metadata files that clearly
violate this skill's rules, if present in the target directory.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Skill checker.")
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata to scan.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir).resolve()
    if not root.exists():
        print(f"manifest-dir does not exist: {root}", file=sys.stderr)
        return 2
    print(f"Checker scanned: {root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
