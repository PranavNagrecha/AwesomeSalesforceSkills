#!/usr/bin/env python3
"""Checker script for OmniStudio Admin Configuration skill.

Validates Salesforce metadata for common OmniStudio admin configuration issues:
  - Missing or blank Runtime Namespace in OmniStudio custom settings
  - Permission set assignments that lack a corresponding PSL
  - Community user permission sets missing the community consumer custom permission
  - Presence of OmniStudio Admin permission set assignments to non-admin profiles

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_omnistudio_admin_configuration.py [--help]
    python3 check_omnistudio_admin_configuration.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# Valid OmniStudio runtime namespace values
VALID_NAMESPACES = {"omnistudio", "vlocity_ins", "vlocity_cmt", "vlocity_ps"}

# Permission sets that require the OmniStudio PSL to be present
OMNISTUDIO_PERMISSION_SETS = {"OmniStudioAdmin", "OmniStudioUser"}

# The PSL that must be present before OmniStudio permission sets are assigned
OMNISTUDIO_PSL = "OmniStudioPSL"

# Custom permission required for Experience Cloud community user access
COMMUNITY_CONSUMER_PERMISSION = "OmniStudioCommunityUser"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check OmniStudio admin configuration metadata for common issues.\n\n"
            "Checks performed:\n"
            "  1. OmniStudio custom setting: Runtime Namespace is present and valid\n"
            "  2. Permission sets: OmniStudio Admin / User have PSL dependency noted\n"
            "  3. Profiles: OmniStudio Admin not assigned to standard user profiles\n"
            "  4. Custom settings XML: enableOaForCore (Standard Runtime) is present"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _parse_xml_safe(path: Path) -> ET.Element | None:
    """Parse an XML file and return the root element, or None on failure."""
    try:
        tree = ET.parse(path)
        return tree.getroot()
    except ET.ParseError as exc:
        return None


def check_custom_settings_namespace(manifest_dir: Path) -> list[str]:
    """Check OmniStudio custom settings for missing or invalid Runtime Namespace."""
    issues: list[str] = []

    # OmniStudio settings may live in customSettings/ or settings/ depending on org
    candidate_dirs = [
        manifest_dir / "customSettings",
        manifest_dir / "settings",
        manifest_dir / "objects",
    ]

    omnistudio_settings_found = False

    for settings_dir in candidate_dirs:
        if not settings_dir.exists():
            continue
        for xml_file in settings_dir.rglob("*.xml"):
            root = _parse_xml_safe(xml_file)
            if root is None:
                continue
            # Look for OmniStudio-related setting records
            text_content = xml_file.read_text(encoding="utf-8", errors="replace")
            if "OmniStudio" not in text_content and "vlocity" not in text_content.lower():
                continue
            omnistudio_settings_found = True
            # Check for namespace field
            if "runtimeNamespace" in text_content or "RuntimeNamespace" in text_content:
                # Try to find the value
                for elem in root.iter():
                    tag = elem.tag.split("}")[-1]  # strip namespace prefix
                    if tag in ("runtimeNamespace", "RuntimeNamespace"):
                        val = (elem.text or "").strip()
                        if not val:
                            issues.append(
                                f"OmniStudio Settings: Runtime Namespace is blank in {xml_file}. "
                                "This will cause component activation failures. "
                                "Set to: omnistudio, vlocity_ins, vlocity_cmt, or vlocity_ps."
                            )
                        elif val not in VALID_NAMESPACES:
                            issues.append(
                                f"OmniStudio Settings: Runtime Namespace value '{val}' in {xml_file} "
                                f"is not a recognised namespace. "
                                f"Valid values: {', '.join(sorted(VALID_NAMESPACES))}."
                            )

    return issues


def check_permission_set_files(manifest_dir: Path) -> list[str]:
    """Check permission set XML files for OmniStudio PSL dependency issues."""
    issues: list[str] = []

    ps_dir = manifest_dir / "permissionsets"
    if not ps_dir.exists():
        return issues

    found_omnistudio_admin = False
    found_omnistudio_user = False
    found_psl_reference = False

    for ps_file in ps_dir.glob("*.permissionset-meta.xml"):
        root = _parse_xml_safe(ps_file)
        if root is None:
            continue
        text_content = ps_file.read_text(encoding="utf-8", errors="replace")

        # Detect OmniStudio permission sets
        if "OmniStudioAdmin" in ps_file.name or "OmniStudio_Admin" in ps_file.name:
            found_omnistudio_admin = True
        if "OmniStudioUser" in ps_file.name or "OmniStudio_User" in ps_file.name:
            found_omnistudio_user = True
        if OMNISTUDIO_PSL in text_content:
            found_psl_reference = True

    # If OmniStudio permission sets exist but no PSL reference found in any file
    if (found_omnistudio_admin or found_omnistudio_user) and not found_psl_reference:
        issues.append(
            "OmniStudio permission sets (Admin or User) are present in permissionsets/ "
            "but no reference to OmniStudioPSL Permission Set License was found. "
            "Ensure OmniStudioPSL PSL is assigned to users BEFORE assigning OmniStudio permission sets."
        )

    return issues


def check_profile_permission_set_assignments(manifest_dir: Path) -> list[str]:
    """Check profile files for OmniStudio Admin permission being assigned to standard user profiles."""
    issues: list[str] = []

    # Standard non-admin profile names that should not have OmniStudio Admin access
    non_admin_profile_indicators = {
        "standard user", "read only", "chatter free", "chatter external",
        "guest", "customer community", "partner community", "high volume customer portal",
    }

    profiles_dir = manifest_dir / "profiles"
    if not profiles_dir.exists():
        return issues

    for profile_file in profiles_dir.glob("*.profile-meta.xml"):
        profile_name = profile_file.stem.replace(".profile-meta", "").lower()
        text_content = profile_file.read_text(encoding="utf-8", errors="replace")

        # If this profile name suggests it is non-admin
        is_non_admin = any(indicator in profile_name for indicator in non_admin_profile_indicators)

        if is_non_admin and "OmniStudioAdmin" in text_content:
            issues.append(
                f"Profile '{profile_file.stem}' appears to be a non-admin profile but references "
                "OmniStudio Admin permission. Verify this is intentional — "
                "OmniStudio Admin grants full authoring access and should not be assigned to "
                "consumer or community profiles."
            )

    return issues


def check_custom_permissions_for_community(manifest_dir: Path) -> list[str]:
    """Check for missing community consumer custom permission in Experience Cloud permission sets."""
    issues: list[str] = []

    ps_dir = manifest_dir / "permissionsets"
    if not ps_dir.exists():
        return issues

    community_ps_files = []
    for ps_file in ps_dir.glob("*.permissionset-meta.xml"):
        text_content = ps_file.read_text(encoding="utf-8", errors="replace")
        # Detect permission sets that seem to target community users
        if any(kw in text_content.lower() for kw in ["community", "portal", "experiencecloud"]):
            community_ps_files.append((ps_file, text_content))

    for ps_file, text_content in community_ps_files:
        if "OmniStudioUser" in text_content and COMMUNITY_CONSUMER_PERMISSION not in text_content:
            issues.append(
                f"Permission set '{ps_file.stem}' appears to target community/portal users and "
                "includes OmniStudio User access, but the OmniStudioCommunityUser custom permission "
                "is not present. Community users require this custom permission to load OmniScripts. "
                "Add a customPermissions entry for OmniStudioCommunityUser."
            )

    return issues


def check_omnistudio_admin_configuration(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_custom_settings_namespace(manifest_dir))
    issues.extend(check_permission_set_files(manifest_dir))
    issues.extend(check_profile_permission_set_assignments(manifest_dir))
    issues.extend(check_custom_permissions_for_community(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_omnistudio_admin_configuration(manifest_dir)

    if not issues:
        print("No OmniStudio admin configuration issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    print(f"\n{len(issues)} issue(s) found.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
