#!/usr/bin/env python3
"""Heuristic checker for LWC performance budget manifests."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_TOP_KEYS = ("components", "pages", "meta")
REQUIRED_META_KEYS = ("reviewCadence", "owner", "waiverProcess")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect LWC budget manifest.")
    parser.add_argument("--manifest", default="budget-manifest.yaml")
    return parser.parse_args()


def check_file(path: Path) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore")

    for key in REQUIRED_TOP_KEYS:
        if not re.search(rf"^{key}\s*:", text, re.MULTILINE):
            issues.append(f"{path}: missing top-level key '{key}'")

    for key in REQUIRED_META_KEYS:
        if not re.search(rf"^\s+{key}\s*:", text, re.MULTILINE):
            issues.append(f"{path}: meta.{key} missing")

    if "maxMinifiedKb" not in text:
        issues.append(f"{path}: no bundle-size cap (maxMinifiedKb)")

    if "maxWireAdapters" not in text:
        issues.append(f"{path}: no wire-adapter cap (maxWireAdapters)")

    if "lcpMs" not in text:
        issues.append(f"{path}: no LCP budget (lcpMs)")

    if "inpMs" not in text:
        issues.append(f"{path}: no INP budget (inpMs)")

    if re.search(r"expiry\s*:", text):
        if re.search(r"expiry\s*:\s*\"?\s*$", text, re.MULTILINE):
            issues.append(f"{path}: waiver entry missing expiry value")

    return issues


def main() -> int:
    args = parse_args()
    path = Path(args.manifest)
    if not path.exists():
        print(f"ERROR: manifest not found: {path}")
        return 1

    issues = check_file(path)
    if not issues:
        print("Budget manifest looks complete.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
