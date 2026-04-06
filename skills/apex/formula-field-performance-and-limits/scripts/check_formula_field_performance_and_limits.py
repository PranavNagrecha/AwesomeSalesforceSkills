#!/usr/bin/env python3
"""Checker script for Formula Field Performance and Limits skill.

Scans Salesforce metadata XML in a retrieved source directory to detect:
- Formula fields referenced in SOQL WHERE / ORDER BY clauses in Apex classes
- Formula fields with cross-object references that may approach the spanning limit
- Apex SOQL queries that filter on a field ending in common formula-field naming patterns

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_formula_field_performance_and_limits.py [--help]
    python3 check_formula_field_performance_and_limits.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FORMULA_COMPILE_LIMIT = 5000  # compiled characters — source count is a proxy only
FORMULA_SPANNING_LIMIT = 10   # unique cross-object relationships per formula

# Regex patterns to detect formula fields in SOQL WHERE / ORDER BY in Apex
SOQL_FILTER_PATTERN = re.compile(
    r"(?:WHERE|ORDER\s+BY)\s+[^;'\"]*?(\w+__c)\b",
    re.IGNORECASE | re.DOTALL,
)

# Salesforce metadata namespace
SF_NS = "http://soap.sforce.com/2006/04/metadata"


# ---------------------------------------------------------------------------
# Metadata helpers
# ---------------------------------------------------------------------------

def find_custom_fields(manifest_dir: Path) -> dict[str, dict]:
    """Return a dict keyed by API name for every CustomField found in object metadata.

    Only formula fields are returned (those with a <formula> element).
    """
    formula_fields: dict[str, dict] = {}

    for obj_dir in manifest_dir.rglob("*.object-meta.xml"):
        try:
            tree = ET.parse(obj_dir)
        except ET.ParseError:
            continue

        root = tree.getroot()
        # Strip namespace for comparison
        ns = SF_NS

        for field in root.findall(f"{{{ns}}}fields"):
            full_name_el = field.find(f"{{{ns}}}fullName")
            formula_el = field.find(f"{{{ns}}}formula")
            if formula_el is None or formula_el.text is None:
                continue
            if full_name_el is None or full_name_el.text is None:
                continue

            field_name = full_name_el.text.strip()
            formula_text = formula_el.text.strip()
            object_name = obj_dir.stem.replace(".object", "")

            formula_fields[f"{object_name}.{field_name}"] = {
                "object": object_name,
                "field": field_name,
                "formula": formula_text,
                "source_file": str(obj_dir),
            }

    return formula_fields


def count_spanning_relationships(formula_text: str) -> int:
    """Count the number of unique cross-object relationship hops in a formula.

    This is an approximation: counts unique dot-notation prefixes that look
    like relationship traversals (e.g., Account.Owner counts as one hop;
    Account.Owner.Profile counts as two hops — two unique objects traversed).
    """
    # Find all tokens that look like Object.Field or Object.Object.Field
    traversal_pattern = re.compile(r"\b([A-Za-z][A-Za-z0-9_]*)\.([A-Za-z][A-Za-z0-9_]*)")
    matches = traversal_pattern.findall(formula_text)

    # Count unique left-hand objects (each unique object name in a traversal = one spanning rel)
    unique_objects: set[str] = set()
    for left, _ in matches:
        # Skip known non-relationship prefixes ($User, $Label, $Organization)
        if left.startswith("$"):
            continue
        unique_objects.add(left)

    return len(unique_objects)


# ---------------------------------------------------------------------------
# Apex SOQL scan
# ---------------------------------------------------------------------------

def find_apex_classes(manifest_dir: Path) -> list[Path]:
    """Return all Apex class files under the manifest directory."""
    return list(manifest_dir.rglob("*.cls"))


def extract_soql_filter_fields(apex_text: str) -> list[str]:
    """Return a list of field names found in SOQL WHERE or ORDER BY clauses."""
    fields: list[str] = []
    # Find inline SOQL blocks (simplified — catches common patterns)
    soql_block_pattern = re.compile(
        r"\[\s*SELECT\b.+?\]",
        re.IGNORECASE | re.DOTALL,
    )
    for soql_match in soql_block_pattern.finditer(apex_text):
        soql = soql_match.group(0)
        for field_match in SOQL_FILTER_PATTERN.finditer(soql):
            fields.append(field_match.group(1))
    return fields


# ---------------------------------------------------------------------------
# Main checks
# ---------------------------------------------------------------------------

def check_formula_fields(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # --- Check 1: Formula field metadata scan ---
    formula_fields = find_custom_fields(manifest_dir)

    formula_field_api_names: set[str] = set()

    for fq_name, meta in formula_fields.items():
        formula_text = meta["formula"]
        field_api = meta["field"]
        object_name = meta["object"]

        formula_field_api_names.add(field_api)

        # Check spanning relationships
        span_count = count_spanning_relationships(formula_text)
        if span_count >= FORMULA_SPANNING_LIMIT:
            issues.append(
                f"SPANNING LIMIT RISK — {fq_name}: formula spans ~{span_count} "
                f"cross-object relationships (limit: {FORMULA_SPANNING_LIMIT}). "
                f"File: {meta['source_file']}"
            )
        elif span_count >= FORMULA_SPANNING_LIMIT - 2:
            issues.append(
                f"SPANNING LIMIT WARNING — {fq_name}: formula spans ~{span_count} "
                f"cross-object relationships (approaching limit of {FORMULA_SPANNING_LIMIT}). "
                f"File: {meta['source_file']}"
            )

        # Check source character length as a proxy for compile size
        source_len = len(formula_text)
        if source_len > 3000:
            issues.append(
                f"COMPILE SIZE WARNING — {fq_name}: formula source length is {source_len} chars. "
                f"Compiled size may exceed the 5,000-char limit — verify by attempting a save in Setup. "
                f"File: {meta['source_file']}"
            )

    # --- Check 2: Apex SOQL filter on formula field names ---
    apex_classes = find_apex_classes(manifest_dir)

    for cls_path in apex_classes:
        try:
            apex_text = cls_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        filter_fields = extract_soql_filter_fields(apex_text)
        for field in filter_fields:
            # Flag if the field name matches a known formula field
            if field in formula_field_api_names:
                issues.append(
                    f"FORMULA IN SOQL FILTER — {cls_path.name}: SOQL WHERE/ORDER BY references "
                    f"'{field}' which is a formula field. Formula fields are not indexable and "
                    f"force a full table scan at scale. Materialize to a stored field. "
                    f"File: {cls_path}"
                )
            # Also flag fields with naming patterns that suggest formula fields
            elif re.search(r"(?i)(formula|calc|computed|derived)", field):
                issues.append(
                    f"POSSIBLE FORMULA IN SOQL FILTER — {cls_path.name}: SOQL WHERE/ORDER BY "
                    f"references '{field}' which may be a formula field (name suggests calculated "
                    f"value). Verify field type in Setup and materialize if it is a formula. "
                    f"File: {cls_path}"
                )

    if not issues:
        pass  # No issues to report

    return issues


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Salesforce metadata for formula field performance and limit issues.\n\n"
            "Checks performed:\n"
            "  1. Formula fields approaching or exceeding the 10 cross-object spanning limit\n"
            "  2. Formula source length exceeding 3,000 chars (proxy for compile-size risk)\n"
            "  3. Apex SOQL WHERE / ORDER BY clauses filtering on formula fields\n\n"
            "NOTE: This script uses source-text heuristics. Always verify findings in Setup."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata source (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_formula_fields(manifest_dir)

    if not issues:
        print("No formula field performance or limit issues detected.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    print(f"\n{len(issues)} issue(s) found.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
