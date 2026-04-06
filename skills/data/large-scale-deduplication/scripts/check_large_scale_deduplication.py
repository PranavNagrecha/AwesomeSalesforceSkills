#!/usr/bin/env python3
"""Checker script for Large Scale Deduplication skill.

Inspects Salesforce metadata in a local manifest directory for common
large-scale deduplication anti-patterns:

  - Apex classes containing Database.merge() calls without batch size constraints
  - Apex classes calling Database.merge() on custom objects
  - Matching rules configured with non-selective (low-cardinality) fields
  - Batch Apex classes with default or oversized batch size declarations

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_large_scale_deduplication.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for large-scale deduplication anti-patterns."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Individual checkers
# ---------------------------------------------------------------------------

def check_apex_merge_in_non_batch_loop(apex_dir: Path) -> list[str]:
    """Flag Apex files where Database.merge() appears inside a for loop
    without an explicit counter guard limiting calls to 10 per transaction.
    """
    issues: list[str] = []
    if not apex_dir.exists():
        return issues

    for apex_file in apex_dir.rglob("*.cls"):
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        # Check if the file contains Database.merge()
        if "Database.merge(" not in content:
            continue

        # Check if it also contains a for/while loop — heuristic risk signal
        has_loop = bool(re.search(r"\bfor\s*\(", content) or re.search(r"\bwhile\s*\(", content))
        # Check if it is a Batchable class
        is_batch = "Database.Batchable" in content
        # Check if there is a merge counter guard (mergeCount, merge_count, etc.)
        has_counter_guard = bool(re.search(r"mergeCount|mergecount|merge_count|mergeLimit|MERGE_LIMIT", content, re.IGNORECASE))

        if has_loop and not is_batch and not has_counter_guard:
            issues.append(
                f"[APEX] {apex_file.name}: Database.merge() inside a loop in a "
                "non-batch class without a call-count guard. Risk: governor limit "
                "exception after 10 merge calls per transaction. "
                "Fix: convert to Batch Apex with batch size = 10."
            )

        if is_batch and has_loop and not has_counter_guard:
            issues.append(
                f"[APEX] {apex_file.name}: Database.merge() inside a loop in a "
                "batch class but no explicit merge-call counter guard found. "
                "Verify batch size is set to 10 when calling Database.executeBatch()."
            )

    return issues


def check_apex_merge_on_custom_objects(apex_dir: Path) -> list[str]:
    """Flag Apex files where Database.merge() is called with a custom object type."""
    issues: list[str] = []
    if not apex_dir.exists():
        return issues

    # Match patterns like: Database.merge(new Something__c(...), ...)
    custom_obj_merge_pattern = re.compile(
        r"Database\.merge\s*\(\s*new\s+\w+__c\s*\(", re.IGNORECASE
    )

    for apex_file in apex_dir.rglob("*.cls"):
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if custom_obj_merge_pattern.search(content):
            issues.append(
                f"[APEX] {apex_file.name}: Database.merge() called with a custom "
                "object (__c suffix). Database.merge() only supports Account, "
                "Contact, and Lead. Fix: use field copy + delete DML for custom "
                "object deduplication."
            )

    return issues


def check_matching_rule_selectivity(matching_rules_dir: Path) -> list[str]:
    """Flag matching rules that use only a single low-cardinality field.

    Checks MatchingRule metadata XML files under matchingRules/.
    """
    issues: list[str] = []
    if not matching_rules_dir.exists():
        return issues

    # Known low-selectivity fields that should not be the sole matching criterion
    low_selectivity_fields = {
        "city", "billingcity", "mailingcity", "state", "billingstate",
        "mailingstate", "country", "billingcountry", "mailingcountry",
        "industry", "leadsource", "rating", "type",
    }

    for xml_file in matching_rules_dir.rglob("*.matchingRule"):
        try:
            content = xml_file.read_text(encoding="utf-8", errors="replace").lower()
        except OSError:
            continue

        # Find all <fieldName> values in the matching rule
        field_names = re.findall(r"<fieldname>([^<]+)</fieldname>", content)
        if not field_names:
            continue

        all_low_selectivity = all(f.strip() in low_selectivity_fields for f in field_names)
        if all_low_selectivity and len(field_names) <= 2:
            issues.append(
                f"[MATCHING_RULE] {xml_file.name}: matching rule uses only "
                f"low-selectivity field(s): {field_names}. At large data volumes, "
                "this causes full-table scans on every save. Include a high-selectivity "
                "field (Email, Phone, External ID) in the matching criteria."
            )

    return issues


def check_batch_apex_size_comments(apex_dir: Path) -> list[str]:
    """Flag batch Apex dedup classes that do not document a batch size recommendation."""
    issues: list[str] = []
    if not apex_dir.exists():
        return issues

    for apex_file in apex_dir.rglob("*.cls"):
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        # Only check batch classes that contain merge calls
        if "Database.Batchable" not in content:
            continue
        if "Database.merge(" not in content:
            continue

        # Check for any mention of batch size guidance
        has_size_guidance = bool(
            re.search(r"batch.?size|batchsize|executeBatch.*,\s*\d+", content, re.IGNORECASE)
        )
        if not has_size_guidance:
            issues.append(
                f"[APEX] {apex_file.name}: Batch Apex class contains Database.merge() "
                "but has no batch size documentation or executeBatch() size argument found. "
                "Always call Database.executeBatch(instance, 10) to enforce the "
                "10-merge-calls-per-transaction governor limit."
            )

    return issues


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def check_large_scale_deduplication(manifest_dir: Path) -> list[str]:
    """Run all deduplication anti-pattern checks and return a list of issues."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Locate common metadata subdirectories
    apex_dir = manifest_dir / "classes"
    if not apex_dir.exists():
        # Try force-app package structure
        apex_dir = manifest_dir / "force-app" / "main" / "default" / "classes"

    matching_rules_dir = manifest_dir / "matchingRules"
    if not matching_rules_dir.exists():
        matching_rules_dir = manifest_dir / "force-app" / "main" / "default" / "matchingRules"

    issues.extend(check_apex_merge_in_non_batch_loop(apex_dir))
    issues.extend(check_apex_merge_on_custom_objects(apex_dir))
    issues.extend(check_matching_rule_selectivity(matching_rules_dir))
    issues.extend(check_batch_apex_size_comments(apex_dir))

    return issues


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_large_scale_deduplication(manifest_dir)

    if not issues:
        print("No large-scale deduplication issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
