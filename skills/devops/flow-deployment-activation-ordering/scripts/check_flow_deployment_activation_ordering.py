#!/usr/bin/env python3
"""Heuristic checker for Flow deploy runbooks.

Scans markdown runbook docs for required sections and common omissions
(no pre-deploy inventory, no rollback plan, no activation-mode decision).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED_SECTIONS = (
    "scope",
    "pre-deploy inventory",
    "activation mode",
    "order",
    "smoke tests",
    "rollback",
    "post-deploy verification",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect Flow deploy runbooks.",
    )
    parser.add_argument(
        "--docs-dir",
        default=".",
        help="Directory containing runbook markdown files.",
    )
    return parser.parse_args()


def check_file(path: Path) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore").lower()

    for section in REQUIRED_SECTIONS:
        if section not in text:
            issues.append(f"{path}: missing required section '{section}'")

    if "paused interview" not in text:
        issues.append(f"{path}: no paused-interview risk analysis")

    if "pointer" not in text and "flowdefinition" not in text and "activeversion" not in text:
        issues.append(f"{path}: rollback plan does not mention FlowDefinition pointer flip")

    if "subflow" not in text and "callee" not in text:
        issues.append(f"{path}: subflow/callee deploy order not addressed")

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.docs_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}")
        return 1

    targets = list(root.rglob("*.md"))
    if not targets:
        print("No runbook docs found.")
        return 0

    all_issues: list[str] = []
    for path in targets:
        all_issues.extend(check_file(path))

    if not all_issues:
        print("Runbooks look complete.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
