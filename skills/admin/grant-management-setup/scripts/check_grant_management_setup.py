#!/usr/bin/env python3
"""Checker script for Grant Management Setup skill.

Checks Salesforce metadata to detect grant management platform path,
verify object availability, and identify common configuration issues.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_grant_management_setup.py [--help]
    python3 check_grant_management_setup.py --manifest-dir path/to/metadata
    python3 check_grant_management_setup.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import sys
import os
import re
from pathlib import Path


# ---------------------------------------------------------------------------
# Platform detection helpers
# ---------------------------------------------------------------------------

OFM_NAMESPACE = "outfunds"
OFM_OBJECTS = {
    "outfunds__Funding_Request__c",
    "outfunds__Disbursement__c",
    "outfunds__Funding_Program__c",
    "outfunds__Requirement__c",
}

NC_GRANTMAKING_OBJECTS = {
    "FundingAward",
    "FundingDisbursement",
    "FundingAwardRequirement",
}

# Patterns that indicate platform confusion (OFM names in NC context or vice versa)
OFM_API_PATTERN = re.compile(r"\boutfunds__\w+", re.IGNORECASE)
NC_GRANT_PATTERN = re.compile(
    r"\b(FundingAward|FundingDisbursement|FundingAwardRequirement)\b"
)

# FundingAwardRequirement valid status values
VALID_REQUIREMENT_STATUSES = {"Open", "Submitted", "Approved"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for grant management setup issues. "
            "Detects platform path (OFM vs NC Grantmaking), mixed platform references, "
            "and common configuration anti-patterns."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print informational messages in addition to warnings.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Detection functions
# ---------------------------------------------------------------------------

def find_metadata_files(manifest_dir: Path, extensions: tuple[str, ...]) -> list[Path]:
    """Recursively find all files with given extensions under manifest_dir."""
    results: list[Path] = []
    for root, _dirs, files in os.walk(manifest_dir):
        for fname in files:
            if fname.endswith(extensions):
                results.append(Path(root) / fname)
    return results


def detect_platform_path(manifest_dir: Path) -> dict:
    """
    Scan metadata files to determine which grant management platform is in use.
    Returns dict with keys: ofm_detected, nc_grantmaking_detected, mixed_platform.
    """
    all_files = find_metadata_files(
        manifest_dir,
        (".xml", ".flow-meta.xml", ".cls", ".trigger", ".js", ".html", ".json"),
    )

    ofm_files: list[Path] = []
    nc_files: list[Path] = []

    for fpath in all_files:
        try:
            content = fpath.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        has_ofm = bool(OFM_API_PATTERN.search(content))
        has_nc = bool(NC_GRANT_PATTERN.search(content))
        if has_ofm:
            ofm_files.append(fpath)
        if has_nc:
            nc_files.append(fpath)

    return {
        "ofm_detected": len(ofm_files) > 0,
        "nc_grantmaking_detected": len(nc_files) > 0,
        "mixed_platform": len(ofm_files) > 0 and len(nc_files) > 0,
        "ofm_files": ofm_files,
        "nc_files": nc_files,
    }


def check_requirement_status_values(manifest_dir: Path) -> list[str]:
    """
    Scan CustomField metadata for FundingAwardRequirement.Status and warn about
    non-standard picklist values beyond the expected Open/Submitted/Approved lifecycle.
    """
    issues: list[str] = []
    field_files = find_metadata_files(manifest_dir, (".field-meta.xml",))

    for fpath in field_files:
        # Only inspect Status fields on FundingAwardRequirement
        fname = fpath.name
        parent_dir = fpath.parent.name
        if "FundingAwardRequirement" not in str(fpath) and "FundingAwardRequirement" not in parent_dir:
            continue
        if "Status" not in fname:
            continue
        try:
            content = fpath.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        # Extract picklist values using a simple regex (stdlib, no XML parser needed for this)
        found_values = re.findall(r"<fullName>(.*?)</fullName>", content)
        custom_values = set(found_values) - VALID_REQUIREMENT_STATUSES - {""}
        if custom_values:
            issues.append(
                f"FundingAwardRequirement.Status has non-standard picklist values in {fpath}: "
                f"{sorted(custom_values)}. The standard lifecycle is Open→Submitted→Approved. "
                "Custom values may break Flow templates and disbursement gating automation."
            )
    return issues


def check_mixed_platform_references(platform_info: dict) -> list[str]:
    """
    Warn if both OFM and NC Grantmaking references are found in the same metadata tree.
    This indicates platform confusion or an incomplete migration.
    """
    issues: list[str] = []
    if platform_info["mixed_platform"]:
        ofm_sample = [str(f) for f in platform_info["ofm_files"][:3]]
        nc_sample = [str(f) for f in platform_info["nc_files"][:3]]
        issues.append(
            "MIXED PLATFORM DETECTED: Both OFM (outfunds__ namespace) and NC Grantmaking "
            "(FundingAward/FundingDisbursement/FundingAwardRequirement) references found in metadata. "
            "These platforms are architecturally incompatible. This may indicate an incomplete "
            "migration or conflated guidance.\n"
            f"  OFM references in: {ofm_sample}\n"
            f"  NC Grantmaking references in: {nc_sample}"
        )
    return issues


def check_funding_disbursement_single_record(manifest_dir: Path) -> list[str]:
    """
    Heuristic: warn if Flow metadata creates exactly one FundingDisbursement per FundingAward
    trigger — a common symptom of treating disbursements as a single payment rather than tranches.
    This is a best-effort heuristic on Flow XML; not exhaustive.
    """
    issues: list[str] = []
    flow_files = find_metadata_files(manifest_dir, (".flow-meta.xml",))

    for fpath in flow_files:
        try:
            content = fpath.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        # Look for flows that reference FundingAward as trigger object and create FundingDisbursement
        # but have no loop or collection — suggesting single-record creation
        has_funding_award_trigger = "FundingAward" in content and (
            "<object>FundingAward</object>" in content
            or "<triggerType>RecordAfterSave</triggerType>" in content
        )
        creates_disbursement = "FundingDisbursement" in content and "recordCreates" in content
        has_loop = "<loop>" in content or "<loops>" in content

        if has_funding_award_trigger and creates_disbursement and not has_loop:
            issues.append(
                f"Flow {fpath.name} appears to create FundingDisbursement records on FundingAward "
                "trigger without a loop or collection. This may indicate single-payment modeling "
                "rather than the correct tranche-per-disbursement pattern. Verify this Flow creates "
                "multiple FundingDisbursement records per award when multi-tranche disbursement is required."
            )
    return issues


# ---------------------------------------------------------------------------
# Main checker
# ---------------------------------------------------------------------------

def check_grant_management_setup(manifest_dir: Path, verbose: bool = False) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # 1. Detect platform path
    platform_info = detect_platform_path(manifest_dir)

    if verbose:
        if platform_info["ofm_detected"]:
            print(f"INFO: NPSP Outbound Funds Module (OFM) references detected "
                  f"({len(platform_info['ofm_files'])} file(s)).")
        if platform_info["nc_grantmaking_detected"]:
            print(f"INFO: Nonprofit Cloud for Grantmaking references detected "
                  f"({len(platform_info['nc_files'])} file(s)).")
        if not platform_info["ofm_detected"] and not platform_info["nc_grantmaking_detected"]:
            print("INFO: No grant management platform references detected in this metadata tree. "
                  "Ensure you are pointing at the correct directory.")

    # 2. Check for mixed platform references
    issues.extend(check_mixed_platform_references(platform_info))

    # 3. Check FundingAwardRequirement status picklist values (NC Grantmaking path)
    if platform_info["nc_grantmaking_detected"]:
        issues.extend(check_requirement_status_values(manifest_dir))

    # 4. Check for single-disbursement anti-pattern in Flows
    if platform_info["nc_grantmaking_detected"]:
        issues.extend(check_funding_disbursement_single_record(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_grant_management_setup(manifest_dir, verbose=args.verbose)

    if not issues:
        print("No grant management setup issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
