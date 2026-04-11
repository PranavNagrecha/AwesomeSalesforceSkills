#!/usr/bin/env python3
"""Checker script for FHIR Integration Architecture skill.

Validates that a Salesforce metadata directory contains artifacts consistent
with a well-architected FHIR integration. Checks are heuristic and pattern-based;
they surface likely gaps that a human architect should confirm.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_fhir_integration_architecture.py [--help]
    python3 check_fhir_integration_architecture.py --manifest-dir path/to/metadata
    python3 check_fhir_integration_architecture.py --manifest-dir path/to/metadata --strict
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Patterns that indicate FHIR integration artifacts are present
# ---------------------------------------------------------------------------

# Named Credential files (XML) — required for Generic FHIR Client and external callouts
NAMED_CREDENTIAL_PATTERN = re.compile(
    r"<endpoint>https?://[^<]+fhir[^<]*</endpoint>", re.IGNORECASE
)

# Raw HL7 v2 parsing inside Apex — the anti-pattern we detect
HL7_APEX_PARSE_PATTERN = re.compile(
    r"split\(['\"][\|^]['\"]|\bMSH\b|\bPID\b|\bOBR\b|\bOBX\b|\bHL7Parser\b",
    re.IGNORECASE,
)

# FHIR payload blob storage anti-pattern — raw JSON stored in Long Text fields
FHIR_BLOB_FIELD_PATTERN = re.compile(
    r"(FHIR_Payload|FHIRBundle|RawFhir|fhir_json|fhirPayload)__c",
    re.IGNORECASE,
)

# Scheduled Apex that polls FHIR endpoints (poll-instead-of-event anti-pattern)
SCHEDULED_FHIR_CALLOUT_PATTERN = re.compile(
    r"(Schedulable|System\.schedule|ScheduledApex).{0,500}(https?://[^'\"]+fhir|Http\.send)",
    re.IGNORECASE | re.DOTALL,
)

# Platform Events — positive signal that event-driven pattern is in use
PLATFORM_EVENT_PATTERN = re.compile(r"<label>[^<]*(Admission|ADT|Clinical|FHIR)[^<]*</label>", re.IGNORECASE)

# External ID on patient objects — required for idempotent upsert in any FHIR pattern
EXTERNAL_ID_PATTERN = re.compile(r"<externalId>true</externalId>", re.IGNORECASE)

# Named Credential file suffix
NAMED_CREDENTIAL_FILE_PATTERN = re.compile(r"\.namedCredential$", re.IGNORECASE)

# Connected App — required for OAuth to external FHIR endpoints
CONNECTED_APP_FILE_PATTERN = re.compile(r"\.connectedApp$", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_files(root: Path, suffix_pattern: re.Pattern) -> list[Path]:
    """Return all files under root whose name matches suffix_pattern."""
    return [p for p in root.rglob("*") if p.is_file() and suffix_pattern.search(p.name)]


def find_apex_files(root: Path) -> list[Path]:
    """Return all .cls Apex class files under root."""
    return list(root.rglob("*.cls"))


def find_object_files(root: Path) -> list[Path]:
    """Return all .object-meta.xml files under root."""
    return list(root.rglob("*.object-meta.xml"))


def find_field_files(root: Path) -> list[Path]:
    """Return all .field-meta.xml files under root."""
    return list(root.rglob("*.field-meta.xml"))


def find_platform_event_files(root: Path) -> list[Path]:
    """Return files that look like Platform Event definitions."""
    return [p for p in root.rglob("*.object-meta.xml") if "__e" in p.stem.lower() or "event" in p.stem.lower()]


def read_text_safe(path: Path) -> str:
    """Read file content, returning empty string on decode error."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_named_credential_present(manifest_dir: Path) -> list[str]:
    """At least one Named Credential referencing a FHIR endpoint should exist."""
    issues: list[str] = []
    nc_files = find_files(manifest_dir, NAMED_CREDENTIAL_FILE_PATTERN)
    if not nc_files:
        issues.append(
            "No Named Credential files (.namedCredential) found. "
            "FHIR integrations require Named Credentials to authenticate against external FHIR endpoints "
            "without embedding credentials in Apex. Add a Named Credential for each external FHIR server."
        )
        return issues

    fhir_nc_found = any(
        NAMED_CREDENTIAL_PATTERN.search(read_text_safe(f)) for f in nc_files
    )
    if not fhir_nc_found:
        issues.append(
            f"Found {len(nc_files)} Named Credential file(s) but none reference a FHIR endpoint URL. "
            "Ensure the Named Credential endpoint includes the FHIR base URL for each EMR system."
        )
    return issues


def check_no_hl7_apex_parsing(manifest_dir: Path) -> list[str]:
    """Detect raw HL7 v2 parsing inside Apex — an anti-pattern."""
    issues: list[str] = []
    apex_files = find_apex_files(manifest_dir)
    offenders: list[str] = []
    for f in apex_files:
        content = read_text_safe(f)
        if HL7_APEX_PARSE_PATTERN.search(content):
            offenders.append(f.name)
    if offenders:
        issues.append(
            f"Possible HL7 v2 parsing detected in Apex class(es): {', '.join(offenders)}. "
            "Salesforce has no native HL7 v2 parser. Route HL7 v2 feeds through MuleSoft Accelerator "
            "for Healthcare (which includes HL7 v2 listener and DataWeave conversion) before Salesforce. "
            "Never parse raw HL7 pipe-delimited segments in Apex."
        )
    return issues


def check_no_fhir_blob_fields(manifest_dir: Path) -> list[str]:
    """Detect fields that appear to store raw FHIR payloads as blobs."""
    issues: list[str] = []
    field_files = find_field_files(manifest_dir)
    offenders: list[str] = []
    for f in field_files:
        if FHIR_BLOB_FIELD_PATTERN.search(f.stem):
            offenders.append(f.name)
    if offenders:
        issues.append(
            f"Field file(s) with names suggesting raw FHIR payload storage: {', '.join(offenders)}. "
            "Storing raw FHIR bundles in Long Text Area fields breaks SOQL, reports, list views, "
            "Flows, and Health Cloud clinical data model functionality. Transform FHIR resources to "
            "structured Health Cloud object fields at ingestion time."
        )
    return issues


def check_external_id_on_patient_object(manifest_dir: Path) -> list[str]:
    """Check that at least one field is marked as an external ID — required for idempotent FHIR upserts."""
    issues: list[str] = []
    field_files = find_field_files(manifest_dir)
    if not field_files:
        # No field metadata present — cannot check, skip
        return issues

    ext_id_found = any(
        EXTERNAL_ID_PATTERN.search(read_text_safe(f)) for f in field_files
    )
    if not ext_id_found:
        issues.append(
            "No field marked as External ID found in custom field definitions. "
            "FHIR ingestion pipelines require an External ID field (e.g., EMR patient MRN, "
            "encounter ID) on Health Cloud objects to enable idempotent upsert operations. "
            "Without this, replayed events or retried jobs will create duplicate records."
        )
    return issues


def check_no_scheduled_fhir_polling(manifest_dir: Path) -> list[str]:
    """Detect Scheduled Apex that appears to poll FHIR endpoints — a performance anti-pattern for real-time use cases."""
    issues: list[str] = []
    apex_files = find_apex_files(manifest_dir)
    offenders: list[str] = []
    for f in apex_files:
        content = read_text_safe(f)
        if SCHEDULED_FHIR_CALLOUT_PATTERN.search(content):
            offenders.append(f.name)
    if offenders:
        issues.append(
            f"Scheduled Apex with FHIR callout detected in: {', '.join(offenders)}. "
            "Scheduled Apex polling of EMR FHIR endpoints introduces 15+ minute latency under load "
            "and does not meet real-time clinical event requirements (ADT, lab results). "
            "Use MuleSoft event-driven ingestion (Platform Events) for near-real-time clinical events. "
            "Reserve Scheduled Apex for true batch reconciliation scenarios where 60+ minute latency is acceptable."
        )
    return issues


def check_platform_events_present(manifest_dir: Path, strict: bool = False) -> list[str]:
    """Verify Platform Events exist if event-driven pattern is expected."""
    issues: list[str] = []
    # Only flag as a WARN in strict mode — not all FHIR integrations require Platform Events
    if not strict:
        return issues

    pe_files = find_platform_event_files(manifest_dir)
    if not pe_files:
        issues.append(
            "[STRICT] No Platform Event object files found. "
            "Event-driven FHIR ingestion (Pattern 2 — ADT events, clinical notifications) "
            "should use Platform Events to decouple record creation from downstream automation. "
            "If this integration uses only real-time query (Pattern 1) or bulk batch (Pattern 3), "
            "Platform Events may not be required — verify the chosen integration pattern."
        )
    return issues


def check_connected_app_present(manifest_dir: Path) -> list[str]:
    """A Connected App is required for OAuth flows to external FHIR endpoints."""
    issues: list[str] = []
    ca_files = find_files(manifest_dir, CONNECTED_APP_FILE_PATTERN)
    if not ca_files:
        issues.append(
            "No Connected App files (.connectedApp) found. "
            "OAuth 2.0 authentication to external FHIR endpoints (Epic, Cerner, or custom EMR) "
            "typically requires a Connected App in Salesforce. If the Named Credential uses "
            "a protocol other than OAuth, confirm the authentication mechanism is documented."
        )
    return issues


def check_transformation_layer_documented(manifest_dir: Path) -> list[str]:
    """Heuristic: check if there is any Apex or metadata that suggests a transformation layer exists."""
    issues: list[str] = []
    apex_files = find_apex_files(manifest_dir)
    transform_pattern = re.compile(
        r"(transform|mapping|FHIRMapper|FhirMapper|DataWeave|deserialize|JSON\.deserialize)",
        re.IGNORECASE,
    )
    transform_found = any(
        transform_pattern.search(read_text_safe(f)) for f in apex_files
    )
    if apex_files and not transform_found:
        issues.append(
            "No Apex code referencing a FHIR transformation or mapping layer detected. "
            "Every FHIR integration pattern requires a transformation layer that maps FHIR R4 "
            "resource fields to Health Cloud object fields before storage. "
            "Confirm the transformation layer is implemented in MuleSoft (DataWeave) rather than "
            "Salesforce, which is the recommended approach. If transformation is entirely in MuleSoft, "
            "this warning can be disregarded."
        )
    return issues


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def check_fhir_integration_architecture(manifest_dir: Path, strict: bool = False) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_named_credential_present(manifest_dir))
    issues.extend(check_no_hl7_apex_parsing(manifest_dir))
    issues.extend(check_no_fhir_blob_fields(manifest_dir))
    issues.extend(check_external_id_on_patient_object(manifest_dir))
    issues.extend(check_no_scheduled_fhir_polling(manifest_dir))
    issues.extend(check_platform_events_present(manifest_dir, strict=strict))
    issues.extend(check_connected_app_present(manifest_dir))
    issues.extend(check_transformation_layer_documented(manifest_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for FHIR integration architecture issues. "
            "Validates Named Credentials, anti-patterns (HL7 Apex parsing, FHIR blob fields, "
            "scheduled polling), External ID presence, and Connected App configuration."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Enable additional checks (e.g., Platform Event presence) for event-driven integrations.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_fhir_integration_architecture(manifest_dir, strict=args.strict)

    if not issues:
        print("No FHIR integration architecture issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    print(f"\n{len(issues)} issue(s) found. Review the warnings above.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
