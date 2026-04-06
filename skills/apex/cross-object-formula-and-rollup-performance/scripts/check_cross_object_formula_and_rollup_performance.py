#!/usr/bin/env python3
"""Checker script for Cross-Object Formula and Rollup Performance skill.

Scans Salesforce metadata for:
- Cross-object formula fields approaching the 15 spanning relationship limit
- Apex triggers that query rollup summary fields in the same transaction
- Rollup summary fields on objects with high child counts (LDV risk)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_cross_object_formula_and_rollup_performance.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check cross-object formula and rollup performance issues in metadata.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def strip_ns(tag: str) -> str:
    """Remove XML namespace prefix from a tag name."""
    return tag.split("}")[-1] if "}" in tag else tag


def find_custom_field_files(manifest_dir: Path) -> list[Path]:
    """Find all .field-meta.xml files in the metadata tree."""
    results = []
    objects_dir = manifest_dir / "objects"
    if not objects_dir.exists():
        # Try force-app structure
        objects_dir = manifest_dir / "force-app" / "main" / "default" / "objects"
    if not objects_dir.exists():
        return results
    for root, _dirs, files in os.walk(objects_dir):
        for f in files:
            if f.endswith(".field-meta.xml"):
                results.append(Path(root) / f)
    return results


def find_trigger_files(manifest_dir: Path) -> list[Path]:
    """Find all .trigger and .cls files that might contain trigger logic."""
    results = []
    for search_dir in [manifest_dir / "triggers", manifest_dir / "classes",
                       manifest_dir / "force-app" / "main" / "default" / "triggers",
                       manifest_dir / "force-app" / "main" / "default" / "classes"]:
        if not search_dir.exists():
            continue
        for root, _dirs, files in os.walk(search_dir):
            for f in files:
                if f.endswith((".trigger", ".cls")):
                    results.append(Path(root) / f)
    return results


def extract_spanning_refs_from_formula(formula: str) -> set[str]:
    """Extract unique relationship names from cross-object references in a formula."""
    # Match patterns like Account.Name, Account.Owner.Name, Custom__r.Field__c
    refs = set()
    # Find dot-notated references that start with a relationship
    pattern = r'([A-Z]\w*(?:__r)?)\.[A-Z]\w*'
    for match in re.finditer(pattern, formula):
        refs.add(match.group(1))
    return refs


def check_formula_spanning(field_files: list[Path]) -> tuple[dict[str, set[str]], list[str]]:
    """Check formula fields for cross-object spanning relationships.

    Returns a dict of object_name -> set of spanning relationship names,
    and a list of issue strings.
    """
    issues = []
    object_spans: dict[str, set[str]] = defaultdict(set)

    for field_file in field_files:
        try:
            tree = ET.parse(field_file)
            root = tree.getroot()
        except ET.ParseError:
            continue

        formula_el = None
        field_type = None
        for child in root:
            tag = strip_ns(child.tag)
            if tag == "formula":
                formula_el = child
            elif tag == "type":
                field_type = child.text

        if formula_el is None or not formula_el.text:
            continue

        # Determine object name from path
        # Typical: objects/Account/fields/MyField__c.field-meta.xml
        parts = field_file.parts
        obj_name = None
        for i, part in enumerate(parts):
            if part in ("objects",):
                if i + 1 < len(parts):
                    obj_name = parts[i + 1]
                break
        if not obj_name:
            continue

        spans = extract_spanning_refs_from_formula(formula_el.text)
        if spans:
            object_spans[obj_name].update(spans)

    # Check limits
    for obj_name, spans in object_spans.items():
        count = len(spans)
        if count >= 15:
            issues.append(
                f"CRITICAL: {obj_name} has {count} unique spanning relationships "
                f"(limit is 15). Relationships: {', '.join(sorted(spans))}"
            )
        elif count >= 12:
            issues.append(
                f"WARNING: {obj_name} has {count}/15 spanning relationships — "
                f"approaching limit. Relationships: {', '.join(sorted(spans))}"
            )

    return object_spans, issues


def check_rollup_in_triggers(trigger_files: list[Path]) -> list[str]:
    """Check for triggers that query rollup summary fields in the same transaction."""
    issues = []

    # Pattern: SOQL query inside a trigger/handler that selects a field with
    # common rollup naming conventions
    rollup_field_pattern = re.compile(
        r'\bSELECT\b[^]]*?'
        r'(Total_\w+|Sum_\w+|Count_\w+|Avg_\w+|Min_\w+|Max_\w+|Rollup_\w+)',
        re.IGNORECASE | re.DOTALL,
    )
    trigger_context_pattern = re.compile(
        r'(Trigger\.(new|old|isAfter|isBefore|isInsert|isUpdate|isDelete))',
        re.IGNORECASE,
    )

    for tf in trigger_files:
        try:
            content = tf.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        # Only check files that reference trigger context
        if not trigger_context_pattern.search(content):
            continue

        matches = rollup_field_pattern.findall(content)
        if matches:
            field_names = [m if isinstance(m, str) else m[0] for m in matches]
            issues.append(
                f"REVIEW: {tf.name} queries fields with rollup-like names "
                f"({', '.join(set(field_names))}) inside a trigger context. "
                f"If these are rollup summary fields, the values may be stale. "
                f"Consider deferring to a Queueable."
            )

    return issues


def check_rollup_fields(field_files: list[Path]) -> list[str]:
    """Check for rollup summary fields and flag potential LDV concerns."""
    issues = []

    for field_file in field_files:
        try:
            tree = ET.parse(field_file)
            root = tree.getroot()
        except ET.ParseError:
            continue

        is_summary = False
        has_filter = False
        field_name = field_file.stem.replace(".field-meta", "")

        for child in root:
            tag = strip_ns(child.tag)
            if tag == "summarizedField" or tag == "summaryOperation":
                is_summary = True
            if tag == "summaryFilterItems":
                has_filter = True

        if not is_summary:
            continue

        # Determine object name
        parts = field_file.parts
        obj_name = None
        for i, part in enumerate(parts):
            if part == "objects" and i + 1 < len(parts):
                obj_name = parts[i + 1]
                break

        if has_filter:
            issues.append(
                f"INFO: Rollup field {obj_name}.{field_name} uses filter criteria. "
                f"On LDV objects (300k+ children), this triggers a full recalculation "
                f"that may time out. Verify child volume and filter field indexing."
            )

    return issues


def check_cross_object_formula_and_rollup_performance(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    field_files = find_custom_field_files(manifest_dir)
    trigger_files = find_trigger_files(manifest_dir)

    if not field_files and not trigger_files:
        issues.append(
            "No metadata found. Ensure --manifest-dir points to a Salesforce "
            "project root containing objects/ or force-app/main/default/objects/."
        )
        return issues

    # Check 1: Spanning relationship limits
    _spans, spanning_issues = check_formula_spanning(field_files)
    issues.extend(spanning_issues)

    # Check 2: Rollup values queried in triggers
    trigger_issues = check_rollup_in_triggers(trigger_files)
    issues.extend(trigger_issues)

    # Check 3: Rollup fields with filters (LDV risk)
    rollup_issues = check_rollup_fields(field_files)
    issues.extend(rollup_issues)

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_cross_object_formula_and_rollup_performance(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"  {issue}")

    error_count = sum(1 for i in issues if i.startswith("CRITICAL"))
    warning_count = sum(1 for i in issues if i.startswith("WARNING") or i.startswith("REVIEW"))
    info_count = sum(1 for i in issues if i.startswith("INFO"))
    print(f"\nSummary: {error_count} critical, {warning_count} warnings, {info_count} info")

    return 1 if error_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
