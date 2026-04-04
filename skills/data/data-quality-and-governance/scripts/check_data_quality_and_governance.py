#!/usr/bin/env python3
"""Data Quality and Governance checker script (entry-point alias).

This script is the scaffolded entry point. It delegates to check_data_quality.py
which contains the full implementation.

For full usage, run check_data_quality.py directly:
    python3 check_data_quality.py --help
    python3 check_data_quality.py --manifest-dir path/to/metadata

This file exists for compatibility with the repo's auto-discovered script naming
convention (check_<skill-name>.py).
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
    return f"{{{_SF_NS}}}{local}"


def _iter_xml_files(root: Path, glob: str) -> Generator[Path, None, None]:
    yield from root.rglob(glob)


def _parse_xml(path: Path) -> ET.Element | None:
    try:
        tree = ET.parse(path)
        return tree.getroot()
    except ET.ParseError as exc:
        print(f"WARNING: Could not parse {path}: {exc}", file=sys.stderr)
        return None


def _text(element: ET.Element, tag: str) -> str:
    child = element.find(_tag(tag))
    if child is not None and child.text:
        return child.text.strip()
    return ""


_CUSTOM_PERMISSION_MARKER = "$Permission."
_DEFAULT_CRITICAL_OBJECTS = {"Account", "Contact", "Lead"}


def check_validation_rules(manifest_dir: Path) -> list[str]:
    """Find validation rules that lack a Custom Permission bypass condition."""
    issues: list[str] = []
    sfdx_rules = list(_iter_xml_files(manifest_dir, "*.validationRule-meta.xml"))
    mdapi_objects = list(_iter_xml_files(manifest_dir, "*.object"))

    if not sfdx_rules and not mdapi_objects:
        issues.append(
            "No validation rule metadata found. "
            "Ensure --manifest-dir points to the root of your sfdx or mdapi metadata tree."
        )
        return issues

    for rule_file in sfdx_rules:
        root = _parse_xml(rule_file)
        if root is None:
            continue
        if _text(root, "active").lower() != "true":
            continue
        formula = _text(root, "errorConditionFormula")
        rule_name = rule_file.stem.replace(".validationRule-meta", "")
        object_name = rule_file.parent.parent.name
        if _CUSTOM_PERMISSION_MARKER not in formula:
            issues.append(
                f"[ValidationRule] {object_name}.{rule_name}: "
                f"No Custom Permission bypass found in error condition formula. "
                f"Wrap with: AND(NOT($Permission.Bypass_Validation_Rules), <original>)"
            )

    for obj_file in mdapi_objects:
        root = _parse_xml(obj_file)
        if root is None:
            continue
        object_name = obj_file.stem
        for vr in root.findall(_tag("validationRules")):
            if _text(vr, "active").lower() != "true":
                continue
            full_name = _text(vr, "fullName")
            formula = _text(vr, "errorConditionFormula")
            if _CUSTOM_PERMISSION_MARKER not in formula:
                issues.append(
                    f"[ValidationRule] {object_name}.{full_name}: "
                    f"No Custom Permission bypass found. "
                    f"Wrap with: AND(NOT($Permission.Bypass_Validation_Rules), <original>)"
                )
    return issues


def check_field_history(manifest_dir: Path) -> list[str]:
    """Find custom objects with no field history tracking enabled."""
    issues: list[str] = []
    object_history: dict[str, int] = {}

    for field_file in _iter_xml_files(manifest_dir, "*.field-meta.xml"):
        root = _parse_xml(field_file)
        if root is None:
            continue
        object_name = field_file.parent.parent.name
        if object_name not in object_history:
            object_history[object_name] = 0
        if _text(root, "trackHistory").lower() == "true":
            object_history[object_name] += 1

    for obj_name, count in object_history.items():
        if count == 0:
            issues.append(
                f"[FieldHistory] {obj_name}: No fields have history tracking enabled. "
                f"Enable tracking on key status, owner, and financial fields (up to 20)."
            )
        elif count > 18:
            issues.append(
                f"[FieldHistory] {obj_name}: {count}/20 fields tracked — "
                f"approaching the 20-field hard limit. Review and prune."
            )

    for obj_file in _iter_xml_files(manifest_dir, "*.object"):
        root = _parse_xml(obj_file)
        if root is None:
            continue
        object_name = obj_file.stem
        if object_name in object_history:
            continue
        tracked = [
            f for f in root.findall(_tag("fields"))
            if _text(f, "trackHistory").lower() == "true"
        ]
        if not tracked:
            issues.append(
                f"[FieldHistory] {object_name}: No fields have history tracking enabled."
            )
        elif len(tracked) > 18:
            issues.append(
                f"[FieldHistory] {object_name}: {len(tracked)}/20 fields tracked — "
                f"approaching the 20-field hard limit."
            )
    return issues


def _extract_duplicate_rule_object(root: ET.Element, rule_file: Path) -> str:
    obj = _text(root, "objectName")
    if obj:
        return obj
    for item in root.iter(_tag("sobjectType")):
        if item.text:
            return item.text.strip()
    stem = rule_file.stem
    for candidate in _DEFAULT_CRITICAL_OBJECTS:
        if candidate.lower() in stem.lower():
            return candidate
    return ""


def _collect_objects_with_duplicate_rules(rule_files: list[Path]) -> set[str]:
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


def check_duplicate_rules(manifest_dir: Path, critical_objects: set[str]) -> list[str]:
    """Find duplicate rules in alert-only mode on critical objects."""
    issues: list[str] = []
    all_rule_files = (
        list(_iter_xml_files(manifest_dir, "*.duplicateRule-meta.xml"))
        + list(_iter_xml_files(manifest_dir, "*.duplicateRule"))
    )
    if not all_rule_files:
        return issues

    for rule_file in all_rule_files:
        root = _parse_xml(rule_file)
        if root is None:
            continue
        active_el = root.find(_tag("isActive")) or root.find(_tag("active"))
        if active_el is None or (active_el.text or "").strip().lower() != "true":
            continue
        object_name = _extract_duplicate_rule_object(root, rule_file)
        action_insert = _text(root, "actionOnInsert").lower()
        action_update = _text(root, "actionOnUpdate").lower()
        is_alert_only = action_insert in ("allow", "") or action_update in ("allow", "")
        if is_alert_only and object_name and object_name in critical_objects:
            issues.append(
                f"[DuplicateRule] {rule_file.stem} (object: {object_name}): "
                f"actionOnInsert='{action_insert or 'allow'}', "
                f"actionOnUpdate='{action_update or 'allow'}'. "
                f"Alert mode allows duplicates through on a critical object. "
                f"Change to 'Block'."
            )

    objects_with_rules = _collect_objects_with_duplicate_rules(all_rule_files)
    for obj in critical_objects:
        if obj not in objects_with_rules:
            issues.append(
                f"[DuplicateRule] {obj}: No active Duplicate Rule found. "
                f"This critical object has no duplicate prevention configured."
            )
    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Data Quality and Governance configuration in Salesforce metadata. "
            "Flags missing Custom Permission bypasses on validation rules, "
            "objects with no field history, and alert-mode duplicate rules."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--critical-objects",
        default=",".join(sorted(_DEFAULT_CRITICAL_OBJECTS)),
        help="Comma-separated critical object API names for duplicate rule checks.",
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
    all_issues.extend(check_validation_rules(manifest_dir))
    all_issues.extend(check_field_history(manifest_dir))
    all_issues.extend(check_duplicate_rules(manifest_dir, critical_objects))

    if not all_issues:
        print("No data quality governance issues found.")
        return 0

    print(f"Found {len(all_issues)} issue(s):\n")
    for issue in all_issues:
        print(f"  ISSUE: {issue}\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
