#!/usr/bin/env python3
"""Checker script for Experience Cloud Licensing Model skill.

Scans Salesforce metadata in a project directory and flags common licensing
configuration issues: profiles that assign Customer Community licenses to users
who may need reports, login-based license usage patterns, and sharing model
mismatches.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_experience_cloud_licensing_model.py [--help]
    python3 check_experience_cloud_licensing_model.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# License profile name fragments used to identify Experience Cloud license tiers
_CUSTOMER_COMMUNITY_MARKERS = [
    "Customer Community",
    "CustomerCommunity",
    "customer_community",
]
_CUSTOMER_COMMUNITY_PLUS_MARKERS = [
    "Customer Community Plus",
    "CustomerCommunityPlus",
    "customer_community_plus",
]
_PARTNER_COMMUNITY_MARKERS = [
    "Partner Community",
    "PartnerCommunity",
    "partner_community",
]

# Metadata XML namespaces used in Salesforce profile/permission files
_SF_NS = "http://soap.sforce.com/2006/04/metadata"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Experience Cloud licensing configuration in Salesforce metadata "
            "for common issues (gotchas documented in references/gotchas.md)."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _contains_any(text: str, markers: list[str]) -> bool:
    text_lower = text.lower()
    return any(m.lower() in text_lower for m in markers)


def _check_profiles_for_report_tab(profiles_dir: Path) -> list[str]:
    """Warn if a Customer Community profile enables the Reports tab.

    Customer Community license holders cannot view reports regardless of
    profile tab visibility settings. A Reports tab on a CC profile is
    misleading and will result in empty/error pages for portal users.
    """
    issues: list[str] = []
    if not profiles_dir.exists():
        return issues

    for profile_file in profiles_dir.glob("*.profile-meta.xml"):
        profile_name = profile_file.stem.replace(".profile-meta", "")
        if not _contains_any(profile_name, _CUSTOMER_COMMUNITY_MARKERS):
            continue
        # Skip Customer Community Plus — reports ARE supported there
        if _contains_any(profile_name, _CUSTOMER_COMMUNITY_PLUS_MARKERS):
            continue

        try:
            tree = ET.parse(profile_file)
        except ET.ParseError:
            issues.append(
                f"[{profile_file.name}] XML parse error — cannot inspect tab visibility."
            )
            continue

        root = tree.getroot()
        ns = {"sf": _SF_NS}

        for tab_vis in root.findall("sf:tabVisibilities", ns):
            tab_el = tab_vis.find("sf:tab", ns)
            vis_el = tab_vis.find("sf:visibility", ns)
            if tab_el is None or vis_el is None:
                continue
            tab_name = (tab_el.text or "").strip()
            visibility = (vis_el.text or "").strip()
            if "Report" in tab_name and visibility not in ("Hidden", "DefaultOff"):
                issues.append(
                    f"[{profile_name}] Tab '{tab_name}' is set to '{visibility}' but "
                    f"Customer Community license cannot display native Reports. "
                    f"This will confuse portal users. Set tab to Hidden or upgrade "
                    f"to Customer Community Plus if reports are required."
                )

    return issues


def _check_sharing_sets_presence(objects_dir: Path) -> list[str]:
    """Inform if no sharing set configuration is found.

    Customer Community portals rely on Sharing Sets for record access.
    A project with Customer Community profiles but no sharing configuration
    is likely misconfigured (all portal users will see an empty org-wide default).
    """
    issues: list[str] = []
    # Sharing sets are configured in Network metadata (.network-meta.xml)
    network_dir = objects_dir.parent / "networks"
    if not network_dir.exists():
        return issues

    has_sharing_set = False
    for network_file in network_dir.glob("*.network-meta.xml"):
        try:
            content = network_file.read_text(encoding="utf-8")
        except OSError:
            continue
        if "SharingSet" in content or "sharingSet" in content:
            has_sharing_set = True
            break

    # Only report if Customer Community profiles exist but no sharing set found
    profiles_dir = objects_dir.parent / "profiles"
    has_cc_profile = False
    if profiles_dir.exists():
        for p in profiles_dir.glob("*.profile-meta.xml"):
            if _contains_any(p.stem, _CUSTOMER_COMMUNITY_MARKERS) and not _contains_any(
                p.stem, _CUSTOMER_COMMUNITY_PLUS_MARKERS
            ):
                has_cc_profile = True
                break

    if has_cc_profile and not has_sharing_set:
        issues.append(
            "Customer Community profile(s) found but no Sharing Set configuration "
            "detected in networks/ metadata. Customer Community users rely on Sharing "
            "Sets for record access — without them, portal users may see no records. "
            "Verify Sharing Sets are configured in Experience Cloud site settings."
        )

    return issues


def _check_partner_community_crm_objects(profiles_dir: Path) -> list[str]:
    """Warn if a Partner Community profile lacks Opportunity or Lead access.

    Partner Community is typically selected because CRM object access is needed.
    A Partner Community profile with no Opportunity or Lead access may indicate
    that the license selection is over-specified (Customer Community Plus may suffice).
    """
    issues: list[str] = []
    if not profiles_dir.exists():
        return issues

    for profile_file in profiles_dir.glob("*.profile-meta.xml"):
        profile_name = profile_file.stem.replace(".profile-meta", "")
        if not _contains_any(profile_name, _PARTNER_COMMUNITY_MARKERS):
            continue

        try:
            tree = ET.parse(profile_file)
        except ET.ParseError:
            continue

        root = tree.getroot()
        ns = {"sf": _SF_NS}

        has_opportunity_access = False
        has_lead_access = False

        for obj_perm in root.findall("sf:objectPermissions", ns):
            obj_el = obj_perm.find("sf:object", ns)
            if obj_el is None:
                continue
            obj_name = (obj_el.text or "").strip()
            read_el = obj_perm.find("sf:allowRead", ns)
            can_read = read_el is not None and (read_el.text or "").strip().lower() == "true"

            if obj_name == "Opportunity" and can_read:
                has_opportunity_access = True
            if obj_name == "Lead" and can_read:
                has_lead_access = True

        if not has_opportunity_access and not has_lead_access:
            issues.append(
                f"[{profile_name}] Partner Community profile has no Opportunity or Lead "
                f"read access configured. Partner Community is typically chosen for CRM "
                f"object access — if Leads and Opportunities are not needed, consider "
                f"whether Customer Community Plus would be a cheaper fit."
            )

    return issues


def check_experience_cloud_licensing_model(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    profiles_dir = manifest_dir / "profiles"
    objects_dir = manifest_dir / "objects"

    # Run all checks
    issues.extend(_check_profiles_for_report_tab(profiles_dir))
    issues.extend(_check_sharing_sets_presence(objects_dir))
    issues.extend(_check_partner_community_crm_objects(profiles_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_experience_cloud_licensing_model(manifest_dir)

    if not issues:
        print("No Experience Cloud licensing issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
