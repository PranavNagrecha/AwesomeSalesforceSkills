#!/usr/bin/env python3
"""Checker script for License Optimization Strategy skill.

Inspects a Salesforce metadata export directory for common license-optimization
issues: profiles bound to high-cost licenses when lower-cost alternatives may
suffice, permission set license assignments in metadata, and user configuration
patterns that indicate over-licensing.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_license_optimization_strategy.py [--help]
    python3 check_license_optimization_strategy.py --manifest-dir path/to/metadata
    python3 check_license_optimization_strategy.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# Salesforce metadata namespace
SF_NS = "http://soap.sforce.com/2006/04/metadata"

# Profiles whose User License should be reviewed for potential Platform downgrade
# These are placeholder names — real orgs will vary.
CANDIDATE_DOWNGRADE_PROFILE_KEYWORDS = [
    "read only",
    "readonly",
    "read-only",
    "viewer",
    "reporting",
    "report only",
    "dashboard",
]

# Standard CRM objects — if a Platform-license candidate profile has object
# permissions on these, the downgrade would remove access.
STANDARD_CRM_OBJECTS = {
    "Lead",
    "Opportunity",
    "OpportunityLineItem",
    "Contract",
    "Order",
    "OrderItem",
    "Quote",
    "QuoteLineItem",
    "Case",
    "Entitlement",
    "ServiceContract",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for common license optimization issues: "
            "over-licensed profiles, CRM object access on potential Platform-license "
            "candidates, and permission set license metadata."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata export (default: current directory).",
    )
    return parser.parse_args()


def _xml_text(element: ET.Element | None) -> str:
    """Return stripped text content of an XML element, or empty string."""
    if element is None:
        return ""
    return (element.text or "").strip()


def check_profiles(manifest_dir: Path) -> list[str]:
    """Check profile XML files for potential downgrade candidates and over-privileged access."""
    issues: list[str] = []

    profiles_dir = manifest_dir / "profiles"
    if not profiles_dir.is_dir():
        # Try alternative DX layout
        profiles_dir = manifest_dir / "force-app" / "main" / "default" / "profiles"

    if not profiles_dir.is_dir():
        return issues  # No profiles directory — skip silently

    profile_files = list(profiles_dir.glob("*.profile-meta.xml")) + list(
        profiles_dir.glob("*.profile")
    )

    for profile_file in profile_files:
        profile_name = profile_file.stem.replace(".profile-meta", "").replace(".profile", "")
        try:
            tree = ET.parse(profile_file)
        except ET.ParseError as exc:
            issues.append(f"Profile XML parse error in {profile_file.name}: {exc}")
            continue

        root = tree.getroot()

        # Check whether this profile name suggests a read-only / reporting role
        name_lower = profile_name.lower()
        is_downgrade_candidate = any(
            kw in name_lower for kw in CANDIDATE_DOWNGRADE_PROFILE_KEYWORDS
        )

        if not is_downgrade_candidate:
            continue

        # Collect object permissions for CRM objects
        crm_objects_with_read = []
        for obj_perm in root.findall(f"{{{SF_NS}}}objectPermissions"):
            obj_name = _xml_text(obj_perm.find(f"{{{SF_NS}}}object"))
            allow_read = _xml_text(obj_perm.find(f"{{{SF_NS}}}allowRead"))
            if obj_name in STANDARD_CRM_OBJECTS and allow_read.lower() == "true":
                crm_objects_with_read.append(obj_name)

        if crm_objects_with_read:
            issues.append(
                f"Profile '{profile_name}' appears to be a read-only/reporting profile "
                f"(name matches downgrade-candidate keywords) but has Read access on "
                f"standard CRM objects: {', '.join(sorted(crm_objects_with_read))}. "
                f"Review whether this profile can be migrated to a Salesforce Platform "
                f"license — if so, CRM object permissions must be removed first."
            )
        else:
            issues.append(
                f"Profile '{profile_name}' appears to be a read-only/reporting profile "
                f"with no standard CRM object access. This profile may be a candidate "
                f"for a Salesforce Platform license downgrade. Validate in sandbox before "
                f"migrating production users."
            )

    return issues


def check_permission_set_licenses(manifest_dir: Path) -> list[str]:
    """Check for permission set metadata that references a license — surfaces PSL assignments."""
    issues: list[str] = []

    perm_sets_dir = manifest_dir / "permissionsets"
    if not perm_sets_dir.is_dir():
        perm_sets_dir = manifest_dir / "force-app" / "main" / "default" / "permissionsets"

    if not perm_sets_dir.is_dir():
        return issues

    perm_set_files = list(perm_sets_dir.glob("*.permissionset-meta.xml")) + list(
        perm_sets_dir.glob("*.permissionset")
    )

    for ps_file in perm_set_files:
        ps_name = ps_file.stem.replace(".permissionset-meta", "").replace(".permissionset", "")
        try:
            tree = ET.parse(ps_file)
        except ET.ParseError as exc:
            issues.append(f"PermissionSet XML parse error in {ps_file.name}: {exc}")
            continue

        root = tree.getroot()
        license_elem = root.find(f"{{{SF_NS}}}license")
        if license_elem is not None and _xml_text(license_elem):
            license_name = _xml_text(license_elem)
            issues.append(
                f"PermissionSet '{ps_name}' references a PSL: '{license_name}'. "
                f"Ensure PSL seat counts are reviewed at renewal. Confirm no inactive "
                f"users hold this PSL assignment unnecessarily — query "
                f"PermissionSetLicenseAssign for users with LastLoginDate older than "
                f"90 days who hold this PSL."
            )

    return issues


def check_profiles_for_user_license_field(manifest_dir: Path) -> list[str]:
    """Check that profiles specify a userLicense element — absence may indicate a metadata gap."""
    issues: list[str] = []

    profiles_dir = manifest_dir / "profiles"
    if not profiles_dir.is_dir():
        profiles_dir = manifest_dir / "force-app" / "main" / "default" / "profiles"

    if not profiles_dir.is_dir():
        return issues

    profile_files = list(profiles_dir.glob("*.profile-meta.xml")) + list(
        profiles_dir.glob("*.profile")
    )

    for profile_file in profile_files:
        profile_name = profile_file.stem.replace(".profile-meta", "").replace(".profile", "")
        try:
            tree = ET.parse(profile_file)
        except ET.ParseError:
            continue  # Already reported above

        root = tree.getroot()
        user_license_elem = root.find(f"{{{SF_NS}}}userLicense")
        if user_license_elem is None or not _xml_text(user_license_elem):
            issues.append(
                f"Profile '{profile_name}' does not specify a <userLicense> element in "
                f"its metadata. The license binding cannot be verified from metadata alone. "
                f"Confirm the license type in Setup > Profiles for this profile."
            )

    return issues


def check_license_optimization_strategy(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_profiles(manifest_dir))
    issues.extend(check_permission_set_licenses(manifest_dir))
    issues.extend(check_profiles_for_user_license_field(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_license_optimization_strategy(manifest_dir)

    if not issues:
        print("No license optimization issues detected in metadata.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")
        print()

    print(f"Total issues: {len(issues)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
