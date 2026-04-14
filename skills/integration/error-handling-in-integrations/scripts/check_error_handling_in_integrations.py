#!/usr/bin/env python3
"""Checker script for Error Handling In Integrations skill.

Scans Salesforce Apex source files in a metadata directory for common
integration error-handling anti-patterns documented in this skill.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_error_handling_in_integrations.py --apex-dir path/to/force-app/main/default/triggers
    python3 check_error_handling_in_integrations.py --apex-dir path/to/force-app/main/default/classes
    python3 check_error_handling_in_integrations.py --apex-dir . --verbose
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Matches a catch block that immediately throws RetryableException without
# first checking for a specific exception type — indicates blanket retry of
# permanent errors.
CATCH_ALL_RETRYABLE = re.compile(
    r"catch\s*\(\s*Exception\s+\w+\s*\)"    # catch (Exception e)
    r".*?"                                    # any content
    r"throw\s+new\s+EventBus\.RetryableException",
    re.DOTALL,
)

# Detects a catch block that only calls System.debug (no DLQ insert, no
# RetryableException throw) — silent discard anti-pattern.
SILENT_DISCARD = re.compile(
    r"catch\s*\([^)]+\)\s*\{[^}]*System\.debug\([^}]*\}",
    re.DOTALL,
)

# Detects Platform Event trigger files — look for "on \w+__e (after insert)"
PLATFORM_EVENT_TRIGGER = re.compile(
    r"trigger\s+\w+\s+on\s+\w+__e\s*\(",
    re.IGNORECASE,
)

# Checks whether a Platform Event trigger stores ReplayId
REPLAY_ID_STORED = re.compile(
    r"Last_Replay_Id__c\s*=\s*\w+\.ReplayId",
    re.IGNORECASE,
)

# Checks whether a Platform Event trigger has a DLQ insert
DLQ_INSERT = re.compile(
    r"insert\s+new\s+Integration_DLQ__c\s*\(",
    re.IGNORECASE,
)

# Detects Apex callout code that retries without any circuit-breaker state check
CALLOUT_NO_CB = re.compile(
    r"Http\(\)\.send\(",
    re.IGNORECASE,
)

CIRCUIT_BREAKER_CHECK = re.compile(
    r"Integration_Circuit_Breaker__c",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# File-level checkers
# ---------------------------------------------------------------------------

def check_apex_file(path: Path, verbose: bool) -> list[str]:
    """Run all checks against a single Apex file. Returns list of issue strings."""
    issues: list[str] = []
    content = path.read_text(encoding="utf-8", errors="replace")
    name = path.name

    is_pe_trigger = bool(PLATFORM_EVENT_TRIGGER.search(content))

    # Anti-pattern 1: catch (Exception e) that directly throws RetryableException
    if CATCH_ALL_RETRYABLE.search(content):
        issues.append(
            f"{name}: catch (Exception e) block throws EventBus.RetryableException — "
            "RetryableException should only be thrown for transient exceptions, not all exceptions. "
            "Permanent errors thrown here will exhaust 9 retries and suspend the trigger. "
            "[anti-pattern: RetryableException for all exceptions]"
        )

    # Anti-pattern 2: catch block with only System.debug (silent discard)
    if SILENT_DISCARD.search(content):
        issues.append(
            f"{name}: catch block appears to only call System.debug without DLQ insert or RetryableException — "
            "silent discard causes permanent data loss. "
            "Persist failed events to Integration_DLQ__c. "
            "[anti-pattern: silent failure discard]"
        )

    # Anti-pattern 3: Platform Event trigger without Replay ID storage
    if is_pe_trigger and not REPLAY_ID_STORED.search(content):
        issues.append(
            f"{name}: Platform Event trigger does not store Last_Replay_Id__c — "
            "without Replay ID tracking, trigger suspension recovery cannot replay missed events. "
            "Store event.ReplayId to Integration_State__c.getInstance() on each successful processing. "
            "[anti-pattern: no Replay ID tracking]"
        )

    # Anti-pattern 4: Platform Event trigger without DLQ insert
    if is_pe_trigger and not DLQ_INSERT.search(content):
        issues.append(
            f"{name}: Platform Event trigger has no Integration_DLQ__c insert — "
            "permanent errors that are not written to a DLQ are silently lost. "
            "Add DLQ insert in the permanent-error catch branch. "
            "[anti-pattern: no DLQ]"
        )

    # Anti-pattern 5: HTTP callout without circuit breaker state check
    if CALLOUT_NO_CB.search(content) and not CIRCUIT_BREAKER_CHECK.search(content):
        issues.append(
            f"{name}: HTTP callout (Http().send()) found without circuit breaker check — "
            "if the external system is down, retrying without a circuit breaker can exhaust Salesforce API limits. "
            "Add Integration_Circuit_Breaker__c state check before every outbound callout. "
            "[anti-pattern: no circuit breaker]"
        )

    if verbose and not issues:
        print(f"  OK  {name}")

    return issues


# ---------------------------------------------------------------------------
# Directory walker
# ---------------------------------------------------------------------------

def scan_directory(apex_dir: Path, verbose: bool) -> list[str]:
    """Walk apex_dir and check all .cls and .trigger files. Returns all issues."""
    all_issues: list[str] = []

    apex_files = list(apex_dir.rglob("*.trigger")) + list(apex_dir.rglob("*.cls"))

    if not apex_files:
        print(f"No .cls or .trigger files found under: {apex_dir}", file=sys.stderr)
        return all_issues

    if verbose:
        print(f"Scanning {len(apex_files)} Apex file(s) under {apex_dir} ...")

    for apex_file in sorted(apex_files):
        file_issues = check_apex_file(apex_file, verbose)
        all_issues.extend(file_issues)

    return all_issues


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Apex metadata for integration error-handling anti-patterns: "
            "RetryableException misuse, silent DLQ discard, missing Replay ID tracking, "
            "no DLQ insert in Platform Event triggers, and missing circuit breakers."
        ),
    )
    parser.add_argument(
        "--apex-dir",
        default=".",
        help="Root directory containing .cls and .trigger files (default: current directory).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print OK lines for files that pass all checks.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    apex_dir = Path(args.apex_dir)

    if not apex_dir.exists():
        print(f"ERROR: Directory not found: {apex_dir}", file=sys.stderr)
        return 2

    issues = scan_directory(apex_dir, verbose=args.verbose)

    if not issues:
        print("No integration error-handling issues found.")
        return 0

    print(f"\n{len(issues)} issue(s) found:\n", file=sys.stderr)
    for issue in issues:
        print(f"WARN: {issue}\n", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
