#!/usr/bin/env python3
"""Checker script for Partner Data Access Patterns skill.

Scans a Salesforce metadata directory for common partner data access
anti-patterns: missing External OWD configuration, sharing rules that
duplicate hierarchy access, and community license mismatches.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_partner_data_access_patterns.py [--help]
    python3 check_partner_data_access_patterns.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for partner data access anti-patterns. "
            "Looks for sharing-settings XML, object XML, and profile XML files."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# XML helpers
# ---------------------------------------------------------------------------

SF_NS = "http://soap.sforce.com/2006/04/metadata"


def _tag(local: str) -> str:
    return f"{{{SF_NS}}}{local}"


def parse_xml(path: Path) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError:
        return None


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_sharing_settings(manifest_dir: Path) -> list[str]:
    """Check SharingSettings metadata for missing or overly permissive External OWD."""
    issues: list[str] = []
    sharing_dir = manifest_dir / "sharingRules"
    settings_path = manifest_dir / "settings" / "Sharing.settings-meta.xml"

    # Check Sharing.settings for External OWD on high-risk objects
    if settings_path.exists():
        root = parse_xml(settings_path)
        if root is not None:
            # Look for defaultSharingAccess entries
            for default in root.iter(_tag("sharingModel")):
                text = (default.text or "").strip()
                if text in ("ReadWrite", "ReadWriteTransfer", "ControlledByLeadOrContact"):
                    parent = default.getparent() if hasattr(default, "getparent") else None
                    issues.append(
                        f"Sharing.settings: found a sharing model of '{text}' — "
                        "verify this is not applied as External OWD on a PRM object "
                        "(Lead, Opportunity) visible to partner users."
                    )
    else:
        issues.append(
            "No Sharing.settings-meta.xml found. Cannot verify External OWD settings. "
            "Manually confirm External OWD is explicitly set (not relying on defaults) "
            "for Lead, Opportunity, and Deal Registration objects."
        )

    return issues


def check_for_redundant_partner_sharing_rules(manifest_dir: Path) -> list[str]:
    """Detect sharing rules that appear to duplicate partner role hierarchy access."""
    issues: list[str] = []
    sharing_rules_dir = manifest_dir / "sharingRules"

    if not sharing_rules_dir.exists():
        return issues

    # Keywords that suggest partner hierarchy role names in sharing rule targets
    partner_role_keywords = [
        "partnerexecutive", "partnermanager", "partneruser",
        "partner_executive", "partner_manager", "partner_user",
        "channelpartner", "channel_partner",
    ]

    for xml_file in sharing_rules_dir.glob("*.sharingRules-meta.xml"):
        root = parse_xml(xml_file)
        if root is None:
            continue

        for rule in root.iter(_tag("sharingOwnerRules")):
            shared_to = rule.find(_tag("sharedTo"))
            shared_to_role = rule.find(f".//{_tag('role')}") or rule.find(f".//{_tag('roleAndSubordinates')}")
            shared_from = rule.find(_tag("sharedFrom"))
            shared_from_role = shared_from.find(_tag("role")) if shared_from is not None else None

            if shared_to_role is not None and shared_from_role is not None:
                to_text = (shared_to_role.text or "").lower()
                from_text = (shared_from_role.text or "").lower()

                to_is_partner = any(kw in to_text for kw in partner_role_keywords)
                from_is_partner = any(kw in from_text for kw in partner_role_keywords)

                if to_is_partner and from_is_partner:
                    issues.append(
                        f"{xml_file.name}: Owner-based sharing rule shares from partner role "
                        f"'{shared_from_role.text}' to partner role '{shared_to_role.text}'. "
                        "Verify this rule is not duplicating visibility already provided by "
                        "the auto-generated partner role hierarchy. Within-account manager "
                        "visibility does not require an explicit sharing rule."
                    )

    return issues


def check_partner_profile_licenses(manifest_dir: Path) -> list[str]:
    """Scan profile XML files for partner-labeled profiles and flag if PRM objects are referenced
    without a Partner Community license context."""
    issues: list[str] = []
    profiles_dir = manifest_dir / "profiles"

    if not profiles_dir.exists():
        return issues

    prm_objects = {"PartnerFundRequest", "PartnerFundClaim", "PartnerMarketingBudget"}
    non_partner_license_keywords = ["CustomerCommunity", "Customer Community", "CustomerPortal"]

    for profile_file in profiles_dir.glob("*.profile-meta.xml"):
        root = parse_xml(profile_file)
        if root is None:
            continue

        profile_name = profile_file.stem.replace(".profile-meta", "")

        # Check if profile name or license suggests a non-Partner Community license
        license_el = root.find(_tag("userLicense"))
        license_text = (license_el.text or "") if license_el is not None else ""

        is_non_partner = any(kw.lower() in license_text.lower() for kw in non_partner_license_keywords)
        if not is_non_partner:
            is_non_partner = any(kw.lower() in profile_name.lower() for kw in ["customercommunity", "customer_community"])

        if is_non_partner:
            # Check for PRM object permissions
            for obj_perm in root.iter(_tag("objectPermissions")):
                obj_name_el = obj_perm.find(_tag("object"))
                if obj_name_el is not None and obj_name_el.text in prm_objects:
                    allow_read = obj_perm.find(_tag("allowRead"))
                    if allow_read is not None and (allow_read.text or "").strip().lower() == "true":
                        issues.append(
                            f"Profile '{profile_name}': PRM object '{obj_name_el.text}' has "
                            "Read access enabled but the profile appears to use a Customer Community "
                            "license. PRM objects are only accessible to Partner Community licensees. "
                            "Verify the license assignment or remove the object permission."
                        )

    return issues


def check_missing_partner_hierarchy_grant(manifest_dir: Path) -> list[str]:
    """Check custom object XML to see if 'sharingModel' is set but hierarchy grant is ambiguous."""
    issues: list[str] = []
    objects_dir = manifest_dir / "objects"

    if not objects_dir.exists():
        return issues

    for obj_dir in objects_dir.iterdir():
        if not obj_dir.is_dir():
            continue
        obj_xml = obj_dir / f"{obj_dir.name}.object-meta.xml"
        if not obj_xml.exists():
            continue

        root = parse_xml(obj_xml)
        if root is None:
            continue

        sharing_model = root.find(_tag("sharingModel"))
        enable_activities = root.find(_tag("enableActivities"))

        if sharing_model is not None and (sharing_model.text or "").strip() == "Private":
            # Check for explicit hierarchy grant setting
            # In Salesforce metadata, custom objects have a 'externalSharingModel' field
            ext_sharing = root.find(_tag("externalSharingModel"))
            if ext_sharing is None:
                issues.append(
                    f"Object '{obj_dir.name}': sharingModel is 'Private' but "
                    "externalSharingModel is not explicitly set in object metadata. "
                    "Verify External OWD is explicitly configured in Sharing Settings "
                    "for this object if it is exposed in a Partner Community."
                )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_partner_data_access_patterns(manifest_dir: Path) -> list[str]:
    """Run all partner data access pattern checks and return a list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_sharing_settings(manifest_dir))
    issues.extend(check_for_redundant_partner_sharing_rules(manifest_dir))
    issues.extend(check_partner_profile_licenses(manifest_dir))
    issues.extend(check_missing_partner_hierarchy_grant(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_partner_data_access_patterns(manifest_dir)

    if not issues:
        print("No partner data access pattern issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
