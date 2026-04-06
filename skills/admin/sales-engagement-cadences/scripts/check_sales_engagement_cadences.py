#!/usr/bin/env python3
"""Checker script for Sales Engagement Cadences skill.

Inspects a Salesforce metadata project directory for common Sales Engagement
configuration anti-patterns. Uses stdlib only — no pip dependencies.

Checks performed:
  1. Detects PermissionSet XML files missing SalesEngagementUser or
     SalesEngagementManager user permission assignments.
  2. Detects Flow XML files that reference "High Velocity Sales" (legacy name)
     instead of "Sales Engagement" — signals stale automation.
  3. Detects email templates that have no subject line (blank subject causes
     cadence email steps to send with empty subjects).
  4. Detects permission sets named with legacy HVS terminology.
  5. Warns if no email templates are found at all (cadence email steps will fail).

Usage:
    python3 check_sales_engagement_cadences.py [--help]
    python3 check_sales_engagement_cadences.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for Sales Engagement cadence configuration issues."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata project (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_permission_sets(manifest_dir: Path) -> list[str]:
    """Warn if no permission set grants SalesEngagementUser or SalesEngagementManager."""
    issues: list[str] = []
    ps_dir = manifest_dir / "permissionsets"
    if not ps_dir.exists():
        return issues  # No permissionsets folder — skip silently

    found_user_ps = False
    found_manager_ps = False

    for ps_file in ps_dir.glob("*.permissionset-meta.xml"):
        try:
            tree = ET.parse(ps_file)
        except ET.ParseError:
            issues.append(f"Could not parse permission set XML: {ps_file.name}")
            continue

        root = tree.getroot()
        ns = ""
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0] + "}"

        for up in root.findall(f"{ns}userPermissions"):
            name_el = up.find(f"{ns}name")
            enabled_el = up.find(f"{ns}enabled")
            if name_el is None or enabled_el is None:
                continue
            if name_el.text == "SalesEngagementUser" and enabled_el.text == "true":
                found_user_ps = True
            if name_el.text == "SalesEngagementManager" and enabled_el.text == "true":
                found_manager_ps = True

    if not found_user_ps:
        issues.append(
            "No permission set found that grants 'SalesEngagementUser'. "
            "Reps require this permission set to access the Work Queue."
        )
    if not found_manager_ps:
        issues.append(
            "No permission set found that grants 'SalesEngagementManager'. "
            "Team leads require this to create and manage cadences."
        )
    return issues


def check_flows_for_legacy_hvs_references(manifest_dir: Path) -> list[str]:
    """Flag Flow XML files that reference legacy 'High Velocity Sales' terminology."""
    issues: list[str] = []
    flows_dir = manifest_dir / "flows"
    if not flows_dir.exists():
        return issues

    legacy_terms = ["High Velocity Sales", "HighVelocitySales", "HVS"]

    for flow_file in flows_dir.glob("*.flow-meta.xml"):
        try:
            content = flow_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for term in legacy_terms:
            if term in content:
                issues.append(
                    f"Flow '{flow_file.name}' contains legacy term '{term}'. "
                    "Update references to 'Sales Engagement' to reflect current product name."
                )
                break  # One warning per file

    return issues


def check_email_templates(manifest_dir: Path) -> list[str]:
    """Warn if no email templates exist, or if any template has a blank subject."""
    issues: list[str] = []
    templates_dir = manifest_dir / "emailtemplates"
    if not templates_dir.exists():
        issues.append(
            "No 'emailtemplates' directory found in manifest. "
            "Email steps in cadences require email templates to be deployed. "
            "Cadences with email steps will fail at runtime if templates are missing."
        )
        return issues

    template_files = list(templates_dir.glob("*.email-meta.xml"))
    if not template_files:
        issues.append(
            "No email templates found in emailtemplates/. "
            "Cadence email steps will fail at runtime without templates."
        )
        return issues

    for tmpl_file in template_files:
        try:
            tree = ET.parse(tmpl_file)
        except ET.ParseError:
            issues.append(f"Could not parse email template XML: {tmpl_file.name}")
            continue

        root = tree.getroot()
        ns = ""
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0] + "}"

        subject_el = root.find(f"{ns}subject")
        if subject_el is None or not (subject_el.text or "").strip():
            issues.append(
                f"Email template '{tmpl_file.stem}' has a blank or missing subject line. "
                "Cadence email steps using this template will send with an empty subject."
            )

    return issues


def check_no_legacy_permission_set_names(manifest_dir: Path) -> list[str]:
    """Flag permission set files whose names contain legacy HVS terminology."""
    issues: list[str] = []
    ps_dir = manifest_dir / "permissionsets"
    if not ps_dir.exists():
        return issues

    legacy_fragments = ["HighVelocitySales", "HVS", "High_Velocity_Sales"]
    for ps_file in ps_dir.glob("*.permissionset-meta.xml"):
        for frag in legacy_fragments:
            if frag.lower() in ps_file.stem.lower():
                issues.append(
                    f"Permission set '{ps_file.stem}' appears to use legacy High Velocity Sales "
                    "naming. Rename to reflect current 'Sales Engagement' product name to avoid "
                    "confusion."
                )
                break

    return issues


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def check_sales_engagement_cadences(manifest_dir: Path) -> list[str]:
    """Run all checks and return a combined list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_permission_sets(manifest_dir))
    issues.extend(check_flows_for_legacy_hvs_references(manifest_dir))
    issues.extend(check_email_templates(manifest_dir))
    issues.extend(check_no_legacy_permission_set_names(manifest_dir))

    return issues


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_sales_engagement_cadences(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
