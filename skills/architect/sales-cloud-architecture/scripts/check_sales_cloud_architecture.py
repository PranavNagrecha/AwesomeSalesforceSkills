#!/usr/bin/env python3
"""Checker script for Sales Cloud Architecture skill.

Scans a Salesforce metadata directory for common Sales Cloud architecture
issues: mixed automation types on key objects, excessive custom fields,
missing sharing model configuration, and deprecated automation usage.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_sales_cloud_architecture.py [--help]
    python3 check_sales_cloud_architecture.py --manifest-dir path/to/metadata
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
        description="Check Sales Cloud Architecture configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Salesforce objects central to Sales Cloud architecture
# ---------------------------------------------------------------------------
SALES_CLOUD_OBJECTS = {"Lead", "Account", "Contact", "Opportunity", "Quote", "Order"}

# Namespace prefix used in metadata XML
SF_NS = "http://soap.sforce.com/2006/04/metadata"


def _tag(local: str) -> str:
    """Return namespace-qualified tag name."""
    return f"{{{SF_NS}}}{local}"


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_mixed_automation(manifest_dir: Path) -> list[str]:
    """Detect objects that have both Workflow Rules and Flows (or Process Builders)."""
    issues: list[str] = []

    # Collect objects with Workflow Rules
    workflow_dir = manifest_dir / "workflows"
    objects_with_workflows: set[str] = set()
    if workflow_dir.is_dir():
        for wf_file in workflow_dir.glob("*.workflow-meta.xml"):
            obj_name = wf_file.stem.replace(".workflow-meta", "").replace(".workflow", "")
            # Only flag if the workflow file actually contains active rules
            try:
                tree = ET.parse(wf_file)
                root = tree.getroot()
                rules = root.findall(_tag("rules"))
                for rule in rules:
                    active = rule.find(_tag("active"))
                    if active is not None and active.text == "true":
                        objects_with_workflows.add(obj_name)
                        break
            except ET.ParseError:
                issues.append(f"Could not parse workflow file: {wf_file}")

    # Collect objects with Flows (Record-Triggered)
    flow_dir = manifest_dir / "flows"
    objects_with_flows: set[str] = set()
    if flow_dir.is_dir():
        for flow_file in flow_dir.glob("*.flow-meta.xml"):
            try:
                tree = ET.parse(flow_file)
                root = tree.getroot()
                proc_type = root.find(_tag("processType"))
                obj_ref = root.find(_tag("start"))
                if obj_ref is not None:
                    obj_elem = obj_ref.find(_tag("object"))
                    if obj_elem is not None and obj_elem.text:
                        objects_with_flows.add(obj_elem.text)
            except ET.ParseError:
                issues.append(f"Could not parse flow file: {flow_file}")

    overlap = (objects_with_workflows & objects_with_flows) & SALES_CLOUD_OBJECTS
    for obj in sorted(overlap):
        issues.append(
            f"Mixed automation on {obj}: both active Workflow Rules and Flows detected. "
            f"Consolidate into Flows per Sales Cloud architecture best practice."
        )

    return issues


def check_custom_field_count(manifest_dir: Path) -> list[str]:
    """Warn when Sales Cloud objects exceed 500 custom fields."""
    issues: list[str] = []
    objects_dir = manifest_dir / "objects"
    if not objects_dir.is_dir():
        return issues

    for obj_name in SALES_CLOUD_OBJECTS:
        fields_dir = objects_dir / obj_name / "fields"
        if fields_dir.is_dir():
            field_count = sum(1 for _ in fields_dir.glob("*.field-meta.xml"))
            if field_count > 500:
                issues.append(
                    f"{obj_name} has {field_count} custom fields (limit is 500 for most editions). "
                    f"Consider archiving unused fields."
                )
            elif field_count > 400:
                issues.append(
                    f"{obj_name} has {field_count} custom fields — approaching the 500-field limit. "
                    f"Plan field rationalization."
                )

    return issues


def check_rollup_summary_fields(manifest_dir: Path) -> list[str]:
    """Warn when Account approaches the 25 roll-up summary field limit."""
    issues: list[str] = []
    account_fields_dir = manifest_dir / "objects" / "Account" / "fields"
    if not account_fields_dir.is_dir():
        return issues

    rollup_count = 0
    for field_file in account_fields_dir.glob("*.field-meta.xml"):
        try:
            tree = ET.parse(field_file)
            root = tree.getroot()
            field_type = root.find(_tag("type"))
            if field_type is not None and field_type.text == "Summary":
                rollup_count += 1
        except ET.ParseError:
            pass

    if rollup_count > 25:
        issues.append(
            f"Account has {rollup_count} roll-up summary fields, exceeding the 25-field limit."
        )
    elif rollup_count > 20:
        issues.append(
            f"Account has {rollup_count} roll-up summary fields — approaching the 25-field limit. "
            f"Consider batch-Apex alternatives for additional aggregates."
        )

    return issues


def check_process_builder_usage(manifest_dir: Path) -> list[str]:
    """Flag any active Process Builder flows (deprecated)."""
    issues: list[str] = []
    flow_dir = manifest_dir / "flows"
    if not flow_dir.is_dir():
        return issues

    for flow_file in flow_dir.glob("*.flow-meta.xml"):
        try:
            tree = ET.parse(flow_file)
            root = tree.getroot()
            proc_type = root.find(_tag("processType"))
            status = root.find(_tag("status"))
            if (proc_type is not None and proc_type.text == "Workflow"
                    and status is not None and status.text == "Active"):
                flow_name = flow_file.stem.replace(".flow-meta", "")
                issues.append(
                    f"Active Process Builder detected: {flow_name}. "
                    f"Process Builder is deprecated — migrate to Record-Triggered Flow."
                )
        except ET.ParseError:
            issues.append(f"Could not parse flow file: {flow_file}")

    return issues


def check_trigger_count_per_object(manifest_dir: Path) -> list[str]:
    """Flag Sales Cloud objects with more than one Apex trigger."""
    issues: list[str] = []
    triggers_dir = manifest_dir / "triggers"
    if not triggers_dir.is_dir():
        return issues

    triggers_by_object: dict[str, list[str]] = {}
    for trigger_file in triggers_dir.glob("*.trigger-meta.xml"):
        # Also check the .trigger source file for the object name
        trigger_name = trigger_file.stem.replace(".trigger-meta", "")
        source_file = trigger_file.parent / f"{trigger_name}.trigger"
        obj_name = None

        # Try to parse the meta XML for object reference
        try:
            tree = ET.parse(trigger_file)
            root = tree.getroot()
            # Some metadata formats store the object in the trigger meta
            # but more commonly it is in the source itself
        except ET.ParseError:
            pass

        # Try to extract object name from trigger source
        if source_file.is_file():
            try:
                content = source_file.read_text(encoding="utf-8", errors="replace")
                match = re.search(r"trigger\s+\w+\s+on\s+(\w+)", content)
                if match:
                    obj_name = match.group(1)
            except OSError:
                pass

        if obj_name and obj_name in SALES_CLOUD_OBJECTS:
            triggers_by_object.setdefault(obj_name, []).append(trigger_name)

    for obj_name, trigger_names in sorted(triggers_by_object.items()):
        if len(trigger_names) > 1:
            issues.append(
                f"{obj_name} has {len(trigger_names)} Apex triggers ({', '.join(trigger_names)}). "
                f"Consolidate into a single dispatcher trigger per object."
            )

    return issues


def check_sharing_model(manifest_dir: Path) -> list[str]:
    """Warn if Opportunity or Lead OWD is set to Public Read/Write in production-like metadata."""
    issues: list[str] = []
    sharing_file = manifest_dir / "settings" / "Security.settings-meta.xml"
    if not sharing_file.is_file():
        # Try alternative location
        sharing_file = manifest_dir / "settings" / "Sharing.settings-meta.xml"
    if not sharing_file.is_file():
        return issues

    try:
        tree = ET.parse(sharing_file)
        root = tree.getroot()
        # Look for default sharing settings
        for sharing in root.iter():
            tag_local = sharing.tag.replace(f"{{{SF_NS}}}", "")
            if tag_local in ("opportunityOwd", "leadOwd"):
                if sharing.text and "ReadWrite" in sharing.text:
                    obj = "Opportunity" if "opportunity" in tag_local else "Lead"
                    issues.append(
                        f"{obj} OWD is Public Read/Write. For most Sales Cloud architectures, "
                        f"Private or Public Read Only provides better security posture."
                    )
    except ET.ParseError:
        issues.append(f"Could not parse sharing settings: {sharing_file}")

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_sales_cloud_architecture(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_mixed_automation(manifest_dir))
    issues.extend(check_custom_field_count(manifest_dir))
    issues.extend(check_rollup_summary_fields(manifest_dir))
    issues.extend(check_process_builder_usage(manifest_dir))
    issues.extend(check_trigger_count_per_object(manifest_dir))
    issues.extend(check_sharing_model(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_sales_cloud_architecture(manifest_dir)

    if not issues:
        print("No Sales Cloud architecture issues found.")
        return 0

    print(f"Found {len(issues)} issue(s):\n")
    for i, issue in enumerate(issues, 1):
        print(f"  {i}. {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
