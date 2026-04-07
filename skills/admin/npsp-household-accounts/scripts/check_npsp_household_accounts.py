#!/usr/bin/env python3
"""Checker script for NPSP Household Accounts skill.

Delegates to check_household.py for all validation logic.
This file is the entry point registered by the skill scaffold.

Usage:
    python3 check_npsp_household_accounts.py [--manifest-dir path/to/metadata]
    python3 check_npsp_household_accounts.py --help
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Re-use logic from the canonical checker in this scripts/ directory.
# Keeping this file as a thin wrapper preserves scaffold compatibility.

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check NPSP Household Account configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata export (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir).resolve()

    # Import and delegate to the full implementation
    scripts_dir = Path(__file__).parent
    sys.path.insert(0, str(scripts_dir))
    from check_household import run_all_checks

    print(f"Checking NPSP Household Account configuration in: {manifest_dir}")
    print()

    issues = run_all_checks(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    print(f"\n{len(issues)} issue(s) found.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
