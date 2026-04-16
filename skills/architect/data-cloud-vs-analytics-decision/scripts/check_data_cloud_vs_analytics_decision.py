#!/usr/bin/env python3
"""Checker script for Data Cloud vs CRM Analytics Decision skill.

Scans Markdown decision documents that mention both Data Cloud and CRM Analytics
(Einstein Analytics / Tableau CRM) and flags missing treatment of harmonized
consumption (DMO / Direct Data) and complementary layering.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_data_cloud_vs_analytics_decision.py [--help]
    python3 check_data_cloud_vs_analytics_decision.py --manifest-dir path/to/project
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DATA_CLOUD = re.compile(
    r"\bdata\s+cloud\b|data\s+360|salesforce\s+genie",
    re.IGNORECASE,
)

CRM_ANALYTICS = re.compile(
    r"\bcrm\s+analytics\b|\beinstein\s+analytics\b|\btableau\s+crm\b",
    re.IGNORECASE,
)

DMO_OR_DIRECT = re.compile(
    r"\bDMO\b|data\s+model\s+objects?|direct\s+data",
    re.IGNORECASE,
)

LAYERING = re.compile(
    r"complement|together|layer|consumer|foundational|harmoniz|unified\s+profile|"
    r"identity\s+resolution|activation|ingest",
    re.IGNORECASE,
)


def find_markdown_files(root: Path) -> list[Path]:
    return list(root.rglob("*.md"))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def check_data_cloud_vs_analytics_decision(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    md_files = find_markdown_files(manifest_dir)
    if not md_files:
        issues.append(
            "No Markdown files found under the manifest directory. "
            "Add decision or architecture notes (.md) to scan."
        )
        return issues

    relevant: list[Path] = []
    for path in md_files:
        try:
            text = read_text(path)
        except OSError:
            continue
        if DATA_CLOUD.search(text) and CRM_ANALYTICS.search(text):
            relevant.append(path)

    if not relevant:
        return issues

    combined_parts: list[str] = []
    for path in relevant:
        try:
            combined_parts.append(read_text(path))
        except OSError:
            issues.append(f"Could not read file: {path}")
    combined = "\n".join(combined_parts)

    if not DMO_OR_DIRECT.search(combined):
        issues.append(
            "Decision docs mention Data Cloud and CRM Analytics but do not reference "
            "DMOs / Data Model Objects or Direct Data. Add how CRM Analytics consumes "
            "harmonized Data Cloud entities per official Direct Data guidance."
        )

    if not LAYERING.search(combined):
        issues.append(
            "Decision docs mention both platforms but lack complementary layering language "
            "(harmonization, identity, activation, ingest, or consumer role). "
            "Clarify which layer owns cross-source truth versus visualization."
        )

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Markdown for Data Cloud vs CRM Analytics decision completeness: "
            "DMO/Direct Data and platform layering."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory to scan for Markdown files (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_data_cloud_vs_analytics_decision(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
