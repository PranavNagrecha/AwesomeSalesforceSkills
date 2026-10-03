#!/usr/bin/env python3
"""Checker script for Health Cloud Referral Management skill.

Checks org metadata for common Health Cloud referral management issues:
- ClinicalServiceRequest object presence in metadata
- HealthCloudICM permission set references
- Flow automation patterns for referral status transitions
- Data Processing Engine job configuration for provider search

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_referral_management_health.py [--help]
    python3 check_referral_management_health.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Health Cloud Referral Management configuration for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_flow_referral_status(manifest_dir: Path) -> list[str]:
    """Check that Flows referencing ClinicalServiceRequest handle required status values."""
    issues: list[str] = []
    flows_dir = manifest_dir / "flows"
    if not flows_dir.exists():
        return issues

    # Standard ClinicalServiceRequest.Status values are the FHIR set; acceptance is the IsAccepted
    # checkbox and reasons go in StatusReason (Health Cloud developer guide). Earlier versions
    # required business values (Submitted/Accepted/Declined/Cancelled) that are not in the picklist.
    required_statuses = {"Active", "Completed"}
    invented_statuses = {"Submitted", "Accepted", "Declined", "Cancelled"}
    for flow_file in flows_dir.glob("*.flow-meta.xml"):
        content = flow_file.read_text(encoding="utf-8")
        if "ClinicalServiceRequest" not in content:
            continue
        for bad in sorted(invented_statuses):
            if f"<stringValue>{bad}</stringValue>" in content or f"<value>{bad}</value>" in content:
                issues.append(
                    f"{flow_file.name}: sets ClinicalServiceRequest.Status to '{bad}', which is not a standard "
                    "value (Active, Completed, Draft, Entered-in-Error, On-Hold, Revoked, Unknown). Model acceptance "
                    "with the IsAccepted checkbox and reasons with StatusReason."
                )
        missing = [s for s in required_statuses if s not in content]
        if missing:
            issues.append(
                f"{flow_file.name}: Flow references ClinicalServiceRequest but may be missing "
                f"status handling for: {', '.join(sorted(missing))}. "
                "Verify all referral status transitions are covered."
            )
    return issues


def check_permission_sets(manifest_dir: Path) -> list[str]:
    """Check for HealthCloudICM permission set references."""
    issues: list[str] = []
    perm_dir = manifest_dir / "permissionsets"
    if not perm_dir.exists():
        return issues

    hc_icm_found = any(
        "HealthCloudICM" in f.name or "HealthCloudICM" in f.read_text(encoding="utf-8")
        for f in perm_dir.glob("*.permissionset-meta.xml")
    )
    if not hc_icm_found:
        issues.append(
            "No HealthCloudICM permission set reference found in permissionsets/. "
            "ClinicalServiceRequest requires HealthCloudICM to be assigned to all referral users. "
            "Confirm this permission set is assigned via a separate mechanism (e.g., Setup > Permission Sets)."
        )
    return issues


def check_clinical_service_request_fields(manifest_dir: Path) -> list[str]:
    """Flag references to fields that do not exist on ClinicalServiceRequest.

    `ReferralType`, `ReferredToId`, `ReferralDate` and `AuthorizationNumber` are not in the object
    reference (earlier versions of this checker REQUIRED two of them). The real fields are
    RequesterId / PerformerId (parties), StartDate / DateSigned (dates), Type / Priority
    (classification) and ClinicalServiceRequestDetail for an authorization number. Corrected 2026-10-03.
    """
    issues: list[str] = []
    invented = ("ReferralType", "ReferredToId", "ReferralDate", "AuthorizationNumber")
    for search_dir, pattern in (("flows", "*.flow-meta.xml"), ("classes", "*.cls"), ("objects", "**/*.validationRule-meta.xml")):
        d = manifest_dir / search_dir
        if not d.exists():
            continue
        for f in sorted(d.glob(pattern)):
            text = f.read_text(encoding="utf-8")
            if "ClinicalServiceRequest" not in text:
                continue
            hits = [name for name in invented if re.search(rf"\b{name}\b", text)]
            if hits:
                issues.append(
                    f"{f.name}: references {', '.join(hits)} on ClinicalServiceRequest; none of these fields "
                    "exists in the object reference. Use RequesterId / PerformerId, StartDate / DateSigned, "
                    "Type / Priority, or a ClinicalServiceRequestDetail record (Health Cloud developer guide)."
                )
    return issues


def check_referral_management_health(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_flow_referral_status(manifest_dir))
    issues.extend(check_permission_sets(manifest_dir))
    issues.extend(check_clinical_service_request_fields(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_referral_management_health(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
