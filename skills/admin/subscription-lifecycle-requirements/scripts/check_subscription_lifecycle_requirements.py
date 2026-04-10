#!/usr/bin/env python3
"""Checker script for Subscription Lifecycle Requirements skill.

Validates Salesforce CPQ subscription lifecycle configuration by scanning
force-app metadata XML files for common misconfigurations and anti-patterns.

Checks performed:
  - Detects direct DML field updates on SBQQ__Subscription__c end date or quantity
    fields in Apex classes and triggers (in-place edit anti-pattern)
  - Detects Flow record-update actions targeting SBQQ__Subscription__c fields
    that should only be changed via CPQ amendment processing
  - Checks that CPQ Subscription and Renewal package settings file exists
    (indicates co-termination and renewal settings have been explicitly configured)
  - Detects hardcoded proration logic using 365-day denominators in Apex
    (wrong formula: should use Effective Term / Product Term, not days/365)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_subscription_lifecycle_requirements.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from xml.etree import ElementTree


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Apex fields that should never be written directly on SBQQ__Subscription__c
IMMUTABLE_SUBSCRIPTION_FIELDS = [
    "SBQQ__EndDate__c",
    "SBQQ__StartDate__c",
    "SBQQ__Quantity__c",
    "SBQQ__RegularPrice__c",
    "SBQQ__NetPrice__c",
    "SBQQ__ListPrice__c",
]

# Flow action type for record updates
FLOW_UPDATE_ACTION = "RecordUpdate"

# File globs to search
APEX_GLOB = "**/*.cls"
TRIGGER_GLOB = "**/*.trigger"
FLOW_GLOB = "**/*.flow-meta.xml"
CPQ_SETTINGS_GLOB = "**/SbqqSettings.settings-meta.xml"

# Regex: direct field assignment like  sub.SBQQ__EndDate__c = ...
# or    sub.SBQQ__Quantity__c = ...
_DIRECT_WRITE_PATTERN = re.compile(
    r"\.(%s)\s*=" % "|".join(re.escape(f) for f in IMMUTABLE_SUBSCRIPTION_FIELDS)
)

# Regex: proration using 365 denominator — wrong for CPQ monthly proration
_PRORATION_365_PATTERN = re.compile(
    r"(?i)(prora|prorated|remaining|days)\s*[/*]\s*365"
)

# Namespace for Flow XML
_FLOW_NS = "{http://soap.sforce.com/2006/04/metadata}"


# ---------------------------------------------------------------------------
# Individual check functions
# ---------------------------------------------------------------------------


def check_apex_direct_subscription_writes(manifest_dir: Path) -> list[str]:
    """Flag Apex/trigger files that directly write to immutable subscription fields."""
    issues: list[str] = []
    patterns = list(manifest_dir.glob(APEX_GLOB)) + list(manifest_dir.glob(TRIGGER_GLOB))

    for apex_file in patterns:
        try:
            source = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        # Only care about files that reference SBQQ__Subscription__c at all
        if "SBQQ__Subscription__c" not in source:
            continue

        for line_num, line in enumerate(source.splitlines(), start=1):
            if _DIRECT_WRITE_PATTERN.search(line):
                field_match = _DIRECT_WRITE_PATTERN.search(line)
                field_name = field_match.group(1) if field_match else "unknown field"
                issues.append(
                    f"{apex_file.relative_to(manifest_dir)}:{line_num} — "
                    f"Direct write to {field_name} on SBQQ__Subscription__c detected. "
                    f"Subscription fields must be changed through CPQ amendment processing, "
                    f"not by direct DML. See subscription-lifecycle-requirements gotchas."
                )

    return issues


def check_flow_subscription_updates(manifest_dir: Path) -> list[str]:
    """Flag Flow files that attempt to update SBQQ__Subscription__c records directly."""
    issues: list[str] = []

    for flow_file in manifest_dir.glob(FLOW_GLOB):
        try:
            tree = ElementTree.parse(flow_file)
        except (OSError, ElementTree.ParseError):
            continue

        root = tree.getroot()
        # Look for recordUpdates elements
        for record_update in root.iter(f"{_FLOW_NS}recordUpdates"):
            # Check if object is SBQQ__Subscription__c
            object_elem = record_update.find(f"{_FLOW_NS}object")
            if object_elem is None or object_elem.text != "SBQQ__Subscription__c":
                continue

            # Check what fields are being set
            for field_elem in record_update.iter(f"{_FLOW_NS}field"):
                name_elem = field_elem.find(f"{_FLOW_NS}name")
                if name_elem is not None and name_elem.text in IMMUTABLE_SUBSCRIPTION_FIELDS:
                    issues.append(
                        f"{flow_file.relative_to(manifest_dir)} — "
                        f"Flow RecordUpdate targets {name_elem.text} on SBQQ__Subscription__c. "
                        f"This field must be modified through a CPQ amendment, not a direct "
                        f"Flow record update. End dates and prices are immutable on activated "
                        f"contract subscriptions."
                    )

    return issues


def check_proration_formula(manifest_dir: Path) -> list[str]:
    """Detect use of /365 denominator in Apex proration calculations."""
    issues: list[str] = []
    patterns = list(manifest_dir.glob(APEX_GLOB)) + list(manifest_dir.glob(TRIGGER_GLOB))

    for apex_file in patterns:
        try:
            source = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if not _PRORATION_365_PATTERN.search(source):
            continue

        for line_num, line in enumerate(source.splitlines(), start=1):
            if _PRORATION_365_PATTERN.search(line):
                issues.append(
                    f"{apex_file.relative_to(manifest_dir)}:{line_num} — "
                    f"Possible /365 proration formula detected. CPQ uses "
                    f"(Effective Term / Product Term) × Unit Price, not days/365. "
                    f"Confirm the proration method is monthly or daily and matches "
                    f"the agreed proration requirements."
                )

    return issues


def check_cpq_settings_present(manifest_dir: Path) -> list[str]:
    """Warn if no SbqqSettings metadata file is found in the project."""
    issues: list[str] = []
    settings_files = list(manifest_dir.glob(CPQ_SETTINGS_GLOB))

    if not settings_files:
        issues.append(
            "No SbqqSettings.settings-meta.xml found under the manifest directory. "
            "CPQ subscription and renewal package settings (co-termination, auto-renew, "
            "default renewal term) may not be explicitly configured. "
            "Verify CPQ Settings in Setup before proceeding with amendments and renewals."
        )

    return issues


def check_subscription_ledger_aggregate_queries(manifest_dir: Path) -> list[str]:
    """Flag SOQL queries on SBQQ__Subscription__c that may return only the latest record.

    Queries that ORDER BY CreatedDate DESC LIMIT 1 return only the most recent
    delta record, not the total entitlement. Total entitlement requires SUM aggregation.
    """
    issues: list[str] = []
    # Pattern: SELECT ... FROM SBQQ__Subscription__c ... LIMIT 1
    # without a SUM() in the SELECT list
    _ledger_query_pattern = re.compile(
        r"FROM\s+SBQQ__Subscription__c.*?LIMIT\s+1",
        re.IGNORECASE | re.DOTALL,
    )
    _has_sum = re.compile(r"\bSUM\s*\(", re.IGNORECASE)

    for apex_file in list(manifest_dir.glob(APEX_GLOB)) + list(manifest_dir.glob(TRIGGER_GLOB)):
        try:
            source = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if "SBQQ__Subscription__c" not in source:
            continue

        for match in _ledger_query_pattern.finditer(source):
            query_fragment = match.group(0)
            if not _has_sum.search(query_fragment):
                line_num = source[: match.start()].count("\n") + 1
                issues.append(
                    f"{apex_file.relative_to(manifest_dir)}:{line_num} — "
                    f"SOQL query on SBQQ__Subscription__c with LIMIT 1 detected without SUM(). "
                    f"CPQ uses an additive ledger model — a contract has multiple subscription "
                    f"records per product after amendments. Reading LIMIT 1 returns only the "
                    f"most recent delta, not total entitlement. Use SUM(SBQQ__Quantity__c) "
                    f"GROUP BY SBQQ__Product__c to aggregate correctly."
                )

    return issues


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def check_subscription_lifecycle_requirements(manifest_dir: Path) -> list[str]:
    """Run all checks and return a list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_apex_direct_subscription_writes(manifest_dir))
    issues.extend(check_flow_subscription_updates(manifest_dir))
    issues.extend(check_proration_formula(manifest_dir))
    issues.extend(check_cpq_settings_present(manifest_dir))
    issues.extend(check_subscription_ledger_aggregate_queries(manifest_dir))

    return issues


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce CPQ subscription lifecycle metadata for common "
            "misconfigurations and anti-patterns."
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
    issues = check_subscription_lifecycle_requirements(manifest_dir)

    if not issues:
        print("No subscription lifecycle issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
