#!/usr/bin/env python3
"""Checker script for Wire Service Patterns skill."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Wire Service Patterns configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_wire_service_patterns(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    for js_path in sorted(manifest_dir.rglob("*.js")):
        text = js_path.read_text(encoding="utf-8", errors="ignore")
        if "@wire" not in text:
            continue

        if "['$" in text or '["$' in text:
            issues.append(f"{js_path}: reactive wire parameters appear inside a quoted array element; review whether the `$` value is being treated as a literal string.")

        if re.search(r"this\.\w+\.data\.[A-Za-z_]\w*\s*=", text):
            issues.append(f"{js_path}: component appears to mutate wired `.data` directly; clone the payload before transformation.")

        reactive_params = set(re.findall(r"\$([A-Za-z_]\w*)", text))
        if reactive_params and "renderedCallback" in text:
            for param in reactive_params:
                pattern = rf"renderedCallback\s*\([^)]*\)\s*\{{[^}}]*this\.{re.escape(param)}\s*="
                if re.search(pattern, text, flags=re.DOTALL):
                    issues.append(
                        f"{js_path}: reactive wire parameter `{param}` is assigned in renderedCallback; review for re-evaluation loops."
                    )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_wire_service_patterns(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
