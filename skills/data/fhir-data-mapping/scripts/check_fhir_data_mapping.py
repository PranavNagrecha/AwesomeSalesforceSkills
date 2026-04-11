#!/usr/bin/env python3
"""Checker script for FHIR Data Mapping skill.

Validates a Salesforce metadata directory for common FHIR-to-Health-Cloud mapping issues.
Checks include:
  - Whether FHIR R4 Support Settings CustomSetting or Settings metadata is present
  - Whether HealthCondition object metadata exists (proxy for org preference)
  - Whether any CustomField named CodeSet16Id or beyond exists on CodeSetBundle (over-limit)
  - Whether any Apex class writes FHIR patient data directly to Account/Contact fields
  - Whether any ExternalId field exists on clinical objects (required for idempotent upsert)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_fhir_data_mapping.py [--help]
    python3 check_fhir_data_mapping.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_CODESETS = 15

# Field names on Account/Contact that should NOT be set from FHIR Patient data
PROHIBITED_PATIENT_FIELDS = {
    "firstname",
    "lastname",
    "middlename",
    "phone",
    "mobilephone",
    "homephone",
    "billingstreet",
    "billingcity",
    "billingstate",
    "billingpostalcode",
    "billingcountry",
    "mailingstreet",
    "mailingcity",
    "mailingstate",
    "mailingpostalcode",
    "mailingcountry",
}

# Clinical objects that require ExternalId fields for idempotent upsert
CLINICAL_OBJECTS_NEEDING_EXTERNAL_ID = {
    "HealthCondition",
    "CareObservation",
    "CarePlan",
    "PersonName",
}

SF_NAMESPACE_PREFIX = "{http://soap.sforce.com/2006/04/metadata}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def strip_ns(tag: str) -> str:
    """Remove XML namespace prefix from an element tag."""
    return tag.replace(SF_NAMESPACE_PREFIX, "")


def find_files(root: Path, extension: str) -> list[Path]:
    """Recursively find all files with the given extension under root."""
    return [p for p in root.rglob(f"*{extension}") if p.is_file()]


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_fhir_preference_indicator(manifest_dir: Path) -> list[str]:
    """
    Check whether a metadata artifact suggests FHIR-Aligned Clinical Data Model is present.
    Looks for:
      - Any .object-meta.xml file for HealthCondition (only exists when pref is enabled)
      - Any Settings XML that mentions FhirAlignedClinicalDataModel
    """
    issues: list[str] = []

    # Look for HealthCondition object metadata
    hc_objects = list(manifest_dir.rglob("HealthCondition.object-meta.xml"))
    settings_files = find_files(manifest_dir, ".settings")
    settings_xml = find_files(manifest_dir, "HealthCloudSettings.settings-meta.xml")

    fhir_pref_found = bool(hc_objects or settings_xml)

    # Also search inside settings files for the preference key
    for sf in settings_files:
        try:
            content = sf.read_text(encoding="utf-8", errors="replace")
            if "FhirAlignedClinicalDataModel" in content or "fhirAligned" in content.lower():
                fhir_pref_found = True
                break
        except OSError:
            pass

    if not fhir_pref_found:
        issues.append(
            "No metadata found confirming FHIR-Aligned Clinical Data Model org preference is "
            "enabled (no HealthCondition.object-meta.xml found). Verify Setup > FHIR R4 Support "
            "Settings before running any clinical data load."
        )

    return issues


def check_codeset_bundle_field_limit(manifest_dir: Path) -> list[str]:
    """
    Detect any custom field definitions on CodeSetBundle that imply exceeding the 15-coding limit.
    Also detect any Apex or metadata reference to CodeSet16Id or higher.
    """
    issues: list[str] = []

    # Check custom fields on CodeSetBundle
    codeset_field_pattern = re.compile(
        r"CodeSet(\d+)Id", re.IGNORECASE
    )

    # Scan all .object-meta.xml files for CodeSetBundle
    for obj_file in manifest_dir.rglob("CodeSetBundle.object-meta.xml"):
        try:
            content = obj_file.read_text(encoding="utf-8", errors="replace")
            matches = codeset_field_pattern.findall(content)
            over_limit = [int(n) for n in matches if int(n) > MAX_CODESETS]
            if over_limit:
                issues.append(
                    f"CodeSetBundle metadata in {obj_file.name} references CodeSet fields beyond "
                    f"the 15-limit: CodeSet{max(over_limit)}Id found. "
                    "The platform supports CodeSet1Id–CodeSet15Id only."
                )
        except OSError:
            pass

    # Scan all Apex files for references beyond limit
    for apex_file in find_files(manifest_dir, ".cls"):
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
            matches = codeset_field_pattern.findall(content)
            over_limit = [int(n) for n in matches if int(n) > MAX_CODESETS]
            if over_limit:
                issues.append(
                    f"{apex_file.name}: References CodeSet field(s) beyond the 15-coding limit "
                    f"(e.g., CodeSet{max(over_limit)}Id). Truncate to 15 codings in middleware."
                )
        except OSError:
            pass

    return issues


def check_apex_patient_field_writes(manifest_dir: Path) -> list[str]:
    """
    Detect Apex code that sets prohibited Account/Contact fields with FHIR patient data.
    Heuristic: look for assignments to prohibited field names in the same file that
    references 'fhir', 'patient', or 'PersonAccount' context.
    """
    issues: list[str] = []

    field_assign_pattern = re.compile(
        r"\b(?:account|contact|acc|con|a|c)\."
        r"(" + "|".join(PROHIBITED_PATIENT_FIELDS) + r")\s*=",
        re.IGNORECASE,
    )
    fhir_context_pattern = re.compile(
        r"\b(fhir|patient|PersonAccount|personaccount)\b", re.IGNORECASE
    )

    for apex_file in find_files(manifest_dir, ".cls"):
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
            if not fhir_context_pattern.search(content):
                continue  # Not a FHIR-related class, skip
            bad_fields = field_assign_pattern.findall(content)
            if bad_fields:
                unique_fields = sorted(set(f.lower() for f in bad_fields))
                issues.append(
                    f"{apex_file.name}: Appears to write FHIR patient data directly to "
                    f"Account/Contact field(s): {', '.join(unique_fields)}. "
                    "Use PersonName, ContactPointPhone, and ContactPointAddress child records instead."
                )
        except OSError:
            pass

    return issues


def check_clinical_objects_have_external_id(manifest_dir: Path) -> list[str]:
    """
    For each clinical object that requires idempotent upsert, check whether an ExternalId
    custom field exists in the object metadata.
    """
    issues: list[str] = []

    for obj_name in CLINICAL_OBJECTS_NEEDING_EXTERNAL_ID:
        obj_files = list(manifest_dir.rglob(f"{obj_name}.object-meta.xml"))
        if not obj_files:
            continue  # Object not present in this metadata set; skip
        for obj_file in obj_files:
            try:
                content = obj_file.read_text(encoding="utf-8", errors="replace")
                if "<externalId>true</externalId>" not in content:
                    issues.append(
                        f"{obj_name}: No ExternalId field found in {obj_file.name}. "
                        "FHIR data loads must be idempotent — define an ExternalId field "
                        "(e.g., storing the FHIR resource Id) to support safe re-runs."
                    )
            except OSError:
                pass

    return issues


def check_condition_code_required(manifest_dir: Path) -> list[str]:
    """
    Detect Apex that inserts HealthCondition without setting the Code field.
    Simple heuristic: find new HealthCondition() initializations that do not include 'Code'.
    """
    issues: list[str] = []

    hc_insert_pattern = re.compile(
        r"new\s+HealthCondition\s*\(([^)]*)\)", re.IGNORECASE | re.DOTALL
    )

    for apex_file in find_files(manifest_dir, ".cls"):
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
            for match in hc_insert_pattern.finditer(content):
                constructor_body = match.group(1)
                if "code" not in constructor_body.lower():
                    issues.append(
                        f"{apex_file.name}: HealthCondition initialized without a Code field "
                        f"(near: 'new HealthCondition({constructor_body[:60].strip()}...'). "
                        "HealthCondition.Code is required in Health Cloud even though "
                        "FHIR Condition.code is 0..1 optional."
                    )
        except OSError:
            pass

    return issues


def check_careteam_not_on_careplan(manifest_dir: Path) -> list[str]:
    """
    Detect custom fields or custom objects named CareTeam on CarePlan metadata,
    which indicates a practitioner tried to replicate FHIR careTeam as a direct relationship
    rather than using Case Teams.
    """
    issues: list[str] = []

    careteam_field_pattern = re.compile(r"careTeam|care_team", re.IGNORECASE)

    for obj_file in manifest_dir.rglob("CarePlan.object-meta.xml"):
        try:
            content = obj_file.read_text(encoding="utf-8", errors="replace")
            if careteam_field_pattern.search(content):
                issues.append(
                    f"CarePlan object metadata ({obj_file.name}) contains a field or relationship "
                    "referencing 'CareTeam'. FHIR careTeam is implemented via Case Teams on the "
                    "parent Case record, not as a direct field or lookup on CarePlan."
                )
        except OSError:
            pass

    # Also flag any custom object named CareTeam that appears to be on CarePlan
    for obj_file in manifest_dir.rglob("*CareTeam*.object-meta.xml"):
        obj_name = obj_file.stem.replace(".object-meta", "")
        if "CarePlan" in obj_name:
            issues.append(
                f"Custom object '{obj_name}' appears to model FHIR careTeam as a junction on "
                "CarePlan. Use Salesforce Case Teams on the parent Case instead."
            )

    return issues


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def check_fhir_data_mapping(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_fhir_preference_indicator(manifest_dir))
    issues.extend(check_codeset_bundle_field_limit(manifest_dir))
    issues.extend(check_apex_patient_field_writes(manifest_dir))
    issues.extend(check_clinical_objects_have_external_id(manifest_dir))
    issues.extend(check_condition_code_required(manifest_dir))
    issues.extend(check_careteam_not_on_careplan(manifest_dir))

    return issues


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a Salesforce metadata directory for common FHIR-to-Health-Cloud mapping issues.\n\n"
            "Checks performed:\n"
            "  1. FHIR-Aligned Clinical Data Model org preference indicator\n"
            "  2. CodeSetBundle field references beyond the 15-coding limit\n"
            "  3. Apex writing FHIR patient data to Account/Contact fields directly\n"
            "  4. Missing ExternalId fields on clinical objects (idempotency)\n"
            "  5. HealthCondition inserts without a Code field\n"
            "  6. CareTeam modeled as a direct CarePlan field instead of Case Teams\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
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
    issues = check_fhir_data_mapping(manifest_dir)

    if not issues:
        print("No FHIR data mapping issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    print(f"\n{len(issues)} issue(s) found.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
