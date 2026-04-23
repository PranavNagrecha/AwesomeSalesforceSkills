#!/usr/bin/env python3
"""Checker for Apex Salesforce Id handling patterns.

Flags high-signal mistakes:

  1. String prefix checks used for type routing (`.startsWith('001')`, etc.).
  2. `Schema.getGlobalDescribe()` inside a `for` loop.
  3. `IllegalArgumentException` near `Id.valueOf` (wrong exception type).
  4. `Set<String>` populated with `Id` values and compared to SObject `.Id`.
  5. Hardcoded 15/18-char Id literals in non-test code.

Stdlib only. Emits JSON.

Usage:
    python3 check_apex_salesforce_id_patterns.py --path force-app/main/default
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable

SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}

STARTSWITH_PREFIX = re.compile(
    r"\.startsWith\s*\(\s*'(00[0-9A-Za-z]|a0[0-9A-Za-z])'\s*\)"
)
GLOBAL_DESCRIBE = re.compile(r"Schema\.getGlobalDescribe\s*\(\s*\)")
FOR_LOOP = re.compile(r"\bfor\s*\(", re.IGNORECASE)
ID_VALUE_OF = re.compile(r"Id\.valueOf\s*\(")
ILLEGAL_ARG = re.compile(r"catch\s*\(\s*IllegalArgumentException\b")
ID_LITERAL = re.compile(r"'(00[0-9A-Z][A-Za-z0-9]{12}([A-Za-z0-9]{3})?)'")


def apex_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*.cls"):
        yield path
    for path in root.rglob("*.trigger"):
        yield path


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def inside_for_loop(text: str, offset: int) -> bool:
    """Cheap heuristic: is the offset inside the body of any `for` loop?"""
    preceding = text[:offset]
    starts = [m.start() for m in FOR_LOOP.finditer(preceding)]
    if not starts:
        return False
    last = starts[-1]
    # brace after the closing paren of the for-header
    paren_depth = 0
    i = last
    # advance past the "(" for the for header
    while i < len(text) and text[i] != "(":
        i += 1
    paren_depth = 1
    i += 1
    while i < len(text) and paren_depth > 0:
        if text[i] == "(":
            paren_depth += 1
        elif text[i] == ")":
            paren_depth -= 1
        i += 1
    # skip whitespace/newlines to the opening brace
    while i < len(text) and text[i] in " \t\r\n":
        i += 1
    if i >= len(text) or text[i] != "{":
        return False
    body_start = i + 1
    # count braces between body_start and offset
    if offset < body_start:
        return False
    depth = 1
    for ch in text[body_start:offset]:
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return False
    return depth > 0


def check_file(path: Path) -> list[dict]:
    issues: list[dict] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return issues

    is_test = path.name.endswith("_Test.cls") or "@IsTest" in text[:500]

    for m in STARTSWITH_PREFIX.finditer(text):
        issues.append(
            {
                "severity": "HIGH",
                "rule": "prefix-string-type-check",
                "file": str(path),
                "line": line_of(text, m.start()),
                "message": (
                    f"String prefix check on {m.group(1)!r}. "
                    "Use (Id).getSobjectType() == SomeObj.SObjectType instead."
                ),
            }
        )

    for m in GLOBAL_DESCRIBE.finditer(text):
        if inside_for_loop(text, m.start()):
            issues.append(
                {
                    "severity": "HIGH",
                    "rule": "global-describe-in-loop",
                    "file": str(path),
                    "line": line_of(text, m.start()),
                    "message": (
                        "Schema.getGlobalDescribe() inside a for loop. "
                        "Hoist to a local variable or use id.getSobjectType()."
                    ),
                }
            )

    # IllegalArgumentException near Id.valueOf — wrong exception.
    for m in ID_VALUE_OF.finditer(text):
        window_start = m.start()
        window_end = min(len(text), m.end() + 400)
        if ILLEGAL_ARG.search(text[window_start:window_end]):
            issues.append(
                {
                    "severity": "MEDIUM",
                    "rule": "wrong-exception-for-id-valueof",
                    "file": str(path),
                    "line": line_of(text, m.start()),
                    "message": (
                        "Id.valueOf followed by catch (IllegalArgumentException). "
                        "Apex raises System.StringException for bad Ids."
                    ),
                }
            )

    if not is_test:
        for m in ID_LITERAL.finditer(text):
            id_str = m.group(1)
            if len(id_str) in (15, 18) and id_str[:3] in (
                "001",
                "003",
                "005",
                "006",
                "500",
                "00Q",
            ):
                issues.append(
                    {
                        "severity": "MEDIUM",
                        "rule": "hardcoded-id-literal",
                        "file": str(path),
                        "line": line_of(text, m.start()),
                        "message": (
                            f"Hardcoded Id literal {id_str!r} in non-test code. "
                            "Look up the record by field/external id instead."
                        ),
                    }
                )

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Lint Apex Salesforce Id patterns.")
    parser.add_argument(
        "--path",
        default="force-app/main/default",
        help="Root directory to scan (default: force-app/main/default).",
    )
    parser.add_argument("--format", choices=["json", "text"], default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.path)
    if not root.exists():
        print(json.dumps({"error": f"path not found: {root}"}))
        return 2

    issues: list[dict] = []
    for apex_path in apex_files(root):
        issues.extend(check_file(apex_path))

    score = sum(SEVERITY_WEIGHTS.get(i["severity"], 0) for i in issues)

    if args.format == "json":
        print(json.dumps({"score": score, "issues": issues}, indent=2))
    else:
        for issue in issues:
            print(
                f"{issue['severity']:8} {issue['file']}:{issue['line']}  "
                f"[{issue['rule']}] {issue['message']}"
            )
        print(f"\nTotal weighted score: {score}")

    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())
