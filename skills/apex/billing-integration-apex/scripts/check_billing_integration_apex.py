#!/usr/bin/env python3
"""Checker script for Billing Integration Apex skill.

Delegates to check_billing_apex.py in the same directory for all checks.
Kept for scaffold compatibility — use check_billing_apex.py directly for
full options.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_billing_integration_apex.py [--help]
    python3 check_billing_integration_apex.py --manifest-dir path/to/force-app
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Import the real checker from the sibling module
_HERE = Path(__file__).parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Billing Integration Apex configuration and metadata for common issues. "
            "Scans .cls files for TransactionAPI callout/DML conflicts, missing blng__ "
            "namespace prefixes, incorrect API versions, and missing billing schedule ID "
            "size guards."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce project containing Apex .cls files (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    # Add the scripts directory to the path so we can import check_billing_apex
    sys.path.insert(0, str(_HERE))
    try:
        import check_billing_apex  # type: ignore
    except ImportError:
        print(
            "ERROR: check_billing_apex.py not found in the same directory. "
            "Ensure both scripts are present.",
            file=sys.stderr,
        )
        return 2

    source_dir = Path(args.manifest_dir)
    issues = check_billing_apex.check_directory(source_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    print(f"\n{len(issues)} issue(s) found.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
