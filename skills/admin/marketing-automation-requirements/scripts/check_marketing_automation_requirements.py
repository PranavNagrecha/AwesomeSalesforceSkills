#!/usr/bin/env python3
"""Checker script for Marketing Automation Requirements skill.

Inspects a Salesforce metadata directory for common marketing automation
requirements gaps: missing lifecycle tracking fields on Lead/Contact,
MCAE-synced score fields that are writable by CRM automation, absence of
MQL/recycle timestamp fields, and formula fields used for score routing.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_marketing_automation_requirements.py [--help]
    python3 check_marketing_automation_requirements.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Custom fields required on the Lead object for a compliant marketing
# automation requirements implementation.
# Format: (api_name, expected_type_hint, description)
REQUIRED_LEAD_FIELDS = [
    ("Is_MQL__c", "Checkbox", "MQL flag — set true when prospect crosses MQL threshold"),
    ("MQL_Date__c", "DateTime", "MQL timestamp — required for funnel velocity reporting"),
    ("SQL_Date__c", "DateTime", "SQL timestamp — required for MQL-to-SQL conversion tracking"),
    ("Lifecycle_Stage__c", "Picklist", "Marketing lifecycle stage picklist — not auto-populated by MCAE Lifecycle Report"),
    ("Recycle_Reason__c", "Picklist", "Recycle reason — required for rep feedback loop and nurture segmentation"),
    ("Recycle_Date__c", "DateTime", "Recycle timestamp — required for SLA compliance tracking"),
    ("Recycle_Count__c", "Number", "Recycle counter — required for attribution analysis on re-engaged leads"),
]

# Fields that MCAE syncs to CRM. If these are writable by CRM automation
# (not protected), they risk being overwritten by CRM processes and then
# silently reverted by the next MCAE sync.
MCAE_SYNCED_SCORE_FIELDS = {
    "Score",            # Standard MCAE score field synced to Lead.Score
    "Pardot_Score__c",  # Common custom mirror field
    "Grade",            # Standard MCAE grade field
    "Pardot_Grade__c",  # Common custom mirror field
}

# Lifecycle_Stage__c must be a Picklist to support Flow conditions and reports.
LIFECYCLE_STAGE_FIELD = "Lifecycle_Stage__c"

# Salesforce Metadata API namespace
SF_NS = "http://soap.sforce.com/2006/04/metadata"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_object_metadata(manifest_dir: Path, object_name: str) -> Path | None:
    """Locate the object metadata file or SFDX fields directory for a given object."""
    # MDAPI-style: objects/{ObjectName}.object or objects/{ObjectName}.object-meta.xml
    for candidate in [
        manifest_dir / "objects" / f"{object_name}.object",
        manifest_dir / "objects" / f"{object_name}.object-meta.xml",
    ]:
        if candidate.exists():
            return candidate

    # SFDX-style: objects/{ObjectName}/fields/
    sfdx_dir = manifest_dir / "objects" / object_name / "fields"
    if sfdx_dir.is_dir():
        return sfdx_dir

    return None


def _load_mdapi_fields(object_file: Path) -> dict[str, str]:
    """Parse an MDAPI-style .object or .object-meta.xml and return {fieldName: type}."""
    fields: dict[str, str] = {}
    try:
        tree = ET.parse(object_file)
        root = tree.getroot()
        ns = {"sf": SF_NS}
        for field_el in root.findall("sf:fields", ns):
            name_el = field_el.find("sf:fullName", ns)
            type_el = field_el.find("sf:type", ns)
            if name_el is not None and type_el is not None:
                fields[name_el.text or ""] = type_el.text or ""
    except ET.ParseError:
        pass
    return fields


def _load_sfdx_fields(fields_dir: Path) -> dict[str, str]:
    """Parse SFDX-style field XML files and return {fieldName: type}."""
    fields: dict[str, str] = {}
    for xml_file in fields_dir.glob("*.field-meta.xml"):
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            ns = {"sf": SF_NS}
            name_el = root.find("sf:fullName", ns)
            type_el = root.find("sf:type", ns)
            if name_el is not None and type_el is not None:
                fields[name_el.text or ""] = type_el.text or ""
        except ET.ParseError:
            pass
    return fields


def _load_fields(manifest_dir: Path, object_name: str) -> dict[str, str] | None:
    """Load fields for the given object. Returns None if metadata not found."""
    path = _find_object_metadata(manifest_dir, object_name)
    if path is None:
        return None
    if path.is_dir():
        return _load_sfdx_fields(path)
    return _load_mdapi_fields(path)


def _check_flow_references_score_fields(manifest_dir: Path) -> list[str]:
    """
    Scan Flow metadata for references to MCAE-synced score fields.
    If a Flow writes to Score, Grade, or common MCAE sync targets, it risks
    being silently overwritten by the next MCAE sync.
    Returns a list of warning strings.
    """
    issues: list[str] = []
    flows_dir = manifest_dir / "flows"
    if not flows_dir.is_dir():
        return issues

    for flow_file in flows_dir.glob("*.flow-meta.xml"):
        try:
            content = flow_file.read_text(encoding="utf-8", errors="replace")
            for synced_field in MCAE_SYNCED_SCORE_FIELDS:
                if synced_field in content:
                    issues.append(
                        f"FLOW RISK: Flow '{flow_file.stem}' references field '{synced_field}'. "
                        f"This field is synced by MCAE to CRM. CRM-side writes to MCAE-synced "
                        f"score/grade fields are silently overwritten by the next MCAE sync. "
                        f"Manual score adjustments must be made in the MCAE prospect record, "
                        f"not via CRM Flow or Process Builder."
                    )
        except OSError:
            pass

    return issues


# ---------------------------------------------------------------------------
# Main check function
# ---------------------------------------------------------------------------

def check_marketing_automation_requirements(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # -----------------------------------------------------------------------
    # Check 1: Lead object field presence
    # -----------------------------------------------------------------------
    lead_fields = _load_fields(manifest_dir, "Lead")

    if lead_fields is None:
        issues.append(
            "Lead object metadata not found. "
            "Expected objects/Lead.object-meta.xml (MDAPI) or objects/Lead/fields/ (SFDX). "
            "Cannot validate marketing automation lifecycle field configuration."
        )
    else:
        if not lead_fields:
            issues.append(
                "No custom fields parsed from Lead metadata. "
                "Check that the file is valid Salesforce Metadata API XML."
            )
        else:
            # Check required fields are present
            for field_name, expected_type, description in REQUIRED_LEAD_FIELDS:
                if field_name not in lead_fields:
                    issues.append(
                        f"MISSING FIELD (Lead): {field_name} ({expected_type}) — {description}. "
                        f"Add this field to the Lead object to support marketing automation "
                        f"lifecycle tracking."
                    )

            # Check Lifecycle_Stage__c is a Picklist (not Text or other type)
            if LIFECYCLE_STAGE_FIELD in lead_fields:
                stage_type = lead_fields[LIFECYCLE_STAGE_FIELD]
                if stage_type not in ("Picklist", "MultiselectPicklist"):
                    issues.append(
                        f"FIELD TYPE (Lead): {LIFECYCLE_STAGE_FIELD} is type '{stage_type}'. "
                        f"Expected Picklist. A text field cannot be safely used in Flow "
                        f"conditions, MCAE automation rule criterion matching, or funnel "
                        f"reports grouped by lifecycle stage."
                    )

            # Check Is_MQL__c is Checkbox
            if "Is_MQL__c" in lead_fields:
                mql_type = lead_fields["Is_MQL__c"]
                if mql_type != "Checkbox":
                    issues.append(
                        f"FIELD TYPE (Lead): Is_MQL__c is type '{mql_type}'. "
                        f"Expected Checkbox. A non-checkbox MQL flag cannot be reliably "
                        f"evaluated in record-triggered Flow entry criteria or MCAE "
                        f"automation rule criteria."
                    )

            # Check timestamp fields are DateTime (not Date)
            for ts_field in ("MQL_Date__c", "SQL_Date__c", "Recycle_Date__c"):
                if ts_field in lead_fields:
                    ts_type = lead_fields[ts_field]
                    if ts_type == "Date":
                        issues.append(
                            f"FIELD TYPE (Lead): {ts_field} is type 'Date'. "
                            f"Expected DateTime. Date-only fields lose time-of-day precision "
                            f"needed for SLA tracking and same-day funnel velocity calculations."
                        )

    # -----------------------------------------------------------------------
    # Check 2: Contact object mirrors (best-effort — warn only if Lead exists)
    # -----------------------------------------------------------------------
    if lead_fields is not None:
        contact_fields = _load_fields(manifest_dir, "Contact")
        if contact_fields is not None and contact_fields:
            for mirror_field in ("Is_MQL__c", "MQL_Date__c", "Lifecycle_Stage__c"):
                if mirror_field not in contact_fields:
                    issues.append(
                        f"MISSING FIELD (Contact): {mirror_field} — "
                        f"Lead has this field but Contact does not. "
                        f"If MCAE prospects can be matched to Contacts, this field "
                        f"must also exist on Contact for lifecycle tracking to work "
                        f"across both objects."
                    )

    # -----------------------------------------------------------------------
    # Check 3: Flow references to MCAE-synced score fields
    # -----------------------------------------------------------------------
    flow_issues = _check_flow_references_score_fields(manifest_dir)
    issues.extend(flow_issues)

    # -----------------------------------------------------------------------
    # Check 4: Presence of at least one Flow referencing MQL logic
    #           (heuristic: look for Is_MQL__c references in Flow metadata)
    # -----------------------------------------------------------------------
    flows_dir = manifest_dir / "flows"
    if flows_dir.is_dir():
        mql_flow_found = False
        for flow_file in flows_dir.glob("*.flow-meta.xml"):
            try:
                content = flow_file.read_text(encoding="utf-8", errors="replace")
                if "Is_MQL__c" in content or "MQL" in content:
                    mql_flow_found = True
                    break
            except OSError:
                pass

        if not mql_flow_found:
            issues.append(
                "NO MQL FLOW DETECTED: No Flow metadata references 'Is_MQL__c' or 'MQL'. "
                "Verify that the MCAE-to-CRM handoff automation (which stamps Is_MQL__c = true "
                "and MQL_Date__c) is configured as an MCAE Automation Rule action, not a "
                "Salesforce Flow — MCAE automation rules do not appear in Flow metadata. "
                "This warning can be ignored if handoff is handled entirely within MCAE."
            )

    return issues


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a Salesforce metadata directory for marketing automation "
            "requirements gaps. Validates required lifecycle tracking fields on "
            "Lead and Contact, detects CRM Flow references to MCAE-synced score "
            "fields, and checks field types for common misconfigurations."
        ),
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
    issues = check_marketing_automation_requirements(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
