#!/usr/bin/env python3
"""Checker script for Marketing Consent Architecture skill.

Checks Salesforce metadata and configuration files for common consent architecture
issues: missing Individual object usage, ContactPointTypeConsent without DataUsePurpose,
consent stored only in custom fields, and MC Consent Management integration gaps.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_marketing_consent_architecture.py [--help]
    python3 check_marketing_consent_architecture.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for Marketing Consent Architecture issues. "
            "Detects missing Individual object references, consent stored in custom fields, "
            "and missing DataUsePurpose on consent records."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _find_xml_files(root: Path, suffix: str) -> list[Path]:
    """Recursively find metadata XML files with the given suffix."""
    return list(root.rglob(f"*.{suffix}"))


def check_custom_consent_fields(manifest_dir: Path) -> list[str]:
    """Warn if custom fields on Contact or Lead are used for consent instead of platform objects."""
    issues: list[str] = []
    consent_keywords = ["optout", "optedout", "optin", "opted_in", "consent", "unsubscribe", "gdpr", "ccpa"]

    field_files = _find_xml_files(manifest_dir, "field-meta.xml")
    for field_file in field_files:
        fname = field_file.stem.lower().replace("-meta", "")
        # Check if field name contains consent-related keywords
        if any(kw in fname for kw in consent_keywords):
            # Only flag fields on Contact or Lead objects (path heuristic)
            parts = [p.lower() for p in field_file.parts]
            if "contact" in parts or "lead" in parts:
                issues.append(
                    f"Custom consent field detected on Contact/Lead: {field_file} — "
                    "consider using ContactPointTypeConsent and Individual objects instead of "
                    "custom fields for GDPR/CCPA-compliant consent tracking."
                )

    return issues


def check_flow_consent_patterns(manifest_dir: Path) -> list[str]:
    """Check Flow metadata for consent anti-patterns."""
    issues: list[str] = []

    flow_files = _find_xml_files(manifest_dir, "flow-meta.xml")
    for flow_file in flow_files:
        try:
            tree = ET.parse(flow_file)
            root = tree.getroot()
            content = flow_file.read_text(encoding="utf-8")
        except Exception:
            continue

        # Check for HasOptedOutOfEmail usage without ContactPointTypeConsent
        uses_opted_out = "HasOptedOutOfEmail" in content
        uses_cptc = "ContactPointTypeConsent" in content
        uses_individual = "Individual" in content

        if uses_opted_out and not uses_cptc:
            issues.append(
                f"Flow {flow_file.name} references HasOptedOutOfEmail but not ContactPointTypeConsent. "
                "For GDPR/CCPA compliance, use ContactPointTypeConsent with DataUsePurpose for "
                "per-purpose consent management rather than the coarse-grained HasOptedOutOfEmail boolean."
            )

        # Check for ContactPointTypeConsent insert/update without DataUsePurpose
        if uses_cptc and "DataUsePurpose" not in content:
            issues.append(
                f"Flow {flow_file.name} references ContactPointTypeConsent but does not reference "
                "DataUsePurpose. ContactPointTypeConsent records should include a DataUsePurposeId "
                "for MC Consent Management integration to function correctly at send time."
            )

    return issues


def check_apex_consent_patterns(manifest_dir: Path) -> list[str]:
    """Check Apex classes for consent anti-patterns."""
    issues: list[str] = []

    apex_files = list(manifest_dir.rglob("*.cls"))
    for apex_file in apex_files:
        try:
            content = apex_file.read_text(encoding="utf-8")
        except Exception:
            continue

        uses_cptc = "ContactPointTypeConsent" in content
        uses_individual = "Individual" in content or "IndividualId" in content
        uses_opted_out = "HasOptedOutOfEmail" in content

        # Flag ContactPointTypeConsent inserts that might be missing IndividualId
        if uses_cptc and "IndividualId" not in content:
            issues.append(
                f"Apex class {apex_file.name} references ContactPointTypeConsent but does not "
                "reference IndividualId. ContactPointTypeConsent.IndividualId must be set to the "
                "Individual record Id, NOT the Contact record Id."
            )

        # Flag ContactPointTypeConsent without DataUsePurpose
        if uses_cptc and "DataUsePurpose" not in content:
            issues.append(
                f"Apex class {apex_file.name} creates or queries ContactPointTypeConsent without "
                "DataUsePurpose. Missing DataUsePurpose prevents MC Consent Management from "
                "performing purpose-scoped suppression at send time."
            )

        # Flag legacy opt-out field usage without platform consent objects
        if uses_opted_out and not uses_cptc and not uses_individual:
            issues.append(
                f"Apex class {apex_file.name} uses HasOptedOutOfEmail without ContactPointTypeConsent "
                "or Individual. This is a legacy consent pattern — evaluate whether platform consent "
                "objects should be used for GDPR/CCPA compliance."
            )

    return issues


def check_permission_sets(manifest_dir: Path) -> list[str]:
    """Warn if consent objects are not included in any permission set."""
    issues: list[str] = []
    consent_objects = {"Individual", "ContactPointTypeConsent", "ContactPointConsent", "DataUsePurpose"}

    perm_files = _find_xml_files(manifest_dir, "permissionset-meta.xml")
    if not perm_files:
        return issues

    objects_granted: set[str] = set()
    for perm_file in perm_files:
        try:
            content = perm_file.read_text(encoding="utf-8")
        except Exception:
            continue
        for obj in consent_objects:
            if obj in content:
                objects_granted.add(obj)

    missing = consent_objects - objects_granted
    if missing:
        issues.append(
            f"Consent data model objects not found in any permission set: {sorted(missing)}. "
            "Ensure profiles and permission sets grant access to Individual, ContactPointTypeConsent, "
            "ContactPointConsent, and DataUsePurpose so consent records can be created and queried."
        )

    return issues


def check_marketing_consent_architecture(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_custom_consent_fields(manifest_dir))
    issues.extend(check_flow_consent_patterns(manifest_dir))
    issues.extend(check_apex_consent_patterns(manifest_dir))
    issues.extend(check_permission_sets(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_marketing_consent_architecture(manifest_dir)

    if not issues:
        print("No consent architecture issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    print(f"\n{len(issues)} issue(s) found.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
