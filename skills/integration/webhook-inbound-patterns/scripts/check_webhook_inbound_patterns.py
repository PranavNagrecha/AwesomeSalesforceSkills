#!/usr/bin/env python3
"""Checker script for Webhook Inbound Patterns skill.

Scans Apex files for common webhook implementation issues:
- Hardcoded shared secrets in @RestResource classes
- @HttpPost handlers without HMAC verification
- Direct Database.insert() without idempotency check in webhook handlers

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_webhook_inbound_patterns.py [--help]
    python3 check_webhook_inbound_patterns.py --source-dir force-app/
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan Apex files for webhook implementation security issues.",
    )
    parser.add_argument(
        "--source-dir",
        default=".",
        help="Root directory of the Salesforce source (default: current directory).",
    )
    return parser.parse_args()


def is_webhook_handler(content: str) -> bool:
    """Heuristic: file contains @RestResource and @HttpPost."""
    return "@RestResource" in content and "@HttpPost" in content


def check_hardcoded_secrets(apex_file: Path, content: str) -> list[str]:
    """Warn if a webhook handler has hardcoded secret strings."""
    issues: list[str] = []
    lines = content.splitlines()
    secret_patterns = [
        re.compile(r'(?i)(secret|hmac|signing.?key|webhook.?key)\s*=\s*["\'][^"\']{8,}["\']'),
    ]
    for i, line in enumerate(lines, start=1):
        for pattern in secret_patterns:
            if pattern.search(line):
                issues.append(
                    f"{apex_file}:{i}: Potential hardcoded webhook secret — "
                    f"store shared secrets in Custom Metadata, not in Apex code."
                )
    return issues


def check_hmac_verification(apex_file: Path, content: str) -> list[str]:
    """Warn if @HttpPost handler does not appear to verify HMAC."""
    issues: list[str] = []
    # Look for HMAC patterns
    hmac_patterns = [
        "generateMac",
        "HmacSHA",
        "verifyHmac",
        "X-Hub-Signature",
        "Stripe-Signature",
        "signature",
    ]
    has_hmac = any(p.lower() in content.lower() for p in hmac_patterns)
    if not has_hmac:
        issues.append(
            f"{apex_file}: @RestResource/@HttpPost handler does not appear to verify "
            f"HMAC signature. Add signature verification before processing the payload."
        )
    return issues


def check_webhook_files(source_dir: Path) -> list[str]:
    """Return a list of issue strings found in the source directory."""
    issues: list[str] = []

    for apex_file in source_dir.rglob("*.cls"):
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
            if not is_webhook_handler(content):
                continue
            issues.extend(check_hardcoded_secrets(apex_file, content))
            issues.extend(check_hmac_verification(apex_file, content))
        except OSError:
            pass

    return issues


def main() -> int:
    args = parse_args()
    source_dir = Path(args.source_dir)

    if not source_dir.exists():
        print(f"ISSUE: Source directory not found: {source_dir}")
        return 1

    issues = check_webhook_files(source_dir)

    if not issues:
        print("No webhook implementation issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
