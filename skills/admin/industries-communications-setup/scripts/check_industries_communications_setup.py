#!/usr/bin/env python3
"""Checker script for Industries Communications Setup skill.

Validates Salesforce metadata for Communications Cloud setup issues:
- Account queries missing RecordType.DeveloperName filter
- Use of Commerce Order Management objects in a Communications Cloud context
- Product2 inserts without EPC namespace fields
- Contract Status field updates bypassing Industries activation
- OmniStudio patterns querying Product2 without EPC catalog filtering

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_industries_communications_setup.py [--help]
    python3 check_industries_communications_setup.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Detection patterns
# ---------------------------------------------------------------------------

# Account query without RecordType.DeveloperName filter
# Matches: FROM Account (case-insensitive), not followed by a RecordType filter
ACCOUNT_NO_RECORDTYPE = re.compile(
    r"\bFROM\s+Account\b(?![\s\S]{0,300}RecordType\.DeveloperName)",
    re.IGNORECASE,
)

# Commerce Order Management objects used in Apex or SOQL
COMMERCE_ORDER_OBJECTS = re.compile(
    r"\b(OrderSummary|FulfillmentOrder|OrderDeliveryGroup|OrderDeliveryMethod)\b",
    re.IGNORECASE,
)

# Commerce Order Management REST API path
COMMERCE_ORDER_API = re.compile(
    r"/commerce/order-management/",
    re.IGNORECASE,
)

# Direct Product2 insert without EPC namespace fields
# Looks for new Product2(...) or Product2 p = new Product2() not accompanied by vlocity_cmt
PRODUCT2_DIRECT_INSERT = re.compile(
    r"new\s+Product2\s*\(",
    re.IGNORECASE,
)
EPC_NAMESPACE_FIELD = re.compile(
    r"vlocity_cmt__",
    re.IGNORECASE,
)

# Contract Status direct field update bypassing Industries activation
CONTRACT_STATUS_ACTIVATED = re.compile(
    r"\.Status\s*=\s*['\"]Activated['\"]",
    re.IGNORECASE,
)
CONTRACT_CLASS_REFERENCE = re.compile(
    r"\bContract\b",
    re.IGNORECASE,
)

# OmniStudio DataRaptor or product query without EPC filtering
OMNISTUDIO_PRODUCT2_QUERY = re.compile(
    r"FROM\s+Product2\b(?![\s\S]{0,200}vlocity_cmt__)",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# File extensions to inspect
# ---------------------------------------------------------------------------

APEX_EXTENSIONS = {".cls", ".trigger"}
SOQL_EXTENSIONS = {".soql", ".sql"}
XML_EXTENSIONS = {".xml"}
ALL_EXTENSIONS = APEX_EXTENSIONS | SOQL_EXTENSIONS | XML_EXTENSIONS | {".json", ".yaml", ".yml"}


# ---------------------------------------------------------------------------
# Per-file checks
# ---------------------------------------------------------------------------

def check_account_recordtype(content: str, file_path: Path) -> list[str]:
    """Warn on Account queries without RecordType.DeveloperName filter."""
    issues = []
    for match in ACCOUNT_NO_RECORDTYPE.finditer(content):
        # Only flag Apex and SOQL files (not metadata XML config)
        if file_path.suffix in APEX_EXTENSIONS | SOQL_EXTENSIONS:
            line_num = content[: match.start()].count("\n") + 1
            issues.append(
                f"{file_path}:{line_num}: Account queried without RecordType.DeveloperName filter "
                f"— in Communications Cloud all Account queries must filter by RecordType subtype "
                f"(Billing_Account, Service_Account, Consumer_Account)"
            )
    return issues


def check_commerce_order_objects(content: str, file_path: Path) -> list[str]:
    """Warn on use of Salesforce Commerce Order Management objects."""
    issues = []
    if COMMERCE_ORDER_OBJECTS.search(content) or COMMERCE_ORDER_API.search(content):
        # Skip if file is clearly a Commerce-specific file (named commerce*)
        name = file_path.stem.lower()
        if "commerce" not in name:
            match = COMMERCE_ORDER_OBJECTS.search(content) or COMMERCE_ORDER_API.search(content)
            line_num = content[: match.start()].count("\n") + 1
            issues.append(
                f"{file_path}:{line_num}: Commerce Order Management object/API detected "
                f"(OrderSummary, FulfillmentOrder, OrderDeliveryGroup, or /commerce/order-management/). "
                f"In Communications Cloud, use Industries Order Management (vlocity_cmt namespace) — "
                f"not Salesforce Commerce Order Management."
            )
    return issues


def check_product2_direct_insert(content: str, file_path: Path) -> list[str]:
    """Warn on direct Product2 inserts without EPC namespace fields in Apex."""
    issues = []
    if file_path.suffix not in APEX_EXTENSIONS:
        return issues
    if PRODUCT2_DIRECT_INSERT.search(content) and not EPC_NAMESPACE_FIELD.search(content):
        match = PRODUCT2_DIRECT_INSERT.search(content)
        line_num = content[: match.start()].count("\n") + 1
        issues.append(
            f"{file_path}:{line_num}: Product2 inserted directly without vlocity_cmt EPC fields. "
            f"In Communications Cloud, products must be created through EPC "
            f"(Product Specification → Product Offering → Catalog Assignment) "
            f"— direct Product2 inserts bypass order decomposition."
        )
    return issues


def check_contract_status_update(content: str, file_path: Path) -> list[str]:
    """Warn on direct Contract.Status = 'Activated' updates in Apex."""
    issues = []
    if file_path.suffix not in APEX_EXTENSIONS:
        return issues
    if CONTRACT_STATUS_ACTIVATED.search(content) and CONTRACT_CLASS_REFERENCE.search(content):
        # Only flag if vlocity_cmt invocable action is NOT also referenced
        if not EPC_NAMESPACE_FIELD.search(content):
            match = CONTRACT_STATUS_ACTIVATED.search(content)
            line_num = content[: match.start()].count("\n") + 1
            issues.append(
                f"{file_path}:{line_num}: Direct Contract.Status = 'Activated' update detected. "
                f"In Communications Cloud, contract activation must go through Industries Contract "
                f"Management (vlocity_cmt namespace invocable action) to trigger entitlement creation, "
                f"provisioning, and billing events — not a direct field update."
            )
    return issues


def check_omnistudio_product2_query(content: str, file_path: Path) -> list[str]:
    """Warn on OmniStudio/DataRaptor files that query Product2 without EPC filtering."""
    issues = []
    name = file_path.stem.lower()
    # Only flag files that look like OmniStudio artifacts
    is_omnistudio = any(kw in name for kw in ("omniscript", "dataraptor", "flexcard", "iprocedure"))
    if not is_omnistudio:
        return issues
    if OMNISTUDIO_PRODUCT2_QUERY.search(content):
        match = OMNISTUDIO_PRODUCT2_QUERY.search(content)
        line_num = content[: match.start()].count("\n") + 1
        issues.append(
            f"{file_path}:{line_num}: OmniStudio/DataRaptor artifact queries Product2 without "
            f"vlocity_cmt EPC catalog filtering. In Communications Cloud, product queries in "
            f"OmniStudio must use EPC-aware DataRaptors that filter by Catalog Assignment "
            f"and subscriber account segment — not generic Product2 lookups."
        )
    return issues


# ---------------------------------------------------------------------------
# Directory walker
# ---------------------------------------------------------------------------

def check_file(file_path: Path) -> list[str]:
    """Run all checks on a single file. Returns list of issue strings."""
    if file_path.suffix not in ALL_EXTENSIONS:
        return []
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return [f"{file_path}: could not read file"]

    issues: list[str] = []
    issues.extend(check_account_recordtype(content, file_path))
    issues.extend(check_commerce_order_objects(content, file_path))
    issues.extend(check_product2_direct_insert(content, file_path))
    issues.extend(check_contract_status_update(content, file_path))
    issues.extend(check_omnistudio_product2_query(content, file_path))
    return issues


def check_industries_communications_setup(manifest_dir: Path) -> list[str]:
    """Walk manifest_dir and return all issues found."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    for file_path in sorted(manifest_dir.rglob("*")):
        if file_path.is_file():
            issues.extend(check_file(file_path))

    return issues


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for Communications Cloud setup issues: "
            "Account RecordType filtering, Industries vs Commerce Order Management, "
            "EPC product creation, Industries contract activation, and OmniStudio EPC integration."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata to scan (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_industries_communications_setup(manifest_dir)

    if not issues:
        print("No Communications Cloud setup issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    print(f"\n{len(issues)} issue(s) found.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
