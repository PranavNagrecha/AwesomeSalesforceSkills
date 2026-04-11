#!/usr/bin/env python3
"""Checker script for Care Coordination Requirements skill.

Checks org metadata for common Health Cloud Integrated Care Management issues:
- ICM-related Flow patterns
- Permission set references for HealthCloudICM
- CareGap object usage patterns

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_care_coordination_requirements.py [--help]
    python3 check_care_coordination_requirements.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Health Cloud care coordination configuration for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_caregap_creation_in_flows(manifest_dir: Path) -> list[str]:
    """Check Flows for patterns that attempt to create CareGap records."""
    issues: list[str] = []
    flows_dir = manifest_dir / "flows"
    if not flows_dir.exists():
        return issues

    for flow_file in flows_dir.glob("*.flow-meta.xml"):
        content = flow_file.read_text(encoding="utf-8")
        if "CareGap" in content and "<recordCreates>" in content:
            issues.append(
                f"{flow_file.name}: Flow contains a recordCreates element that may reference CareGap. "
                "CareGap records (API v59.0+) are system-generated and cannot be created via standard DML. "
                "Verify this is not attempting manual CareGap creation."
            )
    return issues


def check_icm_permission_references(manifest_dir: Path) -> list[str]:
    """Check for HealthCloudICM permission set references."""
    issues: list[str] = []
    perm_dir = manifest_dir / "permissionsets"
    if not perm_dir.exists():
        return issues

    hc_icm_found = any(
        "HealthCloudICM" in f.name
        for f in perm_dir.glob("*.permissionset-meta.xml")
    )
    if not hc_icm_found:
        # Check in permissionsetgroups
        psg_dir = manifest_dir / "permissionsetgroups"
        if psg_dir.exists():
            for f in psg_dir.glob("*.permissionsetgroup-meta.xml"):
                if "HealthCloudICM" in f.read_text(encoding="utf-8"):
                    hc_icm_found = True
                    break

    if not hc_icm_found:
        issues.append(
            "HealthCloudICM permission set not found in permissionsets/ or permissionsetgroups/. "
            "ICM objects (ClinicalServiceRequest, CareGap, CareBarrier, CareEpisode) require "
            "the HealthCloudICM permission set. Verify it is assigned via Setup > Permission Sets."
        )
    return issues


def check_carebarrier_flow_patterns(manifest_dir: Path) -> list[str]:
    """Check for CareBarrier Flow patterns that may lack Case reference."""
    issues: list[str] = []
    flows_dir = manifest_dir / "flows"
    if not flows_dir.exists():
        return issues

    for flow_file in flows_dir.glob("*.flow-meta.xml"):
        content = flow_file.read_text(encoding="utf-8")
        if "CareBarrier" in content and "Case" not in content:
            issues.append(
                f"{flow_file.name}: Flow references CareBarrier but does not appear to reference Case. "
                "CareBarrier records should be linked to both Account (patient) and a related Case "
                "to enable full care coordination Task tracking."
            )
    return issues


def check_care_coordination_requirements(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_caregap_creation_in_flows(manifest_dir))
    issues.extend(check_icm_permission_references(manifest_dir))
    issues.extend(check_carebarrier_flow_patterns(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_care_coordination_requirements(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
