#!/usr/bin/env python3
"""Heuristic scanner for LWC focus-management anti-patterns.

Scans .js files for common bad patterns:
- `document.querySelector` inside an LWC module (shadow DOM leak).
- `.focus()` call inside connectedCallback.
- `.focus()` inside renderedCallback with no guard flag.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan LWC JS for focus-management anti-patterns.",
    )
    parser.add_argument(
        "--src-dir",
        default=".",
        help="LWC source directory.",
    )
    return parser.parse_args()


def check_file(path: Path) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore")

    if "document.querySelector" in text:
        issues.append(f"{path}: uses document.querySelector — shadow DOM leak risk")

    cc_match = re.search(r"connectedCallback\s*\([^)]*\)\s*\{([^}]*)\}", text, re.DOTALL)
    if cc_match and ".focus(" in cc_match.group(1):
        issues.append(f"{path}: .focus() inside connectedCallback (before render)")

    rc_match = re.search(r"renderedCallback\s*\([^)]*\)\s*\{([^}]*)\}", text, re.DOTALL)
    if rc_match:
        body = rc_match.group(1)
        if ".focus(" in body and "if" not in body:
            issues.append(f"{path}: .focus() in renderedCallback with no guard — will fire every render")

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.src_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}")
        return 1

    targets = list(root.rglob("*.js"))
    if not targets:
        print("No .js files found.")
        return 0

    all_issues: list[str] = []
    for path in targets:
        all_issues.extend(check_file(path))

    if not all_issues:
        print("No focus-management anti-patterns detected.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
