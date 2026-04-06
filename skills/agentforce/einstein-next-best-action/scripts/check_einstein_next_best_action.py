#!/usr/bin/env python3
"""Checker script for Einstein Next Best Action skill.

Checks org metadata or configuration relevant to Einstein Next Best Action.
Uses stdlib only -- no pip dependencies.

Validates:
  - Recommendation records have non-empty ActionReference values
  - Strategy Flows define a Recommendation collection output variable
  - No references to deprecated Strategy Builder metadata

Usage:
    python3 check_einstein_next_best_action.py [--help]
    python3 check_einstein_next_best_action.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Einstein Next Best Action configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _strip_ns(tag: str) -> str:
    """Remove XML namespace prefix from a tag name."""
    return re.sub(r"\{[^}]+\}", "", tag)


def _parse_xml_safe(filepath: Path) -> ET.Element | None:
    """Parse an XML file, returning the root element or None on failure."""
    try:
        tree = ET.parse(filepath)
        return tree.getroot()
    except (ET.ParseError, OSError):
        return None


def _get_child_text(element: ET.Element, local_name: str) -> str:
    """Get text content of a child element by local name, namespace-agnostic."""
    for child in element:
        if _strip_ns(child.tag) == local_name:
            return (child.text or "").strip()
    return ""


def check_flow_strategy_outputs(manifest_dir: Path) -> list[str]:
    """Check that Flow files used as NBA strategies define a Recommendation collection output."""
    issues: list[str] = []
    flows_dir = manifest_dir / "flows"
    if not flows_dir.exists():
        flows_dir = manifest_dir / "force-app" / "main" / "default" / "flows"
    if not flows_dir.exists():
        return issues

    for flow_file in flows_dir.glob("*.flow-meta.xml"):
        root = _parse_xml_safe(flow_file)
        if root is None:
            continue

        # Look for elements referencing Recommendation sObject -- indicates an NBA strategy
        flow_text = flow_file.read_text(errors="replace")
        if "Recommendation" not in flow_text:
            continue

        # This is likely an NBA strategy Flow. Check for a Recommendation output variable.
        has_recommendation_output = False
        for var in root.iter():
            if _strip_ns(var.tag) != "variables":
                continue
            is_output = _get_child_text(var, "isOutput") == "true"
            is_collection = _get_child_text(var, "isCollection") == "true"
            object_type = _get_child_text(var, "objectType")
            data_type = _get_child_text(var, "dataType")

            if is_output and is_collection and object_type == "Recommendation":
                has_recommendation_output = True
                break
            # Also accept SObject dataType with Recommendation objectType
            if is_output and is_collection and data_type == "SObject" and object_type == "Recommendation":
                has_recommendation_output = True
                break

        if not has_recommendation_output:
            issues.append(
                f"Flow '{flow_file.name}' references Recommendation but has no "
                f"output collection variable of type Recommendation. "
                f"The Actions & Recommendations component requires this."
            )

    return issues


def check_deprecated_strategy_builder(manifest_dir: Path) -> list[str]:
    """Detect legacy Strategy Builder metadata files."""
    issues: list[str] = []

    # Strategy Builder files have .strategy-meta.xml extension or live in strategies/ folder
    for search_dir in [manifest_dir, manifest_dir / "force-app" / "main" / "default"]:
        strategies_dir = search_dir / "strategies"
        if strategies_dir.exists():
            strategy_files = list(strategies_dir.glob("*.strategy-meta.xml"))
            if strategy_files:
                names = ", ".join(f.stem.replace(".strategy-meta", "") for f in strategy_files)
                issues.append(
                    f"Deprecated Strategy Builder files found in {strategies_dir}: {names}. "
                    f"Strategy Builder was deprecated in Spring '24. "
                    f"Migrate these to Autolaunched Flows."
                )

    # Also check for .strategy files at various depths
    for strategy_file in manifest_dir.rglob("*.strategy-meta.xml"):
        if "strategies" not in str(strategy_file):
            issues.append(
                f"Strategy Builder file found at unexpected location: {strategy_file}. "
                f"Migrate to an Autolaunched Flow."
            )

    return issues


def check_recommendation_records_csv(manifest_dir: Path) -> list[str]:
    """Check exported Recommendation record CSVs for missing ActionReference values."""
    issues: list[str] = []

    # Look for CSV data exports containing Recommendation data
    for csv_file in manifest_dir.rglob("*Recommendation*.csv"):
        try:
            with open(csv_file, "r", encoding="utf-8", errors="replace") as f:
                header_line = f.readline().strip()
                if not header_line:
                    continue
                headers = [h.strip().strip('"') for h in header_line.split(",")]

                action_ref_idx = None
                name_idx = None
                for i, h in enumerate(headers):
                    if h == "ActionReference":
                        action_ref_idx = i
                    elif h == "Name":
                        name_idx = i

                if action_ref_idx is None:
                    continue

                line_num = 1
                for line in f:
                    line_num += 1
                    fields = [field.strip().strip('"') for field in line.split(",")]
                    if action_ref_idx < len(fields):
                        action_ref = fields[action_ref_idx]
                        if not action_ref:
                            rec_name = fields[name_idx] if name_idx is not None and name_idx < len(fields) else f"line {line_num}"
                            issues.append(
                                f"Recommendation '{rec_name}' in {csv_file.name} has empty "
                                f"ActionReference. Acceptance button will silently fail."
                            )
        except OSError:
            continue

    return issues


def check_recommendation_custom_object(manifest_dir: Path) -> list[str]:
    """Check for custom fields on Recommendation object that may indicate good practices."""
    issues: list[str] = []

    # Look for Recommendation object metadata
    for obj_dir in [
        manifest_dir / "objects" / "Recommendation",
        manifest_dir / "force-app" / "main" / "default" / "objects" / "Recommendation",
    ]:
        if not obj_dir.exists():
            continue

        fields_dir = obj_dir / "fields"
        if not fields_dir.exists():
            continue

        # Check if there is a field for object-context tagging
        has_target_object_field = False
        for field_file in fields_dir.glob("*.field-meta.xml"):
            root = _parse_xml_safe(field_file)
            if root is None:
                continue
            label = _get_child_text(root, "label")
            fname = field_file.stem.replace(".field-meta", "")
            if "target" in fname.lower() and "object" in fname.lower():
                has_target_object_field = True
            elif "target" in label.lower() and "object" in label.lower():
                has_target_object_field = True

        if not has_target_object_field:
            issues.append(
                "No Target_Object custom field found on Recommendation object. "
                "Consider adding a field to tag recommendations by object context "
                "(e.g., Case, Opportunity) to prevent cross-contamination in strategy Flows."
            )

    return issues


def check_einstein_next_best_action(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_deprecated_strategy_builder(manifest_dir))
    issues.extend(check_flow_strategy_outputs(manifest_dir))
    issues.extend(check_recommendation_records_csv(manifest_dir))
    issues.extend(check_recommendation_custom_object(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_einstein_next_best_action(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
