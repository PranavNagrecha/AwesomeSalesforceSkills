#!/usr/bin/env python3
"""Checker script for Data Cloud Consent And Privacy skill.

Checks org metadata or configuration relevant to Data Cloud Consent And Privacy.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_data_cloud_consent_and_privacy.py [--help]
    python3 check_data_cloud_consent_and_privacy.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Data Cloud Consent And Privacy configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_data_cloud_consent_and_privacy(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory.

    TODO: Implement real checks relevant to this skill.
    Each returned string should describe a concrete, actionable issue.
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check Flow files for segments without consent filters
    flow_files = list(manifest_dir.rglob("*.flow-meta.xml"))
    for flow_file in flow_files:
        try:
            text = flow_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        # Detect segment-like flow references without ContactPointConsent reference
        if "segment" in text.lower() and "ContactPointConsent" not in text:
            issues.append(
                f"{flow_file}: Flow references segments but no ContactPointConsent filter detected — "
                "Data Cloud consent is NOT auto-enforced. Segment filters must explicitly join "
                "ssot__ContactPointConsent__dlm with OptIn status filter."
            )

    # Check Python/query files for SOQL/SQL that queries Data Cloud profiles without consent filter
    code_files = list(manifest_dir.rglob("*.py")) + list(manifest_dir.rglob("*.sql"))
    for code_file in code_files:
        try:
            text = code_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        # Detect queries against Individual DMO without consent filter
        if "ssot__Individual__dlm" in text and "ContactPointConsent" not in text:
            issues.append(
                f"{code_file}: Queries ssot__Individual__dlm but lacks ContactPointConsent filter — "
                "If this query is for marketing/activation, add explicit consent OptIn filter."
            )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_data_cloud_consent_and_privacy(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
