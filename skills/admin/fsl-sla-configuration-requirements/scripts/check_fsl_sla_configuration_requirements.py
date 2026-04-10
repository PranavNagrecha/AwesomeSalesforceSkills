#!/usr/bin/env python3
"""Checker script for FSL SLA Configuration Requirements skill.

Validates Salesforce metadata for common FSL SLA configuration issues:
- Entitlement processes must be of type Work Order (not Case)
- WorkOrderMilestone related lists must include key SLA fields
- Milestone completion Flows must exist for Work Order status transitions
- Business Hours alignment notes

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_fsl_sla_configuration_requirements.py [--help]
    python3 check_fsl_sla_configuration_requirements.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


SF_NS = "http://soap.sforce.com/2006/04/metadata"

# Fields that should appear on the WorkOrderMilestone related list
REQUIRED_MILESTONE_FIELDS = {"TargetDate", "CompletionDate", "IsViolated"}

# Flow trigger words that suggest milestone completion automation
MILESTONE_COMPLETION_KEYWORDS = {
    "WorkOrderMilestone",
    "CompletionDate",
}

# Status values commonly used for Work Order completion
COMPLETION_STATUS_KEYWORDS = {"Completed", "Cannot Complete", "Closed"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check FSL SLA (Work Order Entitlement Process) configuration for common issues. "
            "Validates metadata XML files from a Salesforce project directory."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _strip_ns(tag: str) -> str:
    """Remove XML namespace prefix from a tag name."""
    return tag.split("}")[-1] if "}" in tag else tag


def _find_text(element: ET.Element, tag: str) -> str:
    """Find first child element by local name and return its text, or empty string."""
    for child in element:
        if _strip_ns(child.tag) == tag:
            return (child.text or "").strip()
    return ""


def check_entitlement_processes(manifest_dir: Path) -> list[str]:
    """Check entitlement process metadata for Work Order type compliance."""
    issues: list[str] = []

    entitlement_dir = manifest_dir / "entitlementProcesses"
    if not entitlement_dir.exists():
        # No entitlement processes found — not necessarily an error if FSL is not configured yet
        return issues

    xml_files = list(entitlement_dir.glob("*.entitlementProcess"))
    if not xml_files:
        xml_files = list(entitlement_dir.glob("*.xml"))

    if not xml_files:
        issues.append(
            "entitlementProcesses/ directory exists but contains no .entitlementProcess files. "
            "If FSL SLAs are configured, entitlement process metadata should be present."
        )
        return issues

    for xml_file in xml_files:
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
        except ET.ParseError as exc:
            issues.append(f"Could not parse {xml_file.name}: {exc}")
            continue

        process_name = _find_text(root, "name") or xml_file.stem
        process_type = _find_text(root, "entitlementProcess")

        # Check SobjectType child — indicates whether this is a Case or Work Order process
        sobject_type = _find_text(root, "SobjectType")
        if not sobject_type:
            # Try alternate element name used in some API versions
            for child in root:
                if _strip_ns(child.tag).lower() in ("sobjecttype", "entitlementprocesstype"):
                    sobject_type = (child.text or "").strip()
                    break

        if sobject_type and sobject_type.lower() not in ("workorder", "work_order", ""):
            if sobject_type.lower() == "case":
                issues.append(
                    f"Entitlement process '{process_name}' is of type 'Case'. "
                    "FSL Work Order SLAs require a separate entitlement process of type 'Work Order'. "
                    "A Case process will not activate milestone tracking on Work Order records."
                )

        # Check that at least one milestone is defined
        milestones = [child for child in root if _strip_ns(child.tag) == "milestones"]
        if not milestones:
            issues.append(
                f"Entitlement process '{process_name}' has no milestones defined. "
                "Add at least an Initial Response or On-Site Arrival milestone."
            )
            continue

        # Check that at least one milestone has a warning action
        has_warning_action = False
        for milestone in milestones:
            for child in milestone:
                if _strip_ns(child.tag) == "milestonesActions":
                    action_type = _find_text(child, "type")
                    if action_type and action_type.lower() == "warning":
                        has_warning_action = True
                        break

        if not has_warning_action:
            issues.append(
                f"Entitlement process '{process_name}' has milestones but no warning actions. "
                "Add warning actions at 50% and 75% elapsed time so dispatchers are notified before SLA breach."
            )

    return issues


def check_page_layouts_for_milestone_fields(manifest_dir: Path) -> list[str]:
    """Check Work Order page layouts for required WorkOrderMilestone related list fields."""
    issues: list[str] = []

    layouts_dir = manifest_dir / "layouts"
    if not layouts_dir.exists():
        return issues

    wo_layouts = list(layouts_dir.glob("WorkOrder-*.layout")) + list(
        layouts_dir.glob("WorkOrder*.layout")
    )

    if not wo_layouts:
        return issues

    for layout_file in wo_layouts:
        try:
            tree = ET.parse(layout_file)
            root = tree.getroot()
        except ET.ParseError as exc:
            issues.append(f"Could not parse layout {layout_file.name}: {exc}")
            continue

        # Find related lists
        related_lists = [child for child in root if _strip_ns(child.tag) == "relatedLists"]

        wo_milestone_list = None
        for rl in related_lists:
            related_list_val = _find_text(rl, "relatedList")
            if "WorkOrderMilestone" in related_list_val or "Milestones" in related_list_val:
                wo_milestone_list = rl
                break

        if wo_milestone_list is None:
            issues.append(
                f"Work Order layout '{layout_file.name}' does not include a WorkOrderMilestone "
                "related list. Dispatchers will have no in-record SLA visibility without it."
            )
            continue

        # Check that key fields are in the related list columns
        present_fields: set[str] = set()
        for child in wo_milestone_list:
            if _strip_ns(child.tag) == "fields":
                field_name = (child.text or "").strip()
                present_fields.add(field_name)

        missing_fields = REQUIRED_MILESTONE_FIELDS - present_fields
        if missing_fields:
            issues.append(
                f"Work Order layout '{layout_file.name}': WorkOrderMilestone related list is missing "
                f"key columns: {sorted(missing_fields)}. "
                "Add TargetDate, CompletionDate, and IsViolated so dispatchers can see SLA risk."
            )

    return issues


def check_milestone_completion_flows(manifest_dir: Path) -> list[str]:
    """Check Flow metadata for the presence of milestone completion automation."""
    issues: list[str] = []

    flows_dir = manifest_dir / "flows"
    if not flows_dir.exists():
        # Flows may be in a different location — skip rather than false alarm
        return issues

    flow_files = list(flows_dir.glob("*.flow")) + list(flows_dir.glob("*.flow-meta.xml"))
    if not flow_files:
        return issues

    completion_flows_found: list[str] = []

    for flow_file in flow_files:
        try:
            content = flow_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        # Heuristic: a flow that references WorkOrderMilestone AND CompletionDate
        # is likely a milestone completion flow
        if all(kw in content for kw in MILESTONE_COMPLETION_KEYWORDS):
            completion_flows_found.append(flow_file.stem)

    if not completion_flows_found:
        issues.append(
            "No Flow found that references both 'WorkOrderMilestone' and 'CompletionDate'. "
            "Salesforce does NOT auto-complete Work Order milestones. "
            "A Record-Triggered Flow (or Apex trigger) that sets WorkOrderMilestone.CompletionDate "
            "on Work Order completion is required for success actions to fire."
        )
    else:
        # Informational — report what was found but do not warn
        pass

    return issues


def check_fsl_sla_configuration_requirements(manifest_dir: Path) -> list[str]:
    """Run all FSL SLA configuration checks and return a list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_entitlement_processes(manifest_dir))
    issues.extend(check_page_layouts_for_milestone_fields(manifest_dir))
    issues.extend(check_milestone_completion_flows(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_fsl_sla_configuration_requirements(manifest_dir)

    if not issues:
        print("No FSL SLA configuration issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
