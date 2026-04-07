#!/usr/bin/env python3
"""Checker script for MCAE (Pardot) Setup skill.

Inspects Salesforce metadata exported via Salesforce CLI (sf project retrieve)
or a standard DX source directory to identify common MCAE setup issues:

- Missing or misconfigured connector user permissions
- Connected App setup for OAuth (if present)
- Profile permission gaps that would block field-level sync
- Campaign member status values that are required for campaign connector

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_mcae_pardot_setup.py [--help]
    python3 check_mcae_pardot_setup.py --manifest-dir path/to/metadata
    python3 check_mcae_pardot_setup.py --manifest-dir force-app/main/default

Expected metadata layout (Salesforce DX source format):
    <manifest-dir>/
        profiles/
            *.profile-meta.xml
        permissionsets/
            *.permissionset-meta.xml
        objects/
            Campaign/
                fields/
                    Status.field-meta.xml
        connectedApps/
            *.connectedApp-meta.xml
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Permissions a connector user profile must contain for MCAE sync to work.
REQUIRED_PROFILE_PERMISSIONS = {
    "ApiEnabled",
    "ViewAllData",
    "ModifyAllData",
    "MarketingUser",
}

# Campaign Member Status values MCAE needs for standard email send attribution.
REQUIRED_CAMPAIGN_MEMBER_STATUSES = {
    "Sent",
    "Opened",
    "Clicked",
    "Responded",
    "Unsubscribed",
}

# Namespace used in Salesforce metadata XML.
SF_NS = "http://soap.sforce.com/2006/04/metadata"


# ---------------------------------------------------------------------------
# XML helpers
# ---------------------------------------------------------------------------

def _text(element: ET.Element | None) -> str:
    """Return stripped text content of an element, or empty string."""
    if element is None:
        return ""
    return (element.text or "").strip()


def _find(root: ET.Element, tag: str) -> ET.Element | None:
    """Find a child element with or without the Salesforce XML namespace."""
    result = root.find(f"{{{SF_NS}}}{tag}")
    if result is None:
        result = root.find(tag)
    return result


def _findall(root: ET.Element, tag: str) -> list[ET.Element]:
    """Find all child elements with or without the Salesforce XML namespace."""
    results = root.findall(f"{{{SF_NS}}}{tag}")
    if not results:
        results = root.findall(tag)
    return results


# ---------------------------------------------------------------------------
# Check: Profile permissions for MCAE connector user
# ---------------------------------------------------------------------------

def _get_profile_permissions(profile_path: Path) -> set[str]:
    """Parse a profile XML file and return all enabled user permissions."""
    enabled: set[str] = set()
    try:
        tree = ET.parse(profile_path)
        root = tree.getroot()
    except ET.ParseError:
        return enabled

    for perm_node in _findall(root, "userPermissions"):
        name_node = _find(perm_node, "name")
        enabled_node = _find(perm_node, "enabled")
        if name_node is not None and _text(enabled_node).lower() == "true":
            enabled.add(_text(name_node))

    return enabled


def check_connector_user_profile_permissions(manifest_dir: Path) -> list[str]:
    """Check all profiles for the permissions required by the MCAE connector user.

    This check does not know which profile is assigned to the connector user,
    so it reports any profile that is missing required permissions. In
    practice, only one profile will be the connector user's profile —
    this makes it easy to spot the gap.
    """
    issues: list[str] = []
    profiles_dir = manifest_dir / "profiles"

    if not profiles_dir.exists():
        issues.append(
            "profiles/ directory not found in manifest-dir. "
            "Cannot validate connector user profile permissions. "
            "Run: sf project retrieve --metadata Profile to export profiles."
        )
        return issues

    profile_files = list(profiles_dir.glob("*.profile-meta.xml"))
    if not profile_files:
        issues.append(
            "No .profile-meta.xml files found in profiles/. "
            "Export at least one profile to validate MCAE connector user permissions."
        )
        return issues

    for profile_path in sorted(profile_files):
        profile_name = profile_path.stem.replace(".profile-meta", "")
        enabled_perms = _get_profile_permissions(profile_path)
        missing = REQUIRED_PROFILE_PERMISSIONS - enabled_perms

        # Only report if this profile is missing any of the required set.
        # We flag all profiles to let the practitioner identify which one
        # is the connector user's profile and confirm it has all required perms.
        if missing:
            missing_str = ", ".join(sorted(missing))
            issues.append(
                f"Profile '{profile_name}' is missing MCAE connector user "
                f"permissions: {missing_str}. "
                "If this profile is assigned to the MCAE connector user, "
                "add these permissions before activating the connector."
            )

    return issues


# ---------------------------------------------------------------------------
# Check: Campaign Member Status values for campaign connector
# ---------------------------------------------------------------------------

def _get_campaign_member_statuses(manifest_dir: Path) -> set[str]:
    """Parse Campaign Member Status picklist values from metadata."""
    statuses: set[str] = set()

    # DX source format: objects/Campaign/fields/Status.field-meta.xml
    status_field = manifest_dir / "objects" / "Campaign" / "fields" / "Status.field-meta.xml"
    if not status_field.exists():
        return statuses

    try:
        tree = ET.parse(status_field)
        root = tree.getroot()
    except ET.ParseError:
        return statuses

    # valueSet/valueSetDefinition/value nodes
    value_set = _find(root, "valueSet")
    if value_set is None:
        return statuses

    value_set_def = _find(value_set, "valueSetDefinition")
    if value_set_def is None:
        return statuses

    for value_node in _findall(value_set_def, "value"):
        label_node = _find(value_node, "label")
        if label_node is not None:
            statuses.add(_text(label_node))

    return statuses


def check_campaign_member_statuses(manifest_dir: Path) -> list[str]:
    """Verify Campaign Member Status picklist has values required by MCAE campaign connector."""
    issues: list[str] = []

    objects_dir = manifest_dir / "objects"
    if not objects_dir.exists():
        # Soft warning — not all metadata exports include Campaign object
        return issues

    campaign_dir = objects_dir / "Campaign"
    if not campaign_dir.exists():
        return issues

    statuses = _get_campaign_member_statuses(manifest_dir)
    if not statuses:
        issues.append(
            "Could not read Campaign Member Status values from "
            "objects/Campaign/fields/Status.field-meta.xml. "
            "Verify the Campaign object is included in the metadata export."
        )
        return issues

    missing = REQUIRED_CAMPAIGN_MEMBER_STATUSES - statuses
    if missing:
        missing_str = ", ".join(sorted(missing))
        issues.append(
            f"Campaign Member Status picklist is missing values required "
            f"for MCAE campaign connector attribution: {missing_str}. "
            "Add these values to the Campaign Status field before configuring "
            "the MCAE campaign connector."
        )

    return issues


# ---------------------------------------------------------------------------
# Check: Connected App presence for OAuth connector
# ---------------------------------------------------------------------------

def check_connected_apps(manifest_dir: Path) -> list[str]:
    """Warn if no Connected App is present — MCAE v2 connector may need one for OAuth."""
    issues: list[str] = []

    connected_apps_dir = manifest_dir / "connectedApps"
    if not connected_apps_dir.exists():
        # Not necessarily an error — connected apps may be managed in MCAE directly.
        return issues

    app_files = list(connected_apps_dir.glob("*.connectedApp-meta.xml"))
    if not app_files:
        issues.append(
            "No Connected App metadata found in connectedApps/. "
            "The MCAE v2 connector uses OAuth 2.0. If the Connected App for MCAE "
            "is not present in source control, confirm it is managed in the org "
            "directly and is not at risk of being overwritten by a deployment."
        )

    return issues


# ---------------------------------------------------------------------------
# Check: Permission Sets for connector user field access
# ---------------------------------------------------------------------------

def check_permission_set_naming(manifest_dir: Path) -> list[str]:
    """Warn if no permission set is present that appears to be for MCAE connector FLS."""
    issues: list[str] = []

    ps_dir = manifest_dir / "permissionsets"
    if not ps_dir.exists():
        return issues

    ps_files = list(ps_dir.glob("*.permissionset-meta.xml"))
    if not ps_files:
        return issues

    # Look for a permission set whose name suggests it is for the MCAE connector.
    mcae_ps_keywords = {"mcae", "pardot", "connector", "account_engagement", "accountengagement"}
    has_mcae_ps = any(
        any(kw in ps_file.stem.lower() for kw in mcae_ps_keywords)
        for ps_file in ps_files
    )

    if not has_mcae_ps:
        issues.append(
            "No permission set found with an MCAE/Pardot/connector-related name. "
            "Best practice is to maintain a dedicated permission set (e.g., "
            "'MCAE_Connector_Field_Access') to manage field-level security for the "
            "MCAE connector user. This makes FLS audits traceable and avoids "
            "modifying the connector user's base profile when new sync fields are added."
        )

    return issues


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def check_mcae_pardot_setup(manifest_dir: Path) -> list[str]:
    """Run all MCAE setup checks and return a consolidated list of issues."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_connector_user_profile_permissions(manifest_dir))
    issues.extend(check_campaign_member_statuses(manifest_dir))
    issues.extend(check_connected_apps(manifest_dir))
    issues.extend(check_permission_set_naming(manifest_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for common MCAE (Pardot) setup issues: "
            "connector user permissions, campaign member statuses, and permission set structure."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help=(
            "Root directory of the Salesforce metadata in DX source format "
            "(default: current directory). Expected subdirectories: "
            "profiles/, permissionsets/, objects/, connectedApps/."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_mcae_pardot_setup(manifest_dir)

    if not issues:
        print("No MCAE setup issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
