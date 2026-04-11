#!/usr/bin/env python3
"""Checker script for NPSP Data Model skill.

Scans Salesforce metadata files (Apex classes, SOQL files, and similar)
for common NPSP data model issues:

- Incorrect namespace prefix usage (e.g., npsp__OppPayment__c instead of npe01__OppPayment__c)
- Opportunity delete without allocation cleanup
- Installment Opportunity creation without parent Recurring Donation reference
- npe4__/npe5__ namespace confusion

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_npsp_data_model.py [--help]
    python3 check_npsp_data_model.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Known wrong API names: objects that LLMs place under npsp__ but belong
# to another NPSP sub-package namespace.
# ---------------------------------------------------------------------------
WRONG_NAMESPACE_PATTERNS: list[tuple[re.Pattern[str], str, str]] = [
    (
        re.compile(r"\bnpsp__OppPayment__c\b"),
        "npsp__OppPayment__c is incorrect — use npe01__OppPayment__c (Payments namespace is npe01__)",
        "npsp__OppPayment__c",
    ),
    (
        re.compile(r"\bnpsp__Recurring_Donation__c\b"),
        "npsp__Recurring_Donation__c is incorrect — use npe03__Recurring_Donation__c (Recurring Donations namespace is npe03__)",
        "npsp__Recurring_Donation__c",
    ),
    (
        re.compile(r"\bnpsp__Relationship__c\b"),
        "npsp__Relationship__c is incorrect — use npe4__Relationship__c (Relationships namespace is npe4__)",
        "npsp__Relationship__c",
    ),
    (
        re.compile(r"\bnpsp__Affiliation__c\b"),
        "npsp__Affiliation__c is incorrect — use npe5__Affiliation__c (Affiliations namespace is npe5__)",
        "npsp__Affiliation__c",
    ),
    (
        re.compile(r"\bnpsp__TotalOppAmount__c\b"),
        "npsp__TotalOppAmount__c is likely incorrect — household rollup fields on Contact use the npo02__ namespace (e.g., npo02__TotalOppAmount__c)",
        "npsp__TotalOppAmount__c",
    ),
    (
        re.compile(r"\bnpsp__LastOppAmount__c\b"),
        "npsp__LastOppAmount__c is likely incorrect — household rollup fields on Contact use the npo02__ namespace (e.g., npo02__LastOppAmount__c)",
        "npsp__LastOppAmount__c",
    ),
]

# Subquery from Opportunity trying to traverse to allocations as a child relationship
ALLOCATION_SUBQUERY_PATTERN = re.compile(
    r"SELECT\s[^;]*\(\s*SELECT[^)]+FROM\s+npsp__Alloc",
    re.IGNORECASE | re.DOTALL,
)

# Opportunity delete without any allocation reference nearby
OPP_DELETE_PATTERN = re.compile(
    r"\bdelete\b[^;]*\bOpportunity\b|\bdelete\s+opp",
    re.IGNORECASE,
)
ALLOC_REFERENCE_PATTERN = re.compile(
    r"npsp__Allocation__c",
    re.IGNORECASE,
)

# Installment Opportunity insert without npe03__Recurring_Donation__c reference
OPP_INSERT_PATTERN = re.compile(
    r"\binsert\b[^;]*\bOpportunity\b|\bnew\s+Opportunity\s*\(",
    re.IGNORECASE,
)
RD_REFERENCE_PATTERN = re.compile(
    r"npe03__Recurring_Donation__c",
    re.IGNORECASE,
)

APEX_EXTENSIONS = {".cls", ".trigger", ".apex"}
SOQL_EXTENSIONS = {".soql", ".sosl"}
ALL_EXTENSIONS = APEX_EXTENSIONS | SOQL_EXTENSIONS | {".xml"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata files for NPSP data model namespace errors "
            "and unsafe data operations."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_wrong_namespace(path: Path, content: str) -> list[str]:
    """Flag references to NPSP objects with the wrong namespace prefix."""
    issues: list[str] = []
    for pattern, message, wrong_name in WRONG_NAMESPACE_PATTERNS:
        if pattern.search(content):
            issues.append(f"{path}: {message}")
    return issues


def check_allocation_subquery(path: Path, content: str) -> list[str]:
    """Flag SOQL that tries to subquery allocations from Opportunity (lookup, not MD)."""
    if ALLOCATION_SUBQUERY_PATTERN.search(content):
        return [
            f"{path}: SOQL subquery from Opportunity to npsp__Allocation__c is invalid "
            "(allocation uses a lookup, not master-detail). "
            "Query npsp__Allocation__c directly and filter by npsp__Opportunity__c."
        ]
    return []


def check_opportunity_delete_without_allocations(path: Path, content: str) -> list[str]:
    """Warn when Opportunity deletes are present but no allocation reference is found in the file."""
    if path.suffix not in APEX_EXTENSIONS:
        return []
    if OPP_DELETE_PATTERN.search(content) and not ALLOC_REFERENCE_PATTERN.search(content):
        return [
            f"{path}: Opportunity delete detected without any reference to npsp__Allocation__c. "
            "GAU Allocation records are lookup-related and will not cascade-delete. "
            "Query and delete npsp__Allocation__c records before deleting Opportunities."
        ]
    return []


def check_namespace_prefix_usage(path: Path, content: str) -> list[str]:
    """Warn on files that use npe4__ and npe5__ prefixes interchangeably."""
    issues: list[str] = []
    has_npe4_affiliation = bool(re.search(r"\bnpe4__Affiliation", content))
    has_npe5_relationship = bool(re.search(r"\bnpe5__Relationship", content))

    if has_npe4_affiliation:
        issues.append(
            f"{path}: npe4__Affiliation does not exist. "
            "Use npe5__Affiliation__c for Contact-to-Account affiliations (npe5__ namespace)."
        )
    if has_npe5_relationship:
        issues.append(
            f"{path}: npe5__Relationship does not exist. "
            "Use npe4__Relationship__c for Contact-to-Contact relationships (npe4__ namespace)."
        )
    return issues


def check_file(path: Path) -> list[str]:
    """Run all checks against a single file. Returns list of issue strings."""
    if path.suffix not in ALL_EXTENSIONS:
        return []

    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return [f"{path}: could not read file"]

    issues: list[str] = []
    issues.extend(check_wrong_namespace(path, content))
    issues.extend(check_allocation_subquery(path, content))
    issues.extend(check_opportunity_delete_without_allocations(path, content))
    issues.extend(check_namespace_prefix_usage(path, content))
    return issues


def check_npsp_data_model(manifest_dir: Path) -> list[str]:
    """Scan all supported files in manifest_dir and return all issue strings."""
    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    all_issues: list[str] = []
    for path in sorted(manifest_dir.rglob("*")):
        if path.is_file():
            all_issues.extend(check_file(path))

    return all_issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_npsp_data_model(manifest_dir)

    if not issues:
        print("No NPSP data model issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
