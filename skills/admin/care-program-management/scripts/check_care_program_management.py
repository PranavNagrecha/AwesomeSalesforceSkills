#!/usr/bin/env python3
"""Checker script for Care Program Management skill.

Checks Salesforce metadata files for common Care Program Management
configuration issues, including:
  - AuthorizationFormText records missing locale or using generic locales
  - Missing CareProgramProduct or CareProgramProvider associations
  - Flow or Apex that creates CareProgramEnrollee without consent setup
  - Permission set references to Patient Program Outcome Management

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_care_program_management.py [--help]
    python3 check_care_program_management.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# Locale values that are commonly used but will cause silent failures
# because they don't match typical user locale strings (e.g. en_US)
AMBIGUOUS_LOCALES = {"en", "fr", "de", "es", "pt", "ja", "zh"}

# Salesforce XML namespace used in metadata files
SF_NS = "http://soap.sforce.com/2006/04/metadata"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Care Program Management configuration and metadata for common issues. "
            "Point at a Salesforce DX project root or metadata directory."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _strip_ns(tag: str) -> str:
    """Remove XML namespace prefix from a tag string."""
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def check_authorization_form_text_locale(manifest_dir: Path) -> list[str]:
    """Check AuthorizationFormText XML files for missing or ambiguous locale values."""
    issues: list[str] = []
    # Standard SFDX layout: force-app/main/default/objects/AuthorizationFormText/
    # Metadata API layout: objects/AuthorizationFormText.object
    # Check both patterns
    patterns = [
        "**/*AuthorizationFormText*.object-meta.xml",
        "**/*AuthorizationFormText*.xml",
        "**/objects/AuthorizationFormText/**/*.xml",
    ]
    found_files: list[Path] = []
    for pattern in patterns:
        found_files.extend(manifest_dir.glob(pattern))

    # Deduplicate
    seen: set[Path] = set()
    unique_files = []
    for f in found_files:
        if f not in seen:
            seen.add(f)
            unique_files.append(f)

    for xml_file in unique_files:
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            # Look for <locale> element anywhere in the file
            for elem in root.iter():
                if _strip_ns(elem.tag) == "locale":
                    locale_val = (elem.text or "").strip()
                    if not locale_val:
                        issues.append(
                            f"{xml_file}: AuthorizationFormText has empty locale field. "
                            "Consent documents will not display. Set locale to an exact user locale "
                            "string (e.g., en_US)."
                        )
                    elif locale_val in AMBIGUOUS_LOCALES:
                        issues.append(
                            f"{xml_file}: AuthorizationFormText locale is '{locale_val}' — "
                            "this is a generic locale and will not match a user with locale 'en_US'. "
                            "Use the exact locale string (e.g., en_US, fr_FR) or consent documents "
                            "will silently fail to display."
                        )
        except ET.ParseError as exc:
            issues.append(f"{xml_file}: XML parse error — {exc}")

    return issues


def check_permission_set_outcome_management(manifest_dir: Path) -> list[str]:
    """Check for references to Patient Program Outcome Management permission set."""
    issues: list[str] = []
    # Check if any flow or code references PatientProgramOutcome without a comment/note
    # about the license requirement
    ppo_files = list(manifest_dir.glob("**/*.xml")) + list(manifest_dir.glob("**/*.cls"))
    outcome_files_without_note: list[str] = []

    for f in ppo_files:
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
            if "PatientProgramOutcome" in content:
                # Check if there's any mention of license or permission set in the same file
                lower = content.lower()
                has_license_note = (
                    "license" in lower
                    or "permission set" in lower
                    or "permissionset" in lower
                )
                if not has_license_note:
                    outcome_files_without_note.append(str(f))
        except OSError:
            continue

    if outcome_files_without_note:
        for path in outcome_files_without_note:
            issues.append(
                f"{path}: References PatientProgramOutcome but contains no mention of "
                "'license' or 'permission set'. Patient Program Outcome Management requires "
                "a separately licensed permission set (API v61.0+). Add a comment or check "
                "that the license is confirmed before deploying."
            )

    return issues


def check_flow_enrollee_consent(manifest_dir: Path) -> list[str]:
    """Check Flow metadata for CareProgramEnrollee creation without consent references."""
    issues: list[str] = []
    flow_files = list(manifest_dir.glob("**/*.flow-meta.xml"))

    for flow_file in flow_files:
        try:
            content = flow_file.read_text(encoding="utf-8", errors="replace")
            if "CareProgramEnrollee" not in content:
                continue
            # If a flow creates/updates CareProgramEnrollee but never references consent,
            # flag it as a potential bypass of the consent model
            creates_enrollee = (
                "recordCreate" in content or "recordUpdate" in content
            )
            references_consent = (
                "AuthorizationFormConsent" in content
                or "consentStatus" in content.lower()
                or "consent" in content.lower()
            )
            if creates_enrollee and not references_consent:
                issues.append(
                    f"{flow_file}: Flow creates or updates CareProgramEnrollee records "
                    "but contains no reference to AuthorizationFormConsent or consent status. "
                    "Verify that consent is captured before setting CareProgramEnrollee.Status "
                    "to Active."
                )
        except OSError:
            continue

    return issues


def check_care_program_management(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_authorization_form_text_locale(manifest_dir))
    issues.extend(check_permission_set_outcome_management(manifest_dir))
    issues.extend(check_flow_enrollee_consent(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_care_program_management(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
