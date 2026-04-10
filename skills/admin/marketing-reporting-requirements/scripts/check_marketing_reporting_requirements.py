#!/usr/bin/env python3
"""Checker script for Marketing Reporting Requirements skill.

Validates Salesforce metadata for Campaign Influence and attribution
reporting configuration issues.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_marketing_reporting_requirements.py [--help]
    python3 check_marketing_reporting_requirements.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
import xml.etree.ElementTree as ET


# Campaign Member Status values required for email engagement KPI reporting
# when MCAE is connected. These must exist on email campaign record types.
REQUIRED_CAMPAIGN_MEMBER_STATUSES = {
    "Sent",
    "Opened",
    "Clicked",
    "Unsubscribed",
    "Responded",
}

# Minimum recommended lookback window in days for Campaign Influence.
# The default 30-day window is too short for most B2B sales cycles.
MIN_RECOMMENDED_LOOKBACK_DAYS = 60

# CampaignInfluence object API name — used to detect if CCI records
# are present in report metadata (indicating CCI is in use).
CCI_OBJECT_NAME = "CampaignInfluence"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check marketing reporting requirements configuration and metadata "
            "for Campaign Influence setup, attribution model prerequisites, and "
            "Campaign Member status configuration."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_campaign_influence_settings(manifest_dir: Path) -> list[str]:
    """Check for Campaign Influence configuration in Custom Settings or Custom Metadata."""
    issues: list[str] = []

    # Look for Campaign Influence settings in customMetadata or customSettings
    settings_dirs = [
        manifest_dir / "customMetadata",
        manifest_dir / "customSettings",
        manifest_dir / "settings",
    ]

    ci_setting_found = False
    for settings_dir in settings_dirs:
        if not settings_dir.exists():
            continue
        for xml_file in settings_dir.glob("CampaignInfluence*.md-meta.xml"):
            ci_setting_found = True
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                ns = root.tag.split("}")[0].lstrip("{") if "}" in root.tag else ""
                ns_prefix = f"{{{ns}}}" if ns else ""

                lookback_elem = root.find(f".//{ns_prefix}lookbackWindow")
                if lookback_elem is not None and lookback_elem.text:
                    try:
                        lookback_days = int(lookback_elem.text)
                        if lookback_days < MIN_RECOMMENDED_LOOKBACK_DAYS:
                            issues.append(
                                f"Campaign Influence lookback window is {lookback_days} days "
                                f"(found in {xml_file.name}). "
                                f"Recommended minimum is {MIN_RECOMMENDED_LOOKBACK_DAYS} days "
                                "for B2B sales cycles. Update in Setup > Campaign Influence Settings."
                            )
                    except ValueError:
                        pass
            except ET.ParseError as exc:
                issues.append(f"Could not parse {xml_file}: {exc}")

    if not ci_setting_found:
        # Not necessarily an error — CI may be configured via Setup UI, not metadata
        pass

    return issues


def check_campaign_member_statuses(manifest_dir: Path) -> list[str]:
    """Check Campaign object metadata for required Campaign Member Status values."""
    issues: list[str] = []

    campaign_dir = manifest_dir / "objects" / "Campaign"
    if not campaign_dir.exists():
        # No Campaign object metadata present — skip check
        return issues

    # Check for standard fields or list views that might indicate CM status configuration
    # Campaign Member Statuses are stored in CampaignMemberStatus records, not metadata
    # so we check for any reference to the required status values in object XML
    found_statuses: set[str] = set()
    for xml_file in (manifest_dir / "objects").glob("CampaignMember.object-meta.xml"):
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            ns = root.tag.split("}")[0].lstrip("{") if "}" in root.tag else ""
            ns_prefix = f"{{{ns}}}" if ns else ""

            for field_elem in root.findall(f".//{ns_prefix}fields"):
                name_elem = field_elem.find(f"{ns_prefix}fullName")
                if name_elem is not None and name_elem.text == "Status":
                    for value_elem in field_elem.findall(f".//{ns_prefix}value"):
                        if value_elem.text:
                            found_statuses.add(value_elem.text.strip())
        except ET.ParseError as exc:
            issues.append(f"Could not parse CampaignMember object metadata: {exc}")

    if found_statuses:
        missing_statuses = REQUIRED_CAMPAIGN_MEMBER_STATUSES - found_statuses
        if missing_statuses:
            issues.append(
                f"Campaign Member Status values missing from metadata: "
                f"{sorted(missing_statuses)}. "
                "These are required for MCAE email engagement KPI reporting "
                "(open rate, click rate). Add them to each email campaign record type."
            )

    return issues


def check_reports_for_attribution_patterns(manifest_dir: Path) -> list[str]:
    """Scan report metadata for common attribution anti-patterns."""
    issues: list[str] = []

    reports_dir = manifest_dir / "reports"
    if not reports_dir.exists():
        return issues

    for report_file in reports_dir.rglob("*.report-meta.xml"):
        try:
            tree = ET.parse(report_file)
            root = tree.getroot()
            report_xml = ET.tostring(root, encoding="unicode")

            # Anti-pattern: report references both Primary Campaign Source
            # and Campaign Influence object in the same report type — this
            # mixes sourced and influenced pipeline metrics.
            has_primary_campaign_source = "PrimaryCampaignSource" in report_xml
            has_campaign_influence = CCI_OBJECT_NAME in report_xml

            if has_primary_campaign_source and has_campaign_influence:
                issues.append(
                    f"Report {report_file.name} references both PrimaryCampaignSource "
                    f"(first-touch/sourced) and {CCI_OBJECT_NAME} (influenced) in the "
                    "same report. These represent different attribution models and should "
                    "not be combined into a single 'marketing pipeline' metric. "
                    "Split into two separate reports."
                )
        except ET.ParseError:
            # Skip unparseable reports
            pass

    return issues


def check_opportunity_contact_role_configuration(manifest_dir: Path) -> list[str]:
    """Check whether Opportunity Contact Roles are referenced, indicating CI can work."""
    issues: list[str] = []

    # Check if OpportunityContactRole object is customized (fields, validation rules)
    # Presence of customizations suggests the org is actively using Contact Roles
    ocr_dir = manifest_dir / "objects" / "OpportunityContactRole"
    objects_dir = manifest_dir / "objects"

    # Check for OpportunityContactRole in objects directory
    ocr_found = (
        (ocr_dir.exists() and any(ocr_dir.iterdir()))
        if ocr_dir.exists()
        else False
    )

    if not ocr_found and objects_dir.exists():
        # Check for monolithic object file
        ocr_file = objects_dir / "OpportunityContactRole.object-meta.xml"
        ocr_found = ocr_file.exists()

    if not ocr_found and objects_dir.exists():
        issues.append(
            "No OpportunityContactRole object metadata found. "
            "Campaign Influence (both standard and Customizable) relies on "
            "Opportunity Contact Roles to associate campaigns to opportunities. "
            "If Contact Roles are not populated on Opportunities, Campaign Influence "
            "will return zero or incomplete attribution data. "
            "Verify Contact Role population rate in the org before enabling Campaign Influence."
        )

    return issues


def check_marketing_reporting_requirements(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory.

    Runs all marketing reporting requirement checks:
    - Campaign Influence lookback window configuration
    - Campaign Member Status values for email engagement KPIs
    - Report-level attribution anti-patterns (sourced vs influenced mixing)
    - Opportunity Contact Role metadata presence
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_campaign_influence_settings(manifest_dir))
    issues.extend(check_campaign_member_statuses(manifest_dir))
    issues.extend(check_reports_for_attribution_patterns(manifest_dir))
    issues.extend(check_opportunity_contact_role_configuration(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_marketing_reporting_requirements(manifest_dir)

    if not issues:
        print("No marketing reporting requirement issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
