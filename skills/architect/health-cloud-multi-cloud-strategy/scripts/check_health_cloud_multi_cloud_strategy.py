#!/usr/bin/env python3
"""Checker script for Health Cloud Multi-Cloud Strategy skill.

Validates a Salesforce metadata project directory for common Health Cloud
multi-cloud configuration issues:

- Experience Cloud for Health Cloud PSL documented in permissionsets/
- OmniStudio three-PSL stack (HealthCloud + HealthCloudPlatform + OmniStudio)
- Marketing Cloud HIPAA BAA note in named credentials or integration config
- PersonAccount enabled (checks for PersonAccount-related metadata markers)
- No duplicate Service Cloud PSL assigned alongside Health Cloud for internal profiles

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_health_cloud_multi_cloud_strategy.py [--manifest-dir path/to/metadata]
    python3 check_health_cloud_multi_cloud_strategy.py --help
"""

from __future__ import annotations

import argparse
import sys
import re
from pathlib import Path


# ---------------------------------------------------------------------------
# PSL names we look for in permission set XML metadata
# ---------------------------------------------------------------------------
REQUIRED_OMNI_PSLS = {
    "HealthCloudPsl",
    "HealthCloudPlatformPsl",
    "OmniStudioUser",
}

EXPERIENCE_CLOUD_HEALTH_PSL = "HealthCloudForExperienceCloud"

MARKETING_CLOUD_CONNECTED_APP_KEYWORDS = [
    "marketingcloud",
    "marketing_cloud",
    "exacttarget",
    "sfmc",
]

HIPAA_BAA_KEYWORDS = [
    "hipaa",
    "baa",
    "business associate",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Health Cloud Multi-Cloud Strategy configuration and metadata "
            "for common licensing, PSL, and compliance issues."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata project (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def find_files(root: Path, pattern: str) -> list[Path]:
    """Return all files matching a glob pattern under root."""
    return list(root.rglob(pattern))


def file_contains_any(path: Path, keywords: list[str], case_insensitive: bool = True) -> bool:
    """Return True if the file contains any of the given keywords."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        if case_insensitive:
            text = text.lower()
            keywords = [k.lower() for k in keywords]
        return any(k in text for k in keywords)
    except OSError:
        return False


def extract_psl_names_from_xml(path: Path) -> set[str]:
    """Extract permissionSetLicense developer names from a permission set XML file.

    Looks for patterns like:
      <permissionSetLicenses>
          <permissionSetLicenseDeveloperName>HealthCloudPsl</permissionSetLicenseDeveloperName>
      </permissionSetLicenses>
    """
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return set()

    pattern = re.compile(
        r"<permissionSetLicenseDeveloperName>(.*?)</permissionSetLicenseDeveloperName>",
        re.IGNORECASE | re.DOTALL,
    )
    return {m.group(1).strip() for m in pattern.finditer(text)}


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_experience_cloud_psl_documented(manifest_dir: Path) -> list[str]:
    """Check that at least one permission set XML references the Experience Cloud for Health PSL."""
    issues: list[str] = []
    perm_set_files = find_files(manifest_dir, "*.permissionset-meta.xml")
    if not perm_set_files:
        # No permission set files to check — not an error for this script
        return issues

    found = any(
        EXPERIENCE_CLOUD_HEALTH_PSL.lower() in f.read_text(encoding="utf-8", errors="replace").lower()
        for f in perm_set_files
    )
    if not found:
        issues.append(
            f"No permission set XML references the '{EXPERIENCE_CLOUD_HEALTH_PSL}' PSL. "
            "If an Experience Cloud patient portal is in scope, this PSL must be assigned "
            "to portal user profiles. Add it to the relevant permission set metadata and "
            "confirm the Experience Cloud for Health Cloud add-on SKU is on the order form."
        )
    return issues


def check_omni_psl_stack(manifest_dir: Path) -> list[str]:
    """Check that if OmniStudio PSL is referenced, all three Health Cloud OmniStudio PSLs are present."""
    issues: list[str] = []
    perm_set_files = find_files(manifest_dir, "*.permissionset-meta.xml")
    if not perm_set_files:
        return issues

    # Collect all PSL names across all permission set files
    all_psls: set[str] = set()
    for f in perm_set_files:
        all_psls.update(extract_psl_names_from_xml(f))

    # If OmniStudio PSL appears, check the full stack
    omni_referenced = any(
        psl.lower() == "omnistudiouser" for psl in all_psls
    )
    if omni_referenced:
        missing = {
            psl for psl in REQUIRED_OMNI_PSLS
            if not any(a.lower() == psl.lower() for a in all_psls)
        }
        if missing:
            issues.append(
                f"OmniStudio User PSL is assigned but the following required PSLs are missing: "
                f"{', '.join(sorted(missing))}. "
                "Health Cloud OmniStudio users require all three PSLs: HealthCloudPsl, "
                "HealthCloudPlatformPsl, and OmniStudioUser. Missing Health Cloud Platform PSL "
                "causes DataRaptor steps on Health Cloud objects to fail silently."
            )
    return issues


def check_marketing_cloud_hipaa_note(manifest_dir: Path) -> list[str]:
    """Check that if Marketing Cloud connected app or named credential is present,
    a HIPAA BAA note is documented somewhere in the project."""
    issues: list[str] = []

    # Look for Marketing Cloud connected apps or named credentials
    connected_app_files = find_files(manifest_dir, "*.connectedApp-meta.xml")
    named_cred_files = find_files(manifest_dir, "*.namedCredential-meta.xml")

    mc_connected_app_found = any(
        file_contains_any(f, MARKETING_CLOUD_CONNECTED_APP_KEYWORDS)
        for f in connected_app_files + named_cred_files
    )

    if not mc_connected_app_found:
        return issues  # Marketing Cloud not in scope for this project

    # Marketing Cloud is referenced — check for HIPAA BAA documentation
    # Check in common documentation locations: README, docs/, architecture notes
    doc_candidates = (
        find_files(manifest_dir, "*.md")
        + find_files(manifest_dir, "*.txt")
        + find_files(manifest_dir, "*.yaml")
        + find_files(manifest_dir, "*.yml")
    )

    hipaa_documented = any(
        file_contains_any(f, HIPAA_BAA_KEYWORDS)
        for f in doc_candidates
    )

    if not hipaa_documented:
        issues.append(
            "Marketing Cloud connected app or named credential detected, but no HIPAA BAA "
            "documentation found in the project. A separate Marketing Cloud HIPAA BAA must be "
            "executed before any PHI from Health Cloud flows into Marketing Cloud. Document the "
            "BAA status in the project's architecture notes or a README in the metadata root."
        )
    return issues


def check_person_account_marker(manifest_dir: Path) -> list[str]:
    """Check for PersonAccount-related object configuration, and warn if PersonAccount
    does not appear to be enabled while Health Cloud objects are present."""
    issues: list[str] = []

    health_cloud_objects = [
        "EpisodeOfCare",
        "CarePlan",
        "CareProgramEnrollee",
        "ClinicalEncounter",
    ]

    # Check if any Health Cloud-specific objects appear in custom object or layout files
    layout_files = find_files(manifest_dir, "*.layout-meta.xml")
    object_files = find_files(manifest_dir, "*.object-meta.xml")
    page_layout_files = layout_files + object_files

    health_cloud_present = any(
        file_contains_any(f, health_cloud_objects, case_insensitive=True)
        for f in page_layout_files
    )

    if not health_cloud_present:
        return issues  # Health Cloud objects not in scope

    # Check for PersonAccount marker in object files or profile/permset
    person_account_files = [
        f for f in object_files
        if "personaccount" in f.name.lower() or "person_account" in f.name.lower()
    ]
    profile_files = find_files(manifest_dir, "*.profile-meta.xml")
    person_account_in_profiles = any(
        file_contains_any(f, ["PersonAccount", "personAccount"])
        for f in profile_files
    )

    if not person_account_files and not person_account_in_profiles:
        issues.append(
            "Health Cloud data model objects detected (EpisodeOfCare, CarePlan, etc.) but no "
            "PersonAccount metadata found. Health Cloud requires PersonAccount enabled for the "
            "patient data model. Verify PersonAccount is enabled in the org and confirm that "
            "existing Contact records have been assessed for migration impact. Note: PersonAccount "
            "cannot be disabled once enabled."
        )
    return issues


def check_no_redundant_service_cloud_psl(manifest_dir: Path) -> list[str]:
    """Warn if a permission set is assigning Service Cloud PSL alongside Health Cloud PSL
    for what appears to be an internal care coordinator profile — Service Cloud is bundled."""
    issues: list[str] = []

    perm_set_files = find_files(manifest_dir, "*.permissionset-meta.xml")
    if not perm_set_files:
        return issues

    SERVICE_CLOUD_PSL_PATTERNS = [
        "servicecloudpsl",
        "service_cloud_psl",
        "servicecloud",
    ]

    for f in perm_set_files:
        psls = {p.lower() for p in extract_psl_names_from_xml(f)}
        has_health_cloud = any("healthcloud" in p for p in psls)
        has_service_cloud_psl = any(
            s in p for p in psls for s in SERVICE_CLOUD_PSL_PATTERNS
        )
        if has_health_cloud and has_service_cloud_psl:
            issues.append(
                f"{f.name}: Permission set assigns both a Health Cloud PSL and a Service Cloud PSL. "
                "Service Cloud capabilities (Cases, Omni-Channel, Entitlements) are implicitly included "
                "in Health Cloud licenses for internal users — a separate Service Cloud PSL is not needed "
                "and may indicate a redundant license purchase. Verify with the Salesforce account team."
            )
    return issues


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def check_health_cloud_multi_cloud_strategy(manifest_dir: Path) -> list[str]:
    """Run all checks and return a list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_experience_cloud_psl_documented(manifest_dir))
    issues.extend(check_omni_psl_stack(manifest_dir))
    issues.extend(check_marketing_cloud_hipaa_note(manifest_dir))
    issues.extend(check_person_account_marker(manifest_dir))
    issues.extend(check_no_redundant_service_cloud_psl(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_health_cloud_multi_cloud_strategy(manifest_dir)

    if not issues:
        print("No Health Cloud multi-cloud strategy issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
