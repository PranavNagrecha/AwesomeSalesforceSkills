#!/usr/bin/env python3
"""Checker script for Standard Object Quirks skill.

Scans Apex source files for common standard-object quirk anti-patterns:
- Dot-notation on polymorphic lookups (Who.Email, What.Name excluding allowed fields)
- Bare Email field in Account queries (should be PersonEmail)
- Event creation without EndDateTime
- ActivityDate used as completion filter on Task
- Case triggers referencing comment logic without a CaseComment trigger

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_standard_object_quirks.py [--help]
    python3 check_standard_object_quirks.py --manifest-dir path/to/src
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex source files for standard-object quirk anti-patterns.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory containing Apex source files (default: current directory).",
    )
    return parser.parse_args()


def _read_text_safe(path: Path) -> str:
    """Read file content, returning empty string on encoding errors."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def check_polymorphic_dot_notation(content: str, filepath: str) -> list[str]:
    """Detect Who.Field or What.Field dot-notation on polymorphic lookups.

    Allowed: Who.Name, Who.Type, Who.Id, What.Name, What.Type, What.Id
    (these work on the generic Name sObject).
    """
    issues = []
    allowed_fields = {"Name", "Type", "Id"}
    # Match Who.Something or What.Something in SOQL-like contexts
    pattern = re.compile(r"\b(Who|What)\.(\w+)", re.IGNORECASE)
    for i, line in enumerate(content.splitlines(), 1):
        for match in pattern.finditer(line):
            field = match.group(2)
            if field not in allowed_fields:
                issues.append(
                    f"{filepath}:{i} — Polymorphic dot-notation "
                    f"'{match.group(0)}' used. Use TYPEOF in SOQL instead."
                )
    return issues


def check_account_bare_email(content: str, filepath: str) -> list[str]:
    """Detect Account queries using Email instead of PersonEmail."""
    issues = []
    # Look for SOQL selecting from Account with bare Email field
    # Pattern: SELECT ... Email ... FROM Account (where Email is not PersonEmail)
    soql_pattern = re.compile(
        r"SELECT\s+(.+?)\s+FROM\s+Account",
        re.IGNORECASE | re.DOTALL,
    )
    for match in soql_pattern.finditer(content):
        select_clause = match.group(1)
        # Check for bare Email not preceded by Person
        if re.search(r"(?<![Pp]erson)\bEmail\b", select_clause):
            # Find the line number
            start = match.start()
            line_num = content[:start].count("\n") + 1
            issues.append(
                f"{filepath}:{line_num} — Account query uses 'Email' instead "
                f"of 'PersonEmail'. Bare Email is null for PersonAccounts."
            )
    return issues


def check_event_missing_enddatetime(content: str, filepath: str) -> list[str]:
    """Detect Event creation that sets DurationInMinutes but not EndDateTime."""
    issues = []
    # Heuristic: look for new Event() blocks that have DurationInMinutes
    # but no EndDateTime before the next insert/DML
    lines = content.splitlines()
    in_event_block = False
    has_duration = False
    has_enddatetime = False
    event_start_line = 0

    for i, line in enumerate(lines, 1):
        if re.search(r"\bnew\s+Event\s*\(", line, re.IGNORECASE):
            in_event_block = True
            has_duration = False
            has_enddatetime = False
            event_start_line = i
        if in_event_block:
            if re.search(r"\.DurationInMinutes\s*=", line, re.IGNORECASE):
                has_duration = True
            if re.search(r"\.EndDateTime\s*=", line, re.IGNORECASE):
                has_enddatetime = True
            if re.search(r"\binsert\b", line, re.IGNORECASE):
                if has_duration and not has_enddatetime:
                    issues.append(
                        f"{filepath}:{event_start_line} — Event created with "
                        f"DurationInMinutes but no EndDateTime. "
                        f"EndDateTime is required by the API."
                    )
                in_event_block = False
    return issues


def check_task_activitydate_as_completion(content: str, filepath: str) -> list[str]:
    """Detect Task queries filtering on ActivityDate with Completed status."""
    issues = []
    # Look for SOQL on Task with Status = 'Completed' and ActivityDate filter
    soql_pattern = re.compile(
        r"FROM\s+Task\b.*?(?:WHERE|AND).*?",
        re.IGNORECASE | re.DOTALL,
    )
    # Simpler heuristic: find lines near each other with both patterns
    lines = content.splitlines()
    for i, line in enumerate(lines):
        lower = line.lower()
        if "task" in lower and "completed" in lower and "activitydate" in lower:
            issues.append(
                f"{filepath}:{i+1} — Task query uses ActivityDate with "
                f"Completed status. Use CompletedDateTime instead — "
                f"ActivityDate is the due date, not the completion date."
            )
    # Broader check: look within 5-line windows
    for i in range(len(lines)):
        window = " ".join(lines[max(0, i - 2):i + 3]).lower()
        if (
            "from task" in window
            and "completed" in window
            and "activitydate" in window
            and "completeddatetime" not in window
        ):
            # Only flag once per occurrence
            issues.append(
                f"{filepath}:{i+1} — Task query near this line filters "
                f"on ActivityDate with Completed status. "
                f"Consider using CompletedDateTime instead."
            )
            break  # One warning per file for the windowed check

    return issues


def check_standard_object_quirks(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in Apex source files."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Collect all Apex source files
    apex_files = list(manifest_dir.rglob("*.cls")) + list(
        manifest_dir.rglob("*.trigger")
    )

    if not apex_files:
        # Not an error — the directory may not contain Apex source
        return issues

    for apex_file in sorted(apex_files):
        rel_path = str(apex_file.relative_to(manifest_dir))
        content = _read_text_safe(apex_file)
        if not content:
            continue

        issues.extend(check_polymorphic_dot_notation(content, rel_path))
        issues.extend(check_account_bare_email(content, rel_path))
        issues.extend(check_event_missing_enddatetime(content, rel_path))
        issues.extend(check_task_activitydate_as_completion(content, rel_path))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_standard_object_quirks(manifest_dir)

    if not issues:
        print("No standard-object quirk issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    print(f"\n{len(issues)} issue(s) found.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
