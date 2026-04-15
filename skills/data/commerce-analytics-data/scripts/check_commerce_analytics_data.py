#!/usr/bin/env python3
"""Checker script for Commerce Analytics Data skill.

Validates metadata patterns relevant to B2B Commerce on Core analytics:
- Detects SOQL queries that use incorrect WebCart Status values
- Detects references to the retired legacy Business Manager Analytics module
- Checks for missing cart abandonment date threshold in SOQL patterns

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_commerce_analytics_data.py [--help]
    python3 check_commerce_analytics_data.py --manifest-dir path/to/metadata
    python3 check_commerce_analytics_data.py --soql-file path/to/queries.soql
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# WebCart Status values that indicate incorrect usage (not valid picklist values)
_INVALID_WEBCART_STATUS = re.compile(
    r"Status\s*=\s*['\"](?:Open|Pending|Draft|New|InProgress)['\"]",
    re.IGNORECASE,
)

# Pattern indicating the retired legacy analytics module is referenced
_LEGACY_ANALYTICS_REFERENCE = re.compile(
    r"Business\s+Manager\s+Analytics(?!\s+(?:retired|deprecated|removed|replaced|was))",
    re.IGNORECASE,
)

# SOQL query against WebCart that may be missing a date threshold
_WEBCART_ACTIVE_NO_DATE = re.compile(
    r"FROM\s+WebCart\b[^;]*Status\s*=\s*['\"]Active['\"](?![^;]*(?:CreatedDate|LastModifiedDate|LAST_N_DAYS|LAST_N_WEEKS|N_DAYS_AGO|TODAY|YESTERDAY))",
    re.IGNORECASE | re.DOTALL,
)

# Reference to "ORDER" object in context that may indicate B2C Commerce confusion
_CRM_ORDER_FOR_B2C = re.compile(
    r"FROM\s+Order\b.*(?:b2c|commerce\s+cloud|storefront|sfcc)",
    re.IGNORECASE | re.DOTALL,
)


def check_soql_content(content: str, source_label: str) -> list[str]:
    """Check SOQL content for anti-patterns. Returns list of issue strings."""
    issues: list[str] = []

    # Check for invalid WebCart Status values
    matches = _INVALID_WEBCART_STATUS.findall(content)
    if matches:
        for m in matches:
            issues.append(
                f"{source_label}: Invalid WebCart Status value detected: '{m}'. "
                "Valid values are 'Active', 'Closed', 'PendingDelete'. "
                "Using 'Open', 'Pending', etc. will return zero rows."
            )

    # Check for WebCart abandonment query without date threshold
    if re.search(r"FROM\s+WebCart\b", content, re.IGNORECASE):
        if re.search(r"Status\s*=\s*['\"]Active['\"]", content, re.IGNORECASE):
            has_date_filter = bool(re.search(
                r"(?:CreatedDate|LastModifiedDate)\s*[<>]=?\s*|LAST_N_DAYS|LAST_N_WEEKS|N_DAYS_AGO",
                content,
                re.IGNORECASE,
            ))
            if not has_date_filter:
                issues.append(
                    f"{source_label}: WebCart abandonment query uses Status='Active' "
                    "but has no date threshold (CreatedDate, LastModifiedDate, or "
                    "LAST_N_DAYS). This will return ALL open carts, not just "
                    "abandoned ones. Add a date filter (e.g., CreatedDate < LAST_N_DAYS:7)."
                )

    return issues


def check_markdown_content(content: str, source_label: str) -> list[str]:
    """Check markdown/text content for anti-patterns. Returns list of issue strings."""
    issues: list[str] = []

    # Check for references to retired legacy analytics module
    if _LEGACY_ANALYTICS_REFERENCE.search(content):
        issues.append(
            f"{source_label}: Reference to 'Business Manager Analytics' (legacy module) detected. "
            "The legacy Business Manager Analytics module was retired January 1, 2021. "
            "The current surface is 'Reports & Dashboards' inside Business Manager."
        )

    return issues


def check_commerce_analytics_data(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Scan all .soql, .sql, .cls, .trigger, .js, .ts, .apex files for SOQL patterns
    soql_extensions = {".soql", ".sql", ".cls", ".trigger", ".apex"}
    text_extensions = {".md", ".txt", ".html", ".xml"}

    all_extensions = soql_extensions | text_extensions

    for path in manifest_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in all_extensions:
            continue

        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        label = str(path.relative_to(manifest_dir))

        if path.suffix.lower() in soql_extensions:
            issues.extend(check_soql_content(content, label))
        elif path.suffix.lower() in text_extensions:
            issues.extend(check_markdown_content(content, label))
            # Also check for embedded SOQL in markdown/XML
            if re.search(r"FROM\s+WebCart\b", content, re.IGNORECASE):
                issues.extend(check_soql_content(content, label + " (embedded SOQL)"))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check project files for commerce analytics anti-patterns: "
            "invalid WebCart Status values, missing date thresholds on abandonment queries, "
            "and references to the retired legacy Business Manager Analytics module."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory to scan for metadata and query files (default: current directory).",
    )
    parser.add_argument(
        "--soql-file",
        default=None,
        help="Optional: path to a single SOQL/Apex file to check instead of scanning a directory.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.soql_file:
        path = Path(args.soql_file)
        if not path.exists():
            print(f"WARN: File not found: {path}", file=sys.stderr)
            return 1
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            print(f"WARN: Could not read {path}: {exc}", file=sys.stderr)
            return 1
        issues = check_soql_content(content, str(path))
    else:
        manifest_dir = Path(args.manifest_dir)
        issues = check_commerce_analytics_data(manifest_dir)

    if not issues:
        print("No commerce analytics anti-patterns found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
