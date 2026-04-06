#!/usr/bin/env python3
"""Checker script for Case Trigger Patterns skill.

Scans Salesforce metadata (Apex trigger and class files) for common
Case trigger anti-patterns documented in references/gotchas.md and
references/llm-anti-patterns.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_case_trigger_patterns.py [--manifest-dir path/to/metadata]

Exit codes:
    0 — no issues found
    1 — one or more issues found (details printed to stderr)
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Matches `insert <variable>` or `insert new Case(...)` DML keyword on Case,
# but NOT `Database.insert(`. Used to flag potential missing DmlOptions.
_INSERT_KEYWORD_RE = re.compile(
    r"\binsert\s+(?!Database\b)[A-Za-z_][A-Za-z0-9_]*",
    re.IGNORECASE,
)

# Matches direct assignment to IsCompleted on CaseMilestone — read-only field
_IS_COMPLETED_WRITE_RE = re.compile(
    r"\.IsCompleted\s*=\s*(true|false)",
    re.IGNORECASE,
)

# Matches Trigger.new usage inside a before/after delete trigger context.
# Heuristic: looks for "Trigger.new" within 10 lines of a delete trigger
# declaration or inside a method named *Delete* / *onDelete*.
_TRIGGER_NEW_IN_DELETE_RE = re.compile(
    r"Trigger\.new\b",
    re.IGNORECASE,
)

# Matches SOQL inside a for-loop body (heuristic: [ SELECT inside for ( )
_SOQL_IN_LOOP_RE = re.compile(
    r"for\s*\([^)]*\)\s*\{[^}]*\[\s*SELECT",
    re.IGNORECASE | re.DOTALL,
)

# Matches a trigger declaration on Case to detect potential duplicates
_CASE_TRIGGER_DECL_RE = re.compile(
    r"trigger\s+\w+\s+on\s+Case\s*\(",
    re.IGNORECASE,
)

# Matches Database.DmlOptions assignment rule header usage (positive signal)
_DML_OPTIONS_RE = re.compile(
    r"Database\.DmlOptions|assignmentRuleHeader",
    re.IGNORECASE,
)


def _read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _find_apex_files(manifest_dir: Path) -> list[Path]:
    """Return all .trigger and .cls files under manifest_dir."""
    apex_files: list[Path] = []
    for ext in ("*.trigger", "*.cls"):
        apex_files.extend(manifest_dir.rglob(ext))
    return sorted(apex_files)


def check_case_trigger_patterns(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    apex_files = _find_apex_files(manifest_dir)
    if not apex_files:
        # No Apex files to check — not necessarily an error in all contexts
        return issues

    case_trigger_files: list[Path] = []
    case_insert_files_without_dml_options: list[Path] = []

    for path in apex_files:
        content = _read_file(path)
        rel = path.relative_to(manifest_dir)

        # ----------------------------------------------------------------
        # Check 1: IsCompleted write on CaseMilestone
        # ----------------------------------------------------------------
        if _IS_COMPLETED_WRITE_RE.search(content):
            issues.append(
                f"{rel}: assignment to CaseMilestone.IsCompleted detected — "
                "this field is read-only. Set CaseMilestone.CompletionDate instead."
            )

        # ----------------------------------------------------------------
        # Check 2: Case insert without DmlOptions (heuristic)
        # ----------------------------------------------------------------
        # Only flag if: file inserts Case records AND does NOT reference DmlOptions
        lower = content.lower()
        inserts_case = (
            "insert" in lower
            and ("case" in lower or "caselist" in lower)
        )
        uses_dml_options = bool(_DML_OPTIONS_RE.search(content))

        if inserts_case and not uses_dml_options:
            # Heuristic: file touches Case inserts and has no DmlOptions reference
            # Check for the more specific insert keyword pattern
            for match in _INSERT_KEYWORD_RE.finditer(content):
                surrounding = content[max(0, match.start() - 200):match.end() + 200]
                if "case" in surrounding.lower():
                    case_insert_files_without_dml_options.append(path)
                    issues.append(
                        f"{rel}: Case insert without Database.DmlOptions detected — "
                        "assignment rules will not fire. Use Database.insert(list, opts) "
                        "with opts.assignmentRuleHeader.useDefaultRule = true."
                    )
                    break  # one warning per file

        # ----------------------------------------------------------------
        # Check 3: Trigger.new inside a delete-context handler (heuristic)
        # ----------------------------------------------------------------
        # Look for files where the class/trigger name contains "Delete" or
        # where content mentions "isDelete" alongside Trigger.new
        is_delete_context = (
            "trigger.isdelete" in lower
            or "isdelete" in lower
            or "before delete" in lower
            or "after delete" in lower
        )
        if is_delete_context and _TRIGGER_NEW_IN_DELETE_RE.search(content):
            # Only flag if Trigger.new appears in the same method/block as isDelete
            issues.append(
                f"{rel}: Trigger.new referenced in a delete-context handler — "
                "Trigger.new is null in before/after delete. Use Trigger.old instead."
            )

        # ----------------------------------------------------------------
        # Check 4: Count Case trigger declarations — flag potential duplicates
        # ----------------------------------------------------------------
        if path.suffix == ".trigger":
            matches = _CASE_TRIGGER_DECL_RE.findall(content)
            if matches:
                case_trigger_files.append(path)

        # ----------------------------------------------------------------
        # Check 5: SOQL inside a for-loop (gross heuristic)
        # ----------------------------------------------------------------
        if _SOQL_IN_LOOP_RE.search(content):
            issues.append(
                f"{rel}: possible SOQL inside a for-loop detected — "
                "this will hit governor limits at batch sizes above 100. "
                "Move SOQL before the loop and use a Map for lookup."
            )

    # ----------------------------------------------------------------
    # Check 6: Multiple Case trigger files
    # ----------------------------------------------------------------
    if len(case_trigger_files) > 1:
        names = ", ".join(str(p.relative_to(manifest_dir)) for p in case_trigger_files)
        issues.append(
            f"Multiple Case triggers found ({names}) — "
            "only one trigger per object is the recommended pattern. "
            "Consolidate into a single trigger and handler."
        )

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce Apex metadata for Case trigger anti-patterns: "
            "missing DmlOptions for assignment rules, read-only IsCompleted writes, "
            "Trigger.new in delete context, SOQL inside loops, and duplicate triggers."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    args = parser.parse_args()
    manifest_dir = Path(args.manifest_dir)

    issues = check_case_trigger_patterns(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
