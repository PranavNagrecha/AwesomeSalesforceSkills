#!/usr/bin/env python3
"""Checker script for Fundraising Integration Patterns skill.

Scans Salesforce metadata in a project directory for anti-patterns documented in this skill:
- blng.PaymentGateway usage in NPSP/NPC contexts
- Hardcoded credentials in Apex callout code
- Direct GiftTransaction DML inserts from integration Apex classes
- API version below 59.0 in Connect REST API callout URLs

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_fundraising_integration_patterns.py [--help]
    python3 check_fundraising_integration_patterns.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# Patterns that indicate known anti-patterns
_BILLING_GATEWAY_PATTERN = re.compile(r"implements\s+blng\.PaymentGateway", re.IGNORECASE)
_HARDCODED_BEARER_PATTERN = re.compile(r"""['\"]Bearer\s+[A-Za-z0-9_\-]{20,}['\"]""")
_HARDCODED_API_KEY_PATTERN = re.compile(r"""(apiKey|api_key|ApiKey)\s*=\s*['\"][A-Za-z0-9_\-]{10,}['\"]""", re.IGNORECASE)
_GIFT_TRANSACTION_INSERT_PATTERN = re.compile(r"insert\s+.*GiftTransaction", re.IGNORECASE)
_LOW_API_VERSION_PATTERN = re.compile(r"/services/data/v([0-9]+)\.0/connect/fundraising/")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for fundraising integration anti-patterns. "
            "Scans Apex classes for blng.PaymentGateway usage, hardcoded credentials, "
            "direct GiftTransaction DML, and low API versions in Elevate callouts."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _check_apex_file(apex_file: Path) -> list[str]:
    """Check a single .cls file for fundraising integration anti-patterns."""
    issues: list[str] = []
    try:
        content = apex_file.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        issues.append(f"{apex_file}: could not read file — {exc}")
        return issues

    # Anti-Pattern 1: blng.PaymentGateway in NPSP/NPC context
    if _BILLING_GATEWAY_PATTERN.search(content):
        issues.append(
            f"{apex_file}: implements blng.PaymentGateway — this interface is Salesforce Billing only "
            "and will not compile in an NPSP/Nonprofit Cloud org. Use Elevate Connect REST API instead."
        )

    # Anti-Pattern 5: Hardcoded bearer tokens
    if _HARDCODED_BEARER_PATTERN.search(content):
        issues.append(
            f"{apex_file}: possible hardcoded Bearer token found in callout code. "
            "Move credentials to Named Credentials."
        )

    # Anti-Pattern 5: Hardcoded API keys
    if _HARDCODED_API_KEY_PATTERN.search(content):
        issues.append(
            f"{apex_file}: possible hardcoded API key assignment found. "
            "Move credentials to Named Credentials."
        )

    # Anti-Pattern 3: Direct GiftTransaction DML insert
    if _GIFT_TRANSACTION_INSERT_PATTERN.search(content):
        issues.append(
            f"{apex_file}: direct DML insert on GiftTransaction detected. "
            "GiftTransaction records should be created through the Elevate gift entry flow, "
            "not inserted directly — doing so skips required gateway metadata population."
        )

    # Anti-Pattern: Connect REST API call with API version below 59.0
    for match in _LOW_API_VERSION_PATTERN.finditer(content):
        version = int(match.group(1))
        if version < 59:
            issues.append(
                f"{apex_file}: Elevate Connect REST API callout uses API v{version}.0 "
                "but requires minimum v59.0. Update the endpoint URL to v59.0 or higher."
            )

    return issues


def check_fundraising_integration_patterns(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory.

    Scans all .cls Apex files under the manifest directory for known
    fundraising integration anti-patterns.
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    apex_files = list(manifest_dir.rglob("*.cls"))

    if not apex_files:
        # Not an error — org may have no Apex or manifest may point to a metadata subset
        return issues

    for apex_file in apex_files:
        file_issues = _check_apex_file(apex_file)
        issues.extend(file_issues)

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_fundraising_integration_patterns(manifest_dir)

    if not issues:
        print("No fundraising integration anti-patterns found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
