#!/usr/bin/env python3
"""Data model design pattern checker for Salesforce metadata.

Analyzes exported Salesforce metadata (force-app project structure or
retrieved metadata) for common data model anti-patterns:

  1. Junction objects with two lookup fields instead of two MDR fields
     (loses rollup summary capability and referential integrity).
  2. MDR chains deeper than two levels (cascade delete risk).
  3. Objects with no External ID field that contain integration-style naming
     (heuristic: field labels containing "Id", "Code", "Key", "Ref" in
     non-external-ID fields).
  4. Text fields with labels suggesting phone or email data.
  5. Objects exceeding the lookup relationship field count warning threshold.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_data_model.py --manifest-dir path/to/force-app/main/default/objects
    python3 check_data_model.py --manifest-dir .  (searches recursively for .object-meta.xml)
    python3 check_data_model.py --help
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import NamedTuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SF_NS = "http://soap.sforce.com/2006/04/metadata"

# Warn when an object has this many or more lookup relationships.
LOOKUP_COUNT_WARNING_THRESHOLD = 30

# Salesforce hard limit on MDR fields per child object.
MDR_HARD_LIMIT = 2

# Phone / email label keywords (case-insensitive) used for field type heuristic.
PHONE_LABEL_KEYWORDS = {"phone", "mobile", "cell", "fax", "tel"}
EMAIL_LABEL_KEYWORDS = {"email", "e-mail"}

# Integration identifier label keywords used for external ID heuristic.
INTEGRATION_ID_KEYWORDS = {"external id", "ext id", "erp id", "erp_id",
                            "source id", "source_id", "legacy id", "legacy_id",
                            "integration key", "ref id", "ref_id"}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

class FieldInfo(NamedTuple):
    label: str
    api_name: str
    field_type: str
    is_external_id: bool
    is_unique: bool
    relationship_name: str  # populated for Lookup / MasterDetail
    reference_to: str       # populated for Lookup / MasterDetail


class ObjectInfo(NamedTuple):
    api_name: str
    file_path: Path
    fields: list[FieldInfo]


# ---------------------------------------------------------------------------
# XML parsing helpers
# ---------------------------------------------------------------------------

def _tag(local: str) -> str:
    return f"{{{SF_NS}}}{local}"


def _text(element: ET.Element, local: str) -> str:
    child = element.find(_tag(local))
    return (child.text or "").strip() if child is not None else ""


def parse_object_file(path: Path) -> ObjectInfo | None:
    """Parse a .object-meta.xml file and return an ObjectInfo, or None on error."""
    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        print(f"WARN: Could not parse {path}: {exc}", file=sys.stderr)
        return None

    root = tree.getroot()
    api_name = path.parent.name  # directory name is the object API name

    fields: list[FieldInfo] = []
    for field_el in root.findall(_tag("fields")):
        label = _text(field_el, "label")
        api_name_field = _text(field_el, "fullName")
        field_type = _text(field_el, "type")
        is_external_id = _text(field_el, "externalId").lower() == "true"
        is_unique = _text(field_el, "unique").lower() == "true"
        relationship_name = _text(field_el, "relationshipName")
        ref_el = field_el.find(_tag("referenceTo"))
        reference_to = (ref_el.text or "").strip() if ref_el is not None else ""
        fields.append(FieldInfo(
            label=label,
            api_name=api_name_field,
            field_type=field_type,
            is_external_id=is_external_id,
            is_unique=is_unique,
            relationship_name=relationship_name,
            reference_to=reference_to,
        ))

    return ObjectInfo(api_name=api_name, file_path=path, fields=fields)


def discover_object_files(manifest_dir: Path) -> list[Path]:
    """Recursively find all .object-meta.xml files under manifest_dir."""
    return sorted(manifest_dir.rglob("*.object-meta.xml"))


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_junction_object_mdr_pattern(objects: list[ObjectInfo]) -> list[str]:
    """Flag objects that look like junction objects but use two lookups instead of two MDR fields.

    Heuristic: a junction object has exactly two relationship fields (Lookup or MasterDetail)
    and no other business fields beyond standard system fields. If both relationship fields
    are Lookup type, flag as a potential anti-pattern.
    """
    issues: list[str] = []
    relationship_types = {"Lookup", "MasterDetail"}

    for obj in objects:
        rel_fields = [f for f in obj.fields if f.field_type in relationship_types]
        non_rel_custom_fields = [
            f for f in obj.fields
            if f.field_type not in relationship_types
            and not f.api_name.endswith("__s")  # skip system fields (heuristic)
            and f.api_name not in {
                "Name", "OwnerId", "CreatedById", "LastModifiedById",
                "IsDeleted", "SystemModstamp", "CreatedDate", "LastModifiedDate",
                "LastActivityDate", "RecordTypeId",
            }
        ]

        if len(rel_fields) == 2 and len(non_rel_custom_fields) == 0:
            # Looks like a pure junction object
            lookup_fields = [f for f in rel_fields if f.field_type == "Lookup"]
            mdr_fields = [f for f in rel_fields if f.field_type == "MasterDetail"]

            if len(lookup_fields) == 2:
                issues.append(
                    f"JUNCTION_LOOKUP: {obj.api_name} appears to be a junction object "
                    f"(two relationship fields, no other custom fields) but both relationship "
                    f"fields are Lookup type ({lookup_fields[0].api_name}, {lookup_fields[1].api_name}). "
                    f"Convert to MasterDetail on both sides to enable rollup summaries and "
                    f"enforce referential integrity. "
                    f"[File: {obj.file_path}]"
                )
            elif len(lookup_fields) == 1 and len(mdr_fields) == 1:
                issues.append(
                    f"JUNCTION_MIXED: {obj.api_name} appears to be a junction object "
                    f"but uses one Lookup ({lookup_fields[0].api_name}) and one MasterDetail "
                    f"({mdr_fields[0].api_name}). The Lookup side cannot support rollup summaries "
                    f"on that parent object. Consider converting the Lookup to MasterDetail if "
                    f"rollup summaries are needed on that parent. "
                    f"[File: {obj.file_path}]"
                )

    return issues


def check_mdr_chain_depth(objects: list[ObjectInfo]) -> list[str]:
    """Detect potential MDR chains deeper than 2 levels.

    Builds a parent graph from MDR fields and checks for objects that are
    both a master-detail child AND a master-detail parent of another object.
    These form three-level chains with silent cascade delete risk.
    """
    issues: list[str] = []

    # Map: child_object_api_name -> list of MDR parent api_names
    mdr_parents: dict[str, list[str]] = {}
    for obj in objects:
        parents = [
            f.reference_to for f in obj.fields
            if f.field_type == "MasterDetail" and f.reference_to
        ]
        if parents:
            mdr_parents[obj.api_name] = parents

    # Map: parent_object_api_name -> list of MDR child api_names
    mdr_children: dict[str, list[str]] = {}
    for child, parents in mdr_parents.items():
        for parent in parents:
            mdr_children.setdefault(parent, []).append(child)

    # An object that is both a parent (has MDR children) AND a child (has MDR parents)
    # forms a chain: grandparent → parent → child
    for obj_name, children in mdr_children.items():
        if obj_name in mdr_parents:
            grandparents = mdr_parents[obj_name]
            issues.append(
                f"MDR_CHAIN_DEPTH: {obj_name} is both an MDR child of "
                f"{grandparents} and an MDR parent of {children}. "
                f"This creates a cascade delete chain: deleting a "
                f"{grandparents[0] if grandparents else 'grandparent'} record "
                f"will permanently delete all {obj_name} records AND all "
                f"{children} records. Verify that cascade delete at all three "
                f"levels is intentional."
            )

    return issues


def check_text_fields_for_phone_email(objects: list[ObjectInfo]) -> list[str]:
    """Flag Text fields whose labels suggest they should be Phone or Email type."""
    issues: list[str] = []

    for obj in objects:
        for field in obj.fields:
            if field.field_type not in {"Text", "String"}:
                continue
            label_lower = field.label.lower()

            if any(kw in label_lower for kw in PHONE_LABEL_KEYWORDS):
                issues.append(
                    f"TEXT_FOR_PHONE: {obj.api_name}.{field.api_name} "
                    f"(label: '{field.label}') is type Text but the label suggests "
                    f"phone data. Use the Phone field type to get click-to-dial, "
                    f"mobile formatting, and phone validation. "
                    f"[File: {obj.file_path}]"
                )
            elif any(kw in label_lower for kw in EMAIL_LABEL_KEYWORDS):
                issues.append(
                    f"TEXT_FOR_EMAIL: {obj.api_name}.{field.api_name} "
                    f"(label: '{field.label}') is type Text but the label suggests "
                    f"email data. Use the Email field type to get email validation "
                    f"and click-to-email behavior. "
                    f"[File: {obj.file_path}]"
                )

    return issues


def check_missing_external_id(objects: list[ObjectInfo]) -> list[str]:
    """Heuristic: flag objects with integration-suggesting field labels but no External ID field."""
    issues: list[str] = []

    for obj in objects:
        has_external_id = any(f.is_external_id for f in obj.fields)
        if has_external_id:
            continue

        integration_fields = [
            f for f in obj.fields
            if any(kw in f.label.lower() for kw in INTEGRATION_ID_KEYWORDS)
        ]

        if integration_fields:
            field_labels = ", ".join(f"'{f.label}'" for f in integration_fields[:3])
            issues.append(
                f"NO_EXTERNAL_ID: {obj.api_name} has fields with integration-suggesting "
                f"labels ({field_labels}) but no field is marked as External ID. "
                f"If an external system writes to this object, add an External ID field "
                f"(Unique) to enable upsert operations and prevent duplicate records. "
                f"[File: {obj.file_path}]"
            )

    return issues


def check_lookup_field_count(objects: list[ObjectInfo]) -> list[str]:
    """Warn when an object is approaching the 40-lookup-field limit."""
    issues: list[str] = []

    for obj in objects:
        lookup_count = sum(1 for f in obj.fields if f.field_type == "Lookup")
        if lookup_count >= LOOKUP_COUNT_WARNING_THRESHOLD:
            issues.append(
                f"LOOKUP_COUNT_HIGH: {obj.api_name} has {lookup_count} Lookup "
                f"relationship fields (Salesforce limit: 40). Review whether all "
                f"relationships are necessary or if some can be consolidated. "
                f"[File: {obj.file_path}]"
            )

    return issues


def check_mdr_count_per_object(objects: list[ObjectInfo]) -> list[str]:
    """Flag objects with more than 2 master-detail fields (Salesforce hard limit is 2)."""
    issues: list[str] = []

    for obj in objects:
        mdr_count = sum(1 for f in obj.fields if f.field_type == "MasterDetail")
        if mdr_count > MDR_HARD_LIMIT:
            issues.append(
                f"MDR_LIMIT_EXCEEDED: {obj.api_name} has {mdr_count} MasterDetail "
                f"fields, which exceeds the Salesforce limit of {MDR_HARD_LIMIT} "
                f"per object. This metadata may not deploy successfully. "
                f"[File: {obj.file_path}]"
            )

    return issues


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run_all_checks(manifest_dir: Path) -> list[str]:
    """Discover object files, parse them, and run all checks."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    object_files = discover_object_files(manifest_dir)
    if not object_files:
        issues.append(
            f"No .object-meta.xml files found under {manifest_dir}. "
            f"Ensure the path points to a retrieved Salesforce metadata directory."
        )
        return issues

    objects: list[ObjectInfo] = []
    for path in object_files:
        obj = parse_object_file(path)
        if obj is not None:
            objects.append(obj)

    print(f"Parsed {len(objects)} object metadata files from {manifest_dir}")

    issues.extend(check_junction_object_mdr_pattern(objects))
    issues.extend(check_mdr_chain_depth(objects))
    issues.extend(check_text_fields_for_phone_email(objects))
    issues.extend(check_missing_external_id(objects))
    issues.extend(check_lookup_field_count(objects))
    issues.extend(check_mdr_count_per_object(objects))

    return issues


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce object metadata for data model anti-patterns. "
            "Analyzes .object-meta.xml files in a retrieved metadata directory."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help=(
            "Root directory to search for .object-meta.xml files "
            "(default: current directory). Typically force-app/main/default/objects."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = run_all_checks(manifest_dir)

    if not issues:
        print("No data model issues found.")
        return 0

    print(f"\n{len(issues)} issue(s) found:\n")
    for issue in issues:
        print(f"ISSUE: {issue}\n")

    return 1


if __name__ == "__main__":
    sys.exit(main())
