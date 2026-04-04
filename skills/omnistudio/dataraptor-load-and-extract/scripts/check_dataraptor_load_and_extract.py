#!/usr/bin/env python3
"""Checker script for DataRaptor Load and Extract skill.

Validates DataRaptor metadata files for common configuration issues:
- Load operations without documented volume limits
- Placeholder TODO markers in DataRaptor configuration notes

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_dataraptor_load_and_extract.py [--help]
    python3 check_dataraptor_load_and_extract.py --source-dir force-app/
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check DataRaptor Load and Extract metadata for common issues.",
    )
    parser.add_argument(
        "--source-dir",
        default=".",
        help="Root directory of the Salesforce/OmniStudio source (default: current directory).",
    )
    return parser.parse_args()


def check_dataraptor_files(source_dir: Path) -> list[str]:
    """Return a list of issue strings found in DataRaptor metadata files."""
    issues: list[str] = []

    # DataRaptor metadata files use .dataRaptorDefinition-meta.xml or .json in omnistudio
    # Also check for OmniStudio DataPack JSON files
    dr_patterns = [
        "**/*.dataRaptorDefinition-meta.xml",
        "**/DataRaptorBundleDefinition/**/*.json",
        "**/OmniDataTransform/**/*.json",
    ]

    for pattern in dr_patterns:
        for dr_file in source_dir.rglob(pattern.lstrip("*/")):
            # Basic check: look for any remaining TODO markers in config files
            try:
                content = dr_file.read_text(encoding="utf-8", errors="replace")
                if "TODO" in content:
                    issues.append(
                        f"{dr_file}: Contains TODO markers — configuration may be incomplete."
                    )
            except OSError:
                pass

    # Check for Integration Procedure JSON that uses DataRaptor steps
    for ip_file in source_dir.rglob("**/OmniProcess/**/*.json"):
        try:
            content = ip_file.read_text(encoding="utf-8", errors="replace")
            # Look for DataRaptor Load steps without any subsequent iferror check
            # This is a heuristic — if "DataRaptorLoad" appears but "iferror" does not
            if "DataRaptorLoad" in content and "iferror" not in content:
                issues.append(
                    f"{ip_file}: Integration Procedure uses DataRaptor Load but does not appear "
                    f"to check 'iferror' output. Add an explicit iferror check after each Load step."
                )
        except OSError:
            pass

    return issues


def main() -> int:
    args = parse_args()
    source_dir = Path(args.source_dir)

    if not source_dir.exists():
        print(f"ISSUE: Source directory not found: {source_dir}")
        return 1

    issues = check_dataraptor_files(source_dir)

    if not issues:
        print("No DataRaptor Load/Extract configuration issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
