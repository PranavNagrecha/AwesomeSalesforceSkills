#!/usr/bin/env python3
"""Checker script for Omniscript Design Patterns skill."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Omniscript Design Patterns configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def count(pattern: str, text: str) -> int:
    return len(re.findall(pattern, text, flags=re.IGNORECASE))


def check_omniscript_design_patterns(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    for path in sorted(manifest_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".json", ".xml"}:
            continue

        text = path.read_text(encoding="utf-8", errors="ignore")
        if "omniscript" not in text.lower() and "omniscript" not in path.name.lower():
            continue

        step_count = count(r"\bstep\b", text)
        branch_count = count(r"branch|conditional", text)
        custom_component_count = count(r"custom\s*lwc|lightning web component|component", text)
        remote_action_count = count(r"remote action|integration procedure action|dataraptor", text)

        if step_count > 15:
            issues.append(f"{path}: OmniScript appears to contain many step markers ({step_count}); review whether the journey should be simplified.")
        if branch_count > 8:
            issues.append(f"{path}: OmniScript appears heavily branched ({branch_count} branch markers); review default paths and testability.")
        if remote_action_count > 6:
            issues.append(f"{path}: OmniScript appears to depend on many backend actions ({remote_action_count}); consider delegating more cleanly behind the guided layer.")
        if custom_component_count > 10:
            issues.append(f"{path}: OmniScript references many component markers ({custom_component_count}); review whether custom LWCs are overused.")

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_omniscript_design_patterns(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
