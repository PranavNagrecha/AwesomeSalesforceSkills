#!/usr/bin/env python3
"""Checker for Platform Event Publish Patterns skill.

Scans Apex for:
- EventBus.publish calls whose SaveResult is discarded
- Single-event publish inside a for/while loop
- Tests that publish events but lack Test.getEventBus().deliver()

Usage:
    python3 check_platform_event_publish_patterns.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


PUBLISH_CALL = re.compile(r"EventBus\.publish\s*\(", re.IGNORECASE)
# A publish whose return is discarded: standalone statement, not assigned.
DISCARDED_PUBLISH = re.compile(
    r"(?<![=<>\w.])EventBus\.publish\s*\([^;]*\)\s*;", re.IGNORECASE
)
PUBLISH_IN_LOOP = re.compile(
    r"(for|while)\s*\([^)]*\)\s*\{[^}]*EventBus\.publish\s*\(",
    re.IGNORECASE | re.DOTALL,
)
TEST_ANNOTATION = re.compile(r"@IsTest", re.IGNORECASE)
DELIVER_CALL = re.compile(r"Test\.getEventBus\(\)\.deliver\s*\(", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Platform Event publish anti-patterns.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of metadata.")
    return parser.parse_args()


def check_apex(root: Path) -> list[str]:
    issues: list[str] = []
    for path in list(root.rglob("*.cls")) + list(root.rglob("*.trigger")):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        # Discarded SaveResult on non-bulk publish — warn when return not captured
        for m in DISCARDED_PUBLISH.finditer(text):
            # Skip if call is part of a List<> bulk publish that still discards; we still warn.
            line_no = text[: m.start()].count("\n") + 1
            issues.append(
                f"{path.relative_to(root)}:{line_no}: EventBus.publish result discarded; inspect SaveResult"
            )

        for m in PUBLISH_IN_LOOP.finditer(text):
            # Avoid false positive when loop body clearly builds a list first; heuristic only.
            window = m.group(0)
            if "new List<" not in window:
                line_no = text[: m.start()].count("\n") + 1
                issues.append(
                    f"{path.relative_to(root)}:{line_no}: EventBus.publish inside loop; build a list and bulk-publish"
                )

        # Test class publishing events without deliver()
        if TEST_ANNOTATION.search(text) and PUBLISH_CALL.search(text):
            if not DELIVER_CALL.search(text):
                issues.append(
                    f"{path.relative_to(root)}: test publishes events but lacks Test.getEventBus().deliver()"
                )
    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}", file=sys.stderr)
        return 1

    issues = check_apex(root)
    if not issues:
        print("No Platform Event publish anti-patterns detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
