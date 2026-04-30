#!/usr/bin/env python3
"""Static checker for lookup-filter-cross-object-patterns skill.

Scans `objects/*/fields/*.field-meta.xml` files in a Salesforce DX project for
common lookup-filter mistakes:

- two-hop $Source traversal (e.g., $Source.A.B.C)
- function calls inside the filter expression
- required filter without an admin-bypass policy comment

Stdlib only; safe in pre-commit / CI.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

TWO_HOP = re.compile(r"\$Source(?:\.[A-Za-z_0-9]+){3,}")
FUNC_CALL = re.compile(r"\b(TRIM|UPPER|LOWER|TEXT|IF|CASE|VALUE|DATE|MID)\s*\(")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Check lookup filters for known bad patterns.")
    p.add_argument("--manifest-dir", default=".", help="Salesforce DX project root.")
    return p.parse_args()


def find_field_metadata(root: Path) -> list[Path]:
    return list(root.rglob("*.field-meta.xml"))


def check_field(path: Path) -> list[str]:
    issues: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"{path}: cannot read ({exc})"]

    if "<lookupFilter>" not in text:
        return issues

    if TWO_HOP.search(text):
        issues.append(
            f"{path}: lookup filter uses two-hop $Source traversal — flatten via formula field"
        )
    if FUNC_CALL.search(text):
        issues.append(
            f"{path}: lookup filter contains a function call — filters allow only field=field/value"
        )
    if "<isOptional>false</isOptional>" in text and "<bypassFlsForLookup>" not in text:
        issues.append(
            f"{path}: required lookup filter present without explicit FLS-bypass declaration; "
            "review profile-by-profile rollout"
        )
    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        print(f"ERROR: manifest dir not found: {root}", file=sys.stderr)
        return 1

    issues: list[str] = []
    for field in find_field_metadata(root):
        issues.extend(check_field(field))

    if not issues:
        print("[lookup-filter-cross-object-patterns] no issues found")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
