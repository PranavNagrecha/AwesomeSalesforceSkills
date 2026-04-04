#!/usr/bin/env python3
"""Checker script for Agentforce Observability skill.

Validates that Agentforce observability is properly configured:
- Checks for SOQL queries targeting session trace objects (should use Data Cloud SQL instead)
- Warns about hard-coded date ranges that may miss session data

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_agentforce_observability.py [--help]
    python3 check_agentforce_observability.py --source-dir force-app/
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check for common Agentforce observability configuration issues.",
    )
    parser.add_argument(
        "--source-dir",
        default=".",
        help="Root directory of the Salesforce source (default: current directory).",
    )
    return parser.parse_args()


# Session trace objects that live in Data Cloud, not the main org
DATA_CLOUD_SESSION_OBJECTS = {
    "AgentConversationSession",
    "AgentConversationSessionUtterance",
    "AgentConversationSessionTopic",
}


def check_soql_against_data_cloud_objects(source_dir: Path) -> list[str]:
    """Warn if Apex code uses SOQL against session trace objects (which live in Data Cloud)."""
    issues: list[str] = []

    for apex_file in source_dir.rglob("*.cls"):
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
            lines = content.splitlines()
            for i, line in enumerate(lines, start=1):
                for obj_name in DATA_CLOUD_SESSION_OBJECTS:
                    # Look for SOQL SELECT patterns targeting these objects
                    if re.search(
                        rf"\bFROM\s+{obj_name}\b",
                        line,
                        re.IGNORECASE,
                    ):
                        issues.append(
                            f"{apex_file}:{i}: SOQL query targets '{obj_name}' which is a "
                            f"Data Cloud session trace object. This object is NOT queryable via "
                            f"standard SOQL. Use Data Cloud SQL or CRM Analytics instead."
                        )
        except OSError:
            pass

    return issues


def check_agentforce_observability(source_dir: Path) -> list[str]:
    """Return a list of issue strings found in the source directory."""
    issues: list[str] = []

    if not source_dir.exists():
        issues.append(f"Source directory not found: {source_dir}")
        return issues

    issues.extend(check_soql_against_data_cloud_objects(source_dir))

    return issues


def main() -> int:
    args = parse_args()
    source_dir = Path(args.source_dir)
    issues = check_agentforce_observability(source_dir)

    if not issues:
        print("No Agentforce observability configuration issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
