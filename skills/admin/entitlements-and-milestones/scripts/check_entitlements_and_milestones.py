#!/usr/bin/env python3
"""Checker script for Entitlements and Milestones skill.

Validates Salesforce metadata exports for common entitlement management
configuration issues: missing business hours references, absent entitlement
process definitions, milestone action gaps, and entitlement template
references that depend on Lightning-incompatible Classic UI patterns.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_entitlements_and_milestones.py [--help]
    python3 check_entitlements_and_milestones.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Entitlements and Milestones metadata for common configuration issues."
        ),
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

def _find_xml_files(root: Path, suffix: str) -> list[Path]:
    """Return all XML files under root matching the given suffix."""
    return list(root.rglob(f"*{suffix}"))


def _parse_xml_safe(path: Path) -> ET.Element | None:
    """Parse an XML file and return the root element, or None on error."""
    try:
        tree = ET.parse(path)
        return tree.getroot()
    except ET.ParseError:
        return None


def _tag_local(element: ET.Element) -> str:
    """Strip namespace from an XML tag."""
    tag = element.tag
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _child_text(element: ET.Element, local_name: str) -> str:
    """Return the text of the first child matching local_name, or empty string."""
    for child in element:
        if _tag_local(child) == local_name:
            return (child.text or "").strip()
    return ""


# ---------------------------------------------------------------------------
# Check: entitlement process files exist
# ---------------------------------------------------------------------------

def check_entitlement_process_files_exist(manifest_dir: Path) -> list[str]:
    """Warn if no entitlement process metadata files are found."""
    issues: list[str] = []
    # Salesforce metadata type: EntitlementProcess — files end in .entitlementProcess-meta.xml
    process_files = _find_xml_files(manifest_dir, ".entitlementProcess-meta.xml")
    if not process_files:
        issues.append(
            "No entitlement process metadata files found "
            "(*entitlementProcess-meta.xml). "
            "If Entitlement Management is in use, at least one process should exist. "
            "Verify the metadata package includes the EntitlementProcess type."
        )
    return issues


# ---------------------------------------------------------------------------
# Check: entitlement process has business hours reference
# ---------------------------------------------------------------------------

def check_business_hours_assigned(manifest_dir: Path) -> list[str]:
    """Warn for each entitlement process that has no businessHoursId set."""
    issues: list[str] = []
    process_files = _find_xml_files(manifest_dir, ".entitlementProcess-meta.xml")
    for path in process_files:
        root = _parse_xml_safe(path)
        if root is None:
            issues.append(f"Could not parse entitlement process file: {path.name}")
            continue
        # businessHoursId is optional but absence means 24/7 timing — flag for review
        bh_id = _child_text(root, "businessHoursId")
        if not bh_id:
            process_name = _child_text(root, "name") or path.stem
            issues.append(
                f"Entitlement process '{process_name}' has no businessHoursId set. "
                "Without business hours, milestone timers run 24/7 including weekends. "
                "Confirm this is intentional (e.g., Platinum 24/7 tier) or assign "
                "business hours to pause timers outside coverage windows."
            )
    return issues


# ---------------------------------------------------------------------------
# Check: milestones have at least one warning action
# ---------------------------------------------------------------------------

def check_milestone_warning_actions(manifest_dir: Path) -> list[str]:
    """Warn for entitlement processes where a milestone has no warning actions."""
    issues: list[str] = []
    process_files = _find_xml_files(manifest_dir, ".entitlementProcess-meta.xml")
    for path in process_files:
        root = _parse_xml_safe(path)
        if root is None:
            continue
        process_name = _child_text(root, "name") or path.stem
        # milestoneItems are nested inside the process XML
        for child in root:
            if _tag_local(child) != "milestoneItems":
                continue
            milestone_name = _child_text(child, "name") or "(unnamed)"
            has_warning = False
            for subchild in child:
                if _tag_local(subchild) == "milestoneCriteriaItems":
                    action_type = _child_text(subchild, "triggerType")
                    if action_type and "Warning" in action_type:
                        has_warning = True
                        break
            if not has_warning:
                issues.append(
                    f"Entitlement process '{process_name}', milestone '{milestone_name}' "
                    "has no warning actions configured. "
                    "Add warning actions at 50%/75%/90% elapsed to give agents notice "
                    "before SLA breach."
                )
    return issues


# ---------------------------------------------------------------------------
# Check: entitlement templates reference check
# ---------------------------------------------------------------------------

def check_entitlement_template_files(manifest_dir: Path) -> list[str]:
    """Note if entitlement templates exist, reminding reviewer of Lightning caveat."""
    issues: list[str] = []
    template_files = _find_xml_files(manifest_dir, ".entitlementTemplate-meta.xml")
    if template_files:
        template_names = [p.stem.replace(".entitlementTemplate", "") for p in template_files]
        issues.append(
            f"Entitlement templates found: {', '.join(template_names)}. "
            "REMINDER: In Lightning Experience, attaching templates to products via the "
            "product page UI is not supported. "
            "Verify a Record-Triggered Flow exists to create entitlements from these "
            "templates when opportunities close or orders activate. "
            "Check skills/admin/entitlements-and-milestones/references/gotchas.md for details."
        )
    return issues


# ---------------------------------------------------------------------------
# Check: flow references entitlement creation (heuristic)
# ---------------------------------------------------------------------------

def check_flow_entitlement_creation(manifest_dir: Path) -> list[str]:
    """Heuristic: warn if no Flow appears to set Case.EntitlementId."""
    issues: list[str] = []
    flow_files = _find_xml_files(manifest_dir, ".flow-meta.xml")
    entitlement_id_flows: list[str] = []
    for path in flow_files:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "EntitlementId" in content or "entitlementId" in content:
            entitlement_id_flows.append(path.stem)

    if not entitlement_id_flows:
        issues.append(
            "No Flow metadata files found that reference EntitlementId. "
            "Cases created via Email-to-Case, Web-to-Case, or the API will not have "
            "an entitlement applied unless a Flow populates Case.EntitlementId. "
            "Without this, milestone processes will not trigger on automated case creation."
        )
    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_entitlements_and_milestones(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_entitlement_process_files_exist(manifest_dir))
    issues.extend(check_business_hours_assigned(manifest_dir))
    issues.extend(check_milestone_warning_actions(manifest_dir))
    issues.extend(check_entitlement_template_files(manifest_dir))
    issues.extend(check_flow_entitlement_creation(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_entitlements_and_milestones(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
