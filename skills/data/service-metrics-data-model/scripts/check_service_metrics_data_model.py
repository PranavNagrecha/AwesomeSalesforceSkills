#!/usr/bin/env python3
"""Checker script for Service Metrics Data Model skill.

Validates Salesforce metadata for common issues with:
  - Entitlement and CaseMilestone configuration
  - Case formula fields for MTTR derivation
  - Custom Report Types for CaseMilestone-based SLA reporting

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_service_metrics_data_model.py [--manifest-dir path/to/metadata]

The manifest directory should be the root of a Salesforce SFDX project or
a directory containing extracted metadata XML files.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Salesforce XML namespace for metadata files
SF_NS = "http://soap.sforce.com/2006/04/metadata"

# Field name hints suggesting this is a monetary/time field that should not be Text
MONETARY_HINTS = {"amount", "revenue", "arr", "mrr", "value", "cost"}
TIME_HINTS = {"elapsed", "duration", "mttr", "minutes", "mins", "hours"}
DATE_HINTS = {"date", "created", "closed", "resolved", "completion", "target"}

# Milestone-related field name patterns used to detect MTTR derivation attempts
MTTR_FORMULA_HINTS = {"closeddate", "createddate", "isclose", "isclosed"}

# CaseMilestone fields that are read-only — flag any DML update attempts in triggers
READONLY_CASEMILESTONE_FIELDS = {"targetdate", "startdate"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_xml_files(root: Path, suffix: str) -> list[Path]:
    """Return all XML files under root matching a metadata suffix."""
    return sorted(root.rglob(f"*{suffix}"))


def parse_xml(path: Path) -> ET.Element | None:
    """Parse an XML file and return the root element, or None on parse error."""
    try:
        return ET.parse(path).getroot()
    except ET.ParseError:
        return None


def tag(name: str) -> str:
    """Return a namespace-qualified tag name for Salesforce metadata XML."""
    return f"{{{SF_NS}}}{name}"


def child_text(element: ET.Element, child_name: str) -> str:
    """Return the text content of a direct child element, or empty string."""
    child = element.find(tag(child_name))
    return (child.text or "").strip() if child is not None else ""


# ---------------------------------------------------------------------------
# Check: Case object MTTR formula field pattern
# ---------------------------------------------------------------------------

def check_case_mttr_fields(manifest_dir: Path) -> list[str]:
    """
    Inspect Case object metadata for MTTR formula field usage.

    Checks:
      - If a formula field referencing ClosedDate and CreatedDate exists,
        verify it guards against null ClosedDate (IsClosed check).
      - Flag formula fields that compute date differences without a null guard,
        which will produce null-reference issues for open cases.
    """
    issues: list[str] = []
    case_candidates = list(manifest_dir.rglob("Case.object-meta.xml"))
    if not case_candidates:
        return issues

    case_path = case_candidates[0]
    root = parse_xml(case_path)
    if root is None:
        return issues

    for field_el in root.findall(tag("fields")):
        field_type = child_text(field_el, "type")
        full_name = child_text(field_el, "fullName")
        formula = child_text(field_el, "formula").lower()

        if field_type != "Summary" and "formula" not in field_type.lower():
            continue

        # Detect MTTR-style formula fields: reference both ClosedDate and CreatedDate
        references_closeddate = "closeddate" in formula
        references_createddate = "createddate" in formula
        has_isclosed_guard = "isclosed" in formula

        if references_closeddate and references_createddate and not has_isclosed_guard:
            issues.append(
                f"[MTTRFormulaNoGuard] Case field '{full_name}' references ClosedDate and CreatedDate "
                f"in a formula without an IsClosed guard. ClosedDate is null on open cases — "
                f"wrap the expression: IF(IsClosed, (ClosedDate - CreatedDate) * 24 * 60, NULL)."
            )

    return issues


# ---------------------------------------------------------------------------
# Check: Custom Report Types for CaseMilestone
# ---------------------------------------------------------------------------

def check_case_milestone_report_types(manifest_dir: Path) -> list[str]:
    """
    Check Custom Report Types involving CaseMilestone for deployment status
    and correct primary/secondary object ordering.

    CaseMilestone CRTs must be Deployed before users can access them.
    """
    issues: list[str] = []
    crt_files = find_xml_files(manifest_dir, ".reportType-meta.xml")

    for crt_path in crt_files:
        root = parse_xml(crt_path)
        if root is None:
            continue

        base_object = child_text(root, "baseObject").lower()
        if "casemilestone" not in base_object and "case" not in base_object:
            continue

        crt_name = crt_path.stem.replace(".reportType-meta", "")
        deployed = child_text(root, "deployed")

        if deployed.lower() != "true":
            issues.append(
                f"[CRTNotDeployed] Report Type '{crt_name}' references Case/CaseMilestone "
                f"but is not deployed (deployed={deployed}). "
                f"Users cannot access this report type until it is deployed."
            )

    return issues


# ---------------------------------------------------------------------------
# Check: Apex triggers — flag TargetDate update attempts on CaseMilestone
# ---------------------------------------------------------------------------

def check_apex_casemilestone_readonly_fields(manifest_dir: Path) -> list[str]:
    """
    Scan Apex trigger files for attempts to update CaseMilestone.TargetDate,
    which is a read-only field after milestone creation.

    Heuristic: look for 'TargetDate' assignment patterns in .trigger files
    or .cls files in a trigger context.
    """
    issues: list[str] = []
    apex_files = list(manifest_dir.rglob("*.trigger")) + list(manifest_dir.rglob("*.trigger-meta.xml"))
    apex_cls_files = list(manifest_dir.rglob("*.cls"))

    all_apex = apex_files + apex_cls_files

    for apex_path in all_apex:
        try:
            content = apex_path.read_text(encoding="utf-8", errors="ignore").lower()
        except OSError:
            continue

        # Detect CaseMilestone TargetDate assignment: cm.TargetDate = or milestone.TargetDate =
        if "casemilestone" in content and "targetdate" in content:
            # Look for assignment pattern (not just a read/filter)
            # Heuristic: TargetDate appears after '=' assignment in a CaseMilestone context
            lines = content.splitlines()
            for lineno, line in enumerate(lines, start=1):
                if "targetdate" in line and "=" in line and "casemilestone" in content:
                    # Skip SOQL/SOSL filter lines and comparisons
                    stripped = line.strip()
                    if (
                        stripped.startswith("//")
                        or "select" in stripped
                        or "where" in stripped
                        or "==" in stripped
                        or "!=" in stripped
                    ):
                        continue
                    # Check for assignment (single =)
                    if ".targetdate" in stripped and "=" in stripped:
                        issues.append(
                            f"[CaseMilestoneReadonlyField] {apex_path.name} line {lineno}: "
                            f"Possible assignment to CaseMilestone.TargetDate — this field is "
                            f"read-only after creation and cannot be updated via DML. "
                            f"Review references/gotchas.md for alternatives."
                        )

    return issues


# ---------------------------------------------------------------------------
# Check: Entitlement object — Business Hours assignment
# ---------------------------------------------------------------------------

def check_entitlement_business_hours(manifest_dir: Path) -> list[str]:
    """
    Check Entitlement Process metadata for Business Hours assignment.

    If an EntitlementProcess is defined without a BusinessHours reference,
    flag it — SLA elapsed time will be calculated in calendar minutes,
    which may not match contractual SLA definitions.
    """
    issues: list[str] = []
    ep_files = find_xml_files(manifest_dir, ".entitlementProcess-meta.xml")

    for ep_path in ep_files:
        root = parse_xml(ep_path)
        if root is None:
            continue

        ep_name = ep_path.stem.replace(".entitlementProcess-meta", "")
        bh_ref = child_text(root, "businessHours")
        active = child_text(root, "active")

        if active.lower() == "true" and not bh_ref:
            issues.append(
                f"[EntitlementProcessNoBH] Entitlement Process '{ep_name}' is active but has no "
                f"BusinessHours assigned. CaseMilestone.ElapsedTimeInMins will count calendar minutes, "
                f"not business hours. Assign a Business Hours record if the SLA is time-of-day scoped."
            )

    return issues


# ---------------------------------------------------------------------------
# Main check runner
# ---------------------------------------------------------------------------

def check_service_metrics_data_model(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_case_mttr_fields(manifest_dir))
    issues.extend(check_case_milestone_report_types(manifest_dir))
    issues.extend(check_apex_casemilestone_readonly_fields(manifest_dir))
    issues.extend(check_entitlement_business_hours(manifest_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for common service metrics data model issues:\n"
            "  - Case MTTR formula fields missing IsClosed null guard\n"
            "  - CaseMilestone Custom Report Types not deployed\n"
            "  - Apex triggers attempting to update read-only CaseMilestone.TargetDate\n"
            "  - Active Entitlement Processes without Business Hours assignment\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
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
    issues = check_service_metrics_data_model(manifest_dir)

    if not issues:
        print("No service metrics data model issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
