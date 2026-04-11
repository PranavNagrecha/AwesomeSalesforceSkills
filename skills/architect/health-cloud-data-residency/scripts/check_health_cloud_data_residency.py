#!/usr/bin/env python3
"""Checker script for Health Cloud Data Residency skill.

Validates org metadata and configuration documentation for Health Cloud
data residency compliance requirements. Checks for common gaps including
missing BAA documentation, undocumented transient processing exceptions,
Data Mask configuration completeness, and Hyperforce region documentation.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_health_cloud_data_residency.py [--help]
    python3 check_health_cloud_data_residency.py --manifest-dir path/to/metadata
    python3 check_health_cloud_data_residency.py --manifest-dir . --compliance-doc path/to/compliance.md
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Health Cloud Data Residency configuration and compliance documentation "
            "for common issues: missing BAA references, undocumented transient processing, "
            "Data Mask gaps, and Hyperforce region documentation."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--compliance-doc",
        default=None,
        help=(
            "Path to a compliance documentation file (Markdown or text) to check for "
            "required data residency documentation elements."
        ),
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print informational messages in addition to warnings.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Metadata checks
# ---------------------------------------------------------------------------

def check_data_mask_profiles(manifest_dir: Path, issues: list[str], verbose: bool) -> None:
    """Check Data Mask profile XML files for missing PHI field coverage."""
    # Data Mask profiles are stored as dataMaskConfigs in some metadata deployments.
    # We also look for any *.dataMask-profile.* or similar naming.
    mask_files = list(manifest_dir.rglob("*.dataMaskConfig"))
    mask_files += list(manifest_dir.rglob("*DataMask*.xml"))
    mask_files += list(manifest_dir.rglob("*data_mask*.xml"))

    if not mask_files:
        issues.append(
            "No Data Mask profile files found. Health Cloud orgs must have an explicit "
            "Data Mask profile that covers all PHI fields before sandbox access is granted "
            "to non-BAA-covered personnel. Verify Data Mask profiles exist and are committed "
            "to the repo or documented in the compliance register."
        )
        return

    # Known high-risk Health Cloud PHI fields that must appear in mask profiles.
    required_phi_fields = [
        "MedicalRecordNumber",
        "SocialSecurityNumber",
        "DateOfBirth",
        "DiagnosisCode",
        "MedProcedureCode",
        "PatientName",
        "HomePhone",
        "MobilePhone",
        "PersonEmail",
    ]

    for mask_file in mask_files:
        if verbose:
            print(f"INFO: Checking Data Mask profile: {mask_file}")
        try:
            content = mask_file.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            issues.append(f"Could not read Data Mask profile {mask_file}: {exc}")
            continue

        for field in required_phi_fields:
            if field.lower() not in content.lower():
                issues.append(
                    f"Data Mask profile '{mask_file.name}' does not appear to mask '{field}'. "
                    f"Verify this PHI field is explicitly included in the mask definition, "
                    f"or document why it is absent (e.g., field does not exist in this org)."
                )


def check_permission_sets_for_einstein(manifest_dir: Path, issues: list[str], verbose: bool) -> None:
    """Check permission sets for Einstein AI feature assignments in Health Cloud context."""
    perm_set_dir = manifest_dir / "permissionsets"
    if not perm_set_dir.exists():
        return  # Not all projects have metadata in this layout

    einstein_patterns = [
        re.compile(r"einstein", re.IGNORECASE),
        re.compile(r"EinsteinGPT", re.IGNORECASE),
        re.compile(r"EinsteinCopilot", re.IGNORECASE),
        re.compile(r"HealthCloudIntelligence", re.IGNORECASE),
        re.compile(r"HealthCloudAI", re.IGNORECASE),
    ]

    for ps_file in perm_set_dir.glob("*.permissionset-meta.xml"):
        try:
            content = ps_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for pattern in einstein_patterns:
            if pattern.search(content):
                if verbose:
                    print(
                        f"INFO: Permission set '{ps_file.name}' includes Einstein/HCI feature. "
                        f"Verify BAA addendum is in place for this feature."
                    )
                issues.append(
                    f"Permission set '{ps_file.name}' grants access to an Einstein AI or "
                    f"Health Cloud Intelligence feature. Verify: (1) the applicable BAA addendum "
                    f"is executed, and (2) transient processing exceptions are documented in the "
                    f"compliance register for this feature."
                )
                break  # Report once per permission set


def check_named_credentials_for_mulesoft(manifest_dir: Path, issues: list[str], verbose: bool) -> None:
    """Check for MuleSoft-related named credentials without BAA documentation flag."""
    nc_patterns = [
        re.compile(r"mulesoft", re.IGNORECASE),
        re.compile(r"anypoint", re.IGNORECASE),
        re.compile(r"muleSoft", re.IGNORECASE),
    ]

    named_cred_files = list(manifest_dir.rglob("*.namedCredential-meta.xml"))
    named_cred_files += list(manifest_dir.rglob("*.namedCredential"))

    for nc_file in named_cred_files:
        try:
            content = nc_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for pattern in nc_patterns:
            if pattern.search(content) or pattern.search(nc_file.name):
                issues.append(
                    f"Named credential '{nc_file.name}' appears to reference MuleSoft/Anypoint. "
                    f"MuleSoft requires a separate BAA addendum — verify it is in place before "
                    f"PHI flows through this integration. Also confirm MuleSoft Anypoint Monitoring "
                    f"is configured to suppress PHI from integration logs."
                )
                break


def check_remote_site_settings(manifest_dir: Path, issues: list[str], verbose: bool) -> None:
    """Check remote site settings for connections to non-Salesforce endpoints that may involve PHI."""
    rss_files = list(manifest_dir.rglob("*.remoteSite-meta.xml"))
    rss_files += list(manifest_dir.rglob("*.remoteSite"))

    marketing_cloud_pattern = re.compile(r"exacttarget|marketingcloud|sfmc", re.IGNORECASE)

    for rss_file in rss_files:
        try:
            content = rss_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if marketing_cloud_pattern.search(content) or marketing_cloud_pattern.search(rss_file.name):
            issues.append(
                f"Remote site setting '{rss_file.name}' references Marketing Cloud / ExactTarget. "
                f"Marketing Cloud requires its own BAA addendum. If PHI flows to Marketing Cloud "
                f"(e.g., patient communications), verify the Marketing Cloud BAA is executed and "
                f"that Marketing Cloud is not used to store PHI beyond transient message delivery."
            )


# ---------------------------------------------------------------------------
# Compliance documentation checks
# ---------------------------------------------------------------------------

REQUIRED_COMPLIANCE_KEYWORDS: list[tuple[str, str]] = [
    (
        "hyperforce",
        "Compliance documentation does not mention 'Hyperforce'. Document the Hyperforce region "
        "selected and confirm both the HIPAA BAA and Hyperforce Infrastructure Agreement are in place.",
    ),
    (
        "baa",
        "Compliance documentation does not reference 'BAA' (Business Associate Agreement). "
        "The BAA coverage matrix must be documented, including any features requiring separate addenda.",
    ),
    (
        "transient",
        "Compliance documentation does not mention 'transient' processing. "
        "All transient processing exceptions (Einstein, CRM Analytics, MuleSoft) must be explicitly "
        "documented with customer/DPO sign-off.",
    ),
    (
        "hipaa",
        "Compliance documentation does not mention 'HIPAA'. Confirm HIPAA applicability is addressed "
        "or explicitly scoped out with justification.",
    ),
    (
        "addendum",
        "Compliance documentation does not reference BAA 'addendum'. Features such as Health Cloud "
        "Intelligence, MuleSoft, and Marketing Cloud require separate addenda — these must be listed.",
    ),
]

JURISDICTION_KEYWORDS: dict[str, tuple[str, str]] = {
    "gdpr": (
        "gdpr",
        "Compliance documentation mentions GDPR but does not explicitly address Article 9 "
        "special-category health data obligations. Verify DPIA completion and Article 9(2) legal basis.",
    ),
    "article 9": (
        "article 9",
        "Compliance documentation references GDPR but Article 9 (special-category data) "
        "is not explicitly discussed.",
    ),
    "my health records": (
        "my health records",
        "Compliance documentation mentions Australia's My Health Records Act but does not "
        "address cross-border disclosure restrictions. Hyperforce AU region selection alone "
        "is insufficient — verify cross-border processing exceptions are evaluated.",
    ),
}


def check_compliance_document(compliance_doc: Path, issues: list[str], verbose: bool) -> None:
    """Check a compliance documentation file for required data residency content."""
    if not compliance_doc.exists():
        issues.append(f"Compliance document not found at path: {compliance_doc}")
        return

    try:
        content = compliance_doc.read_text(encoding="utf-8", errors="replace").lower()
    except OSError as exc:
        issues.append(f"Could not read compliance document {compliance_doc}: {exc}")
        return

    if verbose:
        print(f"INFO: Checking compliance document: {compliance_doc}")

    # Check required keywords
    for keyword, message in REQUIRED_COMPLIANCE_KEYWORDS:
        if keyword.lower() not in content:
            issues.append(message)

    # Check jurisdiction-specific keywords (only flag secondary keyword if primary is present)
    if "gdpr" in content and "article 9" not in content:
        issues.append(
            "Compliance document mentions GDPR but does not address Article 9 special-category "
            "health data obligations. Add explicit coverage of: Article 9(2) legal basis, DPIA "
            "requirement, and DPO sign-off."
        )

    if "my health records" in content or "mhr act" in content:
        if "cross-border" not in content and "cross border" not in content:
            issues.append(
                "Compliance document references the My Health Records Act but does not address "
                "the cross-border disclosure restriction. Document how each transient processing "
                "exception is evaluated against the Act's definition of 'disclosure'."
            )

    # Check for explicit region documentation
    region_pattern = re.compile(
        r"(hyperforce\s+(region|eu|us|au|australia|europe|apac)|"
        r"(eu|us|au|australia|europe|apac)\s+hyperforce)",
        re.IGNORECASE,
    )
    if not region_pattern.search(compliance_doc.read_text(encoding="utf-8", errors="replace")):
        issues.append(
            "Compliance document does not explicitly name the Hyperforce region selected. "
            "Document the specific region (e.g., 'EU Hyperforce', 'AU Hyperforce') and the "
            "regulatory basis for that selection."
        )

    # Check for sign-off documentation
    signoff_pattern = re.compile(
        r"(dpo|privacy officer|sign.?off|approved by|reviewed by|accepted by)",
        re.IGNORECASE,
    )
    if not signoff_pattern.search(compliance_doc.read_text(encoding="utf-8", errors="replace")):
        issues.append(
            "Compliance document does not record stakeholder sign-off (DPO, Privacy Officer, or "
            "compliance team approval). Data residency architecture must be formally accepted by "
            "the responsible compliance authority before go-live."
        )


# ---------------------------------------------------------------------------
# General manifest structure checks
# ---------------------------------------------------------------------------

def check_manifest_structure(manifest_dir: Path, issues: list[str], verbose: bool) -> None:
    """Check for known high-risk metadata patterns in the manifest directory."""
    # Check for ContentDocument / ContentNote references in any metadata
    # (indicates file storage is in use — PHI file de-identification needed)
    flow_files = list(manifest_dir.rglob("*.flow-meta.xml"))
    flow_files += list(manifest_dir.rglob("*.flow"))

    content_doc_pattern = re.compile(r"ContentDocument|ContentVersion|ContentNote", re.IGNORECASE)

    flows_with_content = []
    for flow_file in flow_files:
        try:
            content = flow_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if content_doc_pattern.search(content):
            flows_with_content.append(flow_file.name)

    if flows_with_content:
        issues.append(
            f"The following Flow(s) reference ContentDocument/ContentNote objects, suggesting "
            f"file attachments may be processed: {', '.join(flows_with_content[:5])}. "
            f"Ensure Data Mask configuration explicitly handles ContentDocument and ContentNote "
            f"bodies — file content is not masked by default and may contain PHI documents."
        )


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

def check_health_cloud_data_residency(
    manifest_dir: Path,
    compliance_doc: Path | None,
    verbose: bool,
) -> list[str]:
    """Return a list of issue strings found in the manifest directory and compliance docs."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    if verbose:
        print(f"INFO: Scanning manifest directory: {manifest_dir}")

    # Run metadata-level checks
    check_data_mask_profiles(manifest_dir, issues, verbose)
    check_permission_sets_for_einstein(manifest_dir, issues, verbose)
    check_named_credentials_for_mulesoft(manifest_dir, issues, verbose)
    check_remote_site_settings(manifest_dir, issues, verbose)
    check_manifest_structure(manifest_dir, issues, verbose)

    # Run compliance document checks if provided
    if compliance_doc is not None:
        check_compliance_document(compliance_doc, issues, verbose)

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    compliance_doc = Path(args.compliance_doc) if args.compliance_doc else None

    issues = check_health_cloud_data_residency(
        manifest_dir=manifest_dir,
        compliance_doc=compliance_doc,
        verbose=args.verbose,
    )

    if not issues:
        print("No Health Cloud data residency issues found.")
        return 0

    print(f"Found {len(issues)} issue(s):", file=sys.stderr)
    for i, issue in enumerate(issues, 1):
        print(f"\nWARN [{i}]: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
