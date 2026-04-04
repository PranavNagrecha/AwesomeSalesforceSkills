#!/usr/bin/env python3
"""Data Quality and Governance checker script.

Parses a Salesforce metadata directory (unpackaged sfdx/mdapi format) and
reports concrete governance gaps:

  1. Validation rules that lack a Custom Permission bypass condition.
  2. Objects that have no field history tracking enabled.
  3. Duplicate rules in alert-only mode (not block) on critical objects.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_data_quality.py --help
    python3 check_data_quality.py --manifest-dir path/to/metadata
    python3 check_data_quality.py --manifest-dir path/to/metadata \
        --critical-objects Account,Contact,Lead
"""

from __future__ import annotations

import argparse
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Generator

# ---------------------------------------------------------------------------
# Salesforce metadata namespace
# ---------------------------------------------------------------------------
_SF_NS = "http://soap.sforce.com/2006/04/metadata"


def _tag(local: str) -> str:
    """Return a Clark-notation qualified tag name for the SF metadata namespace."""
    return f"{{{_SF_NS}}}{local}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _iter_xml_files(root: Path, glob: str) -> Generator[Path, None, None]:
    """Yield all files matching *glob* under *root*."""
    yield from root.rglob(glob)


def _parse_xml(path: Path) -> ET.Element | None:
    """Parse an XML file and return its root element, or None on failure."""
    try:
        tree = ET.parse(path)
        return tree.getroot()
    except ET.ParseError as exc:
        print(f"WARNING: Could not parse {path}: {exc}", file=sys.stderr)
        return None


def _text(element: ET.Element, tag: str) -> str:
    """Return the text content of the first child with *tag*, or empty string."""
    child = element.find(_tag(tag))
    if child is not None and child.text:
        return child.text.strip()
    return ""


# ---------------------------------------------------------------------------
# Check 1: Validation rules without Custom Permission bypass
# ---------------------------------------------------------------------------
_CUSTOM_PERMISSION_MARKER = "$Permission."


def check_validation_rules(manifest_dir: Path) -> list[str]:
    """Find validation rules that do not reference any Custom Permission.

    A rule is considered to have a bypass if its error condition formula
    contains '$Permission.' — the standard pattern for Custom Permission checks.

    Heuristic: this catches the absence of ANY bypass. It does not verify
    the bypass is correctly structured.
    """
    issues: list[str] = []

    # mdapi layout: objects/<ObjectName>/<ObjectName>.object
    # sfdx layout:  objects/<ObjectName>/validationRules/<RuleName>.validationRule-meta.xml

    # Try sfdx-style first
    sfdx_rules = list(_iter_xml_files(manifest_dir, "*.validationRule-meta.xml"))
    # Try mdapi-style (validation rules embedded in .object files)
    mdapi_objects = list(_iter_xml_files(manifest_dir, "*.object"))

    if not sfdx_rules and not mdapi_objects:
        issues.append(
            "No validation rule metadata found. "
            "Ensure --manifest-dir points to the root of your sfdx or mdapi metadata tree."
        )
        return issues

    # --- sfdx-style: individual .validationRule-meta.xml files ---
    for rule_file in sfdx_rules:
        root = _parse_xml(rule_file)
        if root is None:
            continue

        active = _text(root, "active").lower()
        if active != "true":
            continue  # Skip inactive rules

        formula = _text(root, "errorConditionFormula")
        rule_name = rule_file.stem.replace(".validationRule-meta", "")
        # Derive object name from parent directory name
        object_name = rule_file.parent.parent.name

        if _CUSTOM_PERMISSION_MARKER not in formula:
            issues.append(
                f"[ValidationRule] {object_name}.{rule_name}: "
                f"No Custom Permission bypass found in error condition formula. "
                f"Integration/migration loads will trigger this rule. "
                f"Wrap formula with: AND(NOT($Permission.Bypass_Validation_Rules), <original>)"
            )

    # --- mdapi-style: validation rules embedded in .object XML ---
    for obj_file in mdapi_objects:
        root = _parse_xml(obj_file)
        if root is None:
            continue

        object_name = obj_file.stem  # e.g., Account from Account.object
        for vr in root.findall(_tag("validationRules")):
            active = _text(vr, "active").lower()
            if active != "true":
                continue

            full_name = _text(vr, "fullName")
            formula = _text(vr, "errorConditionFormula")

            if _CUSTOM_PERMISSION_MARKER not in formula:
                issues.append(
                    f"[ValidationRule] {object_name}.{full_name}: "
                    f"No Custom Permission bypass found in error condition formula. "
                    f"Wrap formula with: AND(NOT($Permission.Bypass_Validation_Rules), <original>)"
                )

    return issues


# ---------------------------------------------------------------------------
# Check 2: Objects with no field history enabled
# ---------------------------------------------------------------------------

def check_field_history(manifest_dir: Path) -> list[str]:
    """Find custom objects that have no fields with history tracking enabled.

    Checks both sfdx-style field metadata and mdapi-style .object files.
    Flags objects where zero fields have trackHistory=true.
    """
    issues: list[str] = []

    # sfdx-style: fields/<FieldName>.field-meta.xml under objects/<ObjectName>/
    # Group field files by object
    object_history: dict[str, int] = {}  # object_name -> count of history-tracked fields

    sfdx_fields = list(_iter_xml_files(manifest_dir, "*.field-meta.xml"))
    for field_file in sfdx_fields:
        root = _parse_xml(field_file)
        if root is None:
            continue

        track = _text(root, "trackHistory").lower()
        # Object name is two levels up (objects/<ObjectName>/fields/<Field>.field-meta.xml)
        object_name = field_file.parent.parent.name
        if object_name not in object_history:
            object_history[object_name] = 0
        if track == "true":
            object_history[object_name] += 1

    for obj_name, tracked_count in object_history.items():
        if tracked_count == 0:
            issues.append(
                f"[FieldHistory] {obj_name}: No fields have history tracking enabled. "
                f"If this object holds important business data, enable tracking on key "
                f"status, owner, and financial fields (up to 20 fields per object)."
            )
        elif tracked_count > 18:
            issues.append(
                f"[FieldHistory] {obj_name}: {tracked_count}/20 fields tracked — "
                f"approaching the 20-field hard limit. "
                f"Review tracked fields and remove any that are no longer audit-critical."
            )

    # mdapi-style: fields inside .object files
    mdapi_objects = list(_iter_xml_files(manifest_dir, "*.object"))
    for obj_file in mdapi_objects:
        root = _parse_xml(obj_file)
        if root is None:
            continue

        object_name = obj_file.stem
        if object_name in object_history:
            continue  # Already processed via sfdx-style

        tracked_fields = [
            f for f in root.findall(_tag("fields"))
            if _text(f, "trackHistory").lower() == "true"
        ]
        if not tracked_fields:
            issues.append(
                f"[FieldHistory] {object_name}: No fields have history tracking enabled "
                f"(mdapi object file). "
                f"Enable tracking on key status, owner, and financial fields."
            )
        elif len(tracked_fields) > 18:
            issues.append(
                f"[FieldHistory] {object_name}: {len(tracked_fields)}/20 fields tracked — "
                f"approaching the 20-field hard limit."
            )

    return issues


# ---------------------------------------------------------------------------
# Check 3: Duplicate rules in alert-only mode on critical objects
# ---------------------------------------------------------------------------

_DEFAULT_CRITICAL_OBJECTS = {"Account", "Contact", "Lead"}


def check_duplicate_rules(
    manifest_dir: Path,
    critical_objects: set[str],
) -> list[str]:
    """Find duplicate rules in alert-only mode on critical objects.

    Alert mode allows duplicates through — Block mode is required for data
    integrity on high-value objects.

    Checks both sfdx-style .duplicateRule-meta.xml and mdapi DuplicateRule
    directory layout.
    """
    issues: list[str] = []

    # sfdx-style: duplicateRules/<RuleName>.duplicateRule-meta.xml
    sfdx_rules = list(_iter_xml_files(manifest_dir, "*.duplicateRule-meta.xml"))
    # mdapi-style: duplicateRules/<RuleName>.duplicateRule
    mdapi_rules = list(_iter_xml_files(manifest_dir, "*.duplicateRule"))

    all_rule_files = sfdx_rules + mdapi_rules

    if not all_rule_files:
        # Not necessarily an issue — some orgs use no Duplicate Rules
        return issues

    for rule_file in all_rule_files:
        root = _parse_xml(rule_file)
        if root is None:
            continue

        # isActive / active
        active_el = root.find(_tag("isActive")) or root.find(_tag("active"))
        if active_el is None or (active_el.text or "").strip().lower() != "true":
            continue  # Skip inactive rules

        # objectName may be in <masterLabel> or derivable from filename
        # Many duplicate rule files embed <sobjectType> on filter items
        # We derive object name from the rule's filter items or master label
        object_name = _extract_duplicate_rule_object(root, rule_file)

        # actionOnInsert and actionOnUpdate: "Allow", "Block", "ReportAsDuplicate"
        action_insert = _text(root, "actionOnInsert").lower()
        action_update = _text(root, "actionOnUpdate").lower()

        # "allow" in this context means alert (show warning but allow save)
        is_alert_only = (
            action_insert in ("allow", "")
            or action_update in ("allow", "")
        )

        if is_alert_only and object_name and object_name in critical_objects:
            issues.append(
                f"[DuplicateRule] {rule_file.stem} (object: {object_name}): "
                f"actionOnInsert='{action_insert or 'allow'}', "
                f"actionOnUpdate='{action_update or 'allow'}'. "
                f"Alert mode allows duplicates through on a critical object. "
                f"Change to 'Block' to enforce data integrity."
            )

    # Check for critical objects with NO duplicate rules at all
    objects_with_rules = _collect_objects_with_duplicate_rules(all_rule_files)
    for obj in critical_objects:
        if obj not in objects_with_rules:
            issues.append(
                f"[DuplicateRule] {obj}: No active Duplicate Rule found in metadata. "
                f"This critical object has no duplicate prevention configured."
            )

    return issues


def _extract_duplicate_rule_object(root: ET.Element, rule_file: Path) -> str:
    """Best-effort extraction of the sobject type from a duplicate rule element."""
    # Try <objectName> (uncommon but possible)
    obj = _text(root, "objectName")
    if obj:
        return obj

    # Try <sobjectType> nested inside <duplicateRuleFilter> > <duplicateRuleFilterItems>
    for item in root.iter(_tag("sobjectType")):
        if item.text:
            return item.text.strip()

    # Fall back to filename heuristics: StandardDuplicateRuleAccount -> Account
    stem = rule_file.stem
    for candidate in _DEFAULT_CRITICAL_OBJECTS:
        if candidate.lower() in stem.lower():
            return candidate

    return ""


def _collect_objects_with_duplicate_rules(rule_files: list[Path]) -> set[str]:
    """Return set of object names that have at least one active duplicate rule."""
    covered: set[str] = set()
    for rule_file in rule_files:
        root = _parse_xml(rule_file)
        if root is None:
            continue
        active_el = root.find(_tag("isActive")) or root.find(_tag("active"))
        if active_el is None or (active_el.text or "").strip().lower() != "true":
            continue
        obj = _extract_duplicate_rule_object(root, rule_file)
        if obj:
            covered.add(obj)
    return covered


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Data Quality and Governance metadata checker. "
            "Flags: validation rules without Custom Permission bypass, "
            "objects with no field history enabled, "
            "duplicate rules in alert-only mode on critical objects."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 check_data_quality.py --manifest-dir force-app/main/default
  python3 check_data_quality.py --manifest-dir metadata/ \\
      --critical-objects Account,Contact,Lead,Opportunity
""",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--critical-objects",
        default=",".join(sorted(_DEFAULT_CRITICAL_OBJECTS)),
        help=(
            "Comma-separated list of object API names considered critical for "
            "duplicate rule enforcement (default: Account,Contact,Lead)."
        ),
    )
    parser.add_argument(
        "--skip-validation-rules",
        action="store_true",
        help="Skip the validation rule bypass check.",
    )
    parser.add_argument(
        "--skip-field-history",
        action="store_true",
        help="Skip the field history check.",
    )
    parser.add_argument(
        "--skip-duplicate-rules",
        action="store_true",
        help="Skip the duplicate rule mode check.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir).expanduser().resolve()
    critical_objects = {o.strip() for o in args.critical_objects.split(",") if o.strip()}

    if not manifest_dir.exists():
        print(f"ERROR: Manifest directory not found: {manifest_dir}", file=sys.stderr)
        return 2

    all_issues: list[str] = []

    if not args.skip_validation_rules:
        vr_issues = check_validation_rules(manifest_dir)
        all_issues.extend(vr_issues)

    if not args.skip_field_history:
        fh_issues = check_field_history(manifest_dir)
        all_issues.extend(fh_issues)

    if not args.skip_duplicate_rules:
        dr_issues = check_duplicate_rules(manifest_dir, critical_objects)
        all_issues.extend(dr_issues)

    if not all_issues:
        print("No data quality governance issues found.")
        return 0

    print(f"Found {len(all_issues)} issue(s):\n")
    for issue in all_issues:
        print(f"  ISSUE: {issue}\n")

    return 1


if __name__ == "__main__":
    sys.exit(main())
