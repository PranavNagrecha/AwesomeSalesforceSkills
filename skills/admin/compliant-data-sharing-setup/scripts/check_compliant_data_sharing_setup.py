#!/usr/bin/env python3
"""Checker script for Compliant Data Sharing Setup skill.

Scans Salesforce metadata files for common CDS configuration issues:
- IndustriesSettings flags enabled without Private/Read-Only OWD
- Missing CDS permission set definitions
- Sharing rules present on CDS-enabled objects (potential ethical-wall leaks)
- Financial Deal CDS enabled without Deal Management flag

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_compliant_data_sharing_setup.py --manifest-dir path/to/metadata
    python3 check_compliant_data_sharing_setup.py  # uses current directory
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# Objects whose OWD must be Private or Read-Only when CDS is enabled
CDS_OBJECT_OWD_MAP = {
    "enableCompliantDataSharingForAccount": "Account",
    "enableCompliantDataSharingForOpportunity": "Opportunity",
    "enableCompliantDataSharingForInteraction": "Interaction",
    "enableCompliantDataSharingForInteractionSummary": "InteractionSummary",
    "enableCompliantDataSharingForFinancialDeal": "FinancialDeal",
}

# OWD values that are incompatible with CDS
INCOMPATIBLE_OWD_VALUES = {"PublicReadWrite", "ControlledByParent"}

# XML namespace used in Salesforce metadata XML
SF_NS = "http://soap.sforce.com/2006/04/metadata"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for Compliant Data Sharing (CDS) "
            "configuration issues in Financial Services Cloud orgs."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def find_xml_files(root: Path, name_pattern: str) -> list[Path]:
    """Return all XML files under root matching a glob name pattern."""
    return list(root.rglob(name_pattern))


def parse_xml_safe(path: Path) -> ET.Element | None:
    """Parse an XML file and return the root element, or None on parse error."""
    try:
        tree = ET.parse(path)
        return tree.getroot()
    except ET.ParseError:
        return None


def ns(tag: str) -> str:
    """Qualify an XML tag with the Salesforce metadata namespace."""
    return f"{{{SF_NS}}}{tag}"


def check_industries_settings(manifest_dir: Path) -> list[str]:
    """Check IndustriesSettings metadata for CDS configuration issues."""
    issues: list[str] = []
    settings_files = find_xml_files(manifest_dir, "IndustriesSettings.settings-meta.xml")
    if not settings_files:
        # No IndustriesSettings file found — cannot validate CDS flags
        return issues

    for settings_file in settings_files:
        root = parse_xml_safe(settings_file)
        if root is None:
            issues.append(
                f"[{settings_file.name}] Could not parse IndustriesSettings XML."
            )
            continue

        enabled_cds_objects: list[str] = []
        deal_mgmt_enabled = False

        for flag_name, object_name in CDS_OBJECT_OWD_MAP.items():
            # Try with namespace first, then without
            flag_el = root.find(f".//{ns(flag_name)}")
            if flag_el is None:
                flag_el = root.find(f".//{flag_name}")
            if flag_el is not None and flag_el.text and flag_el.text.strip().lower() == "true":
                enabled_cds_objects.append(object_name)

        # Check for Deal Management flag
        deal_flag = root.find(f".//{ns('enableDealManagement')}")
        if deal_flag is None:
            deal_flag = root.find(".//enableDealManagement")
        if deal_flag is not None and deal_flag.text and deal_flag.text.strip().lower() == "true":
            deal_mgmt_enabled = True

        # Warn if Financial Deal CDS is enabled but Deal Management is not
        if "FinancialDeal" in enabled_cds_objects and not deal_mgmt_enabled:
            issues.append(
                f"[{settings_file.name}] CDS is enabled for Financial Deal "
                "but Deal Management (enableDealManagement) is not enabled. "
                "Financial Deal CDS has no effect without Deal Management."
            )

        if enabled_cds_objects:
            # Inform which objects have CDS enabled for cross-check with OWD
            issues.append(
                f"[{settings_file.name}] CDS is enabled for: {', '.join(enabled_cds_objects)}. "
                "Verify OWD for each object is Private or Public Read-Only "
                "(see Sharing Settings metadata)."
            )

    return issues


def check_sharing_settings_owd(manifest_dir: Path, cds_enabled_objects: set[str]) -> list[str]:
    """Check SharingRules and SharingSettings for OWD incompatible with CDS."""
    issues: list[str] = []
    if not cds_enabled_objects:
        return issues

    sharing_files = find_xml_files(manifest_dir, "*.sharingRules-meta.xml")
    for sharing_file in sharing_files:
        # Infer object name from filename (e.g., Account.sharingRules-meta.xml)
        object_name = sharing_file.name.split(".")[0]
        if object_name in cds_enabled_objects:
            issues.append(
                f"[{sharing_file.name}] Sharing rules file found for CDS-enabled object "
                f"'{object_name}'. Existing sharing rules run independently of CDS and can "
                "create unintended cross-team access. Audit and remove rules that conflict "
                "with the intended ethical wall."
            )

    return issues


def check_permission_sets(manifest_dir: Path) -> list[str]:
    """Check that CDS Manager and CDS User permission sets are present."""
    issues: list[str] = []
    perm_set_files = find_xml_files(manifest_dir, "*.permissionset-meta.xml")
    perm_set_names = {f.name.split(".")[0].lower() for f in perm_set_files}

    # Check for presence of CDS-related permission sets by heuristic name match
    has_cds_manager = any("cdsmanager" in n or "cds_manager" in n or "configurecds" in n for n in perm_set_names)
    has_cds_user = any("cdsuser" in n or "cds_user" in n or "usecds" in n for n in perm_set_names)

    if not has_cds_manager:
        issues.append(
            "No CDS Manager permission set found in metadata. "
            "A permission set granting 'Configure CDS' is required for CDS administrators. "
            "Expected file pattern: *CDSManager*.permissionset-meta.xml"
        )

    if not has_cds_user:
        issues.append(
            "No CDS User permission set found in metadata. "
            "A permission set granting 'Use CDS' is required for all users who will be "
            "assigned as participants on records. "
            "Expected file pattern: *CDSUser*.permissionset-meta.xml"
        )

    return issues


def check_participant_role_presence(manifest_dir: Path) -> list[str]:
    """Check that at least one ParticipantRole custom metadata or record exists."""
    issues: list[str] = []
    # ParticipantRole records may appear as customMetadata or as data files
    # Check for any participant role related metadata hints
    participant_role_files = list(manifest_dir.rglob("ParticipantRole*.md-meta.xml"))
    participant_role_csv = list(manifest_dir.rglob("ParticipantRole.csv"))

    if not participant_role_files and not participant_role_csv:
        issues.append(
            "No ParticipantRole record definitions found in metadata. "
            "CDS requires at least one Participant Role record defining an access level "
            "(Read or Edit) before participant assignments can be made. "
            "Ensure ParticipantRole records are included in your deployment or created manually in Setup."
        )

    return issues


def check_compliant_data_sharing_setup(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # --- Check 1: IndustriesSettings CDS flags and Deal Management prerequisite ---
    industries_issues = check_industries_settings(manifest_dir)
    issues.extend(industries_issues)

    # Infer which objects have CDS enabled from the issues list (heuristic)
    cds_enabled_objects: set[str] = set()
    for issue in industries_issues:
        for obj in CDS_OBJECT_OWD_MAP.values():
            if obj in issue and "CDS is enabled for" in issue:
                cds_enabled_objects.add(obj)

    # --- Check 2: Sharing rules on CDS-enabled objects ---
    sharing_issues = check_sharing_settings_owd(manifest_dir, cds_enabled_objects)
    issues.extend(sharing_issues)

    # --- Check 3: CDS permission sets present ---
    perm_issues = check_permission_sets(manifest_dir)
    issues.extend(perm_issues)

    # --- Check 4: ParticipantRole records present ---
    role_issues = check_participant_role_presence(manifest_dir)
    issues.extend(role_issues)

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_compliant_data_sharing_setup(manifest_dir)

    if not issues:
        print("No CDS configuration issues found.")
        return 0

    warn_count = 0
    for issue in issues:
        # Informational messages (OWD cross-check reminders) printed as INFO
        if issue.startswith("[") and "Verify OWD" in issue:
            print(f"INFO: {issue}")
        else:
            print(f"WARN: {issue}", file=sys.stderr)
            warn_count += 1

    return 1 if warn_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
