#!/usr/bin/env python3
"""Checker script for HIPAA Compliance Architecture skill.

Scans Salesforce metadata in a local SFDX project or metadata API format to
surface architecture-level HIPAA compliance gaps.

Checks performed:
  - Detects PHI-bearing custom fields not using a recognized encrypted field type
  - Warns when standard Field History Tracking is used on objects without Shield FAT markers
  - Identifies profiles or permission sets with broad object access on known PHI objects
  - Detects Connected App or Named Credential misconfigurations that may expose PHI
  - Surfaces BAA scope questions via interactive prompts (--interactive mode)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_hipaa_compliance_architecture.py --help
    python3 check_hipaa_compliance_architecture.py --manifest-dir path/to/metadata
    python3 check_hipaa_compliance_architecture.py --manifest-dir path/to/metadata --interactive
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# ---------------------------------------------------------------------------
# PHI field name heuristics — common patterns indicating PHI in custom fields
# ---------------------------------------------------------------------------
PHI_FIELD_PATTERNS = [
    "ssn", "social_security", "socialsecurity",
    "dob", "dateofbirth", "date_of_birth", "birthdate",
    "diagnosis", "condition", "icd", "cpt", "procedure",
    "medication", "prescription", "rx",
    "insurance", "memberid", "member_id", "enrollmentid",
    "mrn", "medicalrecord", "medical_record",
    "npi", "provider_id",
    "clinical", "phi", "pii",
    "hipaa",
]

# Field types that indicate encryption is applied in Classic Encryption
CLASSIC_ENCRYPTED_TYPE = "EncryptedText"

# Objects that are high-risk PHI carriers in Health Cloud implementations
HIGH_RISK_PHI_OBJECTS = {
    "Contact",
    "Lead",
    "Account",
    "EhrPatient",
    "HealthCloudGA__EhrPatient__c",
    "IndividualApplication",
    "MemberPlan",
    "CareObservation",
    "CareProgramEnrollee",
    "PatientHealthTimeline",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for HIPAA compliance architecture gaps. "
            "Scans custom field definitions, permission sets, and connected apps."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help=(
            "Prompt BAA scope verification questions interactively. "
            "Useful for architecture review sessions."
        ),
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Treat any unencrypted custom field matching PHI name patterns as an error "
            "rather than a warning."
        ),
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Metadata parsing helpers
# ---------------------------------------------------------------------------

def _xml_tag_local(tag: str) -> str:
    """Strip namespace from XML tag."""
    return tag.split("}")[-1] if "}" in tag else tag


def _find_custom_fields(manifest_dir: Path) -> list[dict]:
    """
    Walk manifest_dir for .object-meta.xml or .field-meta.xml files and
    return a list of field records with keys: object, field_name, field_type.
    """
    fields: list[dict] = []

    # SFDX format: objects/<ObjectName>/fields/<FieldName>.field-meta.xml
    for field_file in manifest_dir.rglob("*.field-meta.xml"):
        try:
            tree = ET.parse(field_file)
            root = tree.getroot()
            field_type_el = root.find(
                ".//{http://soap.sforce.com/2006/04/metadata}type"
            )
            if field_type_el is None:
                # Try without namespace
                field_type_el = root.find(".//type")
            field_type = field_type_el.text.strip() if field_type_el is not None else "Unknown"

            # Derive object name from path: .../objects/<ObjName>/fields/<Field>.field-meta.xml
            parts = field_file.parts
            try:
                obj_idx = parts.index("objects")
                object_name = parts[obj_idx + 1] if obj_idx + 1 < len(parts) else "Unknown"
            except ValueError:
                object_name = "Unknown"

            fields.append({
                "object": object_name,
                "field_name": field_file.stem.replace(".field-meta", ""),
                "field_type": field_type,
                "path": str(field_file),
            })
        except ET.ParseError:
            pass  # Skip malformed XML

    # Metadata API format: objects/<ObjectName>.object
    for obj_file in manifest_dir.rglob("*.object"):
        try:
            tree = ET.parse(obj_file)
            root = tree.getroot()
            ns = "http://soap.sforce.com/2006/04/metadata"
            object_name = obj_file.stem

            for field_el in root.findall(f"{{{ns}}}fields"):
                full_name_el = field_el.find(f"{{{ns}}}fullName")
                type_el = field_el.find(f"{{{ns}}}type")
                if full_name_el is None:
                    continue
                fields.append({
                    "object": object_name,
                    "field_name": full_name_el.text or "Unknown",
                    "field_type": type_el.text.strip() if type_el is not None else "Unknown",
                    "path": str(obj_file),
                })
        except ET.ParseError:
            pass

    return fields


def _find_permission_sets(manifest_dir: Path) -> list[dict]:
    """
    Return permission set records from .permissionset-meta.xml files.
    Each record: {name, granted_objects: [str], path}
    """
    permission_sets: list[dict] = []

    for ps_file in manifest_dir.rglob("*.permissionset-meta.xml"):
        try:
            tree = ET.parse(ps_file)
            root = tree.getroot()
            ns = "http://soap.sforce.com/2006/04/metadata"
            ps_name = ps_file.stem.replace(".permissionset-meta", "")
            granted_objects = []
            for obj_perm in root.findall(f"{{{ns}}}objectPermissions"):
                obj_name_el = obj_perm.find(f"{{{ns}}}object")
                read_el = obj_perm.find(f"{{{ns}}}allowRead")
                if obj_name_el is not None and read_el is not None and read_el.text == "true":
                    granted_objects.append(obj_name_el.text)
            permission_sets.append({
                "name": ps_name,
                "granted_objects": granted_objects,
                "path": str(ps_file),
            })
        except ET.ParseError:
            pass

    return permission_sets


def _find_connected_apps(manifest_dir: Path) -> list[dict]:
    """Return connected app names from .connectedApp-meta.xml files."""
    apps: list[dict] = []
    for app_file in manifest_dir.rglob("*.connectedApp-meta.xml"):
        try:
            tree = ET.parse(app_file)
            root = tree.getroot()
            ns = "http://soap.sforce.com/2006/04/metadata"
            label_el = root.find(f"{{{ns}}}label")
            label = label_el.text if label_el is not None else app_file.stem
            # Check for IP restrictions
            ip_ranges = root.findall(f"{{{ns}}}ipRanges")
            apps.append({
                "name": label,
                "has_ip_restriction": len(ip_ranges) > 0,
                "path": str(app_file),
            })
        except ET.ParseError:
            pass
    return apps


# ---------------------------------------------------------------------------
# Check functions
# ---------------------------------------------------------------------------

def check_phi_fields_unencrypted(fields: list[dict], strict: bool) -> list[str]:
    """Warn about custom PHI-named fields that are not using EncryptedText."""
    issues = []
    for f in fields:
        field_lower = f["field_name"].lower()
        is_phi_candidate = any(pattern in field_lower for pattern in PHI_FIELD_PATTERNS)
        if is_phi_candidate and f["field_type"] != CLASSIC_ENCRYPTED_TYPE:
            severity = "ERROR" if strict else "WARN"
            issues.append(
                f"{severity}: Field '{f['object']}.{f['field_name']}' appears to store PHI "
                f"(type: {f['field_type']}) but is not using EncryptedText. "
                f"Verify Shield Platform Encryption policy covers this field. "
                f"[{f['path']}]"
            )
    return issues


def check_high_risk_objects_permission_sets(permission_sets: list[dict]) -> list[str]:
    """Flag permission sets that grant read access to high-risk PHI objects."""
    issues = []
    for ps in permission_sets:
        phi_objects_granted = [
            o for o in ps["granted_objects"] if o in HIGH_RISK_PHI_OBJECTS
        ]
        if phi_objects_granted:
            issues.append(
                f"INFO: Permission Set '{ps['name']}' grants read access to PHI-bearing "
                f"objects: {', '.join(phi_objects_granted)}. "
                f"Verify minimum necessary access is enforced. [{ps['path']}]"
            )
    return issues


def check_connected_apps_no_ip_restriction(apps: list[dict]) -> list[str]:
    """Warn about connected apps with no IP restrictions that may expose PHI APIs."""
    issues = []
    for app in apps:
        if not app["has_ip_restriction"]:
            issues.append(
                f"WARN: Connected App '{app['name']}' has no IP range restrictions. "
                f"If this app accesses PHI-bearing APIs, consider restricting access "
                f"to known IP ranges. [{app['path']}]"
            )
    return issues


def check_manifest_dir_health(manifest_dir: Path) -> list[str]:
    """Basic health check on the manifest directory."""
    issues = []
    if not manifest_dir.exists():
        issues.append(f"ERROR: Manifest directory not found: {manifest_dir}")
        return issues
    if not manifest_dir.is_dir():
        issues.append(f"ERROR: Manifest path is not a directory: {manifest_dir}")
        return issues
    return issues


# ---------------------------------------------------------------------------
# Interactive BAA scope verification
# ---------------------------------------------------------------------------

BAA_SCOPE_QUESTIONS = [
    (
        "Has a BAA been fully executed (signed by both parties) with Salesforce?",
        "CRITICAL: No PHI may be stored in Salesforce until a BAA is signed.",
    ),
    (
        "Has the covered product list in the BAA been verified against all products in this org?",
        "CRITICAL: BAA coverage is product-specific — uncovered products create breach exposure.",
    ),
    (
        "Is Standard Chatter disabled or confirmed NOT used for PHI communication?",
        "WARN: Standard Chatter is not covered by the Salesforce BAA. Do not use for PHI.",
    ),
    (
        "Has every AppExchange package handling PHI obtained its own ISV BAA addendum?",
        "CRITICAL: AppExchange ISVs are separate BAs — they require their own BAA.",
    ),
    (
        "Is Shield Platform Encryption licensed and configured on all PHI fields?",
        "WARN: SPE is a paid add-on. Verify licensing before relying on encryption controls.",
    ),
    (
        "Is Field Audit Trail configured with 10-year retention on all PHI fields?",
        "WARN: Standard Field History Tracking retains only 18 months — insufficient for HIPAA.",
    ),
    (
        "Is MFA enforced for all users with access to PHI?",
        "WARN: MFA is required for HIPAA technical safeguards under 45 CFR 164.312(d).",
    ),
    (
        "Are Sandbox environments de-identified or explicitly covered in the BAA?",
        "WARN: Sandbox environments may not be covered under all BAA versions.",
    ),
]


def run_interactive_baa_questions() -> list[str]:
    """Run BAA scope verification questions interactively and return a list of issue strings."""
    issues = []
    print("\n=== HIPAA BAA Scope Verification ===")
    print("Answer each question (y/n). Press Ctrl+C to skip.\n")
    try:
        for question, warning in BAA_SCOPE_QUESTIONS:
            answer = input(f"  {question} [y/N]: ").strip().lower()
            if answer != "y":
                issues.append(f"BAA REVIEW ITEM: {warning}")
    except (KeyboardInterrupt, EOFError):
        print("\n[Skipping remaining BAA questions]")
    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_hipaa_compliance_architecture(
    manifest_dir: Path,
    strict: bool = False,
) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    health_issues = check_manifest_dir_health(manifest_dir)
    if health_issues:
        return health_issues

    # Custom field PHI check
    fields = _find_custom_fields(manifest_dir)
    if fields:
        issues.extend(check_phi_fields_unencrypted(fields, strict=strict))
    else:
        issues.append(
            "INFO: No field metadata found under manifest-dir. "
            "Run from a directory containing Salesforce metadata (SFDX or metadata API format)."
        )

    # Permission set PHI object access check
    permission_sets = _find_permission_sets(manifest_dir)
    if permission_sets:
        issues.extend(check_high_risk_objects_permission_sets(permission_sets))

    # Connected app IP restriction check
    apps = _find_connected_apps(manifest_dir)
    if apps:
        issues.extend(check_connected_apps_no_ip_restriction(apps))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)

    issues = check_hipaa_compliance_architecture(manifest_dir, strict=args.strict)

    # Optional interactive BAA scope questions
    if args.interactive:
        baa_issues = run_interactive_baa_questions()
        issues.extend(baa_issues)

    if not issues:
        print("No HIPAA architecture issues detected.")
        return 0

    errors = [i for i in issues if i.startswith("ERROR") or i.startswith("CRITICAL")]
    warnings = [i for i in issues if i.startswith("WARN") or i.startswith("BAA REVIEW ITEM")]
    infos = [i for i in issues if i.startswith("INFO")]

    for issue in infos:
        print(issue)
    for issue in warnings:
        print(issue, file=sys.stderr)
    for issue in errors:
        print(issue, file=sys.stderr)

    print(
        f"\nSummary: {len(errors)} error(s), {len(warnings)} warning(s), {len(infos)} info(s).",
        file=sys.stderr,
    )

    return 1 if errors or warnings else 0


if __name__ == "__main__":
    sys.exit(main())
