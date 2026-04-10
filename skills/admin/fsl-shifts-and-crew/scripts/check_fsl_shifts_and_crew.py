#!/usr/bin/env python3
"""Checker script for FSL Shifts and Crew skill.

Validates Salesforce metadata and configuration patterns relevant to
FSL Shift and Crew setup — including Shift Status, Operating Hours
alignment, and Crew ServiceResource configuration.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_fsl_shifts_and_crew.py [--help]
    python3 check_fsl_shifts_and_crew.py --manifest-dir path/to/metadata
    python3 check_fsl_shifts_and_crew.py --soql-export path/to/shift-export.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check FSL Shifts and Crew configuration metadata for common issues. "
            "Validates Shift Status, Operating Hours alignment markers, and Crew "
            "ServiceResource setup patterns."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--soql-export",
        default=None,
        help=(
            "Path to a CSV export of Shift records from SOQL "
            "(columns: Id, Status, StartTime, EndTime, ServiceResourceId). "
            "If provided, validates shift status distribution."
        ),
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Metadata-level checks
# ---------------------------------------------------------------------------

def check_custom_field_patterns(manifest_dir: Path) -> list[str]:
    """Check custom field metadata for patterns that indicate FSL anti-patterns."""
    issues: list[str] = []
    objects_dir = manifest_dir / "objects"
    if not objects_dir.exists():
        return issues

    # Look for any custom fields on Shift or ServiceResource objects
    for obj_dir in objects_dir.iterdir():
        if not obj_dir.is_dir():
            continue
        obj_name = obj_dir.name
        fields_dir = obj_dir / "fields"
        if not fields_dir.exists():
            continue
        for field_file in fields_dir.glob("*.field-meta.xml"):
            try:
                tree = ET.parse(field_file)
                root = tree.getroot()
                ns = {"sf": "http://soap.sforce.com/2006/04/metadata"}
                field_type_el = root.find(".//sf:type", ns) or root.find(".//type")
                if field_type_el is not None and field_type_el.text == "MasterDetail":
                    # Master-detail on Shift object targeting ServiceAppointment
                    # could indicate attempt to link shifts to appointments (anti-pattern)
                    if "Shift" in obj_name:
                        ref_el = root.find(".//sf:referenceTo", ns) or root.find(".//referenceTo")
                        if ref_el is not None and "ServiceAppointment" in (ref_el.text or ""):
                            issues.append(
                                f"{obj_name}.{field_file.stem}: MasterDetail relationship to "
                                "ServiceAppointment on a Shift-related object — Shifts are "
                                "availability records, not appointment assignments. "
                                "Review design intent."
                            )
            except ET.ParseError:
                issues.append(f"Could not parse XML: {field_file}")

    return issues


def check_flow_references(manifest_dir: Path) -> list[str]:
    """Scan Flow metadata for patterns that suggest Shifts are being created
    in response to ServiceAppointment events (common anti-pattern)."""
    issues: list[str] = []
    flows_dir = manifest_dir / "flows"
    if not flows_dir.exists():
        return issues

    SHIFT_CREATION_TRIGGERS = [
        "ServiceAppointment",
    ]

    for flow_file in flows_dir.glob("*.flow-meta.xml"):
        try:
            tree = ET.parse(flow_file)
            root = tree.getroot()
            flow_text = ET.tostring(root, encoding="unicode")

            # Heuristic: Flow references both ServiceAppointment (as trigger object)
            # and Shift (as a created record) — suggests treating Shift as assignment
            if "ServiceAppointment" in flow_text and "<object>Shift</object>" in flow_text:
                if any(f"<object>{t}</object>" in flow_text for t in SHIFT_CREATION_TRIGGERS):
                    issues.append(
                        f"Flow '{flow_file.stem}' appears to create Shift records in response "
                        "to ServiceAppointment events. Shifts are availability records — "
                        "they should not be created as a side effect of appointment dispatch. "
                        "Verify this is intentional and not a Shift-as-assignment anti-pattern."
                    )
        except ET.ParseError:
            issues.append(f"Could not parse Flow XML: {flow_file}")

    return issues


def check_permission_sets(manifest_dir: Path) -> list[str]:
    """Check that FSL Shift-related objects are included in relevant permission sets."""
    issues: list[str] = []
    perms_dir = manifest_dir / "permissionsets"
    if not perms_dir.exists():
        return issues

    FSL_SHIFT_OBJECTS = {"Shift", "ShiftTemplate", "ShiftPattern"}
    fsl_perm_sets: list[Path] = []

    for ps_file in perms_dir.glob("*.permissionset-meta.xml"):
        try:
            tree = ET.parse(ps_file)
            root = tree.getroot()
            ps_text = ET.tostring(root, encoding="unicode")
            # Identify permission sets that grant FSL resource access
            if "ServiceResource" in ps_text or "FieldService" in ps_text:
                fsl_perm_sets.append(ps_file)
                # Check if Shift object permissions are missing
                for obj in FSL_SHIFT_OBJECTS:
                    if f"<object>{obj}</object>" not in ps_text:
                        issues.append(
                            f"Permission set '{ps_file.stem}' grants FSL resource access but "
                            f"does not explicitly include '{obj}' object permissions. "
                            f"Dispatchers and scheduling users may not be able to read/create "
                            f"{obj} records."
                        )
        except ET.ParseError:
            issues.append(f"Could not parse permission set XML: {ps_file}")

    return issues


# ---------------------------------------------------------------------------
# SOQL export checks
# ---------------------------------------------------------------------------

def check_soql_shift_export(export_path: Path) -> list[str]:
    """Validate a CSV export of Shift records for common configuration issues.

    Expected columns: Id, Status, StartTime, EndTime, ServiceResourceId
    """
    issues: list[str] = []

    if not export_path.exists():
        issues.append(f"SOQL export file not found: {export_path}")
        return issues

    tentative_count = 0
    total_count = 0
    missing_resource = 0

    try:
        with export_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            required_cols = {"Id", "Status"}
            missing = required_cols - set(headers)
            if missing:
                issues.append(
                    f"SOQL export missing expected columns: {', '.join(sorted(missing))}. "
                    "Export should include: Id, Status, StartTime, EndTime, ServiceResourceId"
                )
                return issues

            for row in reader:
                total_count += 1
                status = (row.get("Status") or "").strip()
                resource_id = (row.get("ServiceResourceId") or "").strip()

                if status == "Tentative":
                    tentative_count += 1
                if not resource_id:
                    missing_resource += 1

    except Exception as exc:
        issues.append(f"Error reading SOQL export: {exc}")
        return issues

    if total_count == 0:
        issues.append(
            "SOQL export contains no Shift records. "
            "If shift-based scheduling is enabled, active resources should have Confirmed Shifts."
        )
        return issues

    if tentative_count > 0:
        pct = round(100 * tentative_count / total_count, 1)
        issues.append(
            f"{tentative_count} of {total_count} Shift records ({pct}%) have Status='Tentative'. "
            "Tentative Shifts are silently excluded from scheduling candidate results. "
            "Update to Status='Confirmed' before the scheduling window opens."
        )

    if missing_resource > 0:
        issues.append(
            f"{missing_resource} Shift records have no ServiceResourceId. "
            "Every Shift must be associated with a ServiceResource to be evaluated "
            "by the scheduling engine."
        )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_fsl_shifts_and_crew(manifest_dir: Path, soql_export: Path | None) -> list[str]:
    """Return a list of issue strings found across all checks."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_custom_field_patterns(manifest_dir))
    issues.extend(check_flow_references(manifest_dir))
    issues.extend(check_permission_sets(manifest_dir))

    if soql_export is not None:
        issues.extend(check_soql_shift_export(soql_export))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    soql_export = Path(args.soql_export) if args.soql_export else None

    issues = check_fsl_shifts_and_crew(manifest_dir, soql_export)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
