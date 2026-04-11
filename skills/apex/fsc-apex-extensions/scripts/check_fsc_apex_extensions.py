#!/usr/bin/env python3
"""Checker script for FSC Apex Extensions skill.

Checks Salesforce metadata for common FSC Apex extension misconfigurations:
- TriggerSettings__c disable/re-enable without a try/finally block
- Direct share record DML on CDS-governed objects
- RollupRecalculationBatchable invocations without an explicit batch size
- Missing TriggerSettings__c setup in test classes

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_fsc_apex_extensions.py [--help]
    python3 check_fsc_apex_extensions.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Detects disable of FSC trigger setting (flag set to false)
_TRIGGER_DISABLE_RE = re.compile(
    r"FinServ__\w+Trigger__c\s*=\s*false",
    re.IGNORECASE,
)

# Detects a finally block — used to verify disable is wrapped
_FINALLY_RE = re.compile(r"\bfinally\b")

# Detects direct share record inserts on FSC-governed objects
_SHARE_INSERT_RE = re.compile(
    r"\binsert\b[^;]*?(AccountShare|FinancialAccountShare|FinServ__FinancialAccountShare__c)\b",
    re.IGNORECASE,
)

# Detects RollupRecalculationBatchable invocation
_ROLLUP_BATCH_RE = re.compile(
    r"FinServ\.RollupRecalculationBatchable\(\)",
    re.IGNORECASE,
)

# Detects executeBatch with explicit second argument (batch size)
_EXECUTE_BATCH_WITH_SIZE_RE = re.compile(
    r"Database\.executeBatch\s*\([^,)]+,\s*\d+\s*\)",
    re.IGNORECASE,
)

# Detects test class annotation
_TEST_CLASS_RE = re.compile(r"@IsTest|@isTest", re.IGNORECASE)

# Detects TriggerSettings__c setup in test classes
_TRIGGER_SETTINGS_SETUP_RE = re.compile(
    r"FinServ__TriggerSettings__c",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Per-file checks
# ---------------------------------------------------------------------------

def check_apex_file(path: Path) -> list[str]:
    """Run FSC Apex extension checks on a single .cls file."""
    issues: list[str] = []
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        issues.append(f"{path}: cannot read file — {exc}")
        return issues

    rel = str(path)

    # Check 1: TriggerSettings disable without try/finally
    if _TRIGGER_DISABLE_RE.search(content):
        if not _FINALLY_RE.search(content):
            issues.append(
                f"{rel}: FinServ__TriggerSettings__c flag disabled but no 'finally' block "
                f"found — if an exception occurs the FSC trigger will remain permanently disabled. "
                f"Wrap the disable/re-enable in a try/finally block."
            )

    # Check 2: Direct share record insert on CDS-governed objects
    for match in _SHARE_INSERT_RE.finditer(content):
        issues.append(
            f"{rel}: Direct insert of share record '{match.group(1)}' detected. "
            f"On CDS-governed objects, manual share records are silently deleted by the CDS "
            f"recalculation job. Use FinServ__ShareParticipant__c inserts instead."
        )

    # Check 3: RollupRecalculationBatchable without explicit batch size
    for match in _ROLLUP_BATCH_RE.finditer(content):
        # Find the executeBatch call that contains this match
        # Look for executeBatch in the surrounding ~200 chars
        start = max(0, match.start() - 50)
        end = min(len(content), match.end() + 50)
        surrounding = content[start:end]
        if "Database.executeBatch" in surrounding or "database.executebatch" in surrounding.lower():
            if not _EXECUTE_BATCH_WITH_SIZE_RE.search(surrounding):
                issues.append(
                    f"{rel}: FinServ.RollupRecalculationBatchable invoked without an explicit "
                    f"batch size. Use Database.executeBatch(new FinServ.RollupRecalculationBatchable(), 200) "
                    f"— the FSC Admin Guide recommends 200 to avoid CPU limit errors on complex household graphs."
                )

    # Check 4: Test class that exercises FSC objects but doesn't set up TriggerSettings__c
    if _TEST_CLASS_RE.search(content):
        has_finserv_dml = re.search(
            r"FinServ__FinancialAccount__c|FinServ__FinancialAccountTransaction__c",
            content,
            re.IGNORECASE,
        )
        if has_finserv_dml and not _TRIGGER_SETTINGS_SETUP_RE.search(content):
            issues.append(
                f"{rel}: Test class operates on FSC FinancialAccount objects but does not "
                f"configure FinServ__TriggerSettings__c. In test context, custom setting defaults "
                f"to all-false, causing trigger handlers to take unexpected code paths. "
                f"Add a @TestSetup method that inserts a FinServ__TriggerSettings__c record."
            )

    return issues


# ---------------------------------------------------------------------------
# Directory traversal
# ---------------------------------------------------------------------------

def check_fsc_apex_extensions(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found across all .cls files in manifest_dir."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    apex_files = list(manifest_dir.rglob("*.cls"))
    if not apex_files:
        # Not necessarily an error — the manifest dir may not contain Apex
        return issues

    for apex_file in apex_files:
        issues.extend(check_apex_file(apex_file))

    return issues


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce Apex metadata for common FSC extension misconfigurations: "
            "missing try/finally on TriggerSettings disablement, direct CDS share DML, "
            "RollupRecalculationBatchable without explicit batch size, and missing test setup."
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
    issues = check_fsc_apex_extensions(manifest_dir)

    if not issues:
        print("No FSC Apex extension issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
