#!/usr/bin/env python3
"""Checker script for Industries Data Model skill.

Checks org metadata for common Industries data model anti-patterns:
  - InsurancePolicyParticipant linked to Contact instead of Account
  - Communications Cloud Account queries missing RecordType filter
  - Custom objects that duplicate standard Industries objects
  - Health Cloud CarePlan object presence detection
  - InsurancePolicy object presence detection

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_industries_data_model.py [--help]
    python3 check_industries_data_model.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Standard Industries object API names that should not be duplicated by custom objects
STANDARD_INDUSTRIES_OBJECTS = {
    "InsurancePolicy",
    "InsurancePolicyCoverage",
    "InsurancePolicyParticipant",
    "InsurancePolicyAsset",
    "InsurancePolicyTransaction",
    "CarePlan",
    "CareObservation",
    "ClinicalEncounter",
    "HealthCondition",
    "MedicationStatement",
    "ServicePoint",
    "ServiceContract",
    "CustomerOrder",
    "BillingAccount",
    "ServiceAccount",
}

# Custom object names that likely duplicate standard Industries objects
SHADOW_OBJECT_PATTERNS = [
    (re.compile(r"\bPolicy__c\b", re.IGNORECASE), "InsurancePolicy"),
    (re.compile(r"\bCoverage__c\b", re.IGNORECASE), "InsurancePolicyCoverage"),
    (re.compile(r"\bPolicyCoverage__c\b", re.IGNORECASE), "InsurancePolicyCoverage"),
    (re.compile(r"\bPolicyHolder__c\b", re.IGNORECASE), "InsurancePolicyParticipant"),
    (re.compile(r"\bCarePlan__c\b", re.IGNORECASE), "CarePlan"),
    (re.compile(r"\bServicePoint__c\b", re.IGNORECASE), "ServicePoint"),
    (re.compile(r"\bServiceContract__c\b", re.IGNORECASE), "ServiceContract"),
    (re.compile(r"\bBillingAccount__c\b", re.IGNORECASE), "BillingAccount"),
]

# Pattern: InsurancePolicyParticipant with ContactId — anti-pattern
PARTICIPANT_CONTACT_PATTERN = re.compile(
    r"InsurancePolicyParticipant.*ContactId|ContactId.*InsurancePolicyParticipant",
    re.IGNORECASE | re.DOTALL,
)

# Pattern: Account query without RecordType filter — potential Communications Cloud issue
ACCOUNT_NO_RECORDTYPE_SOQL = re.compile(
    r"\bFROM\s+Account\b(?!.*RecordType)",
    re.IGNORECASE,
)

# Pattern: RecordType.Name used instead of RecordType.DeveloperName
RECORDTYPE_NAME_PATTERN = re.compile(
    r"RecordType\.Name\s*[!=]=\s*['\"]",
    re.IGNORECASE,
)

# Pattern: FHIR resource names used as Salesforce object API names
FHIR_RAW_NAMES = [
    (re.compile(r"\bFROM\s+Observation\b", re.IGNORECASE), "CareObservation"),
    (re.compile(r"\bFROM\s+Condition\b", re.IGNORECASE), "HealthCondition"),
    (re.compile(r"\bFROM\s+Encounter\b", re.IGNORECASE), "ClinicalEncounter"),
    (re.compile(r"\bFROM\s+Patient\b", re.IGNORECASE), "Account (Patient)"),
    (re.compile(r"\bFROM\s+MedicationRequest\b", re.IGNORECASE), "MedicationStatement"),
]

# Industries object presence markers — used for informational detection
INSURANCE_POLICY_MARKER = re.compile(r"\bInsurancePolicy\b", re.IGNORECASE)
CAREPLAN_MARKER = re.compile(r"\bCarePlan\b", re.IGNORECASE)
COMMS_RECORDTYPE_NAMES = re.compile(
    r"(Business_Account|Consumer_Account|Billing_Account|Service_Account)",
    re.IGNORECASE,
)


def _read_text_files(manifest_dir: Path, extensions: tuple[str, ...]) -> list[tuple[Path, str]]:
    """Return list of (path, content) for all text files with the given extensions."""
    results: list[tuple[Path, str]] = []
    for ext in extensions:
        for path in manifest_dir.rglob(f"*{ext}"):
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
                results.append((path, content))
            except OSError:
                pass
    return results


def check_participant_contact_linkage(files: list[tuple[Path, str]]) -> list[str]:
    """Detect InsurancePolicyParticipant linked to ContactId — anti-pattern."""
    issues: list[str] = []
    for path, content in files:
        if PARTICIPANT_CONTACT_PATTERN.search(content):
            issues.append(
                f"{path}: InsurancePolicyParticipant appears to reference ContactId. "
                "InsurancePolicyParticipant must link to AccountId, not ContactId."
            )
    return issues


def check_account_recordtype_filtering(files: list[tuple[Path, str]]) -> list[str]:
    """Detect Account queries that may be missing RecordType filtering in Communications Cloud context."""
    issues: list[str] = []
    for path, content in files:
        # Only flag if file contains Communications Cloud context (Comms record type names)
        # and has Account queries without RecordType
        has_comms_context = COMMS_RECORDTYPE_NAMES.search(content)
        account_queries = list(ACCOUNT_NO_RECORDTYPE_SOQL.finditer(content))
        if has_comms_context and account_queries:
            issues.append(
                f"{path}: Account query found without RecordType.DeveloperName filter in a file "
                "that references Communications Cloud account subtypes. "
                "Add WHERE RecordType.DeveloperName = '...' to avoid returning all account types."
            )
        # Separately flag RecordType.Name usage
        if RECORDTYPE_NAME_PATTERN.search(content):
            issues.append(
                f"{path}: RecordType.Name used for filtering. Use RecordType.DeveloperName instead — "
                "Name is admin-editable and can differ between environments."
            )
    return issues


def check_fhir_raw_names(files: list[tuple[Path, str]]) -> list[str]:
    """Detect FHIR resource names used as Salesforce object API names."""
    issues: list[str] = []
    for path, content in files:
        for pattern, correct_name in FHIR_RAW_NAMES:
            if pattern.search(content):
                issues.append(
                    f"{path}: FHIR resource name used as Salesforce object API name. "
                    f"Use Salesforce Health Cloud object name '{correct_name}' instead."
                )
    return issues


def check_shadow_custom_objects(files: list[tuple[Path, str]]) -> list[str]:
    """Detect custom objects that appear to duplicate standard Industries objects."""
    issues: list[str] = []
    # Focus on object metadata files
    object_files = [
        (p, c) for p, c in files
        if p.suffix in (".xml", ".object", ".cls") or "objects" in str(p).lower()
    ]
    for path, content in object_files:
        for pattern, standard_object in SHADOW_OBJECT_PATTERNS:
            if pattern.search(content):
                issues.append(
                    f"{path}: Custom object '{pattern.pattern.strip(chr(92) + 'b')}' may duplicate "
                    f"standard Industries object '{standard_object}'. "
                    "Use the standard Industries object instead of creating a parallel custom object."
                )
    return issues


def detect_industries_objects(files: list[tuple[Path, str]]) -> dict[str, bool]:
    """Return detection flags for key Industries objects in the metadata."""
    has_insurance_policy = False
    has_careplan = False
    has_comms_record_types = False

    for _, content in files:
        if INSURANCE_POLICY_MARKER.search(content):
            has_insurance_policy = True
        if CAREPLAN_MARKER.search(content):
            has_careplan = True
        if COMMS_RECORDTYPE_NAMES.search(content):
            has_comms_record_types = True

    return {
        "insurance_policy": has_insurance_policy,
        "careplan": has_careplan,
        "comms_record_types": has_comms_record_types,
    }


def check_industries_data_model(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Read all relevant file types
    files = _read_text_files(manifest_dir, (".cls", ".xml", ".soql", ".apex", ".object", ".trigger", ".page", ".component"))

    if not files:
        issues.append(
            f"No Salesforce metadata files found in {manifest_dir}. "
            "Provide a directory containing .cls, .xml, .soql, or .object files."
        )
        return issues

    # Run all checks
    issues.extend(check_participant_contact_linkage(files))
    issues.extend(check_account_recordtype_filtering(files))
    issues.extend(check_fhir_raw_names(files))
    issues.extend(check_shadow_custom_objects(files))

    # Detection summary (informational, not issues)
    detected = detect_industries_objects(files)
    detected_clouds: list[str] = []
    if detected["insurance_policy"]:
        detected_clouds.append("Insurance Cloud (InsurancePolicy)")
    if detected["careplan"]:
        detected_clouds.append("Health Cloud (CarePlan)")
    if detected["comms_record_types"]:
        detected_clouds.append("Communications Cloud (Account record types)")

    if detected_clouds:
        print(f"INFO: Industries objects detected — {', '.join(detected_clouds)}")

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Industries Data Model configuration and metadata for common anti-patterns.",
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
    issues = check_industries_data_model(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
