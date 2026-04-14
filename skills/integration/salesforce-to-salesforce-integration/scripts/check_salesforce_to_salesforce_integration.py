#!/usr/bin/env python3
"""Checker script for Salesforce To Salesforce Integration skill.

Checks org metadata or configuration relevant to Salesforce To Salesforce Integration.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_salesforce_to_salesforce_integration.py [--help]
    python3 check_salesforce_to_salesforce_integration.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Salesforce To Salesforce Integration configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_salesforce_to_salesforce_integration(manifest_dir: Path) -> list[str]:
    """Check metadata for Salesforce-to-Salesforce integration anti-patterns."""
    import re

    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check Apex files for cross-org callout patterns without error handling
    apex_files = list(manifest_dir.rglob("*.cls")) + list(manifest_dir.rglob("*.trigger"))
    for apex_file in apex_files:
        content = apex_file.read_text(encoding="utf-8", errors="ignore")
        # Look for HTTP callouts to Salesforce endpoints
        if re.search(r'salesforce\.com.*http|namedcredential.*sf|Http\(\)', content, re.IGNORECASE):
            # Check for error handling
            if "getStatusCode" not in content and "StatusCode" not in content:
                issues.append(
                    f"{apex_file.name}: Cross-org HTTP callout detected without status code handling. "
                    "Cross-org API calls must handle 401 (token expired), 429 (API limit), and 5xx (target org down)."
                )

    # Check for PartnerNetworkConnection in metadata (S2S enabled indicator)
    xml_files = list(manifest_dir.rglob("*.xml"))
    for xml_file in xml_files:
        content = xml_file.read_text(encoding="utf-8", errors="ignore")
        if "PartnerNetworkConnection" in content or "salesforceToSalesforce" in content.lower():
            issues.append(
                f"{xml_file.name}: Native Salesforce-to-Salesforce (S2S) feature reference detected. "
                "Reminder: S2S cannot be deactivated once enabled and consumes SOAP API limits on both orgs. "
                "Confirm this is the intended integration pattern for your volume requirements."
            )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_salesforce_to_salesforce_integration(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
