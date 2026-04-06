#!/usr/bin/env python3
"""Checker script for Territory API and Assignment skill.

Scans Apex class files (.cls) for common territory API anti-patterns described
in references/gotchas.md and references/llm-anti-patterns.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_territory_api_and_assignment.py [--help]
    python3 check_territory_api_and_assignment.py --manifest-dir path/to/force-app

Checks performed:
  1. Detects Apex triggers declared on ObjectTerritory2Association (never fire).
  2. Detects UserInfo.getSessionId() calls in async Apex classes
     (Database.Batchable, Queueable, Schedulable, @future).
  3. Detects raw `insert` (not Database.insert) on territory association objects.
  4. Detects ObjectTerritory2Association inserts where AssociationCause is set
     to 'Territory2RuleAssociation' (invalid for DML; platform-controlled only).
  5. Detects ObjectTerritory2Association or UserTerritory2Association inserts
     inside a for-loop (DML-in-loop anti-pattern).
  6. Detects SOAP rule evaluation callout patterns that lack chunking logic
     (no subList or modulo 200 guard nearby).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Compiled patterns
# ---------------------------------------------------------------------------

# Trigger declarations on ObjectTerritory2Association — never fire
RE_OTA_TRIGGER = re.compile(
    r'\btrigger\b\s+\w+\s+on\s+ObjectTerritory2Association\b',
    re.IGNORECASE,
)

# UserInfo.getSessionId() usage
RE_GET_SESSION_ID = re.compile(
    r'\bUserInfo\s*\.\s*getSessionId\s*\(\s*\)',
    re.IGNORECASE,
)

# Async class indicators
RE_BATCHABLE = re.compile(r'\bimplements\b[^{]*\bDatabase\.Batchable\b', re.IGNORECASE)
RE_QUEUEABLE = re.compile(r'\bimplements\b[^{]*\bQueueable\b', re.IGNORECASE)
RE_SCHEDULABLE = re.compile(r'\bimplements\b[^{]*\bSchedulable\b', re.IGNORECASE)
RE_FUTURE = re.compile(r'@future', re.IGNORECASE)

# Raw insert on territory association objects (not Database.insert)
# Match lines with bare `insert` keyword followed by a reference to the association objects
RE_RAW_INSERT_UTA = re.compile(
    r'(?<!Database\.)\binsert\b(?!\s*\().*\bUserTerritory2Association\b',
    re.IGNORECASE,
)
RE_RAW_INSERT_OTA = re.compile(
    r'(?<!Database\.)\binsert\b(?!\s*\().*\bObjectTerritory2Association\b',
    re.IGNORECASE,
)

# Safe Database.insert pattern
RE_DB_INSERT = re.compile(r'\bDatabase\s*\.\s*insert\b', re.IGNORECASE)

# Any insert referencing territory association objects (for DML-in-loop check)
RE_ANY_ASSOC_INSERT = re.compile(
    r'\b(?:Database\.insert|insert)\b.*\b(?:UserTerritory2Association|ObjectTerritory2Association)\b',
    re.IGNORECASE,
)

# for-loop detection (simple heuristic: `for (` on its own line or before the insert line)
RE_FOR_LOOP = re.compile(r'\bfor\s*\(', re.IGNORECASE)

# AssociationCause = 'Territory2RuleAssociation'
RE_RULE_ASSOC_CAUSE = re.compile(
    r'''AssociationCause\s*=\s*['"]Territory2RuleAssociation['"]\s*''',
    re.IGNORECASE,
)

# ObjectTerritory2Association reference (for context in AssociationCause check)
RE_OTA_REF = re.compile(r'\bObjectTerritory2Association\b', re.IGNORECASE)

# SOAP rule evaluation heuristic: callout to /services/Soap combined with territory
RE_SOAP_CALLOUT = re.compile(
    r'/services/Soap.*[Tt]erritor|[Tt]erritor.*evaluateRules',
    re.IGNORECASE,
)

# Chunking guard for SOAP callout
RE_CHUNK_GUARD = re.compile(
    r'subList\s*\(|%\s*200\b|\bMath\.min\s*\(',
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Per-file analysis
# ---------------------------------------------------------------------------

def analyse_file(path: Path) -> list[str]:
    """Return a list of issue strings for a single Apex source file."""
    issues: list[str] = []

    try:
        source = path.read_text(encoding='utf-8', errors='replace')
    except OSError as exc:
        return [f"{path}: cannot read file — {exc}"]

    lines = source.splitlines()
    is_trigger_file = path.suffix.lower() == '.trigger'

    # ------------------------------------------------------------------
    # Check 1: Trigger declared on ObjectTerritory2Association
    # ------------------------------------------------------------------
    for i, line in enumerate(lines, start=1):
        if RE_OTA_TRIGGER.search(line):
            issues.append(
                f"{path.name}:{i}: Apex trigger declared on ObjectTerritory2Association. "
                "Apex triggers NEVER fire on this object — the trigger will deploy "
                "successfully but its body will never execute. "
                "Use Platform Events dispatched from the service that performs "
                "ObjectTerritory2Association DML instead."
            )

    # ------------------------------------------------------------------
    # Check 2: UserInfo.getSessionId() in async Apex class
    # ------------------------------------------------------------------
    is_async = (
        bool(RE_BATCHABLE.search(source)) or
        bool(RE_QUEUEABLE.search(source)) or
        bool(RE_SCHEDULABLE.search(source)) or
        bool(RE_FUTURE.search(source))
    )
    if is_async and RE_GET_SESSION_ID.search(source):
        issues.append(
            f"{path.name}: UserInfo.getSessionId() called in an async Apex class "
            "(implements Database.Batchable, Queueable, Schedulable, or @future). "
            "getSessionId() returns null in async contexts. SOAP callouts for ETM "
            "rule evaluation will fail silently. "
            "Move the SOAP callout to a synchronous context via a Platform Event subscriber."
        )

    # ------------------------------------------------------------------
    # Check 3: Raw insert (not Database.insert) on association objects
    # ------------------------------------------------------------------
    has_db_insert = bool(RE_DB_INSERT.search(source))
    for i, line in enumerate(lines, start=1):
        if RE_RAW_INSERT_UTA.search(line) or RE_RAW_INSERT_OTA.search(line):
            # Only flag if Database.insert is not used anywhere in this file
            if not has_db_insert:
                issues.append(
                    f"{path.name}:{i}: Raw 'insert' on UserTerritory2Association or "
                    "ObjectTerritory2Association detected without Database.insert. "
                    "A DUPLICATE_VALUE error on any row rolls back the entire transaction. "
                    "Use Database.insert(list, false) and inspect SaveResult errors."
                )

    # ------------------------------------------------------------------
    # Check 4: AssociationCause = 'Territory2RuleAssociation' in DML context
    # ------------------------------------------------------------------
    if RE_OTA_REF.search(source) and RE_RULE_ASSOC_CAUSE.search(source):
        for i, line in enumerate(lines, start=1):
            if RE_RULE_ASSOC_CAUSE.search(line):
                issues.append(
                    f"{path.name}:{i}: AssociationCause set to 'Territory2RuleAssociation'. "
                    "This value is platform-controlled and cannot be set via Apex DML. "
                    "Inserting an ObjectTerritory2Association with this AssociationCause "
                    "throws a FIELD_INTEGRITY_EXCEPTION at runtime. "
                    "Use AssociationCause = 'Territory' for API-managed inserts."
                )

    # ------------------------------------------------------------------
    # Check 5: DML-in-loop on territory association objects
    # ------------------------------------------------------------------
    for i, line in enumerate(lines, start=1):
        if RE_ANY_ASSOC_INSERT.search(line):
            # Look back up to 5 lines for an unclosed for-loop
            context_start = max(0, i - 6)
            context_lines = lines[context_start:i - 1]
            for ctx_line in context_lines:
                if RE_FOR_LOOP.search(ctx_line):
                    issues.append(
                        f"{path.name}:{i}: Territory association DML "
                        "(UserTerritory2Association or ObjectTerritory2Association insert) "
                        "appears inside or immediately after a for-loop. "
                        "DML inside loops exhausts DML statement limits (150/transaction). "
                        "Collect association records into a list and insert once outside the loop."
                    )
                    break  # Only report once per insert line

    # ------------------------------------------------------------------
    # Check 6: SOAP rule evaluation without chunking guard
    # ------------------------------------------------------------------
    if RE_SOAP_CALLOUT.search(source):
        if not RE_CHUNK_GUARD.search(source):
            issues.append(
                f"{path.name}: SOAP territory rule evaluation callout detected but no "
                "chunking logic found (subList, Math.min, or modulo 200 pattern). "
                "The ETM SOAP rule evaluation endpoint accepts at most 200 Account IDs "
                "per request. Passing more than 200 IDs returns a SOAP fault. "
                "Chunk account ID lists into batches of ≤200 before calling."
            )

    return issues


# ---------------------------------------------------------------------------
# Directory scan
# ---------------------------------------------------------------------------

def check_territory_api_and_assignment(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found across all Apex source files."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Scan .cls and .trigger files
    apex_files = list(manifest_dir.rglob('*.cls')) + list(manifest_dir.rglob('*.trigger'))
    if not apex_files:
        issues.append(
            f"No .cls or .trigger files found under {manifest_dir}. "
            "Pass the root of your Salesforce source directory with --manifest-dir."
        )
        return issues

    territory_files_found = 0
    for apex_file in apex_files:
        try:
            source_peek = apex_file.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue

        # Only analyse files that reference territory association objects or ETM SOAP
        if not (
            'UserTerritory2Association' in source_peek
            or 'ObjectTerritory2Association' in source_peek
            or 'evaluateRules' in source_peek
            or 'Territory2Association' in source_peek
        ):
            continue

        territory_files_found += 1
        file_issues = analyse_file(apex_file)
        issues.extend(file_issues)

    if territory_files_found == 0:
        print(
            f"INFO: No Apex files referencing UserTerritory2Association, "
            f"ObjectTerritory2Association, or evaluateRules found under "
            f"{manifest_dir}. If this org uses ETM programmatic assignment, "
            f"verify --manifest-dir points to the Apex classes directory."
        )

    return issues


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Apex classes and triggers for common ETM territory API issues: "
            "triggers on ObjectTerritory2Association (never fire), "
            "getSessionId() in async context, unsafe raw inserts without "
            "Database.insert(list, false), invalid AssociationCause values, "
            "DML-in-loop patterns, and missing chunking for SOAP rule evaluation."
        ),
    )
    parser.add_argument(
        '--manifest-dir',
        default='.',
        help=(
            'Root directory of the Salesforce source (default: current directory). '
            'Scans all .cls and .trigger files recursively.'
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_territory_api_and_assignment(manifest_dir)

    if not issues:
        print('No territory API and assignment issues found.')
        return 0

    for issue in issues:
        print(f'ISSUE: {issue}')

    return 1


if __name__ == '__main__':
    sys.exit(main())
