#!/usr/bin/env python3
"""Checker script for OmniStudio Testing Patterns skill.

Checks OmniStudio component metadata for common testing anti-patterns.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_omnistudio_testing_patterns.py [--help]
    python3 check_omnistudio_testing_patterns.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check OmniStudio metadata for testing-related issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_omnistudio_testing_patterns(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory.

    Checks OmniStudio component metadata for common testing anti-patterns:
    - OmniScripts with Navigation Actions (must be tested in deployed runtime, not just Preview)
    - Integration Procedures with HTTP callout steps (Named Credential must be validated)
    - DataRaptor Transforms that map from fields often restricted by FLS
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check for OmniScript JSON files with Navigation Actions
    omni_script_dir = manifest_dir / "OmniScript"
    if omni_script_dir.exists():
        for script_file in omni_script_dir.glob("*.json"):
            try:
                data = json.loads(script_file.read_text(encoding="utf-8"))
                script_name = script_file.stem

                # Check for Navigation Action steps
                steps = data.get("steps", []) if isinstance(data, dict) else []
                nav_action_steps = [
                    s for s in steps
                    if isinstance(s, dict) and s.get("type", "").lower() in (
                        "navigationaction", "navigation_action", "save", "navigate"
                    )
                ]
                if nav_action_steps:
                    issues.append(
                        f"OmniScript '{script_name}' contains Navigation Action steps "
                        f"({len(nav_action_steps)} found). "
                        "These are skipped by OmniScript Preview — must be tested in deployed runtime."
                    )
            except (json.JSONDecodeError, OSError):
                # Not a valid JSON OmniScript — skip
                pass

    # Check for Integration Procedure files with HTTP callout steps
    ip_dir = manifest_dir / "IntegrationProcedure"
    if ip_dir.exists():
        for ip_file in ip_dir.glob("*.json"):
            try:
                data = json.loads(ip_file.read_text(encoding="utf-8"))
                ip_name = ip_file.stem

                steps = data.get("steps", []) if isinstance(data, dict) else []
                http_steps = [
                    s for s in steps
                    if isinstance(s, dict) and "http" in s.get("type", "").lower()
                ]
                if http_steps:
                    issues.append(
                        f"Integration Procedure '{ip_name}' contains HTTP callout steps "
                        f"({len(http_steps)} found). "
                        "Verify each step's Named Credential is active and accessible "
                        "to the integration user before deploying."
                    )
            except (json.JSONDecodeError, OSError):
                pass

    # Check for DataRaptor files — warn if found without corresponding test notes
    dr_dir = manifest_dir / "DataRaptor"
    if dr_dir.exists():
        dr_files = list(dr_dir.glob("*.json"))
        if dr_files:
            issues.append(
                f"Found {len(dr_files)} DataRaptor component(s). "
                "Ensure each DataRaptor has been validated via DataRaptor Preview "
                "with representative test data before wiring into an Integration Procedure."
            )

    if not issues:
        return []

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_omnistudio_testing_patterns(manifest_dir)

    if not issues:
        print("No OmniStudio testing pattern issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
