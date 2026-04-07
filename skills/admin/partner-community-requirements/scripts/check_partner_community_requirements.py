#!/usr/bin/env python3
"""Checker script for Partner Community Requirements skill.

Inspects Salesforce metadata in a local SFDX project or retrieved metadata
directory for common PRM configuration issues.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_partner_community_requirements.py [--help]
    python3 check_partner_community_requirements.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
import xml.etree.ElementTree as ET


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check PRM-related metadata for common partner community "
            "requirements issues."
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

def _xml_text(path: Path, tag: str) -> list[str]:
    """Return all text values for *tag* in the XML file at *path*.

    Returns an empty list if the file cannot be parsed.
    """
    try:
        tree = ET.parse(path)
    except ET.ParseError:
        return []
    return [el.text or "" for el in tree.iter() if el.tag.endswith(tag)]


def _xml_tag_exists(path: Path, tag: str) -> bool:
    try:
        tree = ET.parse(path)
    except ET.ParseError:
        return False
    return any(el.tag.endswith(tag) for el in tree.iter())


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_partner_account_flag(manifest_dir: Path) -> list[str]:
    """Warn if Account object metadata does not have IsPartner as a tracked field.

    A missing IsPartner field definition can indicate the metadata package
    was retrieved without the Partner Account checkbox enabled.
    """
    issues: list[str] = []
    account_object = manifest_dir / "objects" / "Account" / "Account.object-meta.xml"
    # Also check flat MDAPI layout
    account_mdapi = manifest_dir / "objects" / "Account.object"

    found_file: Path | None = None
    if account_object.exists():
        found_file = account_object
    elif account_mdapi.exists():
        found_file = account_mdapi

    if found_file is None:
        # Cannot check — Account metadata not present in this directory
        return issues

    names = _xml_text(found_file, "fullName")
    if "IsPartner" not in names:
        issues.append(
            "Account metadata does not include 'IsPartner' field. "
            "Ensure the Partner Account checkbox is enabled in the org before "
            "provisioning partner Experience Cloud users."
        )
    return issues


def check_lead_duplicate_rules(manifest_dir: Path) -> list[str]:
    """Warn if no duplicate rules referencing Lead are present in the metadata."""
    issues: list[str] = []
    dup_dir = manifest_dir / "duplicateRules"
    if not dup_dir.exists():
        issues.append(
            "No 'duplicateRules' metadata directory found. "
            "Deal registration requires Lead duplicate rules to prevent "
            "channel conflict from multi-registration of the same prospect. "
            "Verify duplicate rules are configured and included in the package."
        )
        return issues

    lead_dup_rules = list(dup_dir.glob("Lead*.duplicateRule-meta.xml"))
    if not lead_dup_rules:
        issues.append(
            "No Lead duplicate rules found in 'duplicateRules/'. "
            "Deal registration requires at least one Lead duplicate rule "
            "(e.g., matching on Company + Email) to prevent partners from "
            "registering the same deal multiple times."
        )
    return issues


def check_approval_processes(manifest_dir: Path) -> list[str]:
    """Warn if no Lead approval process is present (deal registration requires one)."""
    issues: list[str] = []
    ap_dir = manifest_dir / "approvalProcesses"
    if not ap_dir.exists():
        issues.append(
            "No 'approvalProcesses' metadata directory found. "
            "Deal registration requires a Lead approval process. "
            "Verify approval processes are included in the metadata package."
        )
        return issues

    lead_aps = list(ap_dir.glob("Lead.*approvalProcess-meta.xml"))
    if not lead_aps:
        issues.append(
            "No Lead approval processes found in 'approvalProcesses/'. "
            "Deal registration in Partner Central requires an approval process "
            "on the Lead object (entry criteria: Status = 'Submitted for Registration'). "
            "Confirm the approval process exists in the org and is included in this package."
        )
    return issues


def check_queue_based_approval_routing(manifest_dir: Path) -> list[str]:
    """Warn if Lead approval processes route to a specific user instead of a queue."""
    issues: list[str] = []
    ap_dir = manifest_dir / "approvalProcesses"
    if not ap_dir.exists():
        return issues

    for ap_file in ap_dir.glob("Lead.*approvalProcess-meta.xml"):
        # Look for assignedTo elements that are type 'user' (named-user routing)
        try:
            tree = ET.parse(ap_file)
        except ET.ParseError:
            continue
        root = tree.getroot()
        for step in root.iter():
            if step.tag.endswith("approvalStep"):
                assignee_type = None
                for child in step:
                    if child.tag.endswith("assigneeType"):
                        assignee_type = (child.text or "").lower()
                if assignee_type == "user":
                    issues.append(
                        f"{ap_file.name}: Approval step routes to a named user "
                        f"('assigneeType = user'). Queue-based routing is strongly "
                        f"preferred for deal registration approvals to avoid single "
                        f"points of failure when channel managers are absent."
                    )
    return issues


def check_experience_cloud_template(manifest_dir: Path) -> list[str]:
    """Warn if Experience Cloud sites present do not reference Partner Central template."""
    issues: list[str] = []
    sites_dir = manifest_dir / "sites"
    network_dir = manifest_dir / "networks"

    site_files = list(sites_dir.glob("*.site-meta.xml")) if sites_dir.exists() else []
    network_files = (
        list(network_dir.glob("*.network-meta.xml")) if network_dir.exists() else []
    )

    if not site_files and not network_files:
        # No Experience Cloud metadata in package — cannot check
        return issues

    prm_template_keywords = {"partnercentral", "partner_central", "prm"}
    for nf in network_files:
        try:
            tree = ET.parse(nf)
        except ET.ParseError:
            continue
        template_vals = [
            (el.text or "").lower().replace(" ", "_")
            for el in tree.iter()
            if el.tag.endswith("template") or el.tag.endswith("networkTemplate")
        ]
        if template_vals and not any(
            any(kw in v for kw in prm_template_keywords) for v in template_vals
        ):
            issues.append(
                f"{nf.name}: Experience Cloud site does not appear to use the "
                f"Partner Central template (template value: {template_vals}). "
                f"PRM features (deal registration, lead inbox, MDF) require "
                f"the Partner Central template."
            )
    return issues


def check_mdf_custom_objects(manifest_dir: Path) -> list[str]:
    """Warn if MDF-related custom objects are missing when the package has PRM content."""
    issues: list[str] = []
    objects_dir = manifest_dir / "objects"
    if not objects_dir.exists():
        return issues

    existing_objects = {p.name.lower() for p in objects_dir.iterdir()}
    mdf_indicators = ["mdf_budget", "mdf_request", "mdf_claim", "mdfrequest", "mdfclaim"]

    has_partner_network = any(
        "partner" in name for name in existing_objects
    )
    if not has_partner_network:
        return issues  # Not a PRM package — skip MDF check

    has_mdf = any(
        any(ind in obj_name for ind in mdf_indicators) for obj_name in existing_objects
    )
    if not has_mdf:
        issues.append(
            "No MDF custom objects detected (expected names containing 'MDF_Budget', "
            "'MDF_Request', or 'MDF_Claim'). "
            "MDF tracking has no standard Salesforce object in base PRM. "
            "If MDF is a requirement, ensure the custom object data model is designed "
            "and included in this package, or confirm that MDF is tracked externally."
        )
    return issues


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def check_partner_community_requirements(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_partner_account_flag(manifest_dir))
    issues.extend(check_lead_duplicate_rules(manifest_dir))
    issues.extend(check_approval_processes(manifest_dir))
    issues.extend(check_queue_based_approval_routing(manifest_dir))
    issues.extend(check_experience_cloud_template(manifest_dir))
    issues.extend(check_mdf_custom_objects(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_partner_community_requirements(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
