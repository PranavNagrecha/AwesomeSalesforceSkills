#!/usr/bin/env python3
"""Heuristic scanner for LWC streaming anti-patterns.

Scans .js files that import from `lightning/empApi` for:
- subscribe() without a matching unsubscribe().
- subscribe() in renderedCallback (wrong lifecycle).
- No onError handler.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan LWC JS for empApi subscription anti-patterns.",
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

    if "lightning/empApi" not in text and "empApi" not in text:
        return issues

    if "subscribe(" in text and "unsubscribe(" not in text:
        issues.append(f"{path}: subscribe() without unsubscribe() — memory/delivery leak")

    if "renderedCallback" in text and "subscribe(" in text:
        rc_idx = text.find("renderedCallback")
        cc_idx = text.find("connectedCallback")
        if cc_idx == -1 or (rc_idx != -1 and rc_idx < text.find("subscribe(") < text.find("}", rc_idx)):
            issues.append(f"{path}: subscribe() appears inside renderedCallback — use connectedCallback")

    if "onError(" not in text:
        issues.append(f"{path}: no onError listener — reconnection not handled")

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
        print("No streaming anti-patterns detected.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
