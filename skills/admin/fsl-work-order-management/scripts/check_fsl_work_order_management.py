#!/usr/bin/env python3
"""Checker script for FSL Work Order Management skill.

Validates Salesforce metadata for common FSL work order configuration issues,
including WorkType settings, status picklist independence, Flow coverage for
status cascade, and Maintenance Plan configuration.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_fsl_work_order_management.py [--help]
    python3 check_fsl_work_order_management.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check FSL Work Order Management configuration and metadata for common issues. "
            "Expects a Salesforce DX project structure or retrieved metadata directory."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_work_type_fields(manifest_dir: Path) -> list[str]:
    """Check WorkType custom field configuration files for missing key fields."""
    issues: list[str] = []

    # WorkType object metadata is typically under objects/WorkType/
    work_type_dir = manifest_dir / "objects" / "WorkType"
    if not work_type_dir.exists():
        # Not a fatal error — may not be in this metadata slice
        return issues

    fields_dir = work_type_dir / "fields"
    if not fields_dir.exists():
        return issues

    field_names = {f.stem for f in fields_dir.glob("*.field-meta.xml")}
    # AutoCreateSvcAppt is a standard FSL field on WorkType — if this dir exists
    # and neither standard nor custom equivalent is referenced, flag it
    auto_create_present = any(
        "autocreate" in name.lower() or "AutoCreate" in name
        for name in field_names
    )
    if not auto_create_present and field_names:
        issues.append(
            "WorkType fields directory found but AutoCreateSvcAppt reference not detected. "
            "Verify that AutoCreateSvcAppt is explicitly configured on WorkType records "
            "to control Service Appointment auto-creation behavior."
        )

    return issues


def check_flow_cascade_coverage(manifest_dir: Path) -> list[str]:
    """Scan Flow metadata for evidence of WO↔SA status cascade automation."""
    issues: list[str] = []

    flows_dir = manifest_dir / "flows"
    if not flows_dir.exists():
        # Try alternate path structure
        flows_dir = manifest_dir / "force-app" / "main" / "default" / "flows"
    if not flows_dir.exists():
        return issues

    flow_files = list(flows_dir.glob("*.flow-meta.xml"))
    if not flow_files:
        return issues

    sa_cascade_found = False
    wo_cascade_found = False

    sa_pattern = re.compile(
        r"ServiceAppointment.*Status|Status.*ServiceAppointment",
        re.IGNORECASE,
    )
    wo_update_pattern = re.compile(
        r"WorkOrder.*Status|Status.*WorkOrder",
        re.IGNORECASE,
    )

    for flow_file in flow_files:
        try:
            content = flow_file.read_text(encoding="utf-8")
        except OSError:
            continue

        # Look for flows that reference both SA status and WO status — cascade candidate
        if sa_pattern.search(content) and wo_update_pattern.search(content):
            sa_cascade_found = True

        # Simpler check: any flow referencing SA trigger object for WO updates
        if "ServiceAppointment" in content and "WorkOrder" in content and "Status" in content:
            wo_cascade_found = True

    if not sa_cascade_found and not wo_cascade_found:
        issues.append(
            "No Flow found that references both ServiceAppointment status and WorkOrder status. "
            "WO and SA statuses do not cascade automatically in FSL. "
            "If the business requires status synchronization (e.g., all SAs Completed → WO Completed), "
            "build an explicit Record-Triggered Flow on ServiceAppointment."
        )

    return issues


def check_work_order_picklist(manifest_dir: Path) -> list[str]:
    """Check that WorkOrder Status picklist has at least the minimum expected values."""
    issues: list[str] = []

    wo_status_path = (
        manifest_dir / "objects" / "WorkOrder" / "fields" / "Status.field-meta.xml"
    )
    if not wo_status_path.exists():
        return issues

    try:
        tree = ET.parse(wo_status_path)
        root = tree.getroot()
        ns = {"sf": "http://soap.sforce.com/2006/04/metadata"}
        values = [
            el.text
            for el in root.findall(".//sf:value", ns)
            if el.text
        ]
        if not values:
            # Try without namespace
            values = [el.text for el in root.findall(".//value") if el.text]
    except ET.ParseError as exc:
        issues.append(f"Could not parse WorkOrder Status field XML: {exc}")
        return issues

    expected_statuses = {"New", "In Progress", "Completed"}
    found_lower = {v.lower() for v in values}
    missing = [s for s in expected_statuses if s.lower() not in found_lower]
    if missing:
        issues.append(
            f"WorkOrder Status picklist may be missing expected values: {missing}. "
            "Verify the status lifecycle covers New → In Progress → Completed at minimum."
        )

    return issues


def check_service_appointment_picklist(manifest_dir: Path) -> list[str]:
    """Check that ServiceAppointment Status picklist exists and is configured separately from WO."""
    issues: list[str] = []

    sa_status_path = (
        manifest_dir
        / "objects"
        / "ServiceAppointment"
        / "fields"
        / "Status.field-meta.xml"
    )
    if not sa_status_path.exists():
        return issues

    try:
        content = sa_status_path.read_text(encoding="utf-8")
    except OSError:
        return issues

    # SA standard statuses per FSL docs
    expected_sa_statuses = ["Scheduled", "Dispatched", "Completed", "Canceled"]
    found_count = sum(1 for s in expected_sa_statuses if s.lower() in content.lower())

    if found_count < 2:
        issues.append(
            "ServiceAppointment Status picklist does not appear to contain standard FSL values "
            "(Scheduled, Dispatched, Completed, Canceled). "
            "Verify the SA status picklist is configured independently from the Work Order status picklist."
        )

    return issues


def check_for_maintenance_plan_objects(manifest_dir: Path) -> list[str]:
    """Detect if MaintenancePlan object metadata is present; flag if missing in FSL org."""
    issues: list[str] = []

    mp_dir = manifest_dir / "objects" / "MaintenancePlan"
    # Only flag if the objects/ dir exists (implying this is a metadata slice)
    objects_dir = manifest_dir / "objects"
    if objects_dir.exists() and not mp_dir.exists():
        issues.append(
            "MaintenancePlan object metadata not found in this manifest. "
            "If recurring work order generation is required, ensure MaintenancePlan "
            "is included in the metadata retrieve and configured with Frequency, "
            "FrequencyType, GenerationHorizon, and a linked WorkTypeId. "
            "Note: Maintenance Plans generate WOs approximately 3x per day, not in real time."
        )

    return issues


def check_woli_limits(manifest_dir: Path) -> list[str]:
    """Warn if any Flow or class references bulk WOLI creation without a limit guard."""
    issues: list[str] = []

    # Scan Apex classes for bulk WOLI insert without a size check
    apex_dirs = [
        manifest_dir / "classes",
        manifest_dir / "force-app" / "main" / "default" / "classes",
    ]
    woli_bulk_pattern = re.compile(
        r"insert\s+\w*[Ww]oli|insert\s+\w*WorkOrderLineItem",
        re.IGNORECASE,
    )
    limit_pattern = re.compile(r"\.size\(\)|\.isEmpty\(\)|limit\s*=|MAX_", re.IGNORECASE)

    for apex_dir in apex_dirs:
        if not apex_dir.exists():
            continue
        for cls_file in apex_dir.glob("*.cls"):
            try:
                content = cls_file.read_text(encoding="utf-8")
            except OSError:
                continue
            if woli_bulk_pattern.search(content) and not limit_pattern.search(content):
                issues.append(
                    f"{cls_file.name}: Bulk WOLI insert detected without an apparent size guard. "
                    "WorkOrders support a maximum of 10,000 child records. "
                    "Verify the insert does not risk exceeding this limit."
                )

    return issues


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def check_fsl_work_order_management(manifest_dir: Path) -> list[str]:
    """Run all FSL work order management checks and return a list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_work_type_fields(manifest_dir))
    issues.extend(check_flow_cascade_coverage(manifest_dir))
    issues.extend(check_work_order_picklist(manifest_dir))
    issues.extend(check_service_appointment_picklist(manifest_dir))
    issues.extend(check_for_maintenance_plan_objects(manifest_dir))
    issues.extend(check_woli_limits(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_fsl_work_order_management(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
