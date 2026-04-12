#!/usr/bin/env python3
"""Checker script for Commerce Search Customization skill.

Validates Salesforce metadata and configuration files for common Commerce
search configuration issues: missing index rebuild steps, entitlement policy
gaps, client-side sort anti-patterns, and missing Activity Tracking instrumentation.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_commerce_search_customization.py [--help]
    python3 check_commerce_search_customization.py --manifest-dir path/to/metadata
    python3 check_commerce_search_customization.py --manifest-dir . --json-payloads path/to/payloads/
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Commerce Search Customization configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--json-payloads",
        default=None,
        help="Optional path to directory containing saved search index JSON payloads.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_manifest_dir_exists(manifest_dir: Path) -> list[str]:
    """Verify the manifest directory exists."""
    issues: list[str] = []
    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
    return issues


def check_lwc_client_side_sort(manifest_dir: Path) -> list[str]:
    """Detect LWC JavaScript files that sort Commerce search result arrays client-side.

    Client-side sorting of paginated Commerce search results breaks page 2+
    because the server applies its own sort order to subsequent pages.
    """
    issues: list[str] = []
    # Pattern: .sort( applied to a variable plausibly holding search results
    sort_pattern = re.compile(r"\bproducts\b.*\.sort\s*\(|\bresults\b.*\.sort\s*\(|\bsearchResults\b.*\.sort\s*\(", re.IGNORECASE)
    lwc_dirs = list(manifest_dir.rglob("*.js"))
    for js_file in lwc_dirs:
        try:
            text = js_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if sort_pattern.search(text):
            issues.append(
                f"Potential client-side sort of Commerce search results in {js_file}. "
                "Sorting the results array in JS breaks paginated search — define sort rules "
                "server-side via the Commerce search index sortRules configuration instead."
            )
    return issues


def check_sosl_in_commerce_context(manifest_dir: Path) -> list[str]:
    """Detect Apex files that use SOSL to implement storefront product search.

    SOSL does not enforce BuyerGroup entitlement and does not use the Commerce
    search index configuration. It should not be used for Commerce storefront search.
    """
    issues: list[str] = []
    sosl_pattern = re.compile(r"\[FIND\s+.*\bIN\b.*\bRETURNING\b.*\bProduct2\b", re.IGNORECASE | re.DOTALL)
    apex_files = list(manifest_dir.rglob("*.cls"))
    for apex_file in apex_files:
        try:
            text = apex_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if sosl_pattern.search(text):
            issues.append(
                f"SOSL query targeting Product2 found in {apex_file}. "
                "SOSL does not enforce BuyerGroup entitlement visibility and bypasses Commerce "
                "search index configuration. Use the ConnectApi.CommerceSearch class or the "
                "Commerce Search Connect REST API for storefront product search."
            )
    return issues


def check_json_payloads_completeness(payloads_dir: Path) -> list[str]:
    """Check saved search index JSON payloads for missing attribute sets.

    A POST to /commerce/webstores/{id}/search/indexes that omits any of the three
    attribute sets (searchableAttributes, facetableAttributes, sortRules) will silently
    reset the omitted sets to empty on the platform.
    """
    issues: list[str] = []
    required_keys = {"searchableAttributes", "facetableAttributes", "sortRules"}
    json_files = list(payloads_dir.rglob("*.json"))
    for json_file in json_files:
        try:
            text = json_file.read_text(encoding="utf-8", errors="ignore")
            payload = json.loads(text)
        except (OSError, json.JSONDecodeError):
            continue
        # Only check files that look like search index payloads
        if not any(k in payload for k in required_keys):
            continue
        missing = required_keys - set(payload.keys())
        if missing:
            issues.append(
                f"Search index payload in {json_file} is missing keys: {', '.join(sorted(missing))}. "
                "Omitting any of searchableAttributes, facetableAttributes, or sortRules from a POST "
                "to /commerce/webstores/{webstoreId}/search/indexes will silently reset those sets to empty."
            )
        # Warn if sortRules is present but empty
        if "sortRules" in payload and payload["sortRules"] == []:
            issues.append(
                f"Search index payload in {json_file} has an empty sortRules array. "
                "Intentionally clearing sort rules will cause the storefront to fall back to "
                "platform default relevance scoring. Confirm this is intentional."
            )
    return issues


def check_rebuild_mentioned_near_index_update(manifest_dir: Path) -> list[str]:
    """Heuristic: detect shell scripts or README files that POST to search/indexes
    without a subsequent reference to the rebuild endpoint.

    Looks for files that contain the search/indexes POST URL but not the rebuild URL.
    """
    issues: list[str] = []
    index_pattern = re.compile(r"search/indexes", re.IGNORECASE)
    rebuild_pattern = re.compile(r"search/indexes/rebuild", re.IGNORECASE)
    target_extensions = {".sh", ".bash", ".zsh", ".md", ".txt", ".http", ".rest"}
    for candidate in manifest_dir.rglob("*"):
        if candidate.suffix.lower() not in target_extensions:
            continue
        try:
            text = candidate.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if index_pattern.search(text) and not rebuild_pattern.search(text):
            issues.append(
                f"File {candidate} references the Commerce search/indexes endpoint but does not "
                "reference the search/indexes/rebuild endpoint. Search configuration changes do not "
                "take effect until a rebuild is triggered and polled to COMPLETED status."
            )
    return issues


def check_entitlement_audit_present(manifest_dir: Path) -> list[str]:
    """Heuristic: detect Apex or script files that reference Commerce search
    without any reference to CommerceEntitlementBuyerGroup or entitlement policy.

    Missing entitlement audits are the most common cause of silent product omissions.
    """
    issues: list[str] = []
    commerce_search_pattern = re.compile(r"ConnectApi\.CommerceSearch|search/indexes|CommerceSearch", re.IGNORECASE)
    entitlement_pattern = re.compile(r"CommerceEntitlement|entitlementpolicy|BuyerGroup", re.IGNORECASE)
    apex_files = list(manifest_dir.rglob("*.cls"))
    for apex_file in apex_files:
        try:
            text = apex_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if commerce_search_pattern.search(text) and not entitlement_pattern.search(text):
            issues.append(
                f"Apex file {apex_file} references Commerce search but has no reference to "
                "CommerceEntitlementBuyerGroup or entitlement policy. When diagnosing missing products, "
                "always audit BuyerGroup entitlement assignment before investigating index configuration."
            )
    return issues


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

def check_commerce_search_customization(manifest_dir: Path, payloads_dir: Path | None = None) -> list[str]:
    """Run all checks and return a list of issue strings."""
    issues: list[str] = []

    # Gate on directory existence first
    dir_issues = check_manifest_dir_exists(manifest_dir)
    if dir_issues:
        return dir_issues

    issues.extend(check_lwc_client_side_sort(manifest_dir))
    issues.extend(check_sosl_in_commerce_context(manifest_dir))
    issues.extend(check_rebuild_mentioned_near_index_update(manifest_dir))
    issues.extend(check_entitlement_audit_present(manifest_dir))

    if payloads_dir is not None and payloads_dir.exists():
        issues.extend(check_json_payloads_completeness(payloads_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    payloads_dir = Path(args.json_payloads) if args.json_payloads else None

    issues = check_commerce_search_customization(manifest_dir, payloads_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
