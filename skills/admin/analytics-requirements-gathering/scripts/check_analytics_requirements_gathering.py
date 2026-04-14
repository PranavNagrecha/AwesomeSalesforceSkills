#!/usr/bin/env python3
"""Checker script for Analytics Requirements Gathering skill.

Checks org metadata or configuration relevant to Analytics Requirements Gathering.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_analytics_requirements_gathering.py [--help]
    python3 check_analytics_requirements_gathering.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Analytics Requirements Gathering configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_requirements_doc(file_path: Path) -> list[str]:
    """Check a CRM Analytics requirements document for completeness."""
    issues: list[str] = []

    if not file_path.exists():
        return issues

    content = file_path.read_text(encoding="utf-8")
    lower = content.lower()

    # Check for CRM Analytics vs Reports decision
    if "crm analytics" not in lower and "wave" not in lower and "einstein analytics" not in lower:
        issues.append(
            f"{file_path.name}: Document does not mention CRM Analytics. "
            "Confirm whether CRM Analytics is required or standard Reports are sufficient."
        )

    # Check for data source type specification
    source_types = ["salesforce object", "external connector", "data cloud", "csv", "snowflake", "bigquery"]
    if not any(t in lower for t in source_types):
        issues.append(
            f"{file_path.name}: Data source types are not specified. "
            "Requirements must identify data source type for each source "
            "(Salesforce object sync / external connector / Data Cloud / CSV)."
        )

    # Check for audience/RLS requirements
    if "audience" not in lower and "row-level" not in lower and "row level" not in lower and "predicate" not in lower:
        issues.append(
            f"{file_path.name}: No audience or row-level security requirements documented. "
            "Audience matrix with RLS mechanism must be specified before dataset design."
        )

    # Check for transformation requirements
    if "transformation" not in lower and "join" not in lower and "computed" not in lower:
        issues.append(
            f"{file_path.name}: No transformation requirements documented. "
            "Specify joins, computed fields, and field renames needed before recipe design."
        )

    return issues


def check_analytics_requirements_gathering(manifest_dir: Path) -> list[str]:
    """Check a documentation directory for CRM Analytics requirements completeness."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Directory not found: {manifest_dir}")
        return issues

    # Look for requirements document files
    req_files = (
        list(manifest_dir.rglob("*analytics*requirement*"))
        + list(manifest_dir.rglob("*crm*analytics*req*"))
        + list(manifest_dir.rglob("*wave*requirement*"))
    )
    for rf in req_files:
        if rf.suffix in (".md", ".txt"):
            issues.extend(check_requirements_doc(rf))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_analytics_requirements_gathering(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
