#!/usr/bin/env python3
"""Checker script for Subscription Management Architecture skill.

Scans Salesforce metadata (retrieved via sfdx/sf force:source:retrieve or similar)
for configuration anti-patterns documented in the subscription-management-architecture skill.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_subscription_arch.py [--help]
    python3 check_subscription_arch.py --manifest-dir path/to/metadata
    python3 check_subscription_arch.py --manifest-dir force-app/main/default

Checks performed:
    1. SBQQ__Subscription__c triggers that perform DML update on subscription records
    2. Flows that set Contract Status = Activated without checking for pending async jobs
    3. CPQ Settings: Preserve Bundle Structure + Combine Subscription Quantities both enabled
    4. Subscription queries using ORDER BY CreatedDate DESC LIMIT 1 (stale-state anti-pattern)
    5. Apex that directly updates SBQQ__Subscription__c fields post-insert
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Anti-pattern 1: Apex DML update targeting SBQQ__Subscription__c
APEX_UPDATE_SUBSCRIPTION_RE = re.compile(
    r"\bupdate\s+\w*[Ss]ubscription\w*\b",
    re.MULTILINE,
)

# Anti-pattern 2: Apex direct field assignment on SBQQ__Subscription__c objects
APEX_SUB_FIELD_ASSIGN_RE = re.compile(
    r"SBQQ__Subscription__c\s*\.\s*(?:SBQQ__Quantity__c|SBQQ__NetPrice__c|SBQQ__SubscriptionStartDate__c)\s*=",
    re.MULTILINE,
)

# Anti-pattern 3: SOQL ORDER BY CreatedDate DESC LIMIT 1 on Subscription
SOQL_LATEST_SUBSCRIPTION_RE = re.compile(
    r"FROM\s+SBQQ__Subscription__c\b[^;]*ORDER\s+BY\s+CreatedDate\s+DESC\s+LIMIT\s+1",
    re.MULTILINE | re.DOTALL,
)

# Anti-pattern 4: Flow metadata setting Contract.Status = 'Activated' (simplified heuristic)
FLOW_ACTIVATE_CONTRACT_RE = re.compile(
    r"<value>Activated</value>",
    re.MULTILINE,
)

# Anti-pattern 5: CPQ Settings metadata with both conflicting settings true
CPQ_PRESERVE_BUNDLE_RE = re.compile(
    r"<SBQQ__PreserveBundleStructure__c>true</SBQQ__PreserveBundleStructure__c>",
    re.MULTILINE,
)
CPQ_COMBINE_QUANTITIES_RE = re.compile(
    r"<SBQQ__CombineSubscriptionQuantities__c>true</SBQQ__CombineSubscriptionQuantities__c>",
    re.MULTILINE,
)


# ---------------------------------------------------------------------------
# File-level checks
# ---------------------------------------------------------------------------

def check_apex_files(manifest_dir: Path) -> list[str]:
    issues: list[str] = []
    apex_files = list(manifest_dir.rglob("*.cls")) + list(manifest_dir.rglob("*.trigger"))
    for apex_file in apex_files:
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if APEX_UPDATE_SUBSCRIPTION_RE.search(content):
            # Only flag if this looks like it is operating on subscription vars
            if "SBQQ__Subscription__c" in content:
                issues.append(
                    f"{apex_file}: possible direct DML update on SBQQ__Subscription__c records — "
                    "amendments must go through CPQ Amendment Quote, not direct DML. "
                    "See references/llm-anti-patterns.md Anti-Pattern 1."
                )

        if APEX_SUB_FIELD_ASSIGN_RE.search(content):
            issues.append(
                f"{apex_file}: direct field assignment on SBQQ__Subscription__c detected "
                "(SBQQ__Quantity__c, SBQQ__NetPrice__c, or SBQQ__SubscriptionStartDate__c). "
                "Existing subscription records must not be mutated post-activation. "
                "See references/gotchas.md Gotcha 1 and Gotcha 2."
            )

        if SOQL_LATEST_SUBSCRIPTION_RE.search(content):
            issues.append(
                f"{apex_file}: SOQL query on SBQQ__Subscription__c uses ORDER BY CreatedDate DESC LIMIT 1. "
                "This returns a delta record, not the effective subscription state. "
                "Aggregate all records by contract+product instead. "
                "See references/llm-anti-patterns.md Anti-Pattern 2."
            )

    return issues


def check_flow_files(manifest_dir: Path) -> list[str]:
    issues: list[str] = []
    flow_files = list(manifest_dir.rglob("*.flow-meta.xml")) + list(manifest_dir.rglob("*.flow"))
    for flow_file in flow_files:
        try:
            content = flow_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if FLOW_ACTIVATE_CONTRACT_RE.search(content) and "Contract" in content:
            issues.append(
                f"{flow_file}: Flow appears to set Contract Status = 'Activated'. "
                "Verify this Flow does not fire before SBQQ.AmendmentBatchJob completes "
                "when Large-Scale async amendments are in use. Premature activation generates "
                "billing schedules against pre-amendment subscription data. "
                "See references/gotchas.md Gotcha 5."
            )

    return issues


def check_cpq_settings(manifest_dir: Path) -> list[str]:
    issues: list[str] = []
    # CPQ Settings are stored in Custom Settings or Custom Metadata — look for any XML
    # that might contain both flags (e.g., retrieved via sfdx as customSettings or similar)
    setting_files = (
        list(manifest_dir.rglob("SBQQ__Preferences__c*"))
        + list(manifest_dir.rglob("*cpq*settings*"))
        + list(manifest_dir.rglob("*CPQSettings*"))
        + list(manifest_dir.rglob("*.settings-meta.xml"))
    )
    for setting_file in setting_files:
        try:
            content = setting_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        has_preserve = CPQ_PRESERVE_BUNDLE_RE.search(content) is not None
        has_combine = CPQ_COMBINE_QUANTITIES_RE.search(content) is not None

        if has_preserve and has_combine:
            issues.append(
                f"{setting_file}: SBQQ__PreserveBundleStructure__c and "
                "SBQQ__CombineSubscriptionQuantities__c are BOTH set to true. "
                "These settings are mutually exclusive — Combine Subscription Quantities "
                "silently overrides Preserve Bundle Structure, destroying bundle hierarchies "
                "in subscription records. Disable one. "
                "See references/gotchas.md Gotcha 3 and references/llm-anti-patterns.md Anti-Pattern 3."
            )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_subscription_arch(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_apex_files(manifest_dir))
    issues.extend(check_flow_files(manifest_dir))
    issues.extend(check_cpq_settings(manifest_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for CPQ subscription architecture anti-patterns. "
            "Covers ledger model violations, co-termination date mutations, conflicting "
            "CPQ settings, and async amendment sequencing issues."
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
    issues = check_subscription_arch(manifest_dir)

    if not issues:
        print("No subscription architecture issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    print(f"\n{len(issues)} issue(s) found.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
