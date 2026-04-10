#!/usr/bin/env python3
"""Checker script for Campaign Planning And Attribution skill.

Checks Salesforce metadata for common Campaign Hierarchy, Customizable Campaign
Influence (CCI), and Campaign Member Status configuration issues.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_campaign_planning_and_attribution.py [--help]
    python3 check_campaign_planning_and_attribution.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# Campaign Member Status values required by MCAE campaign connector.
# Source: SF Help — MCAE Campaign Connector and Attribution setup.
MCAE_REQUIRED_CAMPAIGN_MEMBER_STATUSES = {"Sent", "Opened", "Clicked", "Responded"}

# Campaign object API name as used in metadata file paths.
CAMPAIGN_OBJECT_NAME = "Campaign"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Campaign attribution and hierarchy configuration metadata "
            "for common issues (CCI, Campaign Member Status, hierarchy depth)."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Individual check functions
# ---------------------------------------------------------------------------


def check_campaign_member_statuses(manifest_dir: Path) -> list[str]:
    """Check that Campaign Member Status picklist includes MCAE-required values.

    Looks for Campaign.object-meta.xml or objects/Campaign/Campaign.object-meta.xml
    and validates picklist values.
    """
    issues: list[str] = []

    candidate_paths = [
        manifest_dir / "objects" / "Campaign" / "Campaign.object-meta.xml",
        manifest_dir / "Campaign.object-meta.xml",
    ]
    object_file: Path | None = next(
        (p for p in candidate_paths if p.exists()), None
    )

    if object_file is None:
        # Not present in this manifest — skip rather than flag
        return issues

    try:
        tree = ET.parse(object_file)
    except ET.ParseError as exc:
        issues.append(f"Campaign object metadata could not be parsed: {exc}")
        return issues

    root = tree.getroot()
    ns = {"sf": "http://soap.sforce.com/2006/04/metadata"}

    found_statuses: set[str] = set()
    for field in root.findall(".//sf:fields", ns):
        full_name_el = field.find("sf:fullName", ns)
        if full_name_el is None or full_name_el.text != "Status":
            continue
        for value_el in field.findall(".//sf:value", ns):
            label_el = value_el.find("sf:label", ns)
            if label_el is not None and label_el.text:
                found_statuses.add(label_el.text.strip())

    missing = MCAE_REQUIRED_CAMPAIGN_MEMBER_STATUSES - found_statuses
    if missing:
        issues.append(
            f"Campaign Member Status picklist is missing values required by MCAE: "
            f"{', '.join(sorted(missing))}. Add these before enabling the MCAE "
            f"campaign connector to avoid silent attribution data loss."
        )

    return issues


def check_campaign_hierarchy_depth(manifest_dir: Path) -> list[str]:
    """Warn if any Campaign record metadata indicates unusual nesting.

    In practice, hierarchy depth cannot be fully validated from static metadata
    alone. This check inspects any exported Campaign CSV or manifest data files
    for obvious depth indicators.

    This is a best-effort check; definitive hierarchy depth validation requires
    querying Salesforce directly.
    """
    issues: list[str] = []

    # Look for any exported Campaign data file (e.g., from a data export or ETL)
    data_candidates = list(manifest_dir.glob("**/*[Cc]ampaign*.csv"))
    if not data_candidates:
        return issues  # Nothing to validate statically

    for data_file in data_candidates[:5]:  # Cap at 5 files to avoid long runs
        try:
            lines = data_file.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue

        if not lines:
            continue

        header = lines[0].lower()
        if "parentid" not in header and "parent_id" not in header:
            continue

        # Count campaigns that appear as parent IDs to estimate hierarchy usage.
        # We can't compute actual depth without graph traversal, but a large
        # number of unique ParentId values is a meaningful signal.
        parent_id_index = -1
        for i, col in enumerate(header.split(",")):
            if col.strip() in ("parentid", "parent_id"):
                parent_id_index = i
                break

        if parent_id_index == -1:
            continue

        nested_count = 0
        for line in lines[1:]:
            cols = line.split(",")
            if parent_id_index < len(cols) and cols[parent_id_index].strip():
                nested_count += 1

        if nested_count > 0:
            issues.append(
                f"{data_file.name}: {nested_count} Campaign records have a ParentId set. "
                f"Verify that no hierarchy path exceeds 5 levels — Salesforce enforces "
                f"this limit at the platform layer and will reject deeper nesting."
            )

    return issues


def check_cci_model_presence(manifest_dir: Path) -> list[str]:
    """Check for CampaignInfluenceModel metadata files.

    If no CampaignInfluenceModel metadata is found and CCI appears to be in scope
    (inferred from the presence of Campaign metadata), emit an advisory.
    """
    issues: list[str] = []

    model_files = list(
        manifest_dir.glob("**/*CampaignInfluenceModel*")
    ) + list(
        manifest_dir.glob("**/*campaignInfluenceModel*")
    )

    campaign_files = list(manifest_dir.glob("**/Campaign*"))

    if campaign_files and not model_files:
        issues.append(
            "No CampaignInfluenceModel metadata found. If Customizable Campaign Influence "
            "(CCI) is in scope, at least one model must be configured in Setup before "
            "CampaignInfluence records will be created. "
            "Check Setup > Campaign Influence > Customizable Campaign Influence."
        )

    return issues


def check_opportunity_contact_role_reminder(manifest_dir: Path) -> list[str]:
    """Emit a reminder about Contact Role requirements for CCI.

    This is a policy-level check. Static metadata cannot confirm whether
    Contact Roles are populated at runtime, but we can check for validation
    rules or Flows that enforce Contact Role creation.
    """
    issues: list[str] = []

    validation_rules = list(manifest_dir.glob("**/Opportunity.validationRules*"))
    flows_with_contact_role = list(manifest_dir.glob("**/*[Cc]ontact[Rr]ole*"))

    if not validation_rules and not flows_with_contact_role:
        issues.append(
            "No Opportunity validation rules or Contact Role automation detected. "
            "Customizable Campaign Influence (CCI) requires at least one Contact Role "
            "on each Opportunity to produce CampaignInfluence records. "
            "Consider adding a validation rule or Flow that enforces Contact Role "
            "population before CCI attribution data is relied upon."
        )

    return issues


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------


def check_campaign_planning_and_attribution(manifest_dir: Path) -> list[str]:
    """Run all checks and return a flat list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_campaign_member_statuses(manifest_dir))
    issues.extend(check_campaign_hierarchy_depth(manifest_dir))
    issues.extend(check_cci_model_presence(manifest_dir))
    issues.extend(check_opportunity_contact_role_reminder(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_campaign_planning_and_attribution(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
