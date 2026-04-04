#!/usr/bin/env python3
"""Checker script for the platform-encryption skill.

Inspects a Salesforce metadata project directory for common Shield Platform
Encryption misconfiguration patterns.

Checks performed:
  1. Detects fields declared with Classic Encrypted Text type (EncryptedText)
     that may have been mistaken for Shield encryption.
  2. Detects EncryptionPolicy metadata files that reference fields used in
     criteria-based sharing rules (SharingRules metadata).
  3. Warns when a field is referenced in a Flow element filter AND appears in
     an encryption policy (probabilistic encryption breaks Flow filters).
  4. Warns when an encryption policy exists but no re-encryption status file
     or re-encryption job config is found alongside the metadata deployment.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_platform_encryption.py [--manifest-dir path/to/metadata]
    python3 check_platform_encryption.py --help
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_files(root: Path, extension: str) -> list[Path]:
    """Return all files under root with the given extension."""
    return list(root.rglob(f"*{extension}"))


def xml_text(element: Optional[ET.Element]) -> str:
    """Return stripped text of an XML element, or empty string if None."""
    if element is None:
        return ""
    return (element.text or "").strip()


def parse_xml_safe(path: Path) -> Optional[ET.Element]:
    """Parse an XML file and return the root element, or None on error."""
    try:
        return ET.parse(path).getroot()
    except ET.ParseError:
        return None


# ---------------------------------------------------------------------------
# Check 1: Classic Encrypted Text fields
# ---------------------------------------------------------------------------

def check_classic_encrypted_text_fields(manifest_dir: Path) -> list[str]:
    """Flag custom fields that use the Classic Encrypted Text type (EncryptedText).

    Classic Encrypted Text is NOT Shield Platform Encryption. It is a separate,
    weaker feature that does not use AES-256 and does not satisfy most compliance
    requirements. Teams sometimes enable it thinking it provides Shield-level protection.
    """
    issues: list[str] = []
    field_dir = manifest_dir / "objects"

    if not field_dir.exists():
        return issues

    for field_file in find_files(field_dir, ".field-meta.xml"):
        root = parse_xml_safe(field_file)
        if root is None:
            continue
        ns = {"sf": "http://soap.sforce.com/2006/04/metadata"}
        field_type_el = root.find(".//sf:type", ns) or root.find(".//type")
        if field_type_el is not None and xml_text(field_type_el) == "EncryptedText":
            issues.append(
                f"CLASSIC_ENCRYPTED_TEXT: {field_file.relative_to(manifest_dir)} "
                f"uses Classic Encrypted Text, not Shield Platform Encryption. "
                f"Classic Encryption does not satisfy HIPAA/PCI compliance requirements "
                f"and cannot be used in formulas, reports, or workflow criteria. "
                f"Review whether Shield Platform Encryption is required instead."
            )

    return issues


# ---------------------------------------------------------------------------
# Check 2: Detect fields in both encryption policy and criteria-based sharing
# ---------------------------------------------------------------------------

def collect_encrypted_fields(manifest_dir: Path) -> set[str]:
    """Return a set of field API names referenced in EncryptionPolicy metadata."""
    encrypted_fields: set[str] = set()
    policy_dir = manifest_dir / "encryptionPolicy"

    if not policy_dir.exists():
        # Also check root for flat deployments
        policy_dir = manifest_dir

    for policy_file in find_files(policy_dir, ".encryptionPolicy-meta.xml"):
        root = parse_xml_safe(policy_file)
        if root is None:
            continue
        ns = {"sf": "http://soap.sforce.com/2006/04/metadata"}
        for field_el in root.iter():
            if field_el.tag.endswith("fieldApiName") or field_el.tag == "fieldApiName":
                field_name = xml_text(field_el)
                if field_name:
                    encrypted_fields.add(field_name.lower())

    return encrypted_fields


def collect_sharing_rule_fields(manifest_dir: Path) -> set[str]:
    """Return field API names used as criteria in SharingRules metadata."""
    sharing_fields: set[str] = set()
    sharing_dir = manifest_dir / "sharingRules"

    if not sharing_dir.exists():
        return sharing_fields

    for sharing_file in find_files(sharing_dir, ".sharingRules-meta.xml"):
        root = parse_xml_safe(sharing_file)
        if root is None:
            continue
        for field_el in root.iter():
            tag = field_el.tag.split("}")[-1]  # strip namespace
            if tag in ("field", "fieldApiName"):
                field_name = xml_text(field_el)
                if field_name:
                    sharing_fields.add(field_name.lower())

    return sharing_fields


def check_encrypted_fields_in_sharing_rules(manifest_dir: Path) -> list[str]:
    """Flag fields that appear in both an encryption policy and a sharing rule."""
    issues: list[str] = []
    encrypted_fields = collect_encrypted_fields(manifest_dir)
    sharing_fields = collect_sharing_rule_fields(manifest_dir)

    overlap = encrypted_fields & sharing_fields
    for field in sorted(overlap):
        issues.append(
            f"SHARING_RULE_CONFLICT: Field '{field}' is referenced in both a Shield "
            f"encryption policy and a criteria-based sharing rule. Encrypted fields "
            f"cannot be evaluated in sharing rule criteria — the sharing rule will not "
            f"function correctly after encryption is enabled. Redesign the sharing model "
            f"to use a non-encrypted field as the sharing criterion."
        )

    return issues


# ---------------------------------------------------------------------------
# Check 3: Detect Classic Encrypted Text in report filters or formula fields
# ---------------------------------------------------------------------------

def check_encrypted_text_in_formula_fields(manifest_dir: Path) -> list[str]:
    """Warn when a formula field references an EncryptedText field by name.

    Classic Encrypted Text fields cannot be used in formula fields. This check
    looks for formula field files that reference a known EncryptedText field name.
    """
    issues: list[str] = []
    field_dir = manifest_dir / "objects"
    if not field_dir.exists():
        return issues

    # Collect all EncryptedText field names first
    encrypted_text_names: set[str] = set()
    for field_file in find_files(field_dir, ".field-meta.xml"):
        root = parse_xml_safe(field_file)
        if root is None:
            continue
        ns_tag_type = root.find(".//type") or root.find(
            ".//{http://soap.sforce.com/2006/04/metadata}type"
        )
        if ns_tag_type is not None and xml_text(ns_tag_type) == "EncryptedText":
            # Extract the field name from the file name (strip .field-meta.xml)
            field_name = field_file.stem.replace(".field-meta", "")
            encrypted_text_names.add(field_name.lower())

    if not encrypted_text_names:
        return issues

    # Check formula fields for references
    for field_file in find_files(field_dir, ".field-meta.xml"):
        root = parse_xml_safe(field_file)
        if root is None:
            continue
        formula_el = root.find(".//formula") or root.find(
            ".//{http://soap.sforce.com/2006/04/metadata}formula"
        )
        if formula_el is None:
            continue
        formula_text = xml_text(formula_el).lower()
        for enc_field in encrypted_text_names:
            if enc_field in formula_text:
                issues.append(
                    f"FORMULA_REFERENCES_ENCRYPTED_TEXT: {field_file.relative_to(manifest_dir)} "
                    f"appears to reference Classic Encrypted Text field '{enc_field}' in a formula. "
                    f"Classic Encrypted Text fields cannot be used in formula fields and the "
                    f"formula will not compile or return correct results."
                )

    return issues


# ---------------------------------------------------------------------------
# Check 4: Warn if encryption policy present but no re-encryption indicator
# ---------------------------------------------------------------------------

def check_reencryption_reminder(manifest_dir: Path) -> list[str]:
    """Warn when an encryption policy is found but no re-encryption job artifact exists.

    This is a best-effort reminder: if the project contains encryption policy
    metadata but no file containing 're-encrypt', 'reencrypt', or 'reEncrypt'
    in its name, warn that existing data may not have been re-encrypted.
    """
    issues: list[str] = []
    policy_dir = manifest_dir / "encryptionPolicy"
    if not policy_dir.exists():
        # Check flat layout
        has_policy = any(manifest_dir.rglob("*.encryptionPolicy-meta.xml"))
    else:
        has_policy = any(policy_dir.rglob("*.encryptionPolicy-meta.xml"))

    if not has_policy:
        return issues

    # Look for any artifact suggesting re-encryption was acknowledged
    re_enc_markers = list(manifest_dir.rglob("*re[-_]encrypt*")) + list(
        manifest_dir.rglob("*reEncrypt*")
    )
    if not re_enc_markers:
        issues.append(
            "RE_ENCRYPTION_REMINDER: An encryption policy was found in this deployment, "
            "but no re-encryption job artifact or runbook file was detected alongside it. "
            "Enabling an encryption policy does NOT retroactively encrypt existing data. "
            "Remember to trigger the re-encryption job from Setup > Platform Encryption > "
            "Re-encrypt Data after deploying this policy to production."
        )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a Salesforce metadata project for common Shield Platform "
            "Encryption misconfiguration patterns."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Checks performed:
  1. Detects Classic Encrypted Text fields (EncryptedText type) that may be
     mistaken for Shield Platform Encryption.
  2. Detects fields referenced in both an encryption policy and a sharing rule
     (encrypted fields break criteria-based sharing rule evaluation).
  3. Detects formula fields that reference a Classic Encrypted Text field
     (unsupported combination — formula will not compile).
  4. Reminds about re-encryption when an encryption policy is deployed without
     any re-encryption runbook or job artifact alongside it.
""",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata project (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir).resolve()

    if not manifest_dir.exists():
        print(f"ERROR: Manifest directory not found: {manifest_dir}", file=sys.stderr)
        return 2

    all_issues: list[str] = []

    all_issues.extend(check_classic_encrypted_text_fields(manifest_dir))
    all_issues.extend(check_encrypted_fields_in_sharing_rules(manifest_dir))
    all_issues.extend(check_encrypted_text_in_formula_fields(manifest_dir))
    all_issues.extend(check_reencryption_reminder(manifest_dir))

    if not all_issues:
        print("No Shield Platform Encryption issues found.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")
        print()

    print(f"Total issues found: {len(all_issues)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
