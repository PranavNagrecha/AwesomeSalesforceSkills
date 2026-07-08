#!/usr/bin/env python3
"""Checker script for Knowledge Base Administration skill.

Checks Salesforce metadata for common Lightning Knowledge configuration issues:
- Missing or misconfigured Data Category visibility assignments
- Knowledge__kav page layouts not assigned to record types
- Approval process targets on Knowledge__kav
- Validation Status picklist presence

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_knowledge_base_administration.py [--help]
    python3 check_knowledge_base_administration.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Knowledge Base Administration configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_knowledge_record_types(manifest_dir: Path) -> list[str]:
    """Check that Knowledge__kav has at least one record type defined."""
    issues: list[str] = []
    knowledge_object_dir = manifest_dir / "objects" / "Knowledge__kav"
    record_types_dir = knowledge_object_dir / "recordTypes"

    if not knowledge_object_dir.exists():
        # Lightning Knowledge may not be enabled or metadata not retrieved
        return issues

    if not record_types_dir.exists() or not any(record_types_dir.glob("*.recordType-meta.xml")):
        issues.append(
            "Knowledge__kav has no record types defined. "
            "Lightning Knowledge requires at least one record type for article classification. "
            "Create record types in Setup > Object Manager > Knowledge > Record Types."
        )
    return issues


def check_knowledge_validation_status(manifest_dir: Path) -> list[str]:
    """Check whether Validation_Status picklist field exists on Knowledge__kav."""
    issues: list[str] = []
    fields_dir = manifest_dir / "objects" / "Knowledge__kav" / "fields"

    if not fields_dir.exists():
        return issues

    validation_field = fields_dir / "ValidationStatus.field-meta.xml"
    if not validation_field.exists():
        # Not an error — optional feature — but warn if approval processes exist
        approval_dir = manifest_dir / "approvalProcesses"
        if approval_dir.exists():
            knowledge_approvals = list(approval_dir.glob("Knowledge__kav.*"))
            if knowledge_approvals:
                issues.append(
                    "Approval processes targeting Knowledge__kav exist but Validation Status picklist "
                    "field (ValidationStatus) was not found. Validation Status is the recommended "
                    "handshake signal between authors and approvers in Knowledge publishing workflows. "
                    "Enable it in Setup > Knowledge Settings."
                )
    return issues


def check_knowledge_approval_processes(manifest_dir: Path) -> list[str]:
    """Check approval processes targeting Knowledge__kav for common configuration issues."""
    issues: list[str] = []
    approval_dir = manifest_dir / "approvalProcesses"

    if not approval_dir.exists():
        return issues

    for ap_file in approval_dir.glob("Knowledge__kav.*"):
        try:
            tree = ET.parse(ap_file)
            root = tree.getroot()
            ns = {"sf": "http://soap.sforce.com/2006/04/metadata"}

            # Check that the approval process has at least one approval step
            steps = root.findall(".//sf:approvalStep", ns) or root.findall(".//approvalStep")
            if not steps:
                issues.append(
                    f"Approval process '{ap_file.stem}' on Knowledge__kav has no approval steps. "
                    "An approval process without steps does nothing. Add at least one approval step."
                )

            # Check for final approval actions that auto-publish (common misconfiguration expectation)
            final_actions = root.findall(".//sf:finalApprovalActions", ns) or root.findall(".//finalApprovalActions")
            for action in final_actions:
                action_name = action.findtext("sf:name", namespaces=ns) or action.findtext("name") or ""
                if "publish" in action_name.lower():
                    issues.append(
                        f"Approval process '{ap_file.stem}' has a final action referencing 'publish'. "
                        "Note: Approval processes on Knowledge__kav cannot auto-publish articles. "
                        "The Publish action must be performed manually by the author after approval. "
                        "Verify this action is a Field Update (e.g., set Validation Status = Validated) "
                        "rather than an attempt to auto-publish."
                    )
        except ET.ParseError as exc:
            issues.append(f"Could not parse approval process file '{ap_file.name}': {exc}")

    return issues


def check_data_category_groups(manifest_dir: Path) -> list[str]:
    """Check Data Category Group configurations for Knowledge."""
    issues: list[str] = []
    dcg_dir = manifest_dir / "dataCategoryGroups"

    if not dcg_dir.exists():
        return issues

    knowledge_groups: list[str] = []
    for dcg_file in dcg_dir.glob("*.dataCategory-meta.xml"):
        try:
            tree = ET.parse(dcg_file)
            root = tree.getroot()
            ns = {"sf": "http://soap.sforce.com/2006/04/metadata"}
            # Check if this group is assigned to Knowledge
            objects = root.findall(".//sf:dataCategory/sf:objectAssignment", ns) or \
                      root.findall(".//dataCategory/objectAssignment")
            for obj in objects:
                obj_name = obj.findtext("sf:object", namespaces=ns) or obj.findtext("object") or ""
                if "Knowledge" in obj_name:
                    knowledge_groups.append(dcg_file.stem)
                    break
        except ET.ParseError as exc:
            issues.append(f"Could not parse Data Category Group file '{dcg_file.name}': {exc}")

    if len(knowledge_groups) > 5:
        issues.append(
            f"Found {len(knowledge_groups)} Data Category Groups assigned to Knowledge: "
            f"{', '.join(knowledge_groups[:8])}{'...' if len(knowledge_groups) > 8 else ''}. "
            "Salesforce Knowledge supports a maximum of 5 active Data Category Groups. "
            "Exceeding this limit will cause activation errors. Consolidate groups or "
            "remove Knowledge object assignment from lower-priority groups."
        )

    return issues


def check_knowledge_page_layouts(manifest_dir: Path) -> list[str]:
    """Warn if Knowledge__kav has no layouts defined."""
    issues: list[str] = []
    layouts_dir = manifest_dir / "layouts"

    if not layouts_dir.exists():
        return issues

    knowledge_layouts = list(layouts_dir.glob("Knowledge__kav-*.layout-meta.xml"))
    knowledge_object_dir = manifest_dir / "objects" / "Knowledge__kav"

    if knowledge_object_dir.exists() and not knowledge_layouts:
        issues.append(
            "No page layouts found for Knowledge__kav (expected files matching "
            "'layouts/Knowledge__kav-*.layout-meta.xml'). Each record type requires "
            "a dedicated page layout to control field visibility per article type. "
            "Retrieve layouts from the org or create them in Setup > Object Manager > Knowledge > Page Layouts."
        )

    return issues


def check_knowledge_base_administration(manifest_dir: Path) -> list[str]:
    """Run all Knowledge Base Administration checks and return a list of issues."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_knowledge_record_types(manifest_dir))
    issues.extend(check_knowledge_validation_status(manifest_dir))
    issues.extend(check_knowledge_approval_processes(manifest_dir))
    issues.extend(check_data_category_groups(manifest_dir))
    issues.extend(check_knowledge_page_layouts(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_knowledge_base_administration(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
