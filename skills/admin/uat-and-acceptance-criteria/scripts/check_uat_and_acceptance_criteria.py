#!/usr/bin/env python3
"""Checker script for UAT and Acceptance Criteria skill.

Validates a UAT test script or user story document (Markdown) for common
acceptance criteria and test script anti-patterns:
- Acceptance criteria that are not testable (vague language)
- Test cases missing expected results
- Test cases missing preconditions
- Acceptance criteria missing "if/then" structure
- Test cases that may have been run as admin only (missing profile precondition)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_uat_and_acceptance_criteria.py [--help]
    python3 check_uat_and_acceptance_criteria.py --file path/to/uat-script.md
    python3 check_uat_and_acceptance_criteria.py --file path/to/user-stories.md
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Patterns that indicate untestable acceptance criteria
VAGUE_CRITERIA_PATTERNS = [
    r"\bshould be (fast|easy|simple|intuitive|clean|nice|good|better|user.friendly)\b",
    r"\bshould look\b",
    r"\bshould feel\b",
    r"\bshould work\b",
    r"\bshould be obvious\b",
    r"\bshould be clear\b",
    r"\bshould be responsive\b",
    r"\bpages? should load\b",
    r"\bperformance should\b",
]

# Salesforce admin objects — indicates an acceptance criterion has Salesforce context
SF_OBJECTS = [
    "account", "contact", "opportunity", "case", "lead", "campaign",
    "task", "event", "user", "profile", "permission set", "record type",
    "page layout", "flow", "validation rule", "report", "dashboard",
    "field", "queue", "sharing", "role",
]


def check_acceptance_criteria(content: str) -> list[str]:
    """Check acceptance criteria blocks for common issues."""
    issues: list[str] = []
    lines = content.splitlines()

    in_ac_block = False
    ac_line_start = 0

    for i, line in enumerate(lines):
        # Detect acceptance criteria sections
        if re.search(r"acceptance criteria", line, re.IGNORECASE):
            in_ac_block = True
            ac_line_start = i
            continue

        # Exit acceptance criteria block on next heading
        if in_ac_block and re.match(r"^#{1,6}\s", line):
            in_ac_block = False

        if not in_ac_block:
            continue

        # Check for checklist items (- [ ] or - [x])
        ac_match = re.match(r"^\s*-\s*\[[ xX]\]\s*(.+)", line)
        if not ac_match:
            continue

        criterion = ac_match.group(1).strip()

        # Check for vague language
        for pattern in VAGUE_CRITERIA_PATTERNS:
            if re.search(pattern, criterion, re.IGNORECASE):
                issues.append(
                    f"Line {i + 1}: Acceptance criterion may be untestable (vague language): '{criterion[:80]}'"
                )
                break

        # Check for if/then structure
        has_if_then = bool(
            re.search(r"\bif\b.+\bthen\b", criterion, re.IGNORECASE)
        )
        has_given_when_then = bool(
            re.search(r"\b(given|when|then)\b", criterion, re.IGNORECASE)
        )
        if not has_if_then and not has_given_when_then:
            # Only warn if the criterion is long enough to warrant structure
            if len(criterion) > 30:
                issues.append(
                    f"Line {i + 1}: Acceptance criterion may lack if/then structure: '{criterion[:80]}'"
                )

        # Check for Salesforce object/feature reference
        has_sf_context = any(obj in criterion.lower() for obj in SF_OBJECTS)
        if not has_sf_context and len(criterion) > 20:
            issues.append(
                f"Line {i + 1}: Acceptance criterion may be missing a specific Salesforce object or feature reference: '{criterion[:80]}'"
            )

    return issues


def check_test_cases(content: str) -> list[str]:
    """Check Markdown table test cases for missing required fields."""
    issues: list[str] = []
    lines = content.splitlines()

    # Look for table rows that look like test case entries
    # A test case table row has at least 5 pipe-delimited columns
    in_test_table = False
    header_seen = False

    for i, line in enumerate(lines):
        # Detect test case table headers
        if re.search(r"TC.ID|Test.Case.ID|Scenario", line, re.IGNORECASE) and "|" in line:
            in_test_table = True
            header_seen = True
            continue

        if not in_test_table:
            continue

        # Skip separator rows (| --- | --- |)
        if re.match(r"^\|[-\s|]+\|$", line):
            continue

        # Reset table detection on blank line or heading
        if not line.strip() or re.match(r"^#{1,6}\s", line):
            in_test_table = False
            header_seen = False
            continue

        if not line.startswith("|"):
            continue

        cells = [c.strip() for c in line.split("|") if c.strip()]
        if len(cells) < 4:
            continue

        row_label = f"Line {i + 1} (test case row)"

        # Check for empty expected result (typically column 5 in standard format)
        # Heuristic: if the row has many empty cells, flag it
        empty_cells = sum(1 for c in cells if not c or c in ("-", "TBD", "TODO", ""))
        if empty_cells >= 3:
            issues.append(
                f"{row_label}: Test case row has {empty_cells} empty cells — "
                "ensure Expected Result, Preconditions, and Steps are filled in."
            )

        # Check for TODO markers in test case rows
        if "TODO" in line.upper():
            issues.append(
                f"{row_label}: Test case row contains TODO markers — not ready for execution."
            )

    return issues


def check_sign_off_section(content: str) -> list[str]:
    """Check for presence of a UAT sign-off section."""
    issues: list[str] = []
    has_signoff = bool(
        re.search(r"sign.off|go.no.go|business owner.*approv", content, re.IGNORECASE)
    )
    if not has_signoff:
        issues.append(
            "Document does not appear to contain a UAT sign-off or Go/No-Go section. "
            "Add a formal sign-off section before marking UAT complete."
        )
    return issues


def check_defect_severity(content: str) -> list[str]:
    """Check defect entries for missing severity classification."""
    issues: list[str] = []
    # Look for defect-log-style table rows
    for i, line in enumerate(content.splitlines()):
        if "DEF-" in line and "|" in line:
            cells = [c.strip() for c in line.split("|") if c.strip()]
            # Expect at least Defect ID, TC ID, Severity columns
            if len(cells) >= 3:
                severity_cell = cells[2] if len(cells) > 2 else ""
                if not re.search(r"P[1-4]|Critical|Major|Minor|Cosmetic", severity_cell, re.IGNORECASE):
                    issues.append(
                        f"Line {i + 1}: Defect entry '{cells[0]}' appears to be missing a severity classification (P1–P4)."
                    )
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check a UAT test script or user story document (Markdown) for "
            "common acceptance criteria and test script anti-patterns."
        ),
    )
    parser.add_argument(
        "--file",
        default=None,
        help="Path to the Markdown file to check (UAT test script or user stories document).",
    )
    args = parser.parse_args()

    if args.file is None:
        print("No --file provided. Pass a Markdown UAT test script or user stories file.")
        print("Usage: python3 check_uat_and_acceptance_criteria.py --file path/to/uat-script.md")
        return 0

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"ERROR: File not found: {file_path}")
        return 1

    content = file_path.read_text(encoding="utf-8")

    all_issues: list[str] = []
    all_issues.extend(check_acceptance_criteria(content))
    all_issues.extend(check_test_cases(content))
    all_issues.extend(check_sign_off_section(content))
    all_issues.extend(check_defect_severity(content))

    if not all_issues:
        print("No issues found.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
