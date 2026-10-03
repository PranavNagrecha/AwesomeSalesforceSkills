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
import re
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


def check_caregap_status_writes_in_flows(manifest_dir: Path) -> list[str]:
    """Flag Flows that write CareGap.Status directly.

    `CareGap` supports create(), update() and upsert() (Health Cloud developer guide, CareGap,
    API 59.0) — earlier versions of this checker wrongly flagged every recordCreates on it.
    What is NOT writable is `CareGap.Status` (Open / Closed / Excluded): the field carries no
    Create or Update property. Closure runs through `MeasureEvaluationStatus`. Corrected
    2026-10-03.
    """
    issues: list[str] = []
    flows_dir = manifest_dir / "flows"
    if not flows_dir.exists():
        return issues

    block_re = re.compile(r"<(recordUpdates|recordCreates)>(.*?)</\1>", re.S)
    for flow_file in sorted(flows_dir.glob("*.flow-meta.xml")):
        content = flow_file.read_text(encoding="utf-8")
        if "CareGap" not in content:
            continue
        for m in block_re.finditer(content):
            block = m.group(2)
            if "<object>CareGap</object>" not in block:
                continue
            assigns = re.findall(r"<inputAssignments>(.*?)</inputAssignments>", block, re.S)
            if any("<field>Status</field>" in a for a in assigns):
                issues.append(
                    f"{flow_file.name}: Flow assigns CareGap.Status directly. The field is not "
                    "writable (no Create/Update property); set MeasureEvaluationStatus and let the "
                    "platform derive Status (Health Cloud developer guide, CareGap)."
                )
                break
    return issues


def check_icm_permission_references(manifest_dir: Path) -> list[str]:
    """Check that some permission set grants the ICM / social-determinants objects.

    Earlier versions required a permission set literally named `HealthCloudICM`; that name
    is not in the Summer '26 developer guide and is UNVERIFIED (2026-10-03). The rule now
    checks object permissions, not a name.
    """
    issues: list[str] = []
    perm_dir = manifest_dir / "permissionsets"
    if not perm_dir.exists():
        return issues

    icm_objects = ("CareGap", "CareBarrier", "CareEpisode", "ClinicalServiceRequest")
    referenced: set[str] = set()
    for search_dir, pattern in (("flows", "*.flow-meta.xml"), ("classes", "*.cls")):
        d = manifest_dir / search_dir
        if d.exists():
            for f in d.glob(pattern):
                text = f.read_text(encoding="utf-8")
                referenced.update(o for o in icm_objects if o in text)
    if not referenced:
        return issues

    granted: set[str] = set()
    for f in perm_dir.glob("*.permissionset-meta.xml"):
        text = f.read_text(encoding="utf-8")
        for obj in referenced:
            if re.search(rf"<object>{obj}</object>", text):
                granted.add(obj)
    for obj in sorted(referenced - granted):
        issues.append(
            f"No permission set in permissionsets/ grants object permissions on {obj}, which the "
            "automation references. Health Cloud ICM and social-determinants objects need the Health "
            "Cloud permission set licenses plus a permission set granting the object; add the "
            "objectPermissions entry or confirm the grant comes from a managed permission set."
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

    issues.extend(check_caregap_status_writes_in_flows(manifest_dir))
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
