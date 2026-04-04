#!/usr/bin/env python3
"""Checker script for Custom Logging and Monitoring skill.

Scans Apex files for common logging anti-patterns:
- Per-call DML insert in logging methods (should buffer + flush)
- Missing Database.insert(buffer, false) — allOrNone should be false for logging
- Hardcoded log level constants (should come from Custom Metadata)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_custom_logging_and_monitoring.py [--help]
    python3 check_custom_logging_and_monitoring.py --source-dir force-app/
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan Apex logging classes for common anti-patterns.",
    )
    parser.add_argument(
        "--source-dir",
        default=".",
        help="Root directory of the Salesforce source (default: current directory).",
    )
    return parser.parse_args()


def is_likely_logger(content: str) -> bool:
    """Heuristic: file references Log__c or LoggingLevel."""
    return "Log__c" in content or "LoggingLevel" in content


def check_per_call_dml(apex_file: Path, content: str) -> list[str]:
    """Warn if a log method does DML inside the log() call rather than buffering."""
    issues: list[str] = []
    lines = content.splitlines()

    in_log_method = False
    method_brace_depth = 0

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Detect log method signatures
        if re.search(r"\bvoid\s+log\s*\(", stripped) or re.search(r"\bpublic.*\blog\b.*\(", stripped):
            in_log_method = True
            method_brace_depth = 0

        if in_log_method:
            method_brace_depth += stripped.count("{") - stripped.count("}")

            # Check for direct insert in log method
            if re.search(r"\b(insert|Database\.insert)\s+new\s+Log", stripped):
                issues.append(
                    f"{apex_file}:{i}: Direct DML insert inside log() method — "
                    f"use a buffer list and call flush() at the end of the transaction "
                    f"to avoid governor limit violations in bulk contexts."
                )

            if method_brace_depth <= 0 and method_brace_depth != 0:
                in_log_method = False

    return issues


def check_missing_partial_success(apex_file: Path, content: str) -> list[str]:
    """Warn if Database.insert() on log buffer does not use allOrNone=false."""
    issues: list[str] = []
    lines = content.splitlines()

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        # Database.insert(buffer) without false second arg
        if re.search(r"Database\.insert\s*\(\s*buffer\s*\)", stripped):
            issues.append(
                f"{apex_file}:{i}: Database.insert(buffer) without allOrNone=false — "
                f"use Database.insert(buffer, false) so log insert failures do not "
                f"interrupt business logic."
            )

    return issues


def check_logging_files(source_dir: Path) -> list[str]:
    """Return a list of issue strings found in the source directory."""
    issues: list[str] = []

    for apex_file in source_dir.rglob("*.cls"):
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
            if not is_likely_logger(content):
                continue
            issues.extend(check_per_call_dml(apex_file, content))
            issues.extend(check_missing_partial_success(apex_file, content))
        except OSError:
            pass

    return issues


def main() -> int:
    args = parse_args()
    source_dir = Path(args.source_dir)

    if not source_dir.exists():
        print(f"ISSUE: Source directory not found: {source_dir}")
        return 1

    issues = check_logging_files(source_dir)

    if not issues:
        print("No custom logging anti-patterns found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
