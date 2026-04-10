#!/usr/bin/env python3
"""Checker script for FSL Multi-Region Architecture skill.

Scans CSV territory data and design documents for multi-region FSL issues:
- Single OperatingHours for multiple territory timezone configurations
- UTC offset instead of IANA timezone in OperatingHours data

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_fsl_multi_region_architecture.py [--help]
    python3 check_fsl_multi_region_architecture.py --manifest-dir path/to/data-or-docs
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

_UTC_OFFSET_RE = re.compile(r'UTC[+-]\d|GMT[+-]\d', re.IGNORECASE)
_IANA_TZ_RE = re.compile(r'America/|Europe/|Asia/|Pacific/|Africa/', re.IGNORECASE)


def check_fsl_multi_region_architecture(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check CSV files for OperatingHours timezone issues
    csv_files = list(manifest_dir.rglob("*.csv"))
    for csv_file in csv_files:
        fname_lower = csv_file.name.lower()
        if "operatinghours" in fname_lower or "operating_hours" in fname_lower:
            try:
                with csv_file.open(encoding="utf-8-sig", errors="replace") as f:
                    reader = csv.DictReader(f)
                    headers = reader.fieldnames or []
                    rel = csv_file.relative_to(manifest_dir)

                    tz_col = None
                    for h in headers:
                        if "timezone" in h.lower() or "time_zone" in h.lower():
                            tz_col = h
                            break

                    if tz_col:
                        for i, row in enumerate(reader, start=2):
                            tz_val = row.get(tz_col, "").strip()
                            if tz_val and _UTC_OFFSET_RE.search(tz_val):
                                issues.append(
                                    f"{rel}:row {i}: OperatingHours TimeZone '{tz_val}' uses a UTC offset. "
                                    "Use an IANA timezone identifier (e.g., 'America/New_York') instead. "
                                    "UTC offsets don't automatically handle Daylight Saving Time transitions."
                                )
                            elif tz_col and tz_val and not _IANA_TZ_RE.search(tz_val):
                                issues.append(
                                    f"{rel}:row {i}: OperatingHours TimeZone '{tz_val}' may not be an IANA identifier. "
                                    "Verify this matches a Salesforce-supported IANA timezone value."
                                )
            except (OSError, csv.Error):
                continue

    # Check design documents for single-OperatingHours pattern
    md_files = list(manifest_dir.rglob("*.md")) + list(manifest_dir.rglob("*.txt"))
    for doc_file in md_files:
        try:
            content = doc_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if len(content) < 200:
            continue

        rel = doc_file.relative_to(manifest_dir)

        # Check for "one operating hours" anti-pattern hint
        if re.search(r'one\s+operating\s+hours|single\s+operating\s+hours', content, re.IGNORECASE):
            if re.search(r'multiple\s+timezone|all\s+territories|all\s+regions', content, re.IGNORECASE):
                issues.append(
                    f"{rel}: Document may be recommending a single OperatingHours record for multiple timezones. "
                    "Each timezone in the FSL deployment requires its own OperatingHours record with the correct timezone."
                )

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check FSL Multi-Region data and design documents for timezone issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory containing data files and design documents (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_fsl_multi_region_architecture(manifest_dir)

    if not issues:
        print("No FSL Multi-Region Architecture issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
