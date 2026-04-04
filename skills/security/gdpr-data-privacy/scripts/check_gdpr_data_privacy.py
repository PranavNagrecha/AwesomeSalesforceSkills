#!/usr/bin/env python3
"""Checker script for GDPR Data Privacy skill.

Scans a Salesforce metadata directory for GDPR data privacy anti-patterns:
  - Apex classes that hard-delete Contact/Lead without anonymization
  - Batch Apex that does not query IndividualId or ShouldForget
  - Apex that sets ShouldForget=true without any erasure logic nearby
  - Flows or triggers that write HasOptedOutOfEmail without ContactPointTypeConsent logic
  - Absence of any Individual-related Apex (possible gap in privacy model)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_gdpr_data_privacy.py [--help]
    python3 check_gdpr_data_privacy.py --manifest-dir path/to/metadata
    python3 check_gdpr_data_privacy.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Hard delete of Contact or Lead without anonymization guard
HARD_DELETE_PATTERN = re.compile(
    r"\bdelete\s+\w*[Cc]ontact|\bdelete\s+\w*[Ll]ead",
    re.MULTILINE,
)

# Anonymization markers — presence of these near a delete suggests the
# practitioner is aware of the concern
ANON_MARKER_PATTERN = re.compile(
    r"ANON|anonymi[sz]|token|ERASED|ShouldForget",
    re.IGNORECASE,
)

# Batch Apex implementing Database.Batchable
BATCH_CLASS_PATTERN = re.compile(
    r"implements\s+Database\.Batchable",
    re.IGNORECASE,
)

# Presence of Individual/privacy model references in batch classes
INDIVIDUAL_REF_PATTERN = re.compile(
    r"IndividualId|ShouldForget|Individual\b",
    re.IGNORECASE,
)

# ShouldForget assignment
SHOULD_FORGET_SET_PATTERN = re.compile(
    r"ShouldForget\s*=\s*true",
    re.IGNORECASE,
)

# Erasure/anonymization logic near ShouldForget
ERASURE_PATTERN = re.compile(
    r"delete|update\s+contact|update\s+lead|anonymi[sz]|ANON|BatchForgot|Database\.Batchable",
    re.IGNORECASE,
)

# ContactPointTypeConsent or ContactPointConsent usage
CONSENT_OBJECT_PATTERN = re.compile(
    r"ContactPointTypeConsent|ContactPointConsent",
    re.IGNORECASE,
)

# HasOptedOutOfEmail direct write
HAS_OPTED_OUT_PATTERN = re.compile(
    r"HasOptedOutOfEmail\s*=",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def apex_files(manifest_dir: Path) -> list[Path]:
    """Return all .cls files under manifest_dir."""
    return list(manifest_dir.rglob("*.cls"))


def flow_files(manifest_dir: Path) -> list[Path]:
    """Return all .flow-meta.xml files under manifest_dir."""
    return list(manifest_dir.rglob("*.flow-meta.xml"))


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def check_hard_delete_without_anonymization(apex_paths: list[Path]) -> list[str]:
    """Flag Apex files that delete Contact/Lead without visible anonymization."""
    issues: list[str] = []
    for path in apex_paths:
        text = read_text(path)
        if HARD_DELETE_PATTERN.search(text):
            if not ANON_MARKER_PATTERN.search(text):
                issues.append(
                    f"[HARD-DELETE] {path.name}: deletes Contact or Lead records but has no "
                    "anonymization markers (ANON, anonymize, ERASED, ShouldForget). "
                    "Verify referential integrity — consider anonymization over hard delete "
                    "for records with FK dependencies (Opportunity, Case, Order)."
                )
    return issues


def check_batch_apex_missing_individual_logic(apex_paths: list[Path]) -> list[str]:
    """Flag Batch Apex classes that do not reference Individual/privacy fields."""
    issues: list[str] = []
    for path in apex_paths:
        text = read_text(path)
        if BATCH_CLASS_PATTERN.search(text):
            # Only warn if the batch touches Contact or Lead
            if HARD_DELETE_PATTERN.search(text) or re.search(
                r"\[SELECT.*FROM\s+(Contact|Lead)\b", text, re.IGNORECASE
            ):
                if not INDIVIDUAL_REF_PATTERN.search(text):
                    issues.append(
                        f"[BATCH-PRIVACY] {path.name}: Batch Apex processes Contact or Lead "
                        "records but has no reference to IndividualId or ShouldForget. "
                        "If this batch is the RTBF implementation, it may be silently "
                        "skipping records that lack Individual linkage."
                    )
    return issues


def check_should_forget_without_erasure(apex_paths: list[Path]) -> list[str]:
    """Flag Apex that sets ShouldForget=true without adjacent erasure/anonymization logic."""
    issues: list[str] = []
    for path in apex_paths:
        text = read_text(path)
        if SHOULD_FORGET_SET_PATTERN.search(text):
            if not ERASURE_PATTERN.search(text):
                issues.append(
                    f"[SHOULD-FORGET-ONLY] {path.name}: sets ShouldForget = true but "
                    "contains no erasure or anonymization logic. ShouldForget is a flag only — "
                    "it does not trigger automatic deletion or anonymization. "
                    "Pair this with a Batch Apex erasure job or a Privacy Center policy."
                )
    return issues


def check_opted_out_without_consent_objects(apex_paths: list[Path]) -> list[str]:
    """Flag Apex that writes HasOptedOutOfEmail without using consent objects."""
    issues: list[str] = []
    for path in apex_paths:
        text = read_text(path)
        if HAS_OPTED_OUT_PATTERN.search(text):
            if not CONSENT_OBJECT_PATTERN.search(text):
                issues.append(
                    f"[CONSENT-MODEL] {path.name}: writes HasOptedOutOfEmail but does not "
                    "reference ContactPointTypeConsent or ContactPointConsent. "
                    "HasOptedOutOfEmail is an email suppression flag, not a GDPR consent record. "
                    "For GDPR compliance, capture consent in ContactPointTypeConsent with "
                    "EffectiveFrom, CaptureDate, and CaptureSource populated."
                )
    return issues


def check_individual_model_absent(apex_paths: list[Path]) -> list[str]:
    """Warn if no Apex file in the project references Individual or consent objects at all."""
    issues: list[str] = []
    all_text = "\n".join(read_text(p) for p in apex_paths)
    has_individual = INDIVIDUAL_REF_PATTERN.search(all_text)
    has_consent = CONSENT_OBJECT_PATTERN.search(all_text)
    if apex_paths and not has_individual and not has_consent:
        issues.append(
            "[MISSING-PRIVACY-MODEL] No Apex class references IndividualId, ShouldForget, "
            "ContactPointTypeConsent, or ContactPointConsent. "
            "If this org processes personal data for EU/EEA residents, verify that the "
            "Individual privacy data model has been implemented. "
            "These objects are available from API v42.0 (Winter '18)."
        )
    return issues


def check_flow_opted_out_without_consent(flow_paths: list[Path]) -> list[str]:
    """Flag flows that reference HasOptedOutOfEmail without consent object references."""
    issues: list[str] = []
    for path in flow_paths:
        text = read_text(path)
        if "HasOptedOutOfEmail" in text:
            if "ContactPointTypeConsent" not in text and "ContactPointConsent" not in text:
                issues.append(
                    f"[FLOW-CONSENT-MODEL] {path.name}: references HasOptedOutOfEmail but "
                    "not ContactPointTypeConsent or ContactPointConsent. "
                    "For GDPR-compliant consent tracking, update the flow to also create or "
                    "update a ContactPointTypeConsent record with OptInStatus, EffectiveFrom, "
                    "and CaptureDate."
                )
    return issues


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def check_gdpr_data_privacy(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    apex = apex_files(manifest_dir)
    flows = flow_files(manifest_dir)

    if not apex and not flows:
        issues.append(
            f"No Apex (.cls) or Flow (.flow-meta.xml) files found under {manifest_dir}. "
            "Ensure --manifest-dir points to the root of your Salesforce metadata "
            "(e.g., force-app/main/default)."
        )
        return issues

    issues.extend(check_hard_delete_without_anonymization(apex))
    issues.extend(check_batch_apex_missing_individual_logic(apex))
    issues.extend(check_should_forget_without_erasure(apex))
    issues.extend(check_opted_out_without_consent_objects(apex))
    issues.extend(check_individual_model_absent(apex))
    issues.extend(check_flow_opted_out_without_consent(flows))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for GDPR data privacy anti-patterns: "
            "hard deletes, missing Individual linkage, ShouldForget-only erasure, "
            "and consent model gaps."
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
    issues = check_gdpr_data_privacy(manifest_dir)

    if not issues:
        print("No GDPR data privacy issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")
        print()

    return 1


if __name__ == "__main__":
    sys.exit(main())
