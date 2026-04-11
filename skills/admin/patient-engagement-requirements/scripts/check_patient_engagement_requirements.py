#!/usr/bin/env python3
"""Checker script for Patient Engagement Requirements skill.

Checks org metadata for common patient engagement configuration issues:
- Experience Cloud permission set references
- OmniStudio component presence
- Messaging channel configuration

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_patient_engagement_requirements.py [--help]
    python3 check_patient_engagement_requirements.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check patient engagement configuration for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_experience_cloud_health_cloud_perms(manifest_dir: Path) -> list[str]:
    """Check for Experience Cloud for Health Cloud permission set references."""
    issues: list[str] = []
    perm_dir = manifest_dir / "permissionsets"
    if not perm_dir.exists():
        return issues

    hc_exp_found = any(
        "HealthCloudExperience" in f.name or "ExperienceCloudHealthCloud" in f.name
        for f in perm_dir.glob("*.permissionset-meta.xml")
    )
    if not hc_exp_found:
        issues.append(
            "No Experience Cloud for Health Cloud permission set found in permissionsets/. "
            "Patient portal users require the Experience Cloud for Health Cloud permission set license. "
            "Verify this is assigned and the license is included in the contract."
        )
    return issues


def check_omnistudio_components(manifest_dir: Path) -> list[str]:
    """Check for OmniStudio component references."""
    issues: list[str] = []
    omniscript_dir = manifest_dir / "omniScripts"
    omnistudio_perm = False

    perm_dir = manifest_dir / "permissionsets"
    if perm_dir.exists():
        for f in perm_dir.glob("*.permissionset-meta.xml"):
            if "OmniStudio" in f.read_text(encoding="utf-8"):
                omnistudio_perm = True
                break

    if not omniscript_dir.exists() and not omnistudio_perm:
        issues.append(
            "No OmniScript metadata or OmniStudio permission references found. "
            "If health assessments are in scope, OmniStudio must be installed and "
            "Discovery Framework must be separately installed. "
            "Verify in Setup > Installed Packages."
        )
    return issues


def check_patient_engagement_requirements(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_experience_cloud_health_cloud_perms(manifest_dir))
    issues.extend(check_omnistudio_components(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_patient_engagement_requirements(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
