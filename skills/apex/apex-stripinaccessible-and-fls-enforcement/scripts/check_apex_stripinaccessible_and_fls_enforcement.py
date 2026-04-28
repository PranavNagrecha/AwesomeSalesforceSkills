#!/usr/bin/env python3
"""Checker for Apex stripInaccessible / FLS enforcement skill.

Scans .cls and .trigger files for three anti-patterns:

  P0: Security.stripInaccessible(...).getRecords() / a SObjectAccessDecision is
      captured, then DML is performed on the ORIGINAL parameter rather than the
      stripped result. This silently defeats the strip.

  P1: A method takes a parameter whose name suggests a user-supplied record
      list (records / userSupplied / input / payload) AND performs DML on it
      WITHOUT any Security.stripInaccessible call in the same method.

  P2: Same method has WITH USER_MODE (or WITH SECURITY_ENFORCED) on a SOQL
      query AND a Security.stripInaccessible(AccessType.READABLE, ...) on the
      same path. Redundant double enforcement.

Exit code 1 if any P0 or P1 issue is found. Exit 0 otherwise. P2 issues are
reported as warnings but do not change the exit code.

Usage:
    python3 check_apex_stripinaccessible_and_fls_enforcement.py [--manifest-dir path]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


METHOD_HEADER = re.compile(
    r"(?:public|private|protected|global)\s+(?:static\s+)?"
    r"(?:[\w<>,\[\]\s\?]+?)\s+(\w+)\s*\(([^)]*)\)\s*\{",
    re.MULTILINE,
)
STRIP_CALL = re.compile(
    r"Security\.stripInaccessible\s*\(\s*AccessType\.(\w+)\s*,\s*([\w\.]+)\s*\)",
    re.IGNORECASE,
)
DECISION_ASSIGN = re.compile(
    r"SObjectAccessDecision\s+(\w+)\s*=\s*Security\.stripInaccessible",
)
DML = re.compile(r"\b(insert|update|upsert|delete)\s+([\w\.\(\)]+)\s*;")
USER_MODE_SOQL = re.compile(r"WITH\s+(USER_MODE|SECURITY_ENFORCED)", re.IGNORECASE)
USER_SUPPLIED_NAMES = re.compile(
    r"\b(records|userSupplied|input|payload|incoming|fromClient)\b",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex for stripInaccessible / FLS anti-patterns.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def extract_method_bodies(text: str) -> list[tuple[str, str, int]]:
    """Return list of (method_name, body, start_line) tuples.

    Bodies are extracted by brace-matching from the opening { of each header.
    """
    out: list[tuple[str, str, int]] = []
    for m in METHOD_HEADER.finditer(text):
        method_name = m.group(1)
        # Skip obvious non-methods (constructors, control statements parsed as headers)
        if method_name in {"if", "for", "while", "switch", "catch", "try"}:
            continue
        body_start = m.end() - 1  # position of the opening {
        depth = 0
        i = body_start
        while i < len(text):
            ch = text[i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    body = text[body_start : i + 1]
                    line_no = text[: m.start()].count("\n") + 1
                    out.append((method_name, body, line_no))
                    break
            i += 1
    return out


def analyze_method(name: str, body: str, line_no: int, rel_path: str) -> list[str]:
    issues: list[str] = []

    strip_calls = list(STRIP_CALL.finditer(body))
    decisions = [m.group(1) for m in DECISION_ASSIGN.finditer(body)]
    dmls = list(DML.finditer(body))
    has_user_mode_query = bool(USER_MODE_SOQL.search(body))

    # P0: strip call exists, but DML targets the original argument that was stripped
    stripped_args = {m.group(2).split(".")[0] for m in strip_calls}
    if strip_calls and dmls:
        for dml_match in dmls:
            dml_target = dml_match.group(2).split(".")[0].split("(")[0]
            if dml_target in stripped_args:
                # DML target is the same identifier that was passed into stripInaccessible
                # AND is NOT a decision.getRecords() chain
                if "getRecords" not in dml_match.group(0):
                    line = line_no + body[: dml_match.start()].count("\n")
                    issues.append(
                        f"P0 {rel_path}:{line}: DML on '{dml_target}' after "
                        f"Security.stripInaccessible — strip is bypassed; "
                        f"use decision.getRecords() instead"
                    )

    # P1: method takes a user-supplied-looking parameter and does DML, no strip
    if not strip_calls and dmls:
        # crude param scan from the body opening — re-scan first 200 chars
        if USER_SUPPLIED_NAMES.search(body[:400]):
            line = line_no
            issues.append(
                f"P1 {rel_path}:{line}: method '{name}' performs DML on "
                f"user-supplied input without Security.stripInaccessible"
            )

    # P2: USER_MODE query + READABLE strip in same method (warning only)
    if has_user_mode_query:
        for sm in strip_calls:
            if sm.group(1).upper() == "READABLE":
                line = line_no + body[: sm.start()].count("\n")
                issues.append(
                    f"P2 {rel_path}:{line}: WITH USER_MODE query + "
                    f"stripInaccessible(READABLE, ...) is redundant — pick one"
                )

    # Also flag unused decisions (decision assigned, never .getRecords())
    for dec in decisions:
        if f"{dec}.getRecords" not in body:
            issues.append(
                f"P0 {rel_path}:{line_no}: SObjectAccessDecision '{dec}' "
                f"never has getRecords() called — strip result is unused"
            )

    return issues


def check_apex(root: Path) -> tuple[list[str], list[str]]:
    """Return (blocking_issues, warning_issues)."""
    blocking: list[str] = []
    warning: list[str] = []
    files = list(root.rglob("*.cls")) + list(root.rglob("*.trigger"))
    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        try:
            rel = str(path.relative_to(root))
        except ValueError:
            rel = str(path)
        for name, body, line_no in extract_method_bodies(text):
            for issue in analyze_method(name, body, line_no, rel):
                if issue.startswith("P0") or issue.startswith("P1"):
                    blocking.append(issue)
                else:
                    warning.append(issue)
    return blocking, warning


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}", file=sys.stderr)
        return 1

    blocking, warning = check_apex(root)

    if not blocking and not warning:
        print("No stripInaccessible / FLS anti-patterns detected.")
        return 0

    for issue in warning:
        print(f"WARN: {issue}", file=sys.stderr)
    for issue in blocking:
        print(f"ISSUE: {issue}", file=sys.stderr)

    if blocking:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
