#!/usr/bin/env python3
"""check_einstein_copilot_for_sales.py — Entry point for Einstein Copilot for Sales checker.

Delegates to check_einstein_sales.py which contains the full implementation.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_einstein_copilot_for_sales.py [--manifest-dir path/to/metadata] [--verbose]
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running from any directory by adding scripts/ to the path
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from check_einstein_sales import main, parse_args, run_all_checks  # noqa: E402


def check_einstein_copilot_for_sales(manifest_dir: Path, verbose: bool = False) -> list[str]:
    """Return a list of issue strings for the given manifest directory.

    Validates Einstein Sales AI prerequisites:
    - Permission set metadata presence
    - Opportunity Score fields on Opportunity page layouts
    - Sales settings metadata for Einstein feature flags
    - EAC exclusion rule configuration
    - Pipeline Inspection dependency on Opportunity Scoring
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(run_all_checks(manifest_dir, verbose=verbose))
    if issues:
        print(f"WARN: {len(issues)} Einstein Copilot issue(s) detected", file=sys.stderr)
    return issues


if __name__ == "__main__":
    sys.exit(main())
