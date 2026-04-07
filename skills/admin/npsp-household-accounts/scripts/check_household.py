#!/usr/bin/env python3
"""check_household.py — NPSP Household Account validator.

Checks a Salesforce metadata export directory for common NPSP Household Account
configuration issues: missing custom settings, incorrect record type setup, naming
format placeholders, and known anti-patterns in Flow metadata.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_household.py [--manifest-dir path/to/metadata]
    python3 check_household.py --help
"""

from __future__ import annotations

import argparse
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate NPSP Household Account configuration in a Salesforce metadata export. "
            "Reports issues that commonly cause household naming failures or data corruption."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata export (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_manifest_dir_exists(manifest_dir: Path) -> list[str]:
    issues: list[str] = []
    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
    elif not manifest_dir.is_dir():
        issues.append(f"Manifest path is not a directory: {manifest_dir}")
    return issues


def check_npsp_household_settings_present(manifest_dir: Path) -> list[str]:
    """Check that NPSP Household Settings custom setting metadata exists."""
    issues: list[str] = []
    # NPSP deploys npo02__Household_Settings__c as a custom setting.
    # In a metadata export the settings live under customSettings/ or customObjects/.
    settings_paths = [
        manifest_dir / "customSettings" / "npo02__Household_Settings__c.customSetting-meta.xml",
        manifest_dir / "customObjects" / "npo02__Household_Settings__c.object-meta.xml",
        manifest_dir / "objects" / "npo02__Household_Settings__c" / "npo02__Household_Settings__c.object-meta.xml",
    ]
    found = any(p.exists() for p in settings_paths)
    if not found:
        issues.append(
            "NPSP Household Settings metadata (npo02__Household_Settings__c) not found. "
            "Confirm NPSP is installed and the metadata export includes customSettings or customObjects."
        )
    return issues


def check_household_account_record_type(manifest_dir: Path) -> list[str]:
    """Check that the Account object includes the HH_Account (Household) record type."""
    issues: list[str] = []
    # Record types may live in the Account object folder or as standalone metadata.
    rt_paths = [
        manifest_dir / "objects" / "Account" / "recordTypes" / "HH_Account.recordType-meta.xml",
        manifest_dir / "recordTypes" / "Account.HH_Account.recordType-meta.xml",
    ]
    found = any(p.exists() for p in rt_paths)
    if not found:
        issues.append(
            "Household Account record type (HH_Account) not found under Account object metadata. "
            "Confirm NPSP is installed and the Household Account model is active (not Individual/Bucket)."
        )
    return issues


def check_flows_for_native_account_merge(manifest_dir: Path) -> list[str]:
    """Warn if any Flow metadata invokes a native Account merge action."""
    issues: list[str] = []
    flows_dir = manifest_dir / "flows"
    if not flows_dir.exists():
        return issues  # No flows to check — not an error

    for flow_file in flows_dir.glob("*.flow-meta.xml"):
        try:
            tree = ET.parse(flow_file)
        except ET.ParseError:
            issues.append(f"Could not parse Flow XML: {flow_file.name}")
            continue

        root = tree.getroot()
        # Strip namespace if present
        ns = ""
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0] + "}"

        flow_text = flow_file.read_text(encoding="utf-8")
        # Look for indicators of native Account merge — standard invocable action or Apex reference
        native_merge_indicators = [
            "mergeType=Account",
            "mergeAccounts",
            "MergeAccounts",
            "Database.merge",
        ]
        for indicator in native_merge_indicators:
            if indicator in flow_text:
                issues.append(
                    f"Flow '{flow_file.stem}' may reference a native Account merge action "
                    f"(found '{indicator}'). Native Account merge bypasses NPSP triggers — "
                    f"use NPSP Merge Duplicate Contacts flow instead."
                )
                break

    return issues


def check_flows_for_npsp_namespace_awareness(manifest_dir: Path) -> list[str]:
    """Check if any Flow that references Account also references NPSP fields correctly."""
    issues: list[str] = []
    flows_dir = manifest_dir / "flows"
    if not flows_dir.exists():
        return issues

    for flow_file in flows_dir.glob("*.flow-meta.xml"):
        flow_text = flow_file.read_text(encoding="utf-8")
        # If a Flow touches Household Account fields without npo02__ namespace prefix,
        # it may be referencing the wrong fields.
        if "HH_Account" in flow_text or "Household" in flow_text:
            # Check for common field references missing the namespace
            bare_rollup_fields = [
                "TotalOppAmount",
                "NumberOfClosedOpps",
                "LastCloseDate",
                "Formal_Greeting",
                "Informal_Greeting",
            ]
            for field in bare_rollup_fields:
                # Correct usage includes npo02__ prefix
                if field in flow_text and f"npo02__{field}" not in flow_text:
                    issues.append(
                        f"Flow '{flow_file.stem}' references '{field}' without the 'npo02__' "
                        f"namespace prefix. NPSP household rollup and greeting fields require "
                        f"the npo02__ prefix (e.g., npo02__{field}__c)."
                    )
                    break

    return issues


def check_account_trigger_order_config(manifest_dir: Path) -> list[str]:
    """Check if any custom Apex triggers on Account or Contact could interfere with NPSP."""
    issues: list[str] = []
    triggers_dir = manifest_dir / "triggers"
    if not triggers_dir.exists():
        return issues

    npsp_trigger_names = {
        "NPSP_Trigger_Handler",
        "OppRollup",
        "HouseholdTrigger",
        "ContactMerge",
    }

    for trigger_file in triggers_dir.glob("*.trigger-meta.xml"):
        trigger_text = trigger_file.read_text(encoding="utf-8")
        stem = trigger_file.stem
        # Warn about custom triggers on Account or Contact that might conflict with NPSP
        if stem not in npsp_trigger_names:
            if "Account" in trigger_text or "Contact" in trigger_text:
                issues.append(
                    f"Custom trigger '{stem}' operates on Account or Contact objects. "
                    f"Verify trigger execution order does not conflict with NPSP trigger handlers. "
                    f"NPSP uses a trigger dispatch pattern — custom triggers should not re-fire "
                    f"NPSP logic or update household naming fields directly."
                )

    return issues


def check_naming_format_placeholders(manifest_dir: Path) -> list[str]:
    """Check NPSP custom metadata or settings for TODO placeholder values in naming formats."""
    issues: list[str] = []
    # NPSP stores naming format strings in npo02__Household_Settings__c hierarchy custom setting.
    # In some export formats these appear as CustomSetting records in CSV or XML data files.
    # We check for literal 'TODO' in any XML that references household naming fields.
    for xml_file in manifest_dir.rglob("*.xml"):
        try:
            text = xml_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "Household_Name_Format" in text or "Formal_Greeting_Format" in text:
            if "TODO" in text:
                issues.append(
                    f"File '{xml_file.name}' contains household naming format fields with 'TODO' "
                    f"placeholder values. Ensure Household Name Format, Formal Greeting Format, "
                    f"and Informal Greeting Format are set to real NPSP token strings."
                )
    return issues


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def run_all_checks(manifest_dir: Path) -> list[str]:
    """Run all checks and return a flat list of issue strings."""
    issues: list[str] = []

    existence_issues = check_manifest_dir_exists(manifest_dir)
    issues.extend(existence_issues)
    if existence_issues:
        # Cannot run further checks if the directory does not exist
        return issues

    issues.extend(check_npsp_household_settings_present(manifest_dir))
    issues.extend(check_household_account_record_type(manifest_dir))
    issues.extend(check_flows_for_native_account_merge(manifest_dir))
    issues.extend(check_flows_for_npsp_namespace_awareness(manifest_dir))
    issues.extend(check_account_trigger_order_config(manifest_dir))
    issues.extend(check_naming_format_placeholders(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir).resolve()

    print(f"Checking NPSP Household Account configuration in: {manifest_dir}")
    print()

    issues = run_all_checks(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    print(f"\n{len(issues)} issue(s) found.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
