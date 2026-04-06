#!/usr/bin/env python3
"""Checker script for Apex Order of Execution.

Scans Salesforce metadata in a manifest directory for patterns that commonly
cause order-of-execution bugs: non-idempotent trigger logic, missing recursion
guards, and workflow rules with field updates on objects that also have triggers.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_order_of_execution.py --help
    python3 check_order_of_execution.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Salesforce metadata for common order-of-execution issues:\n"
            "  - Trigger files that lack a static recursion guard\n"
            "  - Workflow rules with field updates (risk of trigger re-fire)\n"
            "  - After triggers that perform DML without a guard\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print additional detail for each check.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_files(root: Path, pattern: str) -> list[Path]:
    """Return all files matching a glob pattern under root."""
    return sorted(root.rglob(pattern))


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_triggers_missing_recursion_guard(
    manifest_dir: Path,
    verbose: bool,
) -> list[str]:
    """Flag trigger .cls files that contain DML in after-trigger contexts
    but do not appear to use a static Set or Boolean guard.
    """
    issues: list[str] = []

    trigger_files = find_files(manifest_dir, "*.trigger")
    handler_files = find_files(manifest_dir, "*Handler*.cls") + find_files(
        manifest_dir, "*handler*.cls"
    )

    # Patterns that suggest after-trigger DML (risk of recursion)
    after_dml_pattern = re.compile(
        r"\b(insert|update|upsert|delete)\s+\w",
        re.IGNORECASE,
    )
    # Pattern for a static guard (Set<Id> or Boolean)
    static_guard_pattern = re.compile(
        r"private\s+static\s+\S*(Set|Boolean|Map)\s*<",
        re.IGNORECASE,
    )

    for cls_file in trigger_files + handler_files:
        content = read_text(cls_file)
        has_after_dml = bool(after_dml_pattern.search(content))
        has_static_guard = bool(static_guard_pattern.search(content))

        if has_after_dml and not has_static_guard:
            issues.append(
                f"MISSING RECURSION GUARD: {cls_file} — contains DML "
                f"but no static Set/Boolean guard detected. "
                f"If this runs in an after-trigger context, add a static Set<Id> guard."
            )
            if verbose:
                # Show first DML match location
                m = after_dml_pattern.search(content)
                if m:
                    line_num = content[: m.start()].count("\n") + 1
                    issues.append(f"  First DML near line {line_num}: {m.group(0)!r}")

    return issues


def check_workflow_field_updates_with_triggers(
    manifest_dir: Path,
    verbose: bool,
) -> list[str]:
    """Flag objects that have both workflow rules with field updates and Apex triggers.

    Workflow field updates cause before+after triggers to re-fire once.
    Triggers on those objects must be idempotent.
    """
    issues: list[str] = []

    # Collect workflow metadata files
    workflow_files = find_files(manifest_dir, "*.workflow") + find_files(
        manifest_dir, "*.workflow-meta.xml"
    )
    field_update_pattern = re.compile(r"<fieldUpdates>", re.IGNORECASE)
    object_name_pattern = re.compile(
        r"workflows/([A-Za-z0-9_]+)\.workflow", re.IGNORECASE
    )

    objects_with_field_updates: set[str] = set()
    for wf_file in workflow_files:
        content = read_text(wf_file)
        if field_update_pattern.search(content):
            m = object_name_pattern.search(str(wf_file))
            if m:
                objects_with_field_updates.add(m.group(1).lower())

    # Collect trigger files
    trigger_files = find_files(manifest_dir, "*.trigger")
    object_trigger_pattern = re.compile(
        r"triggers/([A-Za-z0-9_]+)\.trigger", re.IGNORECASE
    )

    for trig_file in trigger_files:
        m = object_trigger_pattern.search(str(trig_file))
        if not m:
            continue
        obj_name = m.group(1).lower()
        if obj_name in objects_with_field_updates:
            issues.append(
                f"WORKFLOW FIELD UPDATE + TRIGGER: Object '{m.group(1)}' has both "
                f"a workflow rule with field updates and an Apex trigger ({trig_file.name}). "
                f"Triggers will re-fire once after the field update — ensure trigger logic is idempotent."
            )

    return issues


def check_triggers_in_after_context_without_guard(
    manifest_dir: Path,
    verbose: bool,
) -> list[str]:
    """Flag .trigger files that fire on after-insert/update but whose
    body or referenced handler does not contain a static guard.
    """
    issues: list[str] = []

    trigger_files = find_files(manifest_dir, "*.trigger")
    after_event_pattern = re.compile(
        r"\bafter\s+(insert|update|delete|undelete)\b",
        re.IGNORECASE,
    )
    static_guard_pattern = re.compile(
        r"\bstatic\b.*(Set|Boolean)\b",
        re.IGNORECASE,
    )
    dml_in_trigger_pattern = re.compile(
        r"\b(insert|update|upsert|delete)\s+\w",
        re.IGNORECASE,
    )

    for trig_file in trigger_files:
        content = read_text(trig_file)
        is_after = bool(after_event_pattern.search(content))
        has_dml = bool(dml_in_trigger_pattern.search(content))
        has_guard = bool(static_guard_pattern.search(content))

        if is_after and has_dml and not has_guard:
            issues.append(
                f"AFTER TRIGGER DML WITHOUT GUARD: {trig_file.name} — "
                f"fires on after-event and contains inline DML but no static guard detected. "
                f"Consider moving DML to a handler class with a static Set<Id> guard."
            )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir).resolve()

    if not manifest_dir.exists():
        print(f"ERROR: manifest directory not found: {manifest_dir}", file=sys.stderr)
        return 2

    all_issues: list[str] = []

    all_issues.extend(
        check_triggers_missing_recursion_guard(manifest_dir, args.verbose)
    )
    all_issues.extend(
        check_workflow_field_updates_with_triggers(manifest_dir, args.verbose)
    )
    all_issues.extend(
        check_triggers_in_after_context_without_guard(manifest_dir, args.verbose)
    )

    if not all_issues:
        print("No order-of-execution issues found.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")

    print(f"\n{len(all_issues)} issue(s) found.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
