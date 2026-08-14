#!/usr/bin/env python3
"""Checker script for Health Cloud LWC Components skill.

Checks org metadata for common Health Cloud LWC component issues:
- Apex controller FLS enforcement for clinical objects
- Use of WITH SECURITY_ENFORCED, removed in API 67.0 (Summer '26)
- TimelineObjectDefinition metadata presence
- Custom Account fields used for clinical data (anti-pattern)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_health_cloud_lwc_components.py [--help]
    python3 check_health_cloud_lwc_components.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Health Cloud LWC component code for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


CLINICAL_OBJECTS = [
    "HealthCondition",
    "ClinicalEncounter",
    "PatientMedication",
    "CareObservation",
    "EhrPatientMedication",
    "ClinicalServiceRequest",
]


API_VERSION_RE = re.compile(r"<apiVersion>\s*([0-9]+(?:\.[0-9]+)?)\s*</apiVersion>")

# Read-side idioms that enforce FLS and still compile at every current API
# version. WITH SECURITY_ENFORCED is deliberately absent: it was removed in API
# 67.0, so its presence is never on its own evidence of a secure query. `as user`
# is also absent — it is the DML idiom, and a class that writes `insert x as
# user` has said nothing about whether its SELECT of PHI is enforced.
# Lowercased because Apex and SOQL are case-insensitive.
ENFORCEMENT_IDIOMS = (
    "with user_mode",
    "accesslevel.user_mode",
    "security.stripinaccessible",
    "isaccessible",
)


def read_api_version(cls_file: Path) -> float | None:
    """Return the apiVersion pinned in the class's .cls-meta.xml, or None.

    This value, not the org's release, gates the security idiom: a Summer '26
    org runs a class pinned to 58.0 unchanged, and that class still compiles
    WITH SECURITY_ENFORCED.
    """
    meta_file = cls_file.parent / f"{cls_file.name}-meta.xml"
    if not meta_file.exists():
        return None
    match = API_VERSION_RE.search(meta_file.read_text(encoding="utf-8"))
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def describe_removed_security_clause(
    cls_file: Path, lowered: str, api_version: float | None
) -> str | None:
    """Flag WITH SECURITY_ENFORCED, severity by the class's pinned apiVersion."""
    if "with security_enforced" not in lowered:
        return None

    if api_version is None:
        return (
            f"{cls_file.name}: uses WITH SECURITY_ENFORCED, and no apiVersion could be read "
            f"from {cls_file.name}-meta.xml. The clause was removed in API 67.0 (Summer '26): "
            "a 67.0+ class fails to compile with 'WITH SECURITY_ENFORCED is no longer "
            "supported, use WITH USER_MODE instead'. Confirm the pinned apiVersion, then "
            "migrate to WITH USER_MODE."
        )
    if api_version >= 67.0:
        return (
            f"{cls_file.name}: [P0] uses WITH SECURITY_ENFORCED at apiVersion {api_version:.1f}. "
            "The clause was removed in API 67.0 (Summer '26) — this class does not compile: "
            "'WITH SECURITY_ENFORCED is no longer supported, use WITH USER_MODE instead'. "
            "Replace it with WITH USER_MODE."
        )
    if api_version >= 57.0:
        return (
            f"{cls_file.name}: [P2] uses WITH SECURITY_ENFORCED at apiVersion {api_version:.1f}. "
            "It still compiles below 67.0, but it is the weaker construct: it checks only the "
            "SELECT list, mishandles polymorphic fields, and reports one violation rather than "
            "all. Migrate to WITH USER_MODE, GA since API 57.0."
        )
    return (
        f"{cls_file.name}: [P3] uses WITH SECURITY_ENFORCED at apiVersion {api_version:.1f}, the "
        "idiom available at that version. Prefer raising the class's apiVersion to 57.0+ and "
        "moving to WITH USER_MODE over hardening it in place."
    )


def describe_missing_enforcement(
    cls_file: Path, clinical_obj: str, api_version: float | None
) -> str:
    """Describe a clinical query carrying no enforcement idiom, severity by apiVersion."""
    if api_version is not None and api_version >= 67.0:
        return (
            f"{cls_file.name}: [P3] @AuraEnabled method queries {clinical_obj} with no explicit "
            f"security clause at apiVersion {api_version:.1f}. The query is not unenforced — from "
            "API 67.0 SOQL runs in user mode by default and applies the running user's sharing "
            "rules, FLS, and object permissions with no keyword at all. Add WITH USER_MODE to "
            "state the intent, so the enforcement survives a later edit or apiVersion change."
        )

    if api_version is None:
        context = (
            f"No apiVersion could be read from {cls_file.name}-meta.xml; below API 67.0 SOQL runs "
            "in system mode, so an unenforced query returns PHI the running user may not be "
            "entitled to see."
        )
    else:
        context = (
            f"At apiVersion {api_version:.1f} SOQL runs in system mode, so this returns PHI the "
            "running user may not be entitled to see."
        )
    return (
        f"{cls_file.name}: @AuraEnabled method queries {clinical_obj} without FLS enforcement. "
        f"{context} Add WITH USER_MODE to the SOQL query (API 57.0+; it replaced "
        "WITH SECURITY_ENFORCED, removed in 67.0), or run the result through "
        "Security.stripInaccessible(AccessType.READABLE, records).getRecords()."
    )


def check_apex_fls_enforcement(manifest_dir: Path) -> list[str]:
    """Check Apex classes querying clinical objects for FLS enforcement."""
    issues: list[str] = []
    classes_dir = manifest_dir / "classes"
    if not classes_dir.exists():
        return issues

    for cls_file in sorted(classes_dir.glob("*.cls")):
        content = cls_file.read_text(encoding="utf-8")
        if "@AuraEnabled" not in content:
            continue

        lowered = content.lower()
        api_version = read_api_version(cls_file)

        stale_clause = describe_removed_security_clause(cls_file, lowered, api_version)
        if stale_clause:
            issues.append(stale_clause)
            # That finding is the whole story for this class: below 67.0 the
            # clause does enforce FLS, and at 67.0+ the class does not compile,
            # so a second "add WITH USER_MODE" line is noise either way. The
            # migration is already named in the message.
            continue

        if any(idiom in lowered for idiom in ENFORCEMENT_IDIOMS):
            continue

        for clinical_obj in CLINICAL_OBJECTS:
            if f"from {clinical_obj.lower()}" in lowered:
                issues.append(
                    describe_missing_enforcement(cls_file, clinical_obj, api_version)
                )
                break
    return issues


def check_timeline_object_definitions(manifest_dir: Path) -> list[str]:
    """Check for TimelineObjectDefinition metadata."""
    issues: list[str] = []
    tod_dir = manifest_dir / "timelineObjectDefinitions"
    if not tod_dir.exists():
        issues.append(
            "No timelineObjectDefinitions/ directory found. "
            "If custom objects should appear in the Industries Timeline, "
            "create TimelineObjectDefinition metadata records in Setup."
        )
    return issues


def check_account_clinical_summary_fields(manifest_dir: Path) -> list[str]:
    """Check for custom Account fields that appear to store clinical data."""
    issues: list[str] = []
    objects_dir = manifest_dir / "objects"
    if not objects_dir.exists():
        return issues

    account_fields_dir = objects_dir / "Account" / "fields"
    if not account_fields_dir.exists():
        return issues

    clinical_field_patterns = [
        "condition", "diagnosis", "medication", "encounter", "clinical",
        "lab_result", "a1c", "hba1c", "procedure"
    ]

    for field_file in account_fields_dir.glob("*.field-meta.xml"):
        field_name_lower = field_file.stem.lower()
        for pattern in clinical_field_patterns:
            if pattern in field_name_lower:
                issues.append(
                    f"Account.{field_file.stem}: Custom Account field name suggests clinical data storage. "
                    "Health Cloud clinical UI components (PatientCard, Timeline) query clinical standard objects, "
                    "not Account fields. Custom Account fields are invisible to clinical components. "
                    "Store clinical data on HealthCondition, PatientMedication, etc. instead."
                )
                break
    return issues


def check_health_cloud_lwc_components(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_apex_fls_enforcement(manifest_dir))
    issues.extend(check_timeline_object_definitions(manifest_dir))
    issues.extend(check_account_clinical_summary_fields(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_health_cloud_lwc_components(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
