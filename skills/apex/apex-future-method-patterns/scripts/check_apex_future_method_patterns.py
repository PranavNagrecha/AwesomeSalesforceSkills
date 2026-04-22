#!/usr/bin/env python3
"""Checker for Apex Future Method Patterns skill.

Scans Apex for:
- @future methods missing callout=true when callouts are made
- @future methods accepting SObject parameters
- @future methods with non-void return types
- @future methods calling enqueueJob or other @future methods

Usage:
    python3 check_apex_future_method_patterns.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


FUTURE_DECL = re.compile(
    r"@future(?:\(([^)]*)\))?\s*\n?\s*(public|private|global)\s+static\s+(\w+(?:<[^>]+>)?)\s+(\w+)\s*\(([^)]*)\)",
    re.IGNORECASE | re.MULTILINE,
)
SOBJECT_PARAM = re.compile(r"\b(Account|Contact|Opportunity|Lead|Case|SObject|List<\w+>|Map<Id,\s*\w+>)\b")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check @future anti-patterns.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of metadata.")
    return parser.parse_args()


def check_apex(root: Path) -> list[str]:
    issues: list[str] = []
    for path in root.rglob("*.cls"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        for m in FUTURE_DECL.finditer(text):
            annot_args = (m.group(1) or "").lower()
            return_type = m.group(3)
            params = m.group(5)
            method_name = m.group(4)
            line_no = text[: m.start()].count("\n") + 1

            # body detection: find matching braces
            body_start = text.find("{", m.end())
            if body_start == -1:
                continue
            depth = 1
            i = body_start + 1
            while i < len(text) and depth:
                if text[i] == "{":
                    depth += 1
                elif text[i] == "}":
                    depth -= 1
                i += 1
            body = text[body_start:i]

            if return_type.lower() != "void":
                issues.append(
                    f"{path.relative_to(root)}:{line_no}: @future method '{method_name}' has non-void return"
                )

            # SObject param check (exclude primitive-collection variants)
            params_clean = params.replace("Set<Id>", "").replace("List<Id>", "").replace("Set<String>", "").replace("List<String>", "")
            for sm in SOBJECT_PARAM.finditer(params_clean):
                issues.append(
                    f"{path.relative_to(root)}:{line_no}: @future '{method_name}' accepts {sm.group(1)}; pass Ids instead"
                )
                break

            if ("new Http(" in body or "HttpRequest" in body or ".send(" in body) and "callout=true" not in annot_args:
                issues.append(
                    f"{path.relative_to(root)}:{line_no}: @future '{method_name}' makes callouts without callout=true"
                )

            if "enqueueJob" in body:
                issues.append(
                    f"{path.relative_to(root)}:{line_no}: @future '{method_name}' calls enqueueJob; chaining from @future is not allowed"
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
        print("No @future anti-patterns detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
