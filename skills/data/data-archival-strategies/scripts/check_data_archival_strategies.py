#!/usr/bin/env python3
"""Checker script for Data Archival Strategies skill.

Inspects a Salesforce metadata directory for archival-readiness signals
and prints a guided checklist of items to review.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_data_archival_strategies.py [--manifest-dir path/to/metadata]
    python3 check_data_archival_strategies.py --help
"""

from __future__ import annotations

import argparse
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SALESFORCE_NS = "http://soap.sforce.com/2006/04/metadata"

# Objects whose History objects are common hidden storage consumers
HISTORY_OBJECTS = [
    "Account",
    "Case",
    "Contact",
    "Lead",
    "Opportunity",
    "Task",
    "Event",
]

# Field types that tend to be high-churn and expensive to track in history
HIGH_CHURN_TYPES = {"Picklist", "Boolean", "Currency", "Number", "Percent"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Archival readiness checker for Data Archival Strategies skill.\n\n"
            "Scans a Salesforce metadata directory for Big Object definitions, "
            "field history tracking configuration, and provides a guided checklist "
            "of storage and archival items to review in Salesforce Setup."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def find_files_by_extension(root: Path, suffix: str) -> list[Path]:
    """Return all files under root with the given suffix."""
    matches = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for fname in filenames:
            if fname.endswith(suffix):
                matches.append(Path(dirpath) / fname)
    return sorted(matches)


def parse_xml_root(path: Path):
    """Parse an XML file and return the root element, or None on failure."""
    try:
        tree = ET.parse(path)
        return tree.getroot()
    except ET.ParseError:
        return None


def strip_ns(tag: str) -> str:
    """Strip XML namespace from a tag string."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def find_child_text(element, tag: str) -> str | None:
    """Return the text of the first child with the given local tag name."""
    for child in element:
        if strip_ns(child.tag) == tag:
            return child.text
    return None


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_big_object_definitions(manifest_dir: Path) -> list[str]:
    """Scan for custom Big Object definitions (__b objects)."""
    findings = []
    object_dir = manifest_dir / "objects"
    if not object_dir.exists():
        return ["INFO: No 'objects/' directory found — cannot scan for Big Object definitions."]

    big_object_files = [
        f for f in object_dir.iterdir()
        if f.is_file() and f.name.endswith("__b.object-meta.xml")
    ]

    if not big_object_files:
        findings.append(
            "INFO: No custom Big Object definitions found in objects/. "
            "If planning to use Big Objects for archival, define them via Metadata API."
        )
    else:
        findings.append(f"OK: Found {len(big_object_files)} Big Object definition(s):")
        for f in big_object_files:
            root = parse_xml_root(f)
            index_count = 0
            if root is not None:
                for child in root:
                    if strip_ns(child.tag) == "indexes":
                        index_count += 1
            index_note = f"{index_count} index(es) defined" if index_count else "WARNING — no index defined (required for queries)"
            findings.append(f"  - {f.name}: {index_note}")

    return findings


def check_field_history_tracking(manifest_dir: Path) -> list[str]:
    """Scan standard object metadata for Field History Tracking settings."""
    findings = []
    object_dir = manifest_dir / "objects"
    if not object_dir.exists():
        return []

    tracked_objects = []
    high_churn_tracked: list[tuple[str, str, str]] = []

    for obj_name in HISTORY_OBJECTS:
        meta_file = object_dir / f"{obj_name}.object-meta.xml"
        if not meta_file.exists():
            continue

        root = parse_xml_root(meta_file)
        if root is None:
            continue

        for field_el in root:
            if strip_ns(field_el.tag) != "fields":
                continue
            full_name = find_child_text(field_el, "fullName") or ""
            tracked = find_child_text(field_el, "trackHistory")
            field_type = find_child_text(field_el, "type") or ""
            if tracked == "true":
                tracked_objects.append(obj_name)
                if field_type in HIGH_CHURN_TYPES:
                    high_churn_tracked.append((obj_name, full_name, field_type))

    if tracked_objects:
        unique_objects = sorted(set(tracked_objects))
        findings.append(
            f"INFO: Field History Tracking is enabled on {len(unique_objects)} standard object(s): "
            + ", ".join(unique_objects)
        )
        findings.append(
            "  ACTION: Verify Setup > Storage Usage for History object sizes. "
            "History objects count against data storage separately from the parent object."
        )

    if high_churn_tracked:
        findings.append(
            f"WARNING: {len(high_churn_tracked)} potentially high-churn field(s) have History Tracking enabled:"
        )
        for obj, field, ftype in high_churn_tracked:
            findings.append(f"  - {obj}.{field} (type: {ftype})")
        findings.append(
            "  ACTION: Consider disabling tracking on fields that change frequently "
            "and where history is not required for compliance."
        )

    return findings


def check_archival_patterns_in_objects(manifest_dir: Path) -> list[str]:
    """Look for soft-delete archival pattern (IsArchived__c or similar) in custom objects."""
    findings = []
    object_dir = manifest_dir / "objects"
    if not object_dir.exists():
        return []

    archival_field_names = {"IsArchived__c", "Archived__c", "Is_Archived__c"}
    objects_with_archival_field = []

    for meta_file in object_dir.iterdir():
        if not meta_file.name.endswith(".object-meta.xml"):
            continue
        if meta_file.name.endswith("__b.object-meta.xml"):
            continue

        root = parse_xml_root(meta_file)
        if root is None:
            continue

        for field_el in root:
            if strip_ns(field_el.tag) != "fields":
                continue
            full_name = find_child_text(field_el, "fullName") or ""
            if full_name in archival_field_names:
                obj_name = meta_file.name.replace(".object-meta.xml", "")
                objects_with_archival_field.append(obj_name)
                break

    if objects_with_archival_field:
        findings.append(
            f"INFO: Soft-delete archival pattern (IsArchived__c or similar) detected on "
            f"{len(objects_with_archival_field)} object(s): "
            + ", ".join(sorted(objects_with_archival_field))
        )
        findings.append(
            "  ACTION: Confirm all list views, queues, and reports exclude IsArchived__c = true records. "
            "Consider requesting a custom index on the archival field from Salesforce Support."
        )

    return findings


def print_storage_checklist() -> None:
    """Print a guided checklist for storage and archival review in Setup."""
    checklist = """
================================================================================
  DATA ARCHIVAL STRATEGIES — STORAGE & ARCHIVAL READINESS CHECKLIST
================================================================================

Run the following checks in Salesforce Setup before finalizing an archival plan:

[ ] 1. STORAGE BASELINE
      Setup > Storage Usage
      - Note data storage: ___ GB used / ___ GB limit (___ %)
      - Note file storage: ___ GB used / ___ GB limit (___ %)
      - Alert threshold is 85% and 100%

[ ] 2. RECYCLE BIN STATUS
      Setup > Recycle Bin
      - Count of soft-deleted records: ___
      - If count is high: empty the Recycle Bin first (fastest storage win)
      - Apex: Database.emptyRecycleBin(recordList)
      - Note: soft-deleted records affect query optimizer selectivity

[ ] 3. LARGE OBJECT IDENTIFICATION
      Run SOQL in Developer Console:
        SELECT COUNT(Id) recordCount FROM <ObjectName>
      - Check the top 5 objects by record count
      - Check History objects (AccountHistory, CaseHistory, etc.)

[ ] 4. BIG OBJECT REVIEW (if applicable)
      Setup > Big Objects
      - Confirm index is defined on each custom Big Object
      - Confirm query pattern matches the index field order
      - Confirm no standard DML is used against Big Object records

[ ] 5. FIELD HISTORY TRACKING REVIEW
      Setup > Object Manager > [Object] > Fields & Relationships > Set History Tracking
      - Identify fields with tracking enabled on high-volume, high-churn objects
      - Disable tracking on fields where history is not required
      - For extended retention (beyond 18 months): evaluate Salesforce Shield Field Audit Trail

[ ] 6. ARCHIVAL JOB VALIDATION
      - Test Batch Apex archival job in a sandbox with representative data volume
      - Confirm Big Object writes succeed before deleting source records
      - Confirm hard delete (not soft delete) is used after archival writes
      - Monitor batch job via Setup > Apex Jobs

[ ] 7. POST-ARCHIVAL VALIDATION
      - Re-run Setup > Storage Usage after archival job completes
      - Confirm storage % is below 80% alert threshold
      - Run representative SOQL queries on archived object to confirm index works
      - Validate list views, reports, and queues return correct results

================================================================================
"""
    print(checklist)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_checks(manifest_dir: Path) -> list[str]:
    """Run all checks and return a flat list of finding strings."""
    findings: list[str] = []

    if not manifest_dir.exists():
        findings.append(f"ERROR: Manifest directory not found: {manifest_dir}")
        return findings

    findings.append(f"Scanning metadata at: {manifest_dir.resolve()}")
    findings.append("")

    findings.append("--- Big Object Definitions ---")
    findings.extend(check_big_object_definitions(manifest_dir))
    findings.append("")

    findings.append("--- Field History Tracking ---")
    history_findings = check_field_history_tracking(manifest_dir)
    if history_findings:
        findings.extend(history_findings)
    else:
        findings.append("INFO: No standard object metadata found to scan for History Tracking.")
    findings.append("")

    findings.append("--- Soft-Delete Archival Pattern ---")
    pattern_findings = check_archival_patterns_in_objects(manifest_dir)
    if pattern_findings:
        findings.extend(pattern_findings)
    else:
        findings.append("INFO: No soft-delete archival pattern (IsArchived__c) detected in scanned objects.")
    findings.append("")

    return findings


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)

    findings = run_checks(manifest_dir)
    for line in findings:
        print(line)

    print_storage_checklist()

    errors = [f for f in findings if f.startswith("ERROR:") or f.startswith("WARNING:")]
    if errors:
        print(f"WARN: {len(errors)} archival issue(s) detected", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
