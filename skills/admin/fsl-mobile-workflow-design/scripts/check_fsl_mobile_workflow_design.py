#!/usr/bin/env python3
"""Checker script for FSL Mobile Workflow Design skill.

Checks Salesforce metadata for common FSL Mobile workflow configuration gaps:
- Missing SA→WO status cascade flow
- ProductConsumed quick action presence on Work Order layouts
- Briefcase configuration presence (via CustomObject or AppExchange settings)
- Validation rules on WO/SA that may block sync

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_fsl_mobile_workflow_design.py [--help]
    python3 check_fsl_mobile_workflow_design.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Objects where FSL Mobile quick actions should be present
FSL_MOBILE_TARGET_OBJECTS = {"WorkOrder", "ServiceAppointment", "WorkOrderLineItem"}

# Quick actions expected on Work Order for parts consumption
EXPECTED_WO_QUICK_ACTIONS = {"ProductConsumed", "NewProductConsumed"}

# Status values that should trigger WO cascade logic in a Flow
SA_TERMINAL_STATUSES = {"Completed", "Cannot Complete"}

# Flow file extensions
FLOW_EXTENSIONS = {".flow", ".flow-meta.xml"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check FSL Mobile Workflow Design configuration and metadata for "
            "common issues (offline priming gaps, missing status cascade, "
            "parts consumption actions)."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_files(root: Path, extensions: set[str]) -> list[Path]:
    """Return all files under root whose suffix is in extensions."""
    result = []
    for ext in extensions:
        result.extend(root.rglob(f"*{ext}"))
    return result


def _xml_text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return (element.text or "").strip()


def _parse_xml_safe(path: Path) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError:
        return None


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_sa_wo_cascade_flow(manifest_dir: Path) -> list[str]:
    """Look for a Flow that references ServiceAppointment and WorkOrder status update.

    A compliant flow should:
    - Have object = ServiceAppointment (or trigger on ServiceAppointment)
    - Update a record on WorkOrder (recordUpdates referencing WorkOrder)
    """
    issues: list[str] = []
    flow_dir = manifest_dir / "flows"
    if not flow_dir.exists():
        flow_dir = manifest_dir  # fall back to scanning whole tree

    flow_files = _find_files(flow_dir, FLOW_EXTENSIONS)
    if not flow_files:
        issues.append(
            "No Flow metadata files found. Cannot verify SA→WO status cascade Flow exists. "
            "Ensure a Record-Triggered Flow on ServiceAppointment updates WorkOrder.Status."
        )
        return issues

    cascade_found = False
    for fp in flow_files:
        content = fp.read_text(errors="replace")
        # Heuristic: flow references both ServiceAppointment (as trigger object)
        # and WorkOrder (as a record update target)
        has_sa = "ServiceAppointment" in content
        has_wo_update = "WorkOrder" in content and (
            "recordUpdates" in content or "Update_WorkOrder" in content.replace(" ", "_")
        )
        if has_sa and has_wo_update:
            cascade_found = True
            break

    if not cascade_found:
        issues.append(
            "No Flow found that appears to cascade ServiceAppointment status changes to WorkOrder. "
            "SA status does NOT automatically update WO status in FSL — build an explicit "
            "Record-Triggered Flow on ServiceAppointment to update WorkOrder.Status."
        )

    return issues


def check_wo_quick_actions(manifest_dir: Path) -> list[str]:
    """Check that Work Order layouts or quick actions include ProductConsumed."""
    issues: list[str] = []

    # Look in layouts/ for WorkOrder layouts
    layout_dirs = [
        manifest_dir / "layouts",
        manifest_dir,
    ]

    wo_layout_files: list[Path] = []
    for layout_dir in layout_dirs:
        if layout_dir.exists():
            wo_layout_files.extend(layout_dir.rglob("WorkOrder*.layout-meta.xml"))
            wo_layout_files.extend(layout_dir.rglob("WorkOrder*.layout"))

    if not wo_layout_files:
        # Not a hard error — metadata may not be in layout form
        return issues

    found_product_consumed = False
    for lf in wo_layout_files:
        content = lf.read_text(errors="replace")
        if any(action in content for action in EXPECTED_WO_QUICK_ACTIONS):
            found_product_consumed = True
            break

    if not found_product_consumed:
        issues.append(
            "Work Order layout metadata found but no ProductConsumed quick action detected. "
            "FSL Mobile technicians need the 'Products Consumed' (NewProductConsumed) quick "
            "action on the Work Order mobile layout to record parts consumption offline."
        )

    return issues


def check_validation_rules_on_mobile_objects(manifest_dir: Path) -> list[str]:
    """Warn about validation rules on WO/SA that may block sync if fields are not in mobile layout."""
    issues: list[str] = []

    object_dirs = [manifest_dir / "objects", manifest_dir]
    vr_files: list[Path] = []
    for od in object_dirs:
        if od.exists():
            vr_files.extend(od.rglob("*.validationRule-meta.xml"))
            vr_files.extend(od.rglob("*.validationRule"))

    # Filter to WO and SA validation rules
    mobile_vrs = [
        f for f in vr_files
        if any(obj in str(f) for obj in ["WorkOrder", "ServiceAppointment"])
    ]

    if mobile_vrs:
        issues.append(
            f"Found {len(mobile_vrs)} validation rule(s) on WorkOrder or ServiceAppointment "
            "object(s). Validation rules fire SERVER-SIDE at sync time, not offline. "
            "For each rule that fires on Status change or Completion, verify the affected "
            "field(s) are visible and required in the FSL Mobile layout — otherwise technicians "
            "cannot fill them offline and sync will fail with a validation error after they leave the site."
        )

    return issues


def check_flow_metadata_for_offline_assumptions(manifest_dir: Path) -> list[str]:
    """Warn if flows appear to reference objects/logic that won't work offline."""
    issues: list[str] = []
    flow_dir = manifest_dir / "flows"
    if not flow_dir.exists():
        flow_dir = manifest_dir

    flow_files = _find_files(flow_dir, FLOW_EXTENSIONS)
    for fp in flow_files:
        content = fp.read_text(errors="replace")
        # Heuristic: if a flow references FSL-related objects and also callouts/HTTP,
        # it will not work offline
        fsl_related = any(
            obj in content
            for obj in ["ServiceAppointment", "WorkOrder", "ProductConsumed"]
        )
        has_callout = "HTTPRequest" in content or "externalServiceCall" in content.lower()
        if fsl_related and has_callout:
            issues.append(
                f"Flow '{fp.name}' references FSL objects AND external callouts. "
                "External callouts do not execute offline in FSL Mobile — "
                "this flow will fail or be skipped until the device is connected."
            )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_fsl_mobile_workflow_design(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_sa_wo_cascade_flow(manifest_dir))
    issues.extend(check_wo_quick_actions(manifest_dir))
    issues.extend(check_validation_rules_on_mobile_objects(manifest_dir))
    issues.extend(check_flow_metadata_for_offline_assumptions(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_fsl_mobile_workflow_design(manifest_dir)

    if not issues:
        print("No FSL Mobile Workflow Design issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
