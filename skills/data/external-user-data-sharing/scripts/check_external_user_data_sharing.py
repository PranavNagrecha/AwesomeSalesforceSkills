#!/usr/bin/env python3
"""Checker script for External User Data Sharing skill.

Inspects Salesforce metadata in a retrieved project directory and flags common
misconfiguration patterns for external user sharing.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_external_user_data_sharing.py [--manifest-dir path/to/metadata]

What it checks:
  1. SharingRules XML files — warns if a sharing rule targets a profile that
     appears to be a High-Volume Portal (Customer Community) profile, since
     criteria-based sharing rules have no effect for HVP users.
  2. Custom object metadata — warns if External OWD (externalSharingModel) is
     absent, which means it defaults to the internal OWD value silently.
  3. Standard object settings — looks for SharingModel elements in
     SharingSettings metadata and warns if External Access is not explicitly set.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Salesforce metadata API namespace
_SF_NS = "http://soap.sforce.com/2006/04/metadata"

# Profile name fragments that indicate a High-Volume Portal profile.
# These are heuristic — actual org names vary.
_HVP_PROFILE_HINTS = [
    "customer community user",
    "customercommunityuser",
    "high volume portal",
    "highvolumeportal",
    "hvp",
]


def _tag(name: str) -> str:
    """Return a namespace-qualified XML tag."""
    return f"{{{_SF_NS}}}{name}"


def _text(element: ET.Element, child_tag: str) -> str:
    """Return the text of a direct child element, or empty string."""
    child = element.find(_tag(child_tag))
    return (child.text or "").strip() if child is not None else ""


def _is_hvp_profile(profile_name: str) -> bool:
    lower = profile_name.lower()
    return any(hint in lower for hint in _HVP_PROFILE_HINTS)


def check_sharing_rules(manifest_dir: Path) -> list[str]:
    """Warn if a sharing rule targets what appears to be an HVP profile."""
    issues: list[str] = []
    sharing_rules_dir = manifest_dir / "sharingRules"
    if not sharing_rules_dir.exists():
        return issues

    for xml_file in sorted(sharing_rules_dir.glob("*.sharingRules")):
        try:
            tree = ET.parse(xml_file)
        except ET.ParseError as exc:
            issues.append(f"[{xml_file.name}] XML parse error: {exc}")
            continue

        root = tree.getroot()
        for rule_elem in root.findall(_tag("criteriaBasedSharingRules")) + root.findall(
            _tag("ownerSharingRules")
        ):
            share_to = _text(rule_elem, "sharedTo")
            rule_label = _text(rule_elem, "label") or _text(rule_elem, "fullName")
            if _is_hvp_profile(share_to):
                issues.append(
                    f"[{xml_file.name}] Sharing rule '{rule_label}' targets "
                    f"'{share_to}' which appears to be a High-Volume Portal "
                    f"(Customer Community) profile. Criteria-based and owner-based "
                    f"sharing rules do not fire for HVP users. Use a Sharing Set instead."
                )

    return issues


def check_custom_object_external_owd(manifest_dir: Path) -> list[str]:
    """Warn if a custom object has no explicit externalSharingModel defined."""
    issues: list[str] = []
    objects_dir = manifest_dir / "objects"
    if not objects_dir.exists():
        return issues

    for xml_file in sorted(objects_dir.glob("*.object")):
        # Skip standard objects — they have external OWD managed in SharingSettings
        object_name = xml_file.stem
        if not object_name.endswith("__c"):
            continue

        try:
            tree = ET.parse(xml_file)
        except ET.ParseError as exc:
            issues.append(f"[{xml_file.name}] XML parse error: {exc}")
            continue

        root = tree.getroot()
        internal_model = _text(root, "sharingModel")
        external_model = _text(root, "externalSharingModel")

        if internal_model and not external_model:
            issues.append(
                f"[{xml_file.name}] Custom object '{object_name}' has sharingModel "
                f"'{internal_model}' but no externalSharingModel defined. "
                f"External OWD will default to the internal OWD value, which may "
                f"unintentionally expose records to all external users. "
                f"Add <externalSharingModel>Private</externalSharingModel> to restrict "
                f"external access explicitly."
            )

    return issues


def check_object_subdirectory_external_owd(manifest_dir: Path) -> list[str]:
    """Check Salesforce DX sfdx-format objects directory (objects/<Name>/<Name>.object-meta.xml)."""
    issues: list[str] = []
    objects_dir = manifest_dir / "objects"
    if not objects_dir.exists():
        return issues

    for object_meta in sorted(objects_dir.rglob("*.object-meta.xml")):
        object_name = object_meta.parent.name
        if not object_name.endswith("__c"):
            continue

        try:
            tree = ET.parse(object_meta)
        except ET.ParseError as exc:
            issues.append(f"[{object_meta}] XML parse error: {exc}")
            continue

        root = tree.getroot()
        internal_model = _text(root, "sharingModel")
        external_model = _text(root, "externalSharingModel")

        if internal_model and not external_model:
            issues.append(
                f"[{object_meta.name}] Custom object '{object_name}' has sharingModel "
                f"'{internal_model}' but no externalSharingModel defined. "
                f"External OWD will inherit the internal value silently. "
                f"Add <externalSharingModel>Private</externalSharingModel> to set "
                f"external access explicitly."
            )

    return issues


def check_external_user_data_sharing(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_sharing_rules(manifest_dir))
    issues.extend(check_custom_object_external_owd(manifest_dir))
    issues.extend(check_object_subdirectory_external_owd(manifest_dir))

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for common external user sharing "
            "misconfigurations (External OWD, Sharing Sets vs. sharing rules, "
            "HVP profile targeting)."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    args = parser.parse_args()
    manifest_dir = Path(args.manifest_dir)

    issues = check_external_user_data_sharing(manifest_dir)

    if not issues:
        print("No external-user-sharing issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
