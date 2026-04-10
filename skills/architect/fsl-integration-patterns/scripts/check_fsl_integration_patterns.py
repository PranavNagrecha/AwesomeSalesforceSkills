#!/usr/bin/env python3
"""Checker script for FSL Integration Patterns skill.

Scans Apex source and design documents for common FSL integration anti-patterns:
- FSL scheduling callouts inside Platform Event triggers
- Authorization headers from Custom Labels/Settings (not Named Credentials)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_fsl_integration_patterns.py [--help]
    python3 check_fsl_integration_patterns.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_FSL_CALLOUT_IN_EVENT_RE = re.compile(
    r'FSL\.(ScheduleService\.schedule|AppointmentBookingService\.GetSlots)', re.IGNORECASE
)
_PLATFORM_EVENT_TRIGGER_RE = re.compile(r'on\s+\w+__e\s*\(', re.IGNORECASE)
_HARDCODED_AUTH_RE = re.compile(
    r'setHeader\s*\(\s*[\'"]Authorization[\'"]\s*,\s*[\'"]Bearer\s+|'
    r'System\.Label\.\w+.*Authorization|'
    r'Custom_Setting.*Api_Key',
    re.IGNORECASE
)
_NAMED_CRED_RE = re.compile(r'Named_Credential|callout:\w+', re.IGNORECASE)


def check_fsl_integration_patterns(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    apex_files = list(manifest_dir.rglob("*.cls")) + list(manifest_dir.rglob("*.trigger"))

    for apex_file in apex_files:
        try:
            source = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        rel = apex_file.relative_to(manifest_dir)

        # Check 1: FSL scheduling callout inside Platform Event trigger
        if _PLATFORM_EVENT_TRIGGER_RE.search(source) and _FSL_CALLOUT_IN_EVENT_RE.search(source):
            issues.append(
                f"{rel}: FSL scheduling callout detected inside a Platform Event trigger. "
                "Platform Event handlers have DML-before-callout constraints. "
                "Enqueue scheduling in a Queueable (Database.AllowsCallouts) from the event handler."
            )

        # Check 2: Hardcoded authorization credentials (not Named Credentials)
        if _HARDCODED_AUTH_RE.search(source) and not _NAMED_CRED_RE.search(source):
            issues.append(
                f"{rel}: Authorization credentials set directly in HTTP headers, possibly from "
                "Custom Labels or hardcoded values. Use Named Credentials for all outbound "
                "authenticated callouts. Named Credentials handle token refresh and prevent "
                "credential exposure."
            )

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex source for FSL Integration Patterns anti-patterns.",
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
    issues = check_fsl_integration_patterns(manifest_dir)

    if not issues:
        print("No FSL Integration Patterns issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
