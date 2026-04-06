#!/usr/bin/env python3
"""Checker script for CPQ vs Standard Products Decision skill.

Analyzes org metadata to detect indicators of quoting complexity and
flags potential mismatches between the current approach (standard vs CPQ)
and the org's actual requirements.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_cpq_vs_standard_products_decision.py [--help]
    python3 check_cpq_vs_standard_products_decision.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check CPQ vs Standard Products Decision — detect quoting complexity indicators.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _count_files(directory: Path, suffix: str) -> int:
    """Count files with a given suffix in a directory tree."""
    if not directory.exists():
        return 0
    return sum(1 for _ in directory.rglob(f"*{suffix}"))


def _find_cpq_objects(manifest_dir: Path) -> list[str]:
    """Detect SBQQ (CPQ managed package) object references in metadata."""
    cpq_refs: list[str] = []
    for xml_file in manifest_dir.rglob("*.xml"):
        try:
            content = xml_file.read_text(encoding="utf-8", errors="replace")
            if "SBQQ__" in content:
                cpq_refs.append(str(xml_file.relative_to(manifest_dir)))
        except (OSError, UnicodeDecodeError):
            continue
    return cpq_refs


def _count_custom_fields_on_object(manifest_dir: Path, object_name: str) -> int:
    """Count custom fields defined on a given object in the metadata."""
    fields_dir = manifest_dir / "objects" / object_name / "fields"
    if not fields_dir.exists():
        return 0
    return sum(1 for f in fields_dir.iterdir() if f.suffix == ".xml" or f.suffix == ".field-meta.xml")


def _find_product_records(manifest_dir: Path) -> int:
    """Estimate product count from metadata if Product2 records are exported."""
    product_dir = manifest_dir / "objects" / "Product2"
    if product_dir.exists():
        return _count_files(product_dir, ".xml")
    return 0


def check_cpq_vs_standard_products_decision(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory.

    Checks for:
    - Presence of CPQ managed package objects (SBQQ__*)
    - Custom fields on standard Quote/QuoteLineItem suggesting complexity
    - Indicators that standard quoting is being stretched beyond its design
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check for CPQ package references
    cpq_refs = _find_cpq_objects(manifest_dir)
    has_cpq = len(cpq_refs) > 0

    # Check custom fields on standard quoting objects
    quote_custom_fields = _count_custom_fields_on_object(manifest_dir, "Quote")
    qli_custom_fields = _count_custom_fields_on_object(manifest_dir, "QuoteLineItem")

    # Check for custom fields on CPQ objects
    cpq_quote_fields = _count_custom_fields_on_object(manifest_dir, "SBQQ__Quote__c")
    cpq_line_fields = _count_custom_fields_on_object(manifest_dir, "SBQQ__QuoteLine__c")

    # Issue: Heavy customization on standard Quote objects may indicate CPQ need
    total_standard_quote_fields = quote_custom_fields + qli_custom_fields
    if total_standard_quote_fields > 15 and not has_cpq:
        issues.append(
            f"Found {total_standard_quote_fields} custom fields on standard Quote/QuoteLineItem "
            f"objects without CPQ installed. High customization on standard quoting objects "
            f"may indicate complexity that CPQ handles natively. Evaluate whether CPQ would "
            f"reduce maintenance burden."
        )

    # Issue: Both standard and CPQ objects are customized (split architecture)
    if total_standard_quote_fields > 5 and (cpq_quote_fields + cpq_line_fields) > 0:
        issues.append(
            f"Found custom fields on both standard Quote objects ({total_standard_quote_fields}) "
            f"and CPQ objects ({cpq_quote_fields + cpq_line_fields}). This suggests a split "
            f"data architecture. Consolidate quoting on one model to avoid reporting and "
            f"integration inconsistencies."
        )

    # Issue: CPQ references found but no CPQ custom fields — possible partial install
    if has_cpq and cpq_quote_fields == 0 and cpq_line_fields == 0:
        issues.append(
            f"Found {len(cpq_refs)} metadata files referencing SBQQ__ objects, but no custom "
            f"fields on CPQ objects. CPQ may be partially installed or unused. Verify the "
            f"package installation status and license assignment."
        )

    # Check for Apex triggers on quoting objects that suggest custom pricing logic
    triggers_dir = manifest_dir / "triggers"
    if triggers_dir.exists():
        for trigger_file in triggers_dir.rglob("*.trigger-meta.xml"):
            try:
                content = trigger_file.read_text(encoding="utf-8", errors="replace")
                if "QuoteLineItem" in content or "Quote" in content:
                    if not has_cpq:
                        issues.append(
                            f"Apex trigger on standard Quote/QuoteLineItem: {trigger_file.name}. "
                            f"Custom pricing or validation logic in triggers may indicate "
                            f"complexity that CPQ handles declaratively."
                        )
            except (OSError, UnicodeDecodeError):
                continue

    if not issues:
        if has_cpq:
            issues.append(
                "INFO: CPQ managed package detected. No split architecture or configuration "
                "issues found."
            )
        else:
            issues.append(
                "INFO: No CPQ package detected. Standard quoting objects have minimal "
                "customization. Current approach appears appropriate for catalog complexity."
            )
        return []  # INFO messages are not issues

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_cpq_vs_standard_products_decision(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
