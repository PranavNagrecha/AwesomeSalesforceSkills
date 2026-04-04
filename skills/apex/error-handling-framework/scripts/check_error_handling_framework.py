#!/usr/bin/env python3
"""Checker script for Error Handling Framework skill.

Scans a Salesforce metadata directory for common error handling framework issues:
- AuraHandledException thrown outside controller classes
- Direct Error_Log__c DML insert in catch blocks (not rollback-safe)
- EventBus.publish() called inside a for-loop (bulk DML limit risk)
- catch(Exception e) with silent swallowing (return null/false, only System.debug)
- e.getMessage() passed directly to AuraHandledException (information disclosure)
- BatchApexErrorEvent trigger missing DoesExceedJobScopeMaxLength guard

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_error_handling_framework.py [--help]
    python3 check_error_handling_framework.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# AuraHandledException thrown somewhere that is NOT a *Controller.cls file
_AURA_THROW = re.compile(r"throw\s+new\s+AuraHandledException\s*\(", re.IGNORECASE)

# Direct DML insert of Error_Log__c inside what looks like a catch block
# Heuristic: "insert" followed by "Error_Log__c" on the same or next line
_DIRECT_DML_LOG = re.compile(
    r"insert\s+new\s+Error_Log__c\s*\(|insert\s+\w*[Ee]rror[Ll]og\w*",
    re.IGNORECASE,
)

# EventBus.publish( called inside an obvious for-loop (lines between "for (" and next "}")
# We detect the co-occurrence heuristically by scanning per-file line sequences.

# catch (Exception e) without specific type
_CATCH_GENERIC = re.compile(r"catch\s*\(\s*Exception\s+\w+\s*\)", re.IGNORECASE)

# return false / return null / return 0 in a catch context (heuristic)
_RETURN_SILENT = re.compile(r"\breturn\s+(false|null|0)\s*;", re.IGNORECASE)

# Only System.debug inside a catch block (heuristic: debug without rethrow/publish)
_SYSTEM_DEBUG_ONLY = re.compile(r"System\.debug\s*\(", re.IGNORECASE)

# e.getMessage() passed directly to AuraHandledException
_AURA_GET_MESSAGE = re.compile(
    r"new\s+AuraHandledException\s*\(\s*\w+\.getMessage\s*\(\s*\)\s*\)",
    re.IGNORECASE,
)

# BatchApexErrorEvent trigger: JobScope usage without DoesExceedJobScopeMaxLength
_JOB_SCOPE_USE = re.compile(r"evt\.JobScope\b", re.IGNORECASE)
_DOES_EXCEED_GUARD = re.compile(r"DoesExceedJobScopeMaxLength", re.IGNORECASE)

# EventBus.publish inside a for loop
_EVENTBUS_PUBLISH = re.compile(r"EventBus\.publish\s*\(", re.IGNORECASE)
_FOR_LOOP_START = re.compile(r"\bfor\s*\(", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _apex_files(manifest_dir: Path) -> list[Path]:
    """Return all .cls and .trigger files under manifest_dir."""
    results: list[Path] = []
    for ext in ("*.cls", "*.trigger"):
        results.extend(manifest_dir.rglob(ext))
    return sorted(results)


def _is_controller_file(path: Path) -> bool:
    """Return True if the file name suggests an Aura/LWC controller."""
    name = path.stem.lower()
    return name.endswith("controller") or name.endswith("ctrl")


def _is_batch_apex_error_trigger(path: Path, content: str) -> bool:
    """Return True if this file is a trigger on BatchApexErrorEvent."""
    if path.suffix.lower() != ".trigger":
        return False
    return "batchapexerrorevent" in content.lower()


def _lines_with_event_publish_in_for_loop(content: str) -> list[int]:
    """
    Return line numbers (1-based) where EventBus.publish appears to be inside
    a for-loop, using a simple brace-depth heuristic.
    """
    lines = content.splitlines()
    hits: list[int] = []
    in_for_depth: list[int] = []  # stack of brace depths where for-loops started
    brace_depth = 0

    for lineno, line in enumerate(lines, start=1):
        # Count brace changes on this line
        open_count = line.count("{")
        close_count = line.count("}")

        if _FOR_LOOP_START.search(line):
            # Record the depth at which this for-loop opens
            in_for_depth.append(brace_depth + open_count)

        brace_depth += open_count - close_count

        # Pop any for-loop depths that have now closed
        in_for_depth = [d for d in in_for_depth if d <= brace_depth]

        if in_for_depth and _EVENTBUS_PUBLISH.search(line):
            hits.append(lineno)

    return hits


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def check_file(path: Path) -> list[str]:
    """Return a list of issue strings for a single Apex source file."""
    issues: list[str] = []
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [f"{path}: cannot read file — {exc}"]

    rel = path.name

    # 1. AuraHandledException thrown outside a controller file
    if not _is_controller_file(path) and _AURA_THROW.search(content):
        for lineno, line in enumerate(content.splitlines(), start=1):
            if _AURA_THROW.search(line):
                issues.append(
                    f"{rel}:{lineno}: AuraHandledException thrown outside a controller "
                    f"class — move to controller boundary only"
                )

    # 2. Direct DML insert of Error_Log__c (not rollback-safe)
    if _DIRECT_DML_LOG.search(content):
        for lineno, line in enumerate(content.splitlines(), start=1):
            if _DIRECT_DML_LOG.search(line):
                issues.append(
                    f"{rel}:{lineno}: Direct DML insert of Error_Log__c detected — "
                    f"use EventBus.publish(ErrorLog__e) for rollback-safe logging"
                )

    # 3. e.getMessage() passed directly to AuraHandledException (info disclosure)
    if _AURA_GET_MESSAGE.search(content):
        for lineno, line in enumerate(content.splitlines(), start=1):
            if _AURA_GET_MESSAGE.search(line):
                issues.append(
                    f"{rel}:{lineno}: e.getMessage() passed directly to AuraHandledException "
                    f"— use a user-safe message string with correlation ID reference instead"
                )

    # 4. BatchApexErrorEvent trigger missing DoesExceedJobScopeMaxLength guard
    if _is_batch_apex_error_trigger(path, content):
        if _JOB_SCOPE_USE.search(content) and not _DOES_EXCEED_GUARD.search(content):
            issues.append(
                f"{rel}: BatchApexErrorEvent trigger uses JobScope without checking "
                f"DoesExceedJobScopeMaxLength — JobScope may be truncated for large scopes"
            )

    # 5. EventBus.publish inside a for-loop (bulk DML limit risk)
    loop_hits = _lines_with_event_publish_in_for_loop(content)
    for lineno in loop_hits:
        issues.append(
            f"{rel}:{lineno}: EventBus.publish() called inside a for-loop — "
            f"collect ErrorLog__e events in a list and publish once after the loop"
        )

    # 6. Generic catch(Exception e) — flag as advisory
    lines = content.splitlines()
    for lineno, line in enumerate(lines, start=1):
        if _CATCH_GENERIC.search(line):
            # Check if the following ~5 lines contain only debug and silent return
            window = "\n".join(lines[lineno : min(lineno + 8, len(lines))])
            has_rethrow = "throw" in window.lower()
            has_publish = "eventbus" in window.lower() or "errorlogger" in window.lower()
            has_debug_only = _SYSTEM_DEBUG_ONLY.search(window)
            has_silent_return = _RETURN_SILENT.search(window)
            if not has_rethrow and not has_publish and (has_debug_only or has_silent_return):
                issues.append(
                    f"{rel}:{lineno}: Generic catch(Exception) with no rethrow or log publish "
                    f"— exception appears to be swallowed silently"
                )

    return issues


def check_error_handling_framework(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found under manifest_dir."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    apex_files = _apex_files(manifest_dir)
    if not apex_files:
        issues.append(
            f"No .cls or .trigger files found under {manifest_dir} — "
            f"confirm --manifest-dir points to a Salesforce metadata source directory"
        )
        return issues

    for apex_file in apex_files:
        issues.extend(check_file(apex_file))

    return issues


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Apex source files for common error handling framework issues: "
            "rollback-unsafe logging, AuraHandledException boundary violations, "
            "BatchApexErrorEvent truncation risks, and bulk publish anti-patterns."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory containing Salesforce Apex source files (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_error_handling_framework(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
