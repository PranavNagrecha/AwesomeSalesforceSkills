#!/usr/bin/env python3
"""Checker script for Sales Reporting Data Model skill.

Validates Salesforce metadata for common issues with:
  - Historical Trend Reporting configuration
  - Reporting Snapshot target object field types
  - Custom Report Type join configuration

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_sales_reporting_data_model.py [--manifest-dir path/to/metadata]

The manifest directory should be the root of a Salesforce SFDX project or
a directory containing extracted metadata XML files.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Fields eligible for Historical Trend Reporting on Opportunity
# (5 standard + up to 3 custom = 8 max)
HTR_STANDARD_OPPORTUNITY_FIELDS = {
    "Amount",
    "CloseDate",
    "ForecastCategoryName",
    "StageName",
    "OwnerId",
}
HTR_MAX_FIELDS = 8

# Field types that should NOT be used for monetary, date, or percent columns
# in Reporting Snapshot target objects
WRONG_MONETARY_TYPE = "Text"
CORRECT_MONETARY_TYPE = "Currency"
CORRECT_DATE_TYPE = "Date"
CORRECT_PERCENT_TYPE = "Percent"

# Heuristic keywords suggesting a field should be Currency, Date, or Percent
MONETARY_FIELD_NAME_HINTS = {"amount", "revenue", "value", "price", "cost", "arr", "mrr"}
DATE_FIELD_NAME_HINTS = {"date", "closedate", "snapshot"}
PERCENT_FIELD_NAME_HINTS = {"probability", "percent", "rate", "discount"}

# Salesforce XML namespace
SF_NS = "http://soap.sforce.com/2006/04/metadata"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_xml_files(root: Path, suffix: str) -> list[Path]:
    """Return all XML files under root matching a metadata suffix (e.g. '.object-meta.xml')."""
    return sorted(root.rglob(f"*{suffix}"))


def parse_xml(path: Path) -> ET.Element | None:
    """Parse an XML file and return the root element, or None on parse error."""
    try:
        tree = ET.parse(path)
        return tree.getroot()
    except ET.ParseError:
        return None


def tag(name: str) -> str:
    """Return a namespace-qualified tag name for Salesforce metadata XML."""
    return f"{{{SF_NS}}}{name}"


def child_text(element: ET.Element, child_name: str) -> str:
    """Return the text content of a direct child element, or empty string."""
    child = element.find(tag(child_name))
    return (child.text or "").strip() if child is not None else ""


# ---------------------------------------------------------------------------
# Check: Reporting Snapshot target object field types
# ---------------------------------------------------------------------------

def check_snapshot_target_field_types(manifest_dir: Path) -> list[str]:
    """
    Detect custom objects that look like Reporting Snapshot targets and check
    that monetary, date, and percent-style fields use the correct field types.

    Heuristic: objects with a field named 'Snapshot_Date__c' or 'SnapshotDate__c'
    are treated as Reporting Snapshot target objects.
    """
    issues: list[str] = []
    object_files = find_xml_files(manifest_dir, ".object-meta.xml")

    for obj_path in object_files:
        root = parse_xml(obj_path)
        if root is None:
            continue

        # Detect snapshot target: look for a field whose label or name contains "Snapshot" and "Date"
        fields = root.findall(tag("fields"))
        field_names = [child_text(f, "fullName").lower() for f in fields]
        is_snapshot_target = any(
            ("snapshot" in fn and "date" in fn) or fn in {"snapshot_date__c", "snapshotdate__c"}
            for fn in field_names
        )
        if not is_snapshot_target:
            continue

        obj_name = obj_path.stem.replace(".object-meta", "")

        for field_el in fields:
            full_name = child_text(field_el, "fullName").lower()
            field_type = child_text(field_el, "type")
            label = child_text(field_el, "label").lower()

            # Check for monetary fields stored as Text
            if field_type == "Text":
                if any(hint in full_name or hint in label for hint in MONETARY_FIELD_NAME_HINTS):
                    issues.append(
                        f"[SnapshotFieldType] Object '{obj_name}': field '{full_name}' appears monetary "
                        f"but is type Text — should be Currency to enable SUM/AVG aggregation in reports."
                    )
                if any(hint in full_name or hint in label for hint in DATE_FIELD_NAME_HINTS) and "snapshot" not in full_name:
                    issues.append(
                        f"[SnapshotFieldType] Object '{obj_name}': field '{full_name}' appears date-like "
                        f"but is type Text — should be Date for correct sort and filter behavior."
                    )
                if any(hint in full_name or hint in label for hint in PERCENT_FIELD_NAME_HINTS):
                    issues.append(
                        f"[SnapshotFieldType] Object '{obj_name}': field '{full_name}' appears percent-like "
                        f"but is type Text — should be Percent for correct aggregation."
                    )

    return issues


# ---------------------------------------------------------------------------
# Check: Custom Report Type join configuration
# ---------------------------------------------------------------------------

def check_custom_report_type_joins(manifest_dir: Path) -> list[str]:
    """
    Check Custom Report Type metadata for common join-configuration issues.

    Salesforce CRT metadata files use the .reportType-meta.xml suffix.
    Checks:
      - CRT is in "Deployed" status (not Draft)
      - Multi-level "without" joins are flagged for review
    """
    issues: list[str] = []
    crt_files = find_xml_files(manifest_dir, ".reportType-meta.xml")

    for crt_path in crt_files:
        root = parse_xml(crt_path)
        if root is None:
            continue

        crt_name = crt_path.stem.replace(".reportType-meta", "")
        deployed = child_text(root, "deployed")
        if deployed.lower() == "false":
            issues.append(
                f"[CRTNotDeployed] Report Type '{crt_name}' is not deployed (deployed=false). "
                f"Users cannot access report types until they are deployed."
            )

        # Check for "without" joins at non-first relationship steps — flag for manual review
        sections = root.findall(tag("sections"))
        without_steps: list[str] = []
        for i, section in enumerate(sections):
            join = child_text(section, "masterLabel")
            # Look for the relationship join type indicator
            # In metadata XML, "outerJoin" or similar may appear in the section element
            # We check for the presence of outerJoin indicators
            outer_join = section.find(tag("outerJoin"))
            if outer_join is not None and (outer_join.text or "").strip().lower() == "true":
                without_steps.append(f"step {i + 1} ({join})")

        if len(without_steps) > 1:
            issues.append(
                f"[CRTMultipleOuterJoins] Report Type '{crt_name}' has 'without' (outer) join "
                f"at multiple relationship steps: {', '.join(without_steps)}. "
                f"Verify each join step is intentional — outer joins at multiple levels can produce "
                f"unexpected cross-object gap behavior. Review references/gotchas.md."
            )

    return issues


# ---------------------------------------------------------------------------
# Check: Historical Trend Reporting field count heuristic
# ---------------------------------------------------------------------------

def check_htr_field_count(manifest_dir: Path) -> list[str]:
    """
    Check the Opportunity object metadata for fields tagged as historical-trend-enabled.

    In Salesforce metadata, Historical Trend Reporting tracked fields are indicated by
    the <trackHistory> or <trackTrending> element on individual field definitions.
    """
    issues: list[str] = []

    # Look for Opportunity object metadata
    opp_candidates = list(manifest_dir.rglob("Opportunity.object-meta.xml"))
    if not opp_candidates:
        # No Opportunity metadata found — skip silently
        return issues

    opp_path = opp_candidates[0]
    root = parse_xml(opp_path)
    if root is None:
        return issues

    trending_fields: list[str] = []
    for field_el in root.findall(tag("fields")):
        track_trending = child_text(field_el, "trackTrending")
        if track_trending.lower() == "true":
            field_name = child_text(field_el, "fullName")
            trending_fields.append(field_name)

    if len(trending_fields) > HTR_MAX_FIELDS:
        issues.append(
            f"[HTRFieldCap] Opportunity object has {len(trending_fields)} fields marked trackTrending=true "
            f"({', '.join(trending_fields)}). The platform cap is {HTR_MAX_FIELDS} fields. "
            f"Excess tracking may not take effect — review Setup > Historical Trend Reporting."
        )

    custom_trending = [f for f in trending_fields if f.endswith("__c")]
    standard_trending = [f for f in trending_fields if not f.endswith("__c")]
    if len(custom_trending) > 3:
        issues.append(
            f"[HTRCustomFieldCap] Opportunity has {len(custom_trending)} custom fields with "
            f"trackTrending=true ({', '.join(custom_trending)}). "
            f"HTR allows only 3 custom fields on Opportunity (5 standard + 3 custom = 8 max). "
            f"Excess custom field tracking is silently ignored by the platform."
        )

    return issues


# ---------------------------------------------------------------------------
# Main check runner
# ---------------------------------------------------------------------------

def check_sales_reporting_data_model(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_snapshot_target_field_types(manifest_dir))
    issues.extend(check_custom_report_type_joins(manifest_dir))
    issues.extend(check_htr_field_count(manifest_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for common sales reporting data model issues:\n"
            "  - Reporting Snapshot target object fields using wrong field types\n"
            "  - Custom Report Types not deployed or with unexpected multi-level outer joins\n"
            "  - Opportunity Historical Trend Reporting field count exceeding platform cap\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_sales_reporting_data_model(manifest_dir)

    if not issues:
        print("No sales reporting data model issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
