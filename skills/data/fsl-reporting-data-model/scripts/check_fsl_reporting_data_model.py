#!/usr/bin/env python3
"""Checker script for FSL Reporting Data Model skill.

Scans SOQL queries and report metadata for common FSL reporting anti-patterns:
- ServiceReport queries being used for operational metrics
- Missing date filter on ServiceResourceSkill queries
- SchedStartTime used in arrival calculations

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_fsl_reporting_data_model.py [--help]
    python3 check_fsl_reporting_data_model.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Patterns
_SERVICE_REPORT_QUERY_RE = re.compile(
    r'\bFROM\s+ServiceReport\b', re.IGNORECASE
)
_SKILL_QUERY_NO_DATE_RE = re.compile(
    r'\bFROM\s+ServiceResourceSkill\b', re.IGNORECASE
)
_SKILL_DATE_FILTER_RE = re.compile(
    r'EffectiveEndDate', re.IGNORECASE
)
_SCHED_START_ARRIVAL_RE = re.compile(
    r'SchedStartTime\s*[<>=!]+\s*ArrivalWindow|ArrivalWindow\s*[<>=!]+\s*SchedStartTime',
    re.IGNORECASE
)


def check_fsl_reporting_data_model(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check Apex and SOQL files
    files_to_check = (
        list(manifest_dir.rglob("*.cls"))
        + list(manifest_dir.rglob("*.soql"))
        + list(manifest_dir.rglob("*.apex"))
    )

    for source_file in files_to_check:
        try:
            source = source_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        rel = source_file.relative_to(manifest_dir)

        # Check 1: ServiceReport used for operational metrics
        if _SERVICE_REPORT_QUERY_RE.search(source):
            issues.append(
                f"{rel}: Query on ServiceReport detected. "
                "ServiceReport is a customer-facing PDF object — not an operational metrics source. "
                "Use ServiceAppointment for job performance data."
            )

        # Check 2: ServiceResourceSkill query without EffectiveEndDate filter
        if _SKILL_QUERY_NO_DATE_RE.search(source):
            if not _SKILL_DATE_FILTER_RE.search(source):
                issues.append(
                    f"{rel}: Query on ServiceResourceSkill without EffectiveEndDate filter. "
                    "Expired skill records are never auto-deleted. "
                    "Add: WHERE (EffectiveEndDate >= TODAY() OR EffectiveEndDate = NULL)"
                )

        # Check 3: SchedStartTime vs ArrivalWindow comparison
        if _SCHED_START_ARRIVAL_RE.search(source):
            issues.append(
                f"{rel}: SchedStartTime compared to ArrivalWindow field. "
                "SchedStartTime is the FSL engine's planned time, not actual arrival. "
                "For on-time arrival: compare ActualStartTime to ArrivalWindowEnd."
            )

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex/SOQL for FSL Reporting Data Model anti-patterns.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_fsl_reporting_data_model(manifest_dir)

    if not issues:
        print("No FSL Reporting Data Model issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
