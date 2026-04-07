#!/usr/bin/env python3
"""Checker script for Recurring Donations Setup skill.

Checks org metadata or configuration relevant to Enhanced Recurring Donations (ERD).
Looks for common misconfigurations and anti-patterns in NPSP recurring donation setup.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_recurring_donations_setup.py [--help]
    python3 check_recurring_donations_setup.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Enhanced Recurring Donations (ERD) configuration and metadata "
            "for common issues."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def find_xml_files(root: Path, pattern: str) -> list[Path]:
    """Return all XML files matching a glob pattern under root."""
    return sorted(root.rglob(pattern))


def check_custom_metadata_rd_settings(manifest_dir: Path) -> list[str]:
    """Check NPSP Custom Metadata for recurring donation configuration.

    NPSP ERD settings are often stored in Custom Metadata Type records
    (npe03__Recurring_Donations_Settings__c or npsp__Recurring_Donations_Settings__mdt).
    """
    issues: list[str] = []

    # Look for NPSP recurring donation settings in Custom Metadata
    settings_files = find_xml_files(
        manifest_dir, "*.Recurring_Donations_Settings*"
    ) + find_xml_files(manifest_dir, "*npe03__Recurring_Donation*Settings*.xml")

    if not settings_files:
        # Not necessarily an issue — settings may not be in the manifest
        return issues

    for settings_file in settings_files:
        try:
            tree = ET.parse(settings_file)
            root_elem = tree.getroot()
            # Strip namespace for easier access
            ns = ""
            if root_elem.tag.startswith("{"):
                ns = root_elem.tag.split("}")[0] + "}"

            # Check for ERD mode flag if present
            for elem in root_elem.iter(f"{ns}isRecurringDonations2Enabled"):
                if elem.text and elem.text.strip().lower() == "false":
                    issues.append(
                        f"{settings_file.name}: isRecurringDonations2Enabled is false — "
                        "org may still be using the legacy recurring donations model, "
                        "not Enhanced Recurring Donations (ERD). Verify in NPSP Settings "
                        "> Recurring Donations."
                    )

        except ET.ParseError as exc:
            issues.append(f"Could not parse {settings_file}: {exc}")

    return issues


def check_flows_for_rd_antipatterns(manifest_dir: Path) -> list[str]:
    """Scan Flow metadata for common ERD anti-patterns.

    Looks for:
    - Flows that query Opportunity and may assume multiple open pledged records
    - Flows that directly update npe03__Amount__c without schedule awareness
    """
    issues: list[str] = []
    flow_files = find_xml_files(manifest_dir, "*.flow-meta.xml")

    for flow_file in flow_files:
        try:
            content = flow_file.read_text(encoding="utf-8")
        except OSError:
            continue

        # Check if this Flow touches Recurring Donations at all
        if "npe03__Recurring_Donation" not in content and "RecurringDonation" not in content:
            continue

        # Anti-pattern: Flow iterates over Opportunity records and references
        # a Recurring Donation lookup, which in ERD should return at most 1 record.
        # If the flow uses a loop element on queried Opportunities from an RD,
        # warn that only 1 record is expected in ERD mode.
        if (
            "<recordLookups>" in content
            and "npe03__Recurring_Donation__c" in content
            and "<loop>" in content
        ):
            issues.append(
                f"{flow_file.name}: Flow queries Opportunities by Recurring Donation "
                "and contains a loop element. In Enhanced Recurring Donations (ERD), "
                "only ONE open pledged Opportunity exists per Recurring Donation. "
                "Ensure the loop logic handles a list of size 1 and does not assume "
                "12 future Opportunities (legacy model behavior)."
            )

        # Anti-pattern: Flow directly sets npe03__Amount__c on a Recurring Donation
        # without any reference to schedule records — may bypass Effective Date logic.
        if (
            "npe03__Amount__c" in content
            and "<recordUpdates>" in content
            and "npe03__RecurringDonationSchedule__c" not in content
        ):
            issues.append(
                f"{flow_file.name}: Flow appears to update npe03__Amount__c on a "
                "Recurring Donation record without referencing "
                "npe03__RecurringDonationSchedule__c. Direct amount updates may be "
                "overwritten by the NPSP nightly batch. Use the Effective Date "
                "mechanism and a schedule record change for persistent amount updates."
            )

    return issues


def check_apex_for_rd_antipatterns(manifest_dir: Path) -> list[str]:
    """Scan Apex classes for common ERD anti-patterns.

    Looks for:
    - SOQL queries on RecurringDonationSchedule without Status filter
    - Code that iterates over multiple future pledged Opportunities per RD
    """
    issues: list[str] = []
    apex_files = find_xml_files(manifest_dir, "*.cls")

    for apex_file in apex_files:
        try:
            content = apex_file.read_text(encoding="utf-8")
        except OSError:
            continue

        if "npe03__RecurringDonationSchedule__c" not in content:
            continue

        # Anti-pattern: query schedule object without Status filter
        if (
            "npe03__RecurringDonationSchedule__c" in content
            and "FROM npe03__RecurringDonationSchedule__c" in content
            and "Status__c" not in content
        ):
            issues.append(
                f"{apex_file.name}: SOQL query on npe03__RecurringDonationSchedule__c "
                "does not appear to filter by Status__c. NPSP preserves all historical "
                "schedule records (Active and Inactive). Without a Status__c = 'Active' "
                "filter, queries return all schedule history and produce incorrect results."
            )

    return issues


def check_reports_for_legacy_assumptions(manifest_dir: Path) -> list[str]:
    """Scan Report metadata for potential legacy-model assumptions.

    Reports that filter on StageName = 'Pledged' and group/count by Recurring Donation
    may assume 12 Opportunities per Recurring Donation (legacy model).
    """
    issues: list[str] = []
    report_files = find_xml_files(manifest_dir, "*.report-meta.xml")

    for report_file in report_files:
        try:
            content = report_file.read_text(encoding="utf-8")
        except OSError:
            continue

        if "npe03__Recurring_Donation" not in content and "RecurringDonation" not in content:
            continue

        if "Pledged" in content and ("COUNT" in content or "recordCount" in content):
            issues.append(
                f"{report_file.name}: Report references Recurring Donations, filters "
                "on Pledged stage, and includes a count metric. In Enhanced Recurring "
                "Donations (ERD), only ONE open pledged Opportunity exists per active "
                "Recurring Donation. If this report was built for the legacy model "
                "(which creates up to 12 future Opportunities), its counts and totals "
                "will be wrong in ERD orgs. Review and update the report's assumptions."
            )

    return issues


def check_recurring_donations_setup(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_custom_metadata_rd_settings(manifest_dir))
    issues.extend(check_flows_for_rd_antipatterns(manifest_dir))
    issues.extend(check_apex_for_rd_antipatterns(manifest_dir))
    issues.extend(check_reports_for_legacy_assumptions(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_recurring_donations_setup(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
