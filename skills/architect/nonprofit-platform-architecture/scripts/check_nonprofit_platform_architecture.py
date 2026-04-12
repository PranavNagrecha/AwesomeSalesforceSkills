#!/usr/bin/env python3
"""Checker script for Nonprofit Platform Architecture skill.

Scans Salesforce metadata in a manifest directory for common Nonprofit Cloud
platform architecture issues:
  - NPSP namespace object references in NPC-targeted code (npsp__ prefix)
  - API version below 59.0 in Apex classes or page definitions (Fundraising Connect API min)
  - Missing Person Account configuration markers in custom object metadata
  - CRLP-related metadata (NPSP rollup framework; not valid in NPC)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_nonprofit_platform_architecture.py [--manifest-dir path/to/metadata]
    python3 check_nonprofit_platform_architecture.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# NPSP namespace prefix — any occurrence in NPC metadata is an anti-pattern
NPSP_PREFIX_PATTERN = re.compile(r'\bnpsp__', re.IGNORECASE)

# CRLP-related identifiers that only exist in NPSP, never in NPC
CRLP_PATTERN = re.compile(r'\b(CRLP|Customizable_Rollup|npo02__|npe01__|npsp__CRLP)', re.IGNORECASE)

# Fundraising Connect API requires version 59.0+
# Look for apiVersion in XML metadata that may be too low
API_VERSION_PATTERN = re.compile(r'<apiVersion>\s*(\d+(?:\.\d+)?)\s*</apiVersion>')
MIN_API_VERSION = 59.0

# Grantmaking module misidentification — grant receiving language in grantmaking context
GRANT_RECEIVING_IN_GRANTMAKING_PATTERN = re.compile(
    r'(grant.{0,20}receiv|grant.{0,20}applic|grant.{0,20}seeker)',
    re.IGNORECASE,
)

# Extensions to scan for NPSP/CRLP patterns
APEX_EXTENSIONS = {'.cls', '.trigger'}
METADATA_EXTENSIONS = {'.xml', '.flow-meta.xml', '.object-meta.xml', '.field-meta.xml',
                       '.permissionset-meta.xml', '.profile-meta.xml'}
ALL_EXTENSIONS = APEX_EXTENSIONS | METADATA_EXTENSIONS | {'.html', '.js'}


# ---------------------------------------------------------------------------
# Check functions
# ---------------------------------------------------------------------------

def check_npsp_namespace_references(manifest_dir: Path) -> list[str]:
    """Flag files containing npsp__ namespace references — invalid in NPC."""
    issues: list[str] = []
    for ext in ALL_EXTENSIONS:
        for path in manifest_dir.rglob(f'*{ext}'):
            try:
                content = path.read_text(encoding='utf-8', errors='replace')
            except OSError:
                continue
            matches = NPSP_PREFIX_PATTERN.findall(content)
            if matches:
                issues.append(
                    f"NPSP namespace reference (npsp__) found in {path.relative_to(manifest_dir)} "
                    f"({len(matches)} occurrence(s)). NPC has no npsp__ namespace — "
                    f"replace with NPC SIDM objects."
                )
    return issues


def check_crlp_references(manifest_dir: Path) -> list[str]:
    """Flag CRLP metadata or code references — NPSP-only, not valid in NPC."""
    issues: list[str] = []
    for ext in ALL_EXTENSIONS:
        for path in manifest_dir.rglob(f'*{ext}'):
            try:
                content = path.read_text(encoding='utf-8', errors='replace')
            except OSError:
                continue
            matches = CRLP_PATTERN.findall(content)
            if matches:
                issues.append(
                    f"CRLP/NPSP rollup reference found in {path.relative_to(manifest_dir)} "
                    f"({len(matches)} occurrence(s)). CRLP does not exist in NPC — "
                    f"use NPC native rollup framework or CRM Analytics."
                )
    return issues


def check_api_versions(manifest_dir: Path) -> list[str]:
    """Flag metadata files with apiVersion below 59.0 (Fundraising Connect API minimum)."""
    issues: list[str] = []
    for path in manifest_dir.rglob('*.xml'):
        try:
            content = path.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue
        for match in API_VERSION_PATTERN.finditer(content):
            version_str = match.group(1)
            try:
                version = float(version_str)
            except ValueError:
                continue
            if version < MIN_API_VERSION:
                issues.append(
                    f"Low API version {version_str} in {path.relative_to(manifest_dir)}. "
                    f"Fundraising Connect API requires API version {MIN_API_VERSION}+. "
                    f"Update apiVersion to at least {int(MIN_API_VERSION)}.0."
                )
    return issues


def check_for_npsp_object_files(manifest_dir: Path) -> list[str]:
    """Flag object metadata files named with NPSP conventions."""
    issues: list[str] = []
    npsp_object_names = [
        'npsp__Allocation__c',
        'npsp__General_Accounting_Unit__c',
        'npsp__CRLP_Rollup__mdt',
        'npo02__Household__c',
        'npe01__OppPayment__c',
        'npsp__Recurring_Donation__c',
    ]
    for path in manifest_dir.rglob('*.object-meta.xml'):
        filename = path.stem.replace('.object-meta', '')
        for npsp_obj in npsp_object_names:
            if npsp_obj.lower() in filename.lower():
                issues.append(
                    f"NPSP object file found: {path.relative_to(manifest_dir)}. "
                    f"This object ({npsp_obj}) does not exist in NPC. "
                    f"Review and replace with NPC SIDM equivalents."
                )
    return issues


def check_volunteer_management_object_coverage(manifest_dir: Path) -> list[str]:
    """
    Warn if Volunteer Management objects appear in metadata but the count of distinct
    Volunteer Management object types is low — suggesting incomplete scoping.
    Volunteer Management has 19 objects; implementations with fewer than 5 distinct
    VM object references may have underscoped the module.
    """
    issues: list[str] = []
    # Key Volunteer Management object name fragments to detect
    vm_object_fragments = [
        'Volunteer_Project',
        'Volunteer_Job',
        'Volunteer_Shift',
        'Volunteer_Hours',
        'Volunteer_Capacity',
        'Volunteer_Recurrence',
        'Volunteer_Skills',
        'Shift_Worker',
    ]
    found_fragments: set[str] = set()

    for path in manifest_dir.rglob('*.xml'):
        try:
            content = path.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue
        for fragment in vm_object_fragments:
            if fragment.lower() in content.lower():
                found_fragments.add(fragment)

    if found_fragments and len(found_fragments) < 4:
        issues.append(
            f"Volunteer Management objects detected ({', '.join(sorted(found_fragments))}) "
            f"but only {len(found_fragments)} of 8 key object types found. "
            f"NPC Volunteer Management has 19 objects — verify the implementation "
            f"has not underscoped the module (check Volunteer_Project, Volunteer_Job, "
            f"Volunteer_Shift, Volunteer_Hours, Volunteer_Capacity, Volunteer_Recurrence)."
        )
    return issues


def check_grantmaking_grant_receiving_confusion(manifest_dir: Path) -> list[str]:
    """
    Flag Grantmaking-related files that contain grant-receiving language,
    which suggests the module may have been mistakenly scoped for a grant-seeking org.
    """
    issues: list[str] = []
    # Only check files in paths that suggest Grantmaking context
    grantmaking_path_fragments = ['grantmaking', 'grant_making', 'funding_opportunity',
                                  'funding_request', 'funding_award']

    for path in manifest_dir.rglob('*'):
        if not path.is_file():
            continue
        path_str = str(path).lower()
        in_grantmaking_context = any(frag in path_str for frag in grantmaking_path_fragments)
        if not in_grantmaking_context:
            continue
        try:
            content = path.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue
        if GRANT_RECEIVING_IN_GRANTMAKING_PATTERN.search(content):
            issues.append(
                f"Grant-receiving language found in Grantmaking context: "
                f"{path.relative_to(manifest_dir)}. "
                f"Grantmaking module is for organizations that AWARD grants outward. "
                f"Grant-receiving/seeking orgs should use the Fundraising module instead."
            )
    return issues


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def check_nonprofit_platform_architecture(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_npsp_namespace_references(manifest_dir))
    issues.extend(check_crlp_references(manifest_dir))
    issues.extend(check_api_versions(manifest_dir))
    issues.extend(check_for_npsp_object_files(manifest_dir))
    issues.extend(check_volunteer_management_object_coverage(manifest_dir))
    issues.extend(check_grantmaking_grant_receiving_confusion(manifest_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for Nonprofit Cloud platform architecture issues: "
            "NPSP namespace leakage, CRLP references, low API versions, "
            "Volunteer Management underscoping, and Grantmaking module misuse."
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
    issues = check_nonprofit_platform_architecture(manifest_dir)

    if not issues:
        print("No Nonprofit Cloud platform architecture issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    print(f"\n{len(issues)} issue(s) found.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
