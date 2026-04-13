#!/usr/bin/env python3
"""Checker script for Donor Lifecycle Requirements skill.

Checks org metadata or configuration relevant to Donor Lifecycle Requirements.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_donor_lifecycle_requirements.py [--help]
    python3 check_donor_lifecycle_requirements.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Donor Lifecycle Requirements configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def find_files_recursive(root: Path, pattern: str) -> list[Path]:
    """Return all files matching a glob pattern under root."""
    return list(root.rglob(pattern))


def check_npsp_namespace_objects(manifest_dir: Path, issues: list[str]) -> None:
    """Check for npsp namespace objects (npe01__*, npo02__*)."""
    all_object_files = find_files_recursive(manifest_dir, "*.object-meta.xml")
    all_field_files = find_files_recursive(manifest_dir, "*.field-meta.xml")
    all_apex_files = find_files_recursive(manifest_dir, "*.cls")

    all_names = " ".join(f.name for f in all_object_files + all_field_files)
    all_apex = " ".join(
        f.read_text(encoding="utf-8", errors="replace") for f in all_apex_files
    )

    npe01_present = "npe01__" in all_names or "npe01__" in all_apex
    npo02_present = "npo02__" in all_names or "npo02__" in all_apex
    npsp_present = "npsp__" in all_names or "npsp__" in all_apex

    if not npe01_present and not npo02_present and not npsp_present:
        issues.append(
            "No NPSP namespace references (npe01__, npo02__, npsp__) found in manifest. "
            "Donor lifecycle design for NPSP requires the NPSP managed package to be installed. "
            "npe01__ provides Opportunity contact roles (soft credits, primary donor). "
            "npo02__ provides household rollup fields (TotalGifts, NumberOfGifts, LastOppDate) "
            "that power LYBUNT/SYBUNT reports and donor upgrade identification. "
            "If this is a Nonprofit Cloud (NPC) org, NPSP namespace objects are not present — "
            "use NPC Actionable Segmentation instead of NPSP Moves Management."
        )
    else:
        found = [ns for ns, present in [("npe01__", npe01_present), ("npo02__", npo02_present), ("npsp__", npsp_present)] if present]
        print(f"  OK: NPSP namespace signals detected: {found}")


def check_engagement_plan_templates(manifest_dir: Path, issues: list[str]) -> None:
    """Check for Engagement Plan Template metadata (NPSP Moves Management)."""
    # NPSP Engagement Plan Templates are stored as npsp__Engagement_Plan_Template__c records
    # In metadata, they may appear as CustomMetadata or as exported record data
    ep_files = find_files_recursive(manifest_dir, "*EngagementPlan*")
    ep_template_files = find_files_recursive(manifest_dir, "*Engagement_Plan_Template*")
    ep_detail_files = find_files_recursive(manifest_dir, "*Engagement_Plan_Detail*")

    # Also search for references in flows or automation
    flow_files = find_files_recursive(manifest_dir, "*.flow-meta.xml")
    flows_with_ep = []
    for ff in flow_files:
        content = ff.read_text(encoding="utf-8", errors="replace")
        if "EngagementPlan" in content or "Engagement_Plan" in content:
            flows_with_ep.append(ff.name)

    all_ep_references = ep_files + ep_template_files + ep_detail_files

    if not all_ep_references and not flows_with_ep:
        issues.append(
            "No Engagement Plan Template metadata found in manifest. "
            "NPSP Moves Management relies on Engagement Plans to auto-generate cultivation task sequences "
            "for each donor lifecycle stage (e.g., thank-you call, site visit invite, proposal draft). "
            "Without Engagement Plan Templates, moves management workflows must be executed manually. "
            "If this org is newly provisioned on Nonprofit Cloud (NPC), NPSP Engagement Plans are not "
            "available — NPC uses a different portfolio management paradigm."
        )
    else:
        print(
            f"  OK: Found Engagement Plan references: "
            f"{[f.name for f in all_ep_references]} | Flows: {flows_with_ep}"
        )


def check_opportunity_stage_picklist(manifest_dir: Path, issues: list[str]) -> None:
    """Warn if no Opportunity Stage picklist values map to cultivation stages."""
    # Opportunity Stage picklist is in Opportunity.fieldset or StandardValueSet
    stage_files = find_files_recursive(manifest_dir, "OpportunityStage.standardValueSet-meta.xml")
    opp_field_files = find_files_recursive(manifest_dir, "StageName.field-meta.xml")

    cultivation_keywords = [
        "cultivat", "prospect", "identif", "solicit", "proposal", "qualify",
        "cultivation", "moves", "stewardship", "in cultivation", "pending"
    ]

    def has_cultivation_stages(content: str) -> bool:
        lower = content.lower()
        return any(kw in lower for kw in cultivation_keywords)

    found_cultivation = False
    for f in stage_files + opp_field_files:
        content = f.read_text(encoding="utf-8", errors="replace")
        if has_cultivation_stages(content):
            found_cultivation = True
            print(f"  OK: Cultivation-related Opportunity Stage value(s) found in {f.name}.")
            break

    if not stage_files and not opp_field_files:
        issues.append(
            "No OpportunityStage StandardValueSet or StageName field metadata found in manifest. "
            "NPSP Moves Management tracks donor cultivation through Opportunity Stage progression. "
            "Stage picklist values should include cultivation stages such as: "
            "Prospect Identified, In Cultivation, Proposal Pending, Solicitation Made. "
            "Without cultivation-aligned stages, the pipeline report for portfolio review cannot "
            "distinguish where each relationship stands in the solicitation cycle."
        )
    elif not found_cultivation:
        issues.append(
            "Opportunity Stage picklist metadata found but no cultivation-oriented stage values detected. "
            "NPSP Moves Management requires Opportunity Stages that map to cultivation lifecycle phases "
            "(e.g., 'Prospect Identified', 'In Cultivation', 'Solicitation Made'). "
            "Stages like 'Prospecting', 'Proposal/Price Quote', 'Closed Won' are standard CRM stages "
            "but do not reflect donor relationship cultivation. "
            "Work with the fundraising team to define stages that reflect their moves management process."
        )


def check_lybunt_sybunt_reports(manifest_dir: Path, issues: list[str]) -> None:
    """Warn if LYBUNT/SYBUNT reports don't exist (check for reports with those name patterns)."""
    report_files = find_files_recursive(manifest_dir, "*.report-meta.xml")
    report_folder_files = find_files_recursive(manifest_dir, "reports/**/*.report")

    all_report_files = report_files + report_folder_files

    lybunt_pattern = re.compile(r"lybunt|LYBUNT|last.year.but", re.IGNORECASE)
    sybunt_pattern = re.compile(r"sybunt|SYBUNT|some.year.but", re.IGNORECASE)

    found_lybunt = False
    found_sybunt = False

    for rf in all_report_files:
        name_lower = rf.name.lower()
        if lybunt_pattern.search(name_lower):
            found_lybunt = True
        if sybunt_pattern.search(name_lower):
            found_sybunt = True
        # Also check file content for report label/name
        try:
            content = rf.read_text(encoding="utf-8", errors="replace")
            if lybunt_pattern.search(content):
                found_lybunt = True
            if sybunt_pattern.search(content):
                found_sybunt = True
        except Exception:
            pass

    if not all_report_files:
        issues.append(
            "No report metadata found in manifest. "
            "NPSP lapsed donor re-engagement depends on LYBUNT and SYBUNT reports to identify "
            "donors requiring outreach. These reports are built on Opportunity records filtered by "
            "npsp__LastOppDate__c and giving totals from npo02__ household rollup fields. "
            "Confirm these reports exist in the org and are scheduled to run before each solicitation cycle."
        )
    else:
        if not found_lybunt:
            issues.append(
                "No LYBUNT report found in manifest (report name or label containing 'LYBUNT' or "
                "'Last Year But'). LYBUNT (Last Year But Unfortunately Not This Year) is a critical "
                "NPSP lapsed donor identification report. Without it, annual re-engagement campaigns "
                "cannot systematically identify highest-priority lapsed donors. "
                "NPSP installs sample LYBUNT reports — confirm they are present and use the correct "
                "npsp__LastOppDate__c and npo02__TotalOppAmount__c rollup fields."
            )
        else:
            print("  OK: LYBUNT report reference found.")

        if not found_sybunt:
            issues.append(
                "No SYBUNT report found in manifest (report name or label containing 'SYBUNT' or "
                "'Some Year But'). SYBUNT (Some Year But Unfortunately Not This Year) identifies donors "
                "who gave in a prior year but not the most recent year — a longer-lapsed segment "
                "requiring a different re-engagement approach than LYBUNT donors. "
                "Confirm this report is available for portfolio review and campaign planning."
            )
        else:
            print("  OK: SYBUNT report reference found.")


def check_donor_lifecycle_requirements(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    print(f"Checking Donor Lifecycle Requirements in: {manifest_dir.resolve()}")

    check_npsp_namespace_objects(manifest_dir, issues)
    check_engagement_plan_templates(manifest_dir, issues)
    check_opportunity_stage_picklist(manifest_dir, issues)
    check_lybunt_sybunt_reports(manifest_dir, issues)

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_donor_lifecycle_requirements(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    print(f"\n{len(issues)} issue(s) found:", file=sys.stderr)
    for issue in issues:
        print(f"\nWARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
