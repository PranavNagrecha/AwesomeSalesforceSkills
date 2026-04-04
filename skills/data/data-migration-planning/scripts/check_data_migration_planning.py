#!/usr/bin/env python3
"""Checker script for Data Migration Planning skill.

This is the primary skill checker entry point. It delegates to
check_migration_plan.py for detailed validation logic.

For full migration plan validation, run:
    python3 check_migration_plan.py --plan-file <sequence.csv> [--csv-dir <dir>]

This script performs a quick structural check on the skill directory itself
and verifies that any migration plan documents present in the current directory
include the key required sections.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_data_migration_planning.py [--manifest-dir path/to/metadata]
    python3 check_data_migration_planning.py --manifest-dir .
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED_PLAN_SECTIONS = [
    "external id",
    "bypass",
    "rollback",
    "migration sequence",
    "validation",
]

PLAN_FILE_GLOB_PATTERNS = [
    "*.md",
    "*.txt",
    "migration_plan*",
    "data-migration-planning-template*",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Quick structural check for data migration planning artifacts. "
            "For full CSV and sequence validation, use check_migration_plan.py."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Directory containing migration plan documents or metadata (default: current directory).",
    )
    return parser.parse_args()


def _find_plan_files(directory: Path) -> list[Path]:
    """Find markdown or text files that look like migration plan documents."""
    candidates: list[Path] = []
    for pattern in PLAN_FILE_GLOB_PATTERNS:
        candidates.extend(directory.glob(pattern))
    # Deduplicate preserving order
    seen: set[Path] = set()
    result: list[Path] = []
    for p in candidates:
        if p not in seen and p.is_file():
            seen.add(p)
            result.append(p)
    return result


def check_plan_document_sections(plan_file: Path) -> list[str]:
    """Check that a migration plan document covers required sections.

    Returns a list of issue strings for missing sections.
    """
    issues: list[str] = []
    try:
        content = plan_file.read_text(encoding="utf-8", errors="replace").lower()
    except OSError as exc:
        issues.append(f"{plan_file.name}: cannot read file — {exc}")
        return issues

    for section_keyword in REQUIRED_PLAN_SECTIONS:
        if section_keyword not in content:
            issues.append(
                f"{plan_file.name}: missing required topic '{section_keyword}'. "
                "Migration plans must address: external ID strategy, validation rule bypass, "
                "rollback approach, migration sequence, and post-migration validation."
            )

    return issues


def check_data_migration_planning(manifest_dir: Path) -> list[str]:
    """Run structural checks on migration planning artifacts in manifest_dir.

    Returns a list of issue strings found.
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Directory not found: {manifest_dir}")
        return issues

    plan_files = _find_plan_files(manifest_dir)

    if not plan_files:
        # No plan documents found — inform but do not fail; the checker may be
        # run against an org metadata directory that doesn't contain plan docs.
        issues.append(
            "No migration plan documents found in this directory. "
            "Expected a completed data-migration-planning-template.md or similar. "
            "Run the migration plan template at "
            "skills/data/data-migration-planning/templates/data-migration-planning-template.md "
            "and save the completed plan here."
        )
        return issues

    for plan_file in plan_files:
        section_issues = check_plan_document_sections(plan_file)
        issues.extend(section_issues)

    if not issues:
        checked = ", ".join(f.name for f in plan_files)
        print(f"Checked: {checked}")

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_data_migration_planning(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
