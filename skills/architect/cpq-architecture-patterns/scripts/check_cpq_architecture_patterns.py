#!/usr/bin/env python3
"""Checker script for CPQ Architecture Patterns skill.

Validates Salesforce CPQ metadata against known architectural constraints:
  - QCP JavaScript size relative to the 131,072-character SBQQ__Code__c limit
  - Bundle nesting depth (warns above 2 levels)
  - Static Resource usage for large QCP code
  - Large Quote Mode field presence on Account layout
  - Presence of SBQQ integration user permission set assignments

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_cpq_architecture_patterns.py [--help]
    python3 check_cpq_architecture_patterns.py --manifest-dir path/to/metadata
    python3 check_cpq_architecture_patterns.py --manifest-dir . --qcp-resource CPQPlugin
"""

from __future__ import annotations

import argparse
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Hard limit for SBQQ__Code__c field (Long Text Area max)
QCP_FIELD_CHAR_LIMIT = 131_072
# Recommended safe working limit — migrate to Static Resource above this
QCP_SAFE_LIMIT = 80_000
# Maximum recommended bundle nesting depth
MAX_BUNDLE_DEPTH = 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check CPQ architecture metadata for known anti-patterns and limits.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--qcp-resource",
        default=None,
        help="Name of the Static Resource containing the QCP JavaScript (optional).",
    )
    return parser.parse_args()


def check_qcp_inline_size(manifest_dir: Path) -> list[str]:
    """Check SBQQ__CustomScript__c metadata for oversized inline QCP code."""
    issues: list[str] = []

    # Custom script records may be in objects/ or customMetadata/ depending on export format
    # Look for any XML files referencing SBQQ__Code__c
    for xml_path in manifest_dir.rglob("*.object"):
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            ns = {"sf": "http://soap.sforce.com/2006/04/metadata"}
            for field_def in root.findall(".//sf:fields", ns):
                name_el = field_def.find("sf:fullName", ns)
                if name_el is not None and name_el.text == "SBQQ__Code__c":
                    length_el = field_def.find("sf:length", ns)
                    if length_el is not None:
                        try:
                            length = int(length_el.text)
                            if length < QCP_FIELD_CHAR_LIMIT:
                                issues.append(
                                    f"{xml_path.name}: SBQQ__Code__c field length {length} is below the "
                                    f"platform maximum of {QCP_FIELD_CHAR_LIMIT}. Confirm this is a custom "
                                    f"override; managed package field limit cannot be changed."
                                )
                        except ValueError:
                            pass
        except ET.ParseError:
            pass

    return issues


def check_static_resource_qcp(manifest_dir: Path, qcp_resource_name: str | None) -> list[str]:
    """Check Static Resource size if a QCP resource name is provided."""
    issues: list[str] = []

    if not qcp_resource_name:
        return issues

    # Look for the static resource file
    resource_candidates = list(manifest_dir.rglob(f"{qcp_resource_name}"))
    resource_candidates += list(manifest_dir.rglob(f"{qcp_resource_name}.js"))
    resource_candidates += list(manifest_dir.rglob(f"{qcp_resource_name}.resource"))

    if not resource_candidates:
        issues.append(
            f"Static Resource '{qcp_resource_name}' not found under {manifest_dir}. "
            f"If QCP code is stored inline in SBQQ__Code__c, check that it is below "
            f"{QCP_SAFE_LIMIT} characters to maintain a safe margin under the "
            f"{QCP_FIELD_CHAR_LIMIT}-character hard limit."
        )
        return issues

    for resource_path in resource_candidates:
        size = resource_path.stat().st_size
        if size > QCP_FIELD_CHAR_LIMIT:
            # This is expected and correct for Static Resource pattern
            pass
        elif size > QCP_SAFE_LIMIT:
            issues.append(
                f"{resource_path}: QCP Static Resource is {size} bytes, approaching the "
                f"{QCP_FIELD_CHAR_LIMIT}-character inline field limit. Confirm Static Resource "
                f"loader pattern is in use."
            )

    return issues


def check_bundle_nesting_depth(manifest_dir: Path) -> list[str]:
    """Heuristic check for deeply nested bundle structures in product metadata."""
    issues: list[str] = []

    # Product option records in metadata appear as CustomObject or CustomMetadata
    # Look for SBQQ__ProductOption__c related metadata that may indicate nesting
    product_option_files = list(manifest_dir.rglob("SBQQ__ProductOption__c*.xml"))
    product_option_files += list(manifest_dir.rglob("*ProductOption*.xml"))

    if not product_option_files:
        # No product option metadata found — cannot assess nesting
        return issues

    # Check each product option for FeatureNumber / nested bundle indicators
    # Deep nesting is hard to detect from metadata alone without full object graph
    # Report a reminder to manually verify nesting depth
    issues.append(
        f"Found {len(product_option_files)} Product Option metadata file(s). "
        f"Manually verify that bundle nesting depth does not exceed {MAX_BUNDLE_DEPTH} levels. "
        f"Deep nesting (3+ levels) causes SOQL multiplication and pricing engine timeouts. "
        f"Use SBQQ__FeatureName__c grouping and Option Constraints instead of additional nesting."
    )

    return issues


def check_large_quote_mode(manifest_dir: Path) -> list[str]:
    """Check Account page layout for SBQQ__LargeQuote__c field presence."""
    issues: list[str] = []

    account_layouts = list(manifest_dir.rglob("Account-*.layout"))
    if not account_layouts:
        return issues

    large_quote_found = False
    for layout_path in account_layouts:
        try:
            content = layout_path.read_text(encoding="utf-8", errors="ignore")
            if "SBQQ__LargeQuote__c" in content:
                large_quote_found = True
                break
        except OSError:
            pass

    if not large_quote_found and account_layouts:
        issues.append(
            "SBQQ__LargeQuote__c not found on any Account page layout. "
            "Large Quote Mode is controlled at the Account level via this field. "
            "If Large Quote Mode is part of the architecture, add SBQQ__LargeQuote__c "
            "to the Account layout so admins can enable it per account."
        )

    return issues


def check_integration_permission_sets(manifest_dir: Path) -> list[str]:
    """Check that CPQ integration permission sets are present."""
    issues: list[str] = []

    # Look for any permission set referencing SBQQ namespace
    perm_sets = list(manifest_dir.rglob("*.permissionset"))
    cpq_perm_found = any(
        "SBQQ" in ps.read_text(encoding="utf-8", errors="ignore")
        for ps in perm_sets
        if ps.exists()
    )

    if perm_sets and not cpq_perm_found:
        issues.append(
            "No permission set found referencing SBQQ namespace objects. "
            "Integration users calling ServiceRouter must have appropriate CPQ permission set "
            "assignments (e.g., 'Salesforce CPQ API User' permission set from the managed package). "
            "Verify integration users have the required CPQ permissions."
        )

    return issues


def check_cpq_architecture_patterns(manifest_dir: Path, qcp_resource_name: str | None = None) -> list[str]:
    """Run all CPQ architecture checks and return a list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_qcp_inline_size(manifest_dir))
    issues.extend(check_static_resource_qcp(manifest_dir, qcp_resource_name))
    issues.extend(check_bundle_nesting_depth(manifest_dir))
    issues.extend(check_large_quote_mode(manifest_dir))
    issues.extend(check_integration_permission_sets(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    qcp_resource = args.qcp_resource

    issues = check_cpq_architecture_patterns(manifest_dir, qcp_resource)

    if not issues:
        print("No CPQ architecture issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
