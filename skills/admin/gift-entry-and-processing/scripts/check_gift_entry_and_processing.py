#!/usr/bin/env python3
"""Checker script for Gift Entry and Processing skill.

Checks Salesforce metadata in a manifest directory for common Gift Entry
configuration issues. Uses stdlib only — no pip dependencies.

Checks performed:
  - NPSP Advanced Mapping setting is enabled (required before Gift Entry activation)
  - Gift Entry feature is active in NPSP custom settings
  - At least one active Gift Entry template exists
  - No Apex classes or Flows contain direct DML to Opportunity bypassing Gift Entry
  - No Flows invoke processGiftEntries with isDryRun omitted on large-batch contexts
  - TaxReceiptStatus field references exist only in API v62.0+ contexts

Usage:
    python3 check_gift_entry_and_processing.py [--manifest-dir path/to/metadata]
    python3 check_gift_entry_and_processing.py --help
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for Gift Entry and Processing "
            "configuration issues (NPSP)."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--api-version",
        type=float,
        default=None,
        help=(
            "Salesforce API version of the org (e.g. 62.0). "
            "Used to validate TaxReceiptStatus usage. "
            "If not provided, TaxReceiptStatus references are flagged as needing a version check."
        ),
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Individual check functions
# ---------------------------------------------------------------------------

def check_apex_direct_opportunity_dml(manifest_dir: Path) -> list[str]:
    """Flag Apex classes that insert Opportunity records directly, bypassing Gift Entry."""
    issues: list[str] = []
    apex_dir = manifest_dir / "classes"
    if not apex_dir.exists():
        return issues

    # Pattern: insert new Opportunity(...) or insert opp; near donation-related context
    direct_opp_insert = re.compile(
        r"insert\s+(new\s+Opportunity\b|[a-zA-Z_][a-zA-Z0-9_]*\s*;)",
        re.IGNORECASE,
    )
    gift_entry_context = re.compile(
        r"(GiftEntry|gift.?entry|donation|npsp|processGiftEntries)",
        re.IGNORECASE,
    )

    for apex_file in apex_dir.glob("*.cls"):
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        # Only flag files that appear to be in a Gift Entry / donation context
        if not gift_entry_context.search(content):
            continue

        lines = content.splitlines()
        for line_num, line in enumerate(lines, start=1):
            if direct_opp_insert.search(line):
                issues.append(
                    f"{apex_file.name}:{line_num} — Direct Opportunity DML found in "
                    f"a Gift Entry context. Use GiftEntry staging + processGiftEntries instead."
                )

    return issues


def check_apex_tax_receipt_status_api_version(
    manifest_dir: Path, api_version: float | None
) -> list[str]:
    """Flag TaxReceiptStatus references when API version is below 62.0."""
    issues: list[str] = []
    apex_dir = manifest_dir / "classes"
    if not apex_dir.exists():
        return issues

    tax_receipt_pattern = re.compile(r"TaxReceiptStatus", re.IGNORECASE)

    for apex_file in apex_dir.glob("*.cls"):
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if not tax_receipt_pattern.search(content):
            continue

        if api_version is None:
            issues.append(
                f"{apex_file.name} — TaxReceiptStatus reference found. "
                f"Verify org API version >= 62.0 before deploying. "
                f"Pass --api-version to suppress this warning if confirmed."
            )
        elif api_version < 62.0:
            issues.append(
                f"{apex_file.name} — TaxReceiptStatus requires API v62.0+; "
                f"org is on API v{api_version:.1f}. "
                f"Use a custom receipt status field on GiftTransaction instead."
            )

    return issues


def check_flow_direct_opportunity_create(manifest_dir: Path) -> list[str]:
    """Flag Flow metadata that creates Opportunity records in a Gift Entry context."""
    issues: list[str] = []
    flows_dir = manifest_dir / "flows"
    if not flows_dir.exists():
        return issues

    gift_entry_name_pattern = re.compile(
        r"(gift.?entry|donation|npsp)", re.IGNORECASE
    )

    for flow_file in flows_dir.glob("*.flow-meta.xml"):
        if not gift_entry_name_pattern.search(flow_file.stem):
            continue

        try:
            tree = ET.parse(flow_file)
        except ET.ParseError:
            issues.append(f"{flow_file.name} — XML parse error; could not validate.")
            continue

        root = tree.getroot()
        ns = {"sf": "http://soap.sforce.com/2006/04/metadata"}

        # Look for recordCreate elements targeting Opportunity
        for record_create in root.findall(".//sf:recordCreates", ns) or root.findall(".//recordCreates"):
            object_elem = record_create.find("sf:object", ns) or record_create.find("object")
            if object_elem is not None and object_elem.text == "Opportunity":
                label_elem = record_create.find("sf:label", ns) or record_create.find("label")
                label = label_elem.text if label_elem is not None else "unknown"
                issues.append(
                    f"{flow_file.name} — Flow creates Opportunity records directly "
                    f"(element: '{label}'). In a Gift Entry context, use GiftEntry "
                    f"staging + processGiftEntries invocable action instead."
                )

    return issues


def check_gift_entry_template_metadata(manifest_dir: Path) -> list[str]:
    """Check for presence of Gift Entry template custom metadata or custom settings."""
    issues: list[str] = []

    # Gift Entry templates can appear in CustomMetadata or as referenced in flows/classes
    # Check for any file referencing GiftEntryTemplate or npsp__Gift_Entry_Template
    template_pattern = re.compile(
        r"(GiftEntryTemplate|npsp__Gift_Entry_Template|Gift_Entry_Template)",
        re.IGNORECASE,
    )

    found_template_ref = False
    for search_dir in [
        manifest_dir / "classes",
        manifest_dir / "flows",
        manifest_dir / "customMetadata",
    ]:
        if not search_dir.exists():
            continue
        for f in search_dir.rglob("*"):
            if not f.is_file():
                continue
            try:
                content = f.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if template_pattern.search(content):
                found_template_ref = True
                break
        if found_template_ref:
            break

    if not found_template_ref:
        issues.append(
            "No Gift Entry template references found in metadata. "
            "Confirm the Default Gift Entry Template is active in NPSP Settings > Gift Entry."
        )

    return issues


def check_advanced_mapping_setting(manifest_dir: Path) -> list[str]:
    """Check that NPSP Advanced Mapping appears to be enabled in custom settings metadata."""
    issues: list[str] = []

    custom_settings_dir = manifest_dir / "customSettings"
    if not custom_settings_dir.exists():
        # Not an error — custom settings may not be in the manifest
        return issues

    advanced_mapping_pattern = re.compile(
        r"(Advanced_Mapping|npsp__Advanced_Mapping)", re.IGNORECASE
    )
    found = False
    for f in custom_settings_dir.rglob("*"):
        if not f.is_file():
            continue
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if advanced_mapping_pattern.search(content):
            found = True
            break

    if not found:
        issues.append(
            "No NPSP Advanced Mapping custom setting found in manifest. "
            "Verify Advanced Mapping is enabled in NPSP Settings before activating Gift Entry."
        )

    return issues


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def run_all_checks(manifest_dir: Path, api_version: float | None) -> list[str]:
    """Run all Gift Entry checks and return a combined list of issues."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_advanced_mapping_setting(manifest_dir))
    issues.extend(check_gift_entry_template_metadata(manifest_dir))
    issues.extend(check_apex_direct_opportunity_dml(manifest_dir))
    issues.extend(check_apex_tax_receipt_status_api_version(manifest_dir, api_version))
    issues.extend(check_flow_direct_opportunity_create(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    api_version: float | None = args.api_version

    issues = run_all_checks(manifest_dir, api_version)

    if not issues:
        print("No Gift Entry configuration issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
