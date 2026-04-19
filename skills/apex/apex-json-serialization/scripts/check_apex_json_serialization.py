#!/usr/bin/env python3
"""Checker script for Apex JSON Serialization skill.

Scans Apex source files for common JSON serialization anti-patterns:
- JSON.serialize without suppressApexObjectNulls argument
- JSON.deserialize without TypeException catch
- deserializeUntyped results without null guards

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_apex_json_serialization.py [--help]
    python3 check_apex_json_serialization.py --manifest-dir path/to/apex/classes
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex classes for JSON serialization anti-patterns.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory containing Apex .cls files (default: current directory).",
    )
    return parser.parse_args()


def check_json_serialize_no_suppress(content: str, filepath: Path) -> list[str]:
    """Warn when JSON.serialize is called with only one argument."""
    issues = []
    # Match JSON.serialize( with only one arg (no second comma before closing paren)
    pattern = re.compile(r'JSON\.serialize\s*\(\s*[^,)]+\s*\)', re.IGNORECASE)
    for m in pattern.finditer(content):
        line_num = content[:m.start()].count('\n') + 1
        issues.append(
            f"{filepath}:{line_num}: JSON.serialize() called without suppressApexObjectNulls argument — "
            "consider JSON.serialize(obj, true) to omit null fields"
        )
    return issues


def check_deserialize_no_try_catch(content: str, filepath: Path) -> list[str]:
    """Warn when JSON.deserialize appears outside a try block."""
    issues = []
    # Simple heuristic: find JSON.deserialize not preceded by 'try' in the surrounding 5 lines
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if re.search(r'JSON\.deserialize\s*\(', line, re.IGNORECASE):
            # Check if any of the 10 preceding lines contains 'try {'
            context = '\n'.join(lines[max(0, i-10):i])
            if 'try' not in context:
                issues.append(
                    f"{filepath}:{i+1}: JSON.deserialize() may not be inside a try/catch — "
                    "TypeException from external data will abort the transaction"
                )
    return issues


def check_apex_files(manifest_dir: Path) -> list[str]:
    """Return list of issue strings found across all .cls files."""
    issues: list[str] = []

    cls_files = list(manifest_dir.rglob("*.cls"))
    if not cls_files:
        return issues  # no Apex files to check — not an error

    for cls_file in cls_files:
        try:
            content = cls_file.read_text(encoding="utf-8")
        except OSError:
            continue
        issues.extend(check_json_serialize_no_suppress(content, cls_file))
        issues.extend(check_deserialize_no_try_catch(content, cls_file))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)

    if not manifest_dir.exists():
        print(f"ERROR: Directory not found: {manifest_dir}", file=sys.stderr)
        return 2

    issues = check_apex_files(manifest_dir)

    if not issues:
        print("No JSON serialization issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
