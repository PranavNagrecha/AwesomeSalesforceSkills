#!/usr/bin/env python3
"""Checker script for FSC Referral Management skill.

Validates Salesforce metadata relevant to FSC Referral Management:
- ReferralRecordTypeMapping__mdt entries (checks for active entries and required fields)
- Lead object custom fields (checks for the 11 FSC referral fields)
- Lead Assignment Rules (detects missing or empty rule files)
- References to Einstein Referral Scoring (retiring feature — flag any usage)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_fsc_referral_management.py [--help]
    python3 check_fsc_referral_management.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# The 11 FSC Referral Management custom fields expected on the Lead object.
FSC_REFERRAL_LEAD_FIELDS = {
    "ExpressedInterest__c",
    "ReferredBy__c",
    "ReferrerScore__c",
    "ReferralType__c",
    "ReferralDate__c",
    "ReferralStatus__c",
    "ReferralChannel__c",
    "ReferralSource__c",
    "ReferralNotes__c",
    "ReferralOutcome__c",
    "ReferralPriority__c",
}

# Einstein Referral Scoring is a retiring feature — flag any references.
RETIRING_FEATURE_PATTERNS = [
    "EinsteinReferralScoring",
    "Einstein_Referral_Scoring",
    "einsteinReferralScoring",
    "einstein_referral_scoring",
    "enableEinsteinReferralScoring",
]

SF_NAMESPACE = "http://soap.sforce.com/2006/04/metadata"


def _strip_ns(tag: str) -> str:
    """Remove XML namespace from a tag string."""
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def check_referral_record_type_mappings(manifest_dir: Path) -> list[str]:
    """Check ReferralRecordTypeMapping__mdt files for required structure."""
    issues: list[str] = []

    # Custom metadata files live under customMetadata/
    metadata_dir = manifest_dir / "customMetadata"
    if not metadata_dir.exists():
        # Try force-app style paths
        for candidate in manifest_dir.rglob("customMetadata"):
            if candidate.is_dir():
                metadata_dir = candidate
                break
        else:
            return issues  # No customMetadata dir found — skip check

    mapping_files = list(metadata_dir.glob("ReferralRecordTypeMapping.*.md-meta.xml"))
    if not mapping_files:
        issues.append(
            "No ReferralRecordTypeMapping__mdt files found under customMetadata/. "
            "Every referral type requires an active entry or routing will silently fail."
        )
        return issues

    for mf in mapping_files:
        try:
            tree = ET.parse(mf)
        except ET.ParseError as exc:
            issues.append(f"ReferralRecordTypeMapping file is not valid XML: {mf} — {exc}")
            continue

        root = tree.getroot()
        values: dict[str, str] = {}
        for val_elem in root.findall(f".//{{{SF_NAMESPACE}}}values"):
            field_elem = val_elem.find(f"{{{SF_NAMESPACE}}}field")
            value_elem = val_elem.find(f"{{{SF_NAMESPACE}}}value")
            if field_elem is not None and value_elem is not None:
                values[field_elem.text or ""] = value_elem.text or ""

        # Check IsActive__c
        is_active = values.get("IsActive__c", "").lower()
        if is_active == "false":
            issues.append(
                f"ReferralRecordTypeMapping entry is inactive: {mf.name}. "
                "Inactive entries will not register the referral type for routing."
            )

        # Check LeadRecordTypeDeveloperName__c is present and non-empty
        record_type_name = values.get("LeadRecordTypeDeveloperName__c", "").strip()
        if not record_type_name:
            issues.append(
                f"ReferralRecordTypeMapping entry is missing LeadRecordTypeDeveloperName__c: {mf.name}. "
                "This field must match the Lead record type developer name exactly."
            )

    return issues


def check_lead_referral_fields(manifest_dir: Path) -> list[str]:
    """Check that FSC referral custom fields exist on the Lead object."""
    issues: list[str] = []

    # Lead field files: objects/Lead/fields/*.field-meta.xml (source format)
    # or objectTranslations / object XML in metadata format
    lead_fields_dir: Path | None = None
    for candidate in manifest_dir.rglob("Lead/fields"):
        if candidate.is_dir():
            lead_fields_dir = candidate
            break

    if lead_fields_dir is None:
        # No Lead/fields directory found — check for Lead.object-meta.xml (metadata format)
        lead_object_files = list(manifest_dir.rglob("Lead.object-meta.xml"))
        if not lead_object_files:
            # No Lead metadata found at all — cannot validate fields
            return issues
        # Parse the object XML for field names
        found_field_names: set[str] = set()
        for lead_file in lead_object_files:
            try:
                tree = ET.parse(lead_file)
            except ET.ParseError:
                continue
            for field_elem in tree.findall(f".//{{{SF_NAMESPACE}}}fields"):
                fn = field_elem.find(f"{{{SF_NAMESPACE}}}fullName")
                if fn is not None and fn.text:
                    found_field_names.add(fn.text)
        missing = FSC_REFERRAL_LEAD_FIELDS - found_field_names
        for f in sorted(missing):
            issues.append(
                f"Expected FSC Referral Management Lead field not found in Lead.object-meta.xml: {f}"
            )
        return issues

    found_field_names = {f.stem.replace(".field-meta", "") for f in lead_fields_dir.glob("*.field-meta.xml")}
    missing = FSC_REFERRAL_LEAD_FIELDS - found_field_names
    for f in sorted(missing):
        issues.append(
            f"Expected FSC Referral Management Lead field file not found: Lead/fields/{f}.field-meta.xml"
        )

    return issues


def check_lead_assignment_rules(manifest_dir: Path) -> list[str]:
    """Check Lead Assignment Rules for routing entries."""
    issues: list[str] = []

    rule_files = list(manifest_dir.rglob("Lead.assignmentRules-meta.xml"))
    if not rule_files:
        issues.append(
            "No Lead.assignmentRules-meta.xml found. "
            "FSC Referral routing requires Lead Assignment Rules keyed on Expressed Interest values."
        )
        return issues

    for rf in rule_files:
        try:
            tree = ET.parse(rf)
        except ET.ParseError as exc:
            issues.append(f"Lead assignment rules file is not valid XML: {rf} — {exc}")
            continue

        root = tree.getroot()
        rule_entries = root.findall(f".//{{{SF_NAMESPACE}}}ruleEntry") + root.findall(".//ruleEntry")
        if not rule_entries:
            issues.append(
                f"Lead Assignment Rules file exists but contains no rule entries: {rf}. "
                "At least one rule entry keyed on Expressed Interest is required per referral type."
            )
            continue

        # Check if any entry references ExpressedInterest__c
        expressed_interest_entries = 0
        for entry in rule_entries:
            for criteria in entry.iter():
                tag = _strip_ns(criteria.tag)
                if tag == "field" and criteria.text and "ExpressedInterest" in criteria.text:
                    expressed_interest_entries += 1

        if expressed_interest_entries == 0:
            issues.append(
                f"Lead Assignment Rules contain no entries filtering on ExpressedInterest__c: {rf}. "
                "FSC referral routing uses Expressed Interest as the primary routing key."
            )

    return issues


def check_retiring_feature_references(manifest_dir: Path) -> list[str]:
    """Flag any XML metadata referencing the retiring Einstein Referral Scoring feature."""
    issues: list[str] = []

    for xml_file in manifest_dir.rglob("*.xml"):
        try:
            content = xml_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for pattern in RETIRING_FEATURE_PATTERNS:
            if pattern in content:
                issues.append(
                    f"Reference to retiring Einstein Referral Scoring feature found in: {xml_file}. "
                    f"Pattern matched: '{pattern}'. Use Intelligent Need-Based Referrals instead."
                )
                break  # One issue per file is enough

    return issues


def check_fsc_referral_management(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_referral_record_type_mappings(manifest_dir))
    issues.extend(check_lead_referral_fields(manifest_dir))
    issues.extend(check_lead_assignment_rules(manifest_dir))
    issues.extend(check_retiring_feature_references(manifest_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check FSC Referral Management configuration and metadata for common issues. "
            "Validates ReferralRecordTypeMapping__mdt entries, Lead referral fields, "
            "Lead Assignment Rules, and flags retiring Einstein Referral Scoring references."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_fsc_referral_management(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
