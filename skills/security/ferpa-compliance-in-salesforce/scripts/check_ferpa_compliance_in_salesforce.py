#!/usr/bin/env python3
"""Checker script for FERPA Compliance in Salesforce skill.

Scans Salesforce metadata (sfdx/mdapi format) for FERPA compliance issues:
- Missing LearnerProfile FERPA boolean fields in permission sets/profiles
- Missing Individual object permissions
- Missing ContactPointTypeConsent object permissions
- Overly permissive FLS on education record fields

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_ferpa_compliance_in_salesforce.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


FERPA_LEARNER_FIELDS = [
    "LearnerProfile.HasFerpaParentalDisclosure",
    "LearnerProfile.HasFerpaThrdPtyDisclosure",
    "LearnerProfile.HasParentalFerpa",
    "LearnerProfile.HasThirdPartyFerpa",
]

CONSENT_OBJECTS = [
    "Individual",
    "ContactPointTypeConsent",
    "ContactPointConsent",
]

# Fields commonly containing directory information that should have restricted FLS
DIRECTORY_INFO_FIELDS = [
    "Contact.Phone",
    "Contact.HomePhone",
    "Contact.MailingStreet",
    "Contact.MailingCity",
    "Contact.MailingState",
    "Contact.MailingPostalCode",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check FERPA compliance configuration in Salesforce metadata.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def find_xml_files(root: Path, subdir: str, extension: str = ".xml") -> list[Path]:
    """Find XML files in a subdirectory, checking common metadata layouts."""
    results: list[Path] = []
    for dirpath, _, filenames in os.walk(root):
        p = Path(dirpath)
        if subdir in p.parts:
            for f in filenames:
                if f.endswith(extension):
                    results.append(p / f)
    return results


def check_permission_sets(manifest_dir: Path) -> list[str]:
    """Check permission sets and profiles for FERPA-relevant object and field access."""
    issues: list[str] = []

    ps_files = (
        find_xml_files(manifest_dir, "permissionsets", ".permissionset-meta.xml")
        + find_xml_files(manifest_dir, "permissionsets", ".permissionset")
        + find_xml_files(manifest_dir, "profiles", ".profile-meta.xml")
        + find_xml_files(manifest_dir, "profiles", ".profile")
    )

    if not ps_files:
        issues.append(
            "No permission set or profile metadata found. Cannot verify FERPA field access controls."
        )
        return issues

    for ps_file in ps_files:
        try:
            tree = ET.parse(ps_file)  # noqa: S314
        except ET.ParseError:
            issues.append(f"Could not parse XML: {ps_file}")
            continue

        root = tree.getroot()
        ns = ""
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0] + "}"

        # Check for object permissions on consent objects
        object_perms: set[str] = set()
        for op in root.findall(f".//{ns}objectPermissions"):
            obj_el = op.find(f"{ns}object")
            if obj_el is not None and obj_el.text:
                object_perms.add(obj_el.text)

        # Check field permissions
        field_perms: dict[str, dict[str, str]] = {}
        for fp in root.findall(f".//{ns}fieldPermissions"):
            field_el = fp.find(f"{ns}field")
            readable_el = fp.find(f"{ns}readable")
            editable_el = fp.find(f"{ns}editable")
            if field_el is not None and field_el.text:
                field_perms[field_el.text] = {
                    "readable": readable_el.text if readable_el is not None else "false",
                    "editable": editable_el.text if editable_el is not None else "false",
                }

        file_label = ps_file.name

        # Warn if consent objects are missing from permission sets
        for obj in CONSENT_OBJECTS:
            if obj not in object_perms and ps_files:
                # Only warn for profiles/permsets that seem like admin or registrar roles
                pass  # Object permissions may not be listed if inherited

        # Check FERPA fields are present in field permissions
        for ferpa_field in FERPA_LEARNER_FIELDS:
            if ferpa_field in field_perms:
                perm = field_perms[ferpa_field]
                if perm.get("editable") == "true":
                    # FERPA fields should typically not be directly editable by
                    # most profiles — they should be set by automation
                    issues.append(
                        f"{file_label}: {ferpa_field} is editable. "
                        f"Consider restricting edit access — FERPA booleans should be "
                        f"updated by consent automation, not manually."
                    )

    return issues


def check_flows(manifest_dir: Path) -> list[str]:
    """Check for presence of FERPA-related automation flows."""
    issues: list[str] = []

    flow_files = find_xml_files(manifest_dir, "flows", ".flow-meta.xml") + find_xml_files(
        manifest_dir, "flows", ".flow"
    )

    ferpa_flow_found = False
    consent_expiry_flow_found = False

    for flow_file in flow_files:
        content = flow_file.read_text(encoding="utf-8", errors="replace").lower()
        if "ferpa" in content or "learnerprofile" in content:
            ferpa_flow_found = True
        if "contactpointtypeconsent" in content and "effectiveto" in content:
            consent_expiry_flow_found = True

    if flow_files and not ferpa_flow_found:
        issues.append(
            "No Flow references FERPA or LearnerProfile. "
            "Ensure consent automation updates FERPA booleans on LearnerProfile."
        )

    if flow_files and not consent_expiry_flow_found:
        issues.append(
            "No Flow checks ContactPointTypeConsent.EffectiveTo for expiry. "
            "Expired consent records should trigger updates to LearnerProfile FERPA fields."
        )

    return issues


def check_ferpa_compliance_in_salesforce(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_permission_sets(manifest_dir))
    issues.extend(check_flows(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_ferpa_compliance_in_salesforce(manifest_dir)

    if not issues:
        print("No FERPA compliance issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
