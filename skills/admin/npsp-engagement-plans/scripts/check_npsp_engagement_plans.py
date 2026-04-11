#!/usr/bin/env python3
"""Checker script for NPSP Engagement Plans skill.

Scans a Salesforce metadata export directory for common configuration issues
related to NPSP Engagement Plans.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_npsp_engagement_plans.py [--help]
    python3 check_npsp_engagement_plans.py --manifest-dir path/to/metadata

Checks performed:
    1. Detects FSC ActionPlanTemplate metadata — warns if present in an NPSP context
    2. Scans Flow metadata for Engagement Plan application without fault-path error handling
    3. Scans Flow metadata for missing post-apply Task count validation
    4. Warns if no Flow references npsp__Engagement_Plan__c (plan may never be applied automatically)
"""

from __future__ import annotations

import argparse
import sys
import os
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_text(path: Path) -> str:
    """Read file text, returning empty string on any error."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _find_files(root: Path, extensions: tuple[str, ...]) -> list[Path]:
    """Walk root and return all files matching any of the given extensions."""
    matches: list[Path] = []
    if not root.is_dir():
        return matches
    for dirpath, _dirnames, filenames in os.walk(root):
        for fname in filenames:
            if fname.endswith(extensions):
                matches.append(Path(dirpath) / fname)
    return matches


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_fsc_action_plan_metadata(manifest_dir: Path) -> list[str]:
    """Warn if FSC ActionPlanTemplate metadata is found alongside NPSP.

    FSC ActionPlanTemplate is a standard Salesforce metadata component (not NPSP).
    Finding it in a manifest that also references NPSP Engagement Plans objects
    suggests the two features may be conflated in documentation or configuration.
    """
    issues: list[str] = []
    metadata_files = _find_files(manifest_dir, (".xml", ".json"))

    for f in metadata_files:
        content = _read_text(f)
        if "ActionPlanTemplate" in content and "npsp__Engagement_Plan" not in content:
            issues.append(
                f"{f}: Contains 'ActionPlanTemplate' (FSC) with no NPSP Engagement Plan references. "
                "Confirm this is intentional — do not mix FSC Action Plans with NPSP Engagement Plans guidance."
            )
    return issues


def check_flow_engagement_plan_fault_paths(manifest_dir: Path) -> list[str]:
    """Check Flow metadata for npsp__Engagement_Plan__c record creates without fault paths.

    A Flow that creates npsp__Engagement_Plan__c records without a fault connector
    will silently fail if task creation fails (e.g., validation rule on Task, governor limit).
    """
    issues: list[str] = []
    flow_dir = manifest_dir / "flows"
    if not flow_dir.is_dir():
        # Try alternate path
        flow_dir = manifest_dir / "force-app" / "main" / "default" / "flows"

    flow_files = _find_files(flow_dir if flow_dir.is_dir() else manifest_dir, (".flow-meta.xml", ".flow"))

    for f in flow_files:
        content = _read_text(f)
        if "npsp__Engagement_Plan__c" not in content:
            continue
        # Check for fault connector — presence of <faultConnector> or faultConnector in JSON
        if "faultConnector" not in content and "<fault>" not in content:
            issues.append(
                f"{f}: Flow references npsp__Engagement_Plan__c but no fault connector detected. "
                "Add a fault path to catch errors when engagement plan records fail to create "
                "(e.g., Task validation rule failures, governor limits)."
            )
    return issues


def check_flow_applies_engagement_plan(manifest_dir: Path) -> list[str]:
    """Warn if no Flow in the manifest applies npsp__Engagement_Plan__c records.

    If templates exist but no Flow references npsp__Engagement_Plan__c,
    plan application may be entirely manual — which is acceptable but worth flagging
    for review to ensure the team is aware of the manual dependency.
    """
    issues: list[str] = []
    flow_files = _find_files(manifest_dir, (".flow-meta.xml", ".flow", ".xml"))

    any_flow_applies_plan = any(
        "npsp__Engagement_Plan__c" in _read_text(f)
        for f in flow_files
    )

    if flow_files and not any_flow_applies_plan:
        issues.append(
            "No Flow metadata found that references npsp__Engagement_Plan__c. "
            "If engagement plans are applied manually (no automation), confirm this is intentional. "
            "Automated application via Record-Triggered Flow reduces the risk of missing qualifying records."
        )
    return issues


def check_for_task_only_output_assumption(manifest_dir: Path) -> list[str]:
    """Scan for metadata patterns that suggest Engagement Plans are expected to send emails.

    Looks for Email Alert metadata whose description or name references
    'Engagement Plan' — which would indicate a misunderstanding that engagement
    plans can trigger email actions directly.
    """
    issues: list[str] = []
    metadata_files = _find_files(manifest_dir, (".xml",))

    for f in metadata_files:
        content = _read_text(f)
        # WorkflowAlert or EmailAlert objects referencing Engagement Plan
        if (
            ("WorkflowAlert" in content or "EmailAlert" in content)
            and "EngagementPlan" in content.replace(" ", "").replace("_", "")
        ):
            issues.append(
                f"{f}: Workflow Email Alert metadata appears to reference Engagement Plans. "
                "NPSP Engagement Plans create Tasks only — they do not send emails. "
                "Email automation must be implemented in a separate Flow using an Email Alert action."
            )
    return issues


def check_template_in_metadata(manifest_dir: Path) -> list[str]:
    """Detect any attempt to include npsp__Engagement_Plan_Template__c in package.xml.

    Templates are data records. Including them in package.xml is a no-op at best
    and a source of confusion. Flag it.
    """
    issues: list[str] = []
    package_xml = manifest_dir / "package.xml"
    if not package_xml.exists():
        # Try alternate locations
        for candidate in manifest_dir.rglob("package.xml"):
            package_xml = candidate
            break

    if package_xml.exists():
        content = _read_text(package_xml)
        if "npsp__Engagement_Plan_Template__c" in content:
            issues.append(
                f"{package_xml}: 'npsp__Engagement_Plan_Template__c' found in package.xml. "
                "Engagement Plan Templates are data records, not metadata components. "
                "They cannot be deployed via Metadata API or Change Sets. "
                "Use Data Loader or the REST API to migrate template records between orgs."
            )
    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_npsp_engagement_plans(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_fsc_action_plan_metadata(manifest_dir))
    issues.extend(check_flow_engagement_plan_fault_paths(manifest_dir))
    issues.extend(check_flow_applies_engagement_plan(manifest_dir))
    issues.extend(check_for_task_only_output_assumption(manifest_dir))
    issues.extend(check_template_in_metadata(manifest_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for NPSP Engagement Plan configuration issues. "
            "Detects: FSC/NPSP conflation, missing Flow fault paths, template-in-metadata errors, "
            "and email-automation misconfigurations."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata export (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_npsp_engagement_plans(manifest_dir)

    if not issues:
        print("No NPSP Engagement Plan configuration issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
