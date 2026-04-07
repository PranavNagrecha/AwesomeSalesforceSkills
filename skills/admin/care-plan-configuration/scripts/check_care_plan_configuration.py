#!/usr/bin/env python3
"""Checker script for Care Plan Configuration skill.

Checks Salesforce org metadata for common care plan configuration issues,
with a focus on the ICM model (ActionPlanTemplate + PGI library) and the
legacy managed-package model (CarePlanTemplate__c + Case Tasks).

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_care_plan_configuration.py [--help]
    python3 check_care_plan_configuration.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check care plan configuration metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_files(root: Path, pattern: str) -> list[Path]:
    """Return all files matching a glob pattern under root."""
    return list(root.rglob(pattern))


def parse_xml_safe(path: Path) -> ET.Element | None:
    """Parse an XML file and return the root element, or None on error."""
    try:
        tree = ET.parse(path)
        return tree.getroot()
    except ET.ParseError:
        return None


def strip_ns(tag: str) -> str:
    """Strip XML namespace prefix from a tag name."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def element_text(element: ET.Element, tag: str) -> str:
    """Return stripped text of a child element, or empty string if absent."""
    child = element.find(f".//{tag}")
    if child is None:
        # Try with namespace stripping via iteration
        for el in element.iter():
            if strip_ns(el.tag) == tag:
                return (el.text or "").strip()
        return ""
    return (child.text or "").strip()


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_permission_sets(manifest_dir: Path, issues: list[str]) -> None:
    """Warn if HealthCloudICM permission set is absent but ActionPlanTemplate metadata is present."""
    apt_files = find_files(manifest_dir, "ActionPlanTemplate*.object-meta.xml")
    apt_files += find_files(manifest_dir, "ActionPlanTemplate*.recordType-meta.xml")

    ps_files = find_files(manifest_dir, "*.permissionset-meta.xml")
    ps_names = {f.stem.replace(".permissionset", "") for f in ps_files}

    if apt_files:
        if "HealthCloudICM" not in ps_names:
            issues.append(
                "ActionPlanTemplate metadata found but 'HealthCloudICM' permission set is absent. "
                "Care coordinators need HealthCloudICM to create and edit ICM care plans."
            )
        if "HealthCloudFoundation" not in ps_names:
            issues.append(
                "ActionPlanTemplate metadata found but 'HealthCloudFoundation' permission set is absent. "
                "HealthCloudFoundation is required as the base Health Cloud permission set."
            )


def check_legacy_references_in_flows(manifest_dir: Path, issues: list[str]) -> None:
    """Detect legacy CarePlanTemplate__c references inside Flow metadata."""
    flow_files = find_files(manifest_dir, "*.flow-meta.xml")
    legacy_indicators = ["CarePlanTemplate__c", "CarePlanTemplateTask__c"]

    for flow_file in flow_files:
        content = flow_file.read_text(encoding="utf-8", errors="replace")
        for indicator in legacy_indicators:
            if indicator in content:
                issues.append(
                    f"Flow '{flow_file.name}' references legacy care plan object '{indicator}'. "
                    "If this org uses the ICM model, migrate Flow logic to CarePlan/ActionPlanTemplate objects."
                )
                break  # one warning per flow is enough


def check_action_plan_template_status(manifest_dir: Path, issues: list[str]) -> None:
    """Warn if ActionPlanTemplate records have Draft status in production-like metadata."""
    apt_files = find_files(manifest_dir, "ActionPlanTemplate*.object-meta.xml")

    for apt_file in apt_files:
        root = parse_xml_safe(apt_file)
        if root is None:
            continue
        status = element_text(root, "status")
        if status.lower() == "draft":
            issues.append(
                f"ActionPlanTemplate metadata in '{apt_file.name}' has status 'Draft'. "
                "Templates must be set to 'Active' before care coordinators can instantiate them."
            )


def check_flows_for_missing_pgi_setup(manifest_dir: Path, issues: list[str]) -> None:
    """Detect Flows that create CarePlan records but do not reference ProblemDefinition or GoalDefinition."""
    flow_files = find_files(manifest_dir, "*.flow-meta.xml")

    for flow_file in flow_files:
        content = flow_file.read_text(encoding="utf-8", errors="replace")
        creates_care_plan = "CarePlan" in content and ("recordCreate" in content or "RecordCreate" in content)
        references_pgi = "ProblemDefinition" in content or "GoalDefinition" in content

        if creates_care_plan and not references_pgi:
            issues.append(
                f"Flow '{flow_file.name}' creates CarePlan records but does not reference "
                "ProblemDefinition or GoalDefinition. Verify PGI library records are linked; "
                "omitting PGI links results in care plans with no standardized problems or goals."
            )


def check_case_task_care_plan_references(manifest_dir: Path, issues: list[str]) -> None:
    """Warn if report or flow metadata references Case-linked care plan tasks (legacy pattern)."""
    report_files = find_files(manifest_dir, "*.report-meta.xml")
    legacy_task_indicators = ["CarePlanTask", "Type = 'CarePlanTask'", "CarePlanTask__c"]

    for rpt_file in report_files:
        content = rpt_file.read_text(encoding="utf-8", errors="replace")
        for indicator in legacy_task_indicators:
            if indicator in content:
                issues.append(
                    f"Report '{rpt_file.name}' references legacy care plan task pattern '{indicator}'. "
                    "If this org uses the ICM model, update reports to use CarePlanActivity instead."
                )
                break


def check_conflicting_care_plan_architectures(manifest_dir: Path, issues: list[str]) -> None:
    """Warn if metadata for both ICM and legacy care plan models is present simultaneously."""
    has_icm = bool(
        find_files(manifest_dir, "ActionPlanTemplate*.object-meta.xml")
        or find_files(manifest_dir, "ActionPlanTemplate*.recordType-meta.xml")
    )

    # Legacy indicators: presence of CarePlanTemplate__c custom object or permission set
    has_legacy = False
    for flow_file in find_files(manifest_dir, "*.flow-meta.xml"):
        content = flow_file.read_text(encoding="utf-8", errors="replace")
        if "CarePlanTemplate__c" in content:
            has_legacy = True
            break

    if not has_legacy:
        for ps_file in find_files(manifest_dir, "*.permissionset-meta.xml"):
            content = ps_file.read_text(encoding="utf-8", errors="replace")
            if "HealthCloudCarePlan" in content and "CarePlanTemplate" in content:
                has_legacy = True
                break

    if has_icm and has_legacy:
        issues.append(
            "Metadata contains references to both ICM care plan objects (ActionPlanTemplate) "
            "and legacy care plan objects (CarePlanTemplate__c). Running both architectures "
            "simultaneously without a migration plan creates split care plan workflows. "
            "Confirm this is an intentional migration-in-progress state."
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_care_plan_configuration(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    check_permission_sets(manifest_dir, issues)
    check_legacy_references_in_flows(manifest_dir, issues)
    check_action_plan_template_status(manifest_dir, issues)
    check_flows_for_missing_pgi_setup(manifest_dir, issues)
    check_case_task_care_plan_references(manifest_dir, issues)
    check_conflicting_care_plan_architectures(manifest_dir, issues)

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_care_plan_configuration(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
