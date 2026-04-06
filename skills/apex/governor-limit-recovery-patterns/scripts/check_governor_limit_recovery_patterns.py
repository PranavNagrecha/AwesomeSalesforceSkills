#!/usr/bin/env python3
"""Checker script for Governor Limit Recovery Patterns skill.

Scans Apex source files (.cls) for common governor-limit anti-patterns:
  1. try/catch blocks that attempt to catch LimitException (uncatchable)
  2. Database.rollback() calls not followed by an explicit Id null-out
  3. Savepoint usage exceeding 5 per file (proxy for per-transaction overuse)
  4. BatchApexErrorEvent trigger handlers that parse JobScope without checking
     DoesExceedJobScopeMaxLength
  5. Limits.* checks placed only before a for-loop header, not inside it

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_governor_limit_recovery_patterns.py [--help]
    python3 check_governor_limit_recovery_patterns.py --manifest-dir path/to/metadata
    python3 check_governor_limit_recovery_patterns.py --manifest-dir force-app/main/default/classes
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Anti-pattern 1: catching LimitException (or bare Exception near limit commentary)
_P_CATCH_LIMIT = re.compile(
    r"catch\s*\(\s*(System\.)?LimitException",
    re.IGNORECASE,
)

# Anti-pattern 2: Database.rollback without a subsequent .Id = null in same block
# We use a heuristic: find rollback lines and scan forward N lines for Id nulling.
_P_ROLLBACK = re.compile(r"Database\.rollback\s*\(", re.IGNORECASE)
_P_ID_NULL = re.compile(r"\.Id\s*=\s*null\b", re.IGNORECASE)

# Anti-pattern 3: savepoint creation — count per file
_P_SAVEPOINT = re.compile(r"Database\.setSavepoint\s*\(", re.IGNORECASE)

# Anti-pattern 4: JobScope.split without DoesExceedJobScopeMaxLength guard
_P_JOBSCOPE_SPLIT = re.compile(r"JobScope\s*\.\s*split\s*\(", re.IGNORECASE)
_P_DOES_EXCEED = re.compile(r"DoesExceedJobScopeMaxLength", re.IGNORECASE)

# Anti-pattern 5: Limits check immediately before a for-loop but not inside
# Heuristic: Limits.getLimit* or Limits.get* appears on the line directly above `for (`
_P_LIMITS_CHECK = re.compile(r"Limits\.\w+\s*\(", re.IGNORECASE)
_P_FOR_LOOP = re.compile(r"\bfor\s*\(", re.IGNORECASE)


_LOOKAHEAD_LINES = 15  # lines to scan after a rollback for Id null-out


# ---------------------------------------------------------------------------
# Per-file analysis
# ---------------------------------------------------------------------------

def _check_file(path: Path) -> list[str]:
    issues: list[str] = []
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        issues.append(f"{path}: cannot read file — {exc}")
        return issues

    lines = content.splitlines()

    savepoint_count = 0
    jobscope_split_lines: list[int] = []
    has_does_exceed_check = False
    rollback_line_indices: list[int] = []

    # Track whether we are inside a for-loop body for anti-pattern 5
    # Simple heuristic: flag if a Limits check appears on the line before `for (`
    limits_check_lines: set[int] = set()

    for i, line in enumerate(lines, start=1):

        # Anti-pattern 1
        if _P_CATCH_LIMIT.search(line):
            issues.append(
                f"{path}:{i}: LimitException caught in catch block — "
                "LimitException is uncatchable; this catch block will never execute. "
                "Use Limits.* proactive checks instead."
            )

        # Savepoint counter (anti-pattern 3)
        if _P_SAVEPOINT.search(line):
            savepoint_count += 1

        # Rollback tracking (anti-pattern 2)
        if _P_ROLLBACK.search(line):
            rollback_line_indices.append(i)

        # JobScope split tracking (anti-pattern 4)
        if _P_JOBSCOPE_SPLIT.search(line):
            jobscope_split_lines.append(i)
        if _P_DOES_EXCEED.search(line):
            has_does_exceed_check = True

        # Limits check line tracking (anti-pattern 5)
        if _P_LIMITS_CHECK.search(line):
            limits_check_lines.add(i)

    # Anti-pattern 3: more than 5 savepoints in a single file
    if savepoint_count > 5:
        issues.append(
            f"{path}: {savepoint_count} Database.setSavepoint() calls found in one file. "
            "A transaction may only have 5 savepoints; exceeding this throws LimitException. "
            "Refactor so savepoint ownership lives at the outermost transaction boundary."
        )

    # Anti-pattern 2: rollback without nearby Id null-out
    for rollback_lineno in rollback_line_indices:
        idx = rollback_lineno - 1  # convert to 0-based
        window = lines[idx : idx + _LOOKAHEAD_LINES]
        window_text = "\n".join(window)
        if not _P_ID_NULL.search(window_text):
            issues.append(
                f"{path}:{rollback_lineno}: Database.rollback() call with no '.Id = null' "
                f"found in the following {_LOOKAHEAD_LINES} lines. "
                "After rollback, sObject Id fields retain their values; "
                "explicitly null them to prevent false-positive Id checks."
            )

    # Anti-pattern 4: JobScope.split without DoesExceedJobScopeMaxLength check
    if jobscope_split_lines and not has_does_exceed_check:
        for lineno in jobscope_split_lines:
            issues.append(
                f"{path}:{lineno}: JobScope.split() called without a DoesExceedJobScopeMaxLength check. "
                "When DoesExceedJobScopeMaxLength is true, JobScope is truncated and must not be parsed. "
                "Add: if (!evt.DoesExceedJobScopeMaxLength) {{ ... }} guard."
            )

    # Anti-pattern 5: Limits check immediately before a for-loop (not inside it)
    for i, line in enumerate(lines, start=1):
        if _P_FOR_LOOP.search(line):
            # Check if the immediately preceding non-blank line is a Limits check
            prev_idx = i - 2  # 0-based index of line before this one
            while prev_idx >= 0 and lines[prev_idx].strip() == "":
                prev_idx -= 1
            if prev_idx >= 0 and (prev_idx + 1) in limits_check_lines:
                # The Limits check is only before the for-loop, not inside it
                # Only flag if there is no Limits check inside the loop body
                # Heuristic: scan next 20 lines for another Limits check
                body_lines = lines[i : i + 20]
                body_text = "\n".join(body_lines)
                if not _P_LIMITS_CHECK.search(body_text):
                    issues.append(
                        f"{path}:{i}: Limits.* check appears immediately before for-loop "
                        "but not inside the loop body. A single pre-loop check does not "
                        "protect against per-iteration limit consumption. "
                        "Move the Limits check inside the loop."
                    )

    return issues


# ---------------------------------------------------------------------------
# Directory walk
# ---------------------------------------------------------------------------

def check_governor_limit_recovery_patterns(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in Apex files under manifest_dir."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    apex_files = sorted(manifest_dir.rglob("*.cls"))
    if not apex_files:
        # Not an error — project may have no Apex classes
        return issues

    for apex_file in apex_files:
        issues.extend(_check_file(apex_file))

    return issues


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Apex source files for governor-limit recovery anti-patterns. "
            "Checks: uncatchable LimitException catch blocks, missing Id null after rollback, "
            "excess savepoints, missing DoesExceedJobScopeMaxLength guard, "
            "and Limits checks outside of loops."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory containing Apex .cls files (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_governor_limit_recovery_patterns(manifest_dir)

    if not issues:
        print("No governor-limit recovery anti-patterns found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
