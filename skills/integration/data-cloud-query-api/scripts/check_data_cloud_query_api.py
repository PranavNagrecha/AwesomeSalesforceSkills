#!/usr/bin/env python3
"""Checker script for Data Cloud Query Api skill.

Checks org metadata or configuration relevant to Data Cloud Query Api.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_data_cloud_query_api.py [--help]
    python3 check_data_cloud_query_api.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Data Cloud Query Api configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_data_cloud_query_api(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory.

    TODO: Implement real checks relevant to this skill.
    Each returned string should describe a concrete, actionable issue.
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check for Python files that use standard SF instance_url for Data Cloud API calls
    py_files = list(manifest_dir.rglob("*.py"))
    for py_file in py_files:
        try:
            text = py_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        # Detect use of instance_url for Data Cloud api/v2/query calls (should be dcInstanceUrl)
        if "api/v2/query" in text and "instance_url" in text and "dcInstanceUrl" not in text:
            issues.append(
                f"{py_file}: Uses instance_url for Data Cloud Query API — "
                "should use dcInstanceUrl from /services/a360/token response."
            )
        # Detect SOQL patterns in Data Cloud query strings
        if "api/v2/query" in text:
            soql_patterns = ["FROM Contact", "FROM Account", "FROM Lead", "FROM Opportunity"]
            for pattern in soql_patterns:
                if pattern in text:
                    issues.append(
                        f"{py_file}: Possible SOQL object name '{pattern}' in Data Cloud query — "
                        "use Data Cloud DMO API names (e.g., ssot__Individual__dlm)."
                    )
        # Detect missing pagination (nextBatchId check)
        if "api/v2/query" in text and "nextBatchId" not in text:
            issues.append(
                f"{py_file}: Data Cloud Query API call found but no 'nextBatchId' pagination — "
                "result set may be silently truncated."
            )

    # Check for connected app XML missing cdp_api scope
    xml_files = list(manifest_dir.rglob("*.connectedApp-meta.xml"))
    for xml_file in xml_files:
        try:
            text = xml_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "cdp_api" not in text and "DataCloud" in text:
            issues.append(
                f"{xml_file}: Connected app may be missing 'cdp_api' OAuth scope — "
                "required for Data Cloud Query API access."
            )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_data_cloud_query_api(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
