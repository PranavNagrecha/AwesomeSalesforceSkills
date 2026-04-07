#!/usr/bin/env python3
"""Checker script for CPQ Approval Workflows skill.

Checks Salesforce metadata in a local SFDX/Metadata API project for
common CPQ Advanced Approvals configuration issues.

Checks performed:
  1. Detects standard ApprovalProcess metadata targeting SBQQ__Quote__c
     (anti-pattern: should use SBAA__ Advanced Approvals instead).
  2. Warns when standard approval processes reference SBQQ__ objects but
     no SBAA__ CustomObject metadata is present (package not deployed).
  3. Scans Flows for references to SBQQ__Quote__c approval submit actions
     that bypass the Advanced Approvals package.
  4. Warns when permission set metadata does not include SBAA__ object
     permissions alongside existing CPQ (SBQQ__) object permissions.
  5. Detects hardcoded user IDs in Flow variables or approval-related
     metadata (fragile; breaks when user is deactivated).

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_cpq_approval_workflows.py [--manifest-dir path/to/metadata]
    python3 check_cpq_approval_workflows.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_xml_files(root: Path, suffix: str) -> list[Path]:
    """Return all files matching *suffix* under *root*, recursively."""
    return sorted(root.rglob(f"*{suffix}"))


def _parse_xml(path: Path) -> ET.Element | None:
    """Parse an XML file and return the root element, or None on failure."""
    try:
        return ET.parse(path).getroot()
    except ET.ParseError:
        return None


def _xml_text(element: ET.Element | None, tag: str, ns: str = "") -> str:
    """Return text of first matching child tag, or empty string."""
    if element is None:
        return ""
    full_tag = f"{{{ns}}}{tag}" if ns else tag
    child = element.find(f".//{full_tag}")
    return (child.text or "").strip() if child is not None else ""


# ---------------------------------------------------------------------------
# Check 1: Standard ApprovalProcess targeting SBQQ__Quote__c
# ---------------------------------------------------------------------------

SBQQ_QUOTE_OBJECT = "SBQQ__Quote__c"
SBAA_NAMESPACE = "SBAA__"

def check_standard_approval_processes_on_cpq_quote(manifest_dir: Path) -> list[str]:
    """Warn when a standard ApprovalProcess targets SBQQ__Quote__c.

    Standard approval processes cannot aggregate across SBQQ__QuoteLine__c
    child records. They should be replaced with SBAA__ Advanced Approvals rules.
    """
    issues: list[str] = []
    approval_dir = manifest_dir / "approvalProcesses"
    if not approval_dir.exists():
        return issues

    for ap_file in _find_xml_files(approval_dir, ".approvalProcess-meta.xml"):
        root = _parse_xml(ap_file)
        if root is None:
            continue
        # ApprovalProcess metadata has <object> element
        ns = "http://soap.sforce.com/2006/04/metadata"
        obj_el = root.find(f"{{{ns}}}object")
        if obj_el is None:
            obj_el = root.find("object")
        obj_name = (obj_el.text or "").strip() if obj_el is not None else ""
        if obj_name == SBQQ_QUOTE_OBJECT:
            issues.append(
                f"[AP-001] Standard ApprovalProcess '{ap_file.stem}' targets "
                f"{SBQQ_QUOTE_OBJECT}. Standard processes cannot evaluate "
                f"discount aggregates across SBQQ__QuoteLine__c child records. "
                f"Use SBAA__ApprovalRule__c (CPQ Advanced Approvals) instead. "
                f"File: {ap_file.relative_to(manifest_dir)}"
            )
    return issues


# ---------------------------------------------------------------------------
# Check 2: SBQQ__ objects present but no SBAA__ CustomObject metadata
# ---------------------------------------------------------------------------

def check_sbaa_package_metadata_present(manifest_dir: Path) -> list[str]:
    """Warn when SBQQ__ objects exist but no SBAA__ CustomObject metadata is found.

    CPQ Advanced Approvals (SBAA__) is a separate managed package. If a project
    has SBQQ__ metadata but no SBAA__ metadata, the Advanced Approvals package
    may not be installed or its metadata may not have been retrieved.
    """
    issues: list[str] = []
    objects_dir = manifest_dir / "objects"
    if not objects_dir.exists():
        return issues

    sbqq_objects = [
        p for p in objects_dir.iterdir()
        if p.is_dir() and p.name.startswith("SBQQ__")
    ]
    if not sbqq_objects:
        return issues  # No CPQ at all — skip

    sbaa_objects = [
        p for p in objects_dir.iterdir()
        if p.is_dir() and p.name.startswith(SBAA_NAMESPACE)
    ]
    if not sbaa_objects:
        issues.append(
            "[AP-002] SBQQ__ (CPQ) objects are present in metadata but no "
            "SBAA__ (Advanced Approvals) object metadata was found. "
            "Confirm the CPQ Advanced Approvals managed package is installed "
            "and its metadata has been retrieved. Without this package, "
            "SBAA__ApprovalRule__c and SBAA__ApprovalVariable__c do not exist."
        )
    return issues


# ---------------------------------------------------------------------------
# Check 3: Flows using approval submit actions on SBQQ__Quote__c
# ---------------------------------------------------------------------------

SBQQ_QUOTE_SUBMIT_KEYWORDS = ["submit", "approval", "SBQQ__Quote"]

def check_flows_for_standard_approval_submit_on_cpq(manifest_dir: Path) -> list[str]:
    """Warn when Flows submit SBQQ__Quote__c records through standard approval."""
    issues: list[str] = []
    flows_dir = manifest_dir / "flows"
    if not flows_dir.exists():
        return issues

    for flow_file in _find_xml_files(flows_dir, ".flow-meta.xml"):
        try:
            content = flow_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        # Heuristic: flow contains both SBQQ__Quote and approval submit action
        # without SBAA__ references — suggests standard approval bypass
        has_sbqq_quote = SBQQ_QUOTE_OBJECT in content or "SBQQ__Quote__c" in content
        has_approval_submit = (
            "submitForApproval" in content or "submit_for_approval" in content.lower()
        )
        has_sbaa = SBAA_NAMESPACE in content

        if has_sbqq_quote and has_approval_submit and not has_sbaa:
            issues.append(
                f"[AP-003] Flow '{flow_file.stem}' appears to submit "
                f"SBQQ__Quote__c records through a standard approval submit "
                f"action without referencing SBAA__ objects. Standard approval "
                f"actions cannot evaluate cross-line discount aggregates. "
                f"Review whether this flow should invoke the CPQ Advanced "
                f"Approvals submission instead. "
                f"File: {flow_file.relative_to(manifest_dir)}"
            )
    return issues


# ---------------------------------------------------------------------------
# Check 4: Permission sets with SBQQ__ permissions but no SBAA__ permissions
# ---------------------------------------------------------------------------

def check_permission_sets_include_sbaa(manifest_dir: Path) -> list[str]:
    """Warn when a permission set grants SBQQ__ access but no SBAA__ access.

    The 'CPQ Advanced Approvals' permission set must be assigned separately.
    A project with custom permission sets granting SBQQ__ access but no SBAA__
    access may be missing the Advanced Approvals permission set assignment.
    """
    issues: list[str] = []
    ps_dir = manifest_dir / "permissionsets"
    if not ps_dir.exists():
        return issues

    for ps_file in _find_xml_files(ps_dir, ".permissionset-meta.xml"):
        try:
            content = ps_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        has_sbqq = "SBQQ__" in content
        has_sbaa = SBAA_NAMESPACE in content

        if has_sbqq and not has_sbaa:
            issues.append(
                f"[AP-004] Permission set '{ps_file.stem}' grants access to "
                f"SBQQ__ (CPQ) objects but does not reference SBAA__ "
                f"(Advanced Approvals) objects. If this permission set is "
                f"assigned to CPQ users, they may be missing the "
                f"'CPQ Advanced Approvals' permission set required to submit "
                f"or approve quotes. Verify that 'CPQ Advanced Approvals' is "
                f"assigned as a separate permission set. "
                f"File: {ps_file.relative_to(manifest_dir)}"
            )
    return issues


# ---------------------------------------------------------------------------
# Check 5: Hardcoded user IDs in Flow metadata (fragile approver references)
# ---------------------------------------------------------------------------

import re

# Salesforce user IDs begin with 005 and are 15 or 18 characters
_USER_ID_PATTERN = re.compile(r"\b005[A-Za-z0-9]{12,15}\b")

def check_hardcoded_user_ids_in_flows(manifest_dir: Path) -> list[str]:
    """Warn when Flow metadata contains hardcoded Salesforce user IDs.

    Hardcoded user IDs break when the referenced user is deactivated or
    their record changes. Dynamic user references (e.g., a field on the
    quote or a named credential) are preferred.
    """
    issues: list[str] = []
    flows_dir = manifest_dir / "flows"
    if not flows_dir.exists():
        return issues

    for flow_file in _find_xml_files(flows_dir, ".flow-meta.xml"):
        try:
            content = flow_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        matches = _USER_ID_PATTERN.findall(content)
        if matches:
            unique_ids = sorted(set(matches))
            issues.append(
                f"[AP-005] Flow '{flow_file.stem}' contains {len(unique_ids)} "
                f"hardcoded Salesforce user ID(s): {', '.join(unique_ids[:3])}"
                f"{'...' if len(unique_ids) > 3 else ''}. "
                f"Hardcoded user IDs in approval-related flows break when the "
                f"referenced user is deactivated. Use dynamic approver fields "
                f"on the quote or a custom setting to store approver references. "
                f"File: {flow_file.relative_to(manifest_dir)}"
            )
    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for CPQ Approval Workflows anti-patterns. "
            "Detects standard approval process misuse, missing SBAA__ package "
            "metadata, Flow-based approval bypasses, permission set gaps, and "
            "hardcoded user IDs in approval-related flows."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help=(
            "Root directory of the Salesforce metadata (e.g., force-app/main/default). "
            "Default: current directory."
        ),
    )
    return parser.parse_args()


def check_cpq_approval_workflows(manifest_dir: Path) -> list[str]:
    """Run all checks and return a list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_standard_approval_processes_on_cpq_quote(manifest_dir))
    issues.extend(check_sbaa_package_metadata_present(manifest_dir))
    issues.extend(check_flows_for_standard_approval_submit_on_cpq(manifest_dir))
    issues.extend(check_permission_sets_include_sbaa(manifest_dir))
    issues.extend(check_hardcoded_user_ids_in_flows(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_cpq_approval_workflows(manifest_dir)

    if not issues:
        print("No CPQ Approval Workflows issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
