#!/usr/bin/env python3
"""Checker script for Insurance Cloud Architecture skill.

Checks org metadata or configuration relevant to Insurance Cloud Architecture.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_insurance_cloud_architecture.py [--help]
    python3 check_insurance_cloud_architecture.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Insurance Cloud Architecture configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def find_files_recursive(root: Path, pattern: str) -> list[Path]:
    """Return all files matching a glob pattern under root."""
    return list(root.rglob(pattern))


def check_insurance_policy_metadata(manifest_dir: Path, issues: list[str]) -> None:
    """Check for InsurancePolicy object-meta.xml in the manifest."""
    insurance_policy_files = find_files_recursive(manifest_dir, "InsurancePolicy*.object-meta.xml")
    if not insurance_policy_files:
        issues.append(
            "No InsurancePolicy*.object-meta.xml found in manifest. "
            "Insurance Cloud requires the FSC Insurance Add-On (Brokerage Management module) "
            "to be provisioned. Confirm the InsurancePolicy standard object is available in this org."
        )
    else:
        print(f"  OK: Found InsurancePolicy metadata: {[f.name for f in insurance_policy_files]}")


def check_insurance_policy_participant(manifest_dir: Path, issues: list[str]) -> None:
    """Warn if InsurancePolicyParticipant object metadata is missing."""
    participant_files = find_files_recursive(manifest_dir, "InsurancePolicyParticipant*.object-meta.xml")
    if not participant_files:
        issues.append(
            "No InsurancePolicyParticipant*.object-meta.xml found in manifest. "
            "InsurancePolicyParticipant is the critical junction object linking InsurancePolicy to "
            "Account records for policyholder, beneficiary, and named insured roles. "
            "Its absence suggests the Brokerage Management module may not be fully provisioned, "
            "or participant relationship design has not been started."
        )
    else:
        print(f"  OK: Found InsurancePolicyParticipant metadata: {[f.name for f in participant_files]}")


def check_sharing_rules_contact_reference(manifest_dir: Path, issues: list[str]) -> None:
    """Check sharing rule files for Contact references where Account is expected for policy participants."""
    sharing_files = find_files_recursive(manifest_dir, "*.sharingRules-meta.xml")
    contact_pattern = re.compile(r"<booleanFilter>.*Contact.*</booleanFilter>|<criteriaItems>.*Contact.*</criteriaItems>", re.DOTALL)
    participant_sharing_with_contact: list[str] = []

    for sf in sharing_files:
        content = sf.read_text(encoding="utf-8", errors="replace")
        # Flag sharing rule files that reference Contact in the context of insurance participant objects
        if "InsurancePolicyParticipant" in content or "InsurancePolicy" in content:
            if re.search(r"<field>Contact", content) or re.search(r"ContactId", content):
                participant_sharing_with_contact.append(sf.name)

    if participant_sharing_with_contact:
        issues.append(
            f"Sharing rule file(s) {participant_sharing_with_contact} reference InsurancePolicy objects "
            "with Contact field criteria. InsurancePolicyParticipant uses AccountId (not ContactId) as "
            "the participant lookup. Sharing rules for policy participants must reference Account, not Contact. "
            "For FSC Person Account orgs, the Person Account IS an Account record — SOQL and sharing "
            "criteria must query AccountId."
        )
    else:
        if sharing_files:
            print(f"  OK: No InsurancePolicy sharing rules with unexpected Contact references found.")


def check_underwriting_rule_metadata(manifest_dir: Path, issues: list[str]) -> None:
    """Warn if InsuranceUnderwritingRule metadata is absent."""
    underwriting_files = find_files_recursive(manifest_dir, "InsuranceUnderwritingRule*.object-meta.xml")
    # Also check for any records/metadata referencing underwriting rules
    underwriting_record_files = find_files_recursive(manifest_dir, "InsuranceUnderwritingRule*.xml")

    if not underwriting_files and not underwriting_record_files:
        issues.append(
            "No InsuranceUnderwritingRule metadata found in manifest. "
            "InsuranceUnderwritingRule is required for configurable underwriting eligibility logic "
            "(Policy Administration module). Without it, underwriting decisions cannot be evaluated "
            "by the Insurance Product Administration APIs. "
            "If underwriting is in scope, confirm the Policy Administration module is licensed and "
            "provisioned, and that underwriting rule records are deployed with Active status "
            "(Draft/Inactive rules are silently skipped by the APIs)."
        )
    else:
        found = underwriting_files or underwriting_record_files
        print(f"  OK: Found InsuranceUnderwritingRule metadata: {[f.name for f in found]}")


def check_sync_apex_callouts_in_insurance(manifest_dir: Path, issues: list[str]) -> None:
    """Detect synchronous Apex callout patterns in classes related to insurance processing."""
    apex_files = find_files_recursive(manifest_dir, "*.cls")
    # Pattern: HttpRequest/HttpResponse usage outside of @future or Queueable or InvocableMethod
    callout_pattern = re.compile(r"\bHttpRequest\b|\bHttpResponse\b|\bHttp\(\)")
    future_pattern = re.compile(r"@future\s*\(\s*callout\s*=\s*true\s*\)|implements\s+Queueable|implements\s+Schedulable")
    insurance_keywords = re.compile(
        r"InsurancePolicy|InsuranceUnderwriting|InsurancePolicyCoverage|underwriting|rating.*engine|ratingEngine",
        re.IGNORECASE,
    )

    flagged: list[str] = []
    for apex_file in apex_files:
        content = apex_file.read_text(encoding="utf-8", errors="replace")
        if not insurance_keywords.search(content):
            continue
        if callout_pattern.search(content) and not future_pattern.search(content):
            flagged.append(apex_file.name)

    if flagged:
        issues.append(
            f"Apex class(es) {flagged} appear to contain synchronous HTTP callouts related to insurance "
            "processing but are not annotated @future(callout=true) or implementing Queueable/Schedulable. "
            "Synchronous callouts in insurance rating or underwriting contexts violate the "
            "100-callout-per-transaction limit and cannot be used in before/after trigger contexts. "
            "Use Integration Procedures (OmniStudio) or @future/Queueable Apex for all external calls."
        )


def check_insurance_cloud_architecture(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    print(f"Checking Insurance Cloud Architecture in: {manifest_dir.resolve()}")

    check_insurance_policy_metadata(manifest_dir, issues)
    check_insurance_policy_participant(manifest_dir, issues)
    check_sharing_rules_contact_reference(manifest_dir, issues)
    check_underwriting_rule_metadata(manifest_dir, issues)
    check_sync_apex_callouts_in_insurance(manifest_dir, issues)

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_insurance_cloud_architecture(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    print(f"\n{len(issues)} issue(s) found:", file=sys.stderr)
    for issue in issues:
        print(f"\nWARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
