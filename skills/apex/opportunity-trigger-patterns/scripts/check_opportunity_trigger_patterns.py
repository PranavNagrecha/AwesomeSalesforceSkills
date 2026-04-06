#!/usr/bin/env python3
"""Checker script for Opportunity Trigger Patterns skill.

Scans Apex metadata in a Salesforce project directory for common anti-patterns
specific to Opportunity triggers: missing stage-change delta checks, DML on
OpportunitySplit in before contexts, SOQL/DML inside loops, and missing oldMap
null guards.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_opportunity_trigger_patterns.py [--help]
    python3 check_opportunity_trigger_patterns.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Trigger event line — detects before-context registrations
_RE_BEFORE_CONTEXT = re.compile(
    r'\btrigger\s+\w+\s+on\s+\w+\s*\([^)]*\b(before\s+insert|before\s+update|before\s+delete)',
    re.IGNORECASE,
)

# DML on OpportunitySplit (insert/update/delete/upsert)
_RE_SPLIT_DML = re.compile(
    r'\b(insert|update|delete|upsert)\b[^;]*\bOpportunitySplit\b',
    re.IGNORECASE,
)

# Stage-name comparison without oldMap delta check
_RE_STAGE_CONDITION = re.compile(
    r'\.StageName\s*[!=]=\s*["\']',
    re.IGNORECASE,
)
_RE_OLD_STAGE_CONDITION = re.compile(
    r'\bold\b.*\.StageName|Trigger\.oldMap',
    re.IGNORECASE,
)

# SOQL inside a for-loop body — simplified heuristic
_RE_FOR_LOOP = re.compile(r'\bfor\s*\(', re.IGNORECASE)
_RE_SOQL_SELECT = re.compile(r'\bSELECT\b', re.IGNORECASE)

# DML inside a for-loop body
_RE_DML_STMT = re.compile(r'\b(insert|update|delete|upsert)\s+\w', re.IGNORECASE)

# Access to Trigger.oldMap without null check
_RE_OLDMAP_ACCESS = re.compile(r'Trigger\.oldMap\.get\(', re.IGNORECASE)
_RE_OLDMAP_NULL_GUARD = re.compile(
    r'Trigger\.oldMap\s*!=\s*null|if\s*\(\s*Trigger\.isUpdate\b|if\s*\(\s*!\s*Trigger\.isInsert\b',
    re.IGNORECASE,
)


def _find_apex_files(root: Path) -> list[Path]:
    """Return all .cls and .trigger files under root."""
    files: list[Path] = []
    for ext in ("*.cls", "*.trigger"):
        files.extend(root.rglob(ext))
    return sorted(files)


def _file_source(path: Path) -> str:
    """Read file contents, returning empty string on error."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def check_split_dml_in_before_context(path: Path, source: str) -> list[str]:
    """Flag OpportunitySplit DML found in a trigger file that also declares a before context."""
    issues: list[str] = []
    if not _RE_SPLIT_DML.search(source):
        return issues

    if path.suffix == ".trigger" and _RE_BEFORE_CONTEXT.search(source):
        issues.append(
            f"{path}: OpportunitySplit DML detected in a trigger file that registers "
            "a before context. DML on OpportunitySplit is not allowed in before triggers."
        )
    return issues


def check_stage_comparison_missing_delta(path: Path, source: str) -> list[str]:
    """Flag stage-name equality checks without an oldMap/old delta check nearby."""
    issues: list[str] = []
    lines = source.splitlines()

    for i, line in enumerate(lines):
        if _RE_STAGE_CONDITION.search(line):
            window_start = max(0, i - 10)
            window_end = min(len(lines), i + 11)
            window = "\n".join(lines[window_start:window_end])
            if not _RE_OLD_STAGE_CONDITION.search(window):
                issues.append(
                    f"{path}:{i + 1}: StageName comparison without a corresponding "
                    "old.StageName or Trigger.oldMap delta check. "
                    "This fires on every save, not only on stage transitions."
                )
    return issues


def check_soql_inside_loop(path: Path, source: str) -> list[str]:
    """Heuristic: flag SOQL SELECT statements that appear inside for-loop blocks."""
    issues: list[str] = []
    lines = source.splitlines()
    depth = 0
    in_for = False
    for_depth = 0

    for i, line in enumerate(lines):
        stripped = line.strip()

        if _RE_FOR_LOOP.search(stripped):
            in_for = True
            for_depth = depth + stripped.count("{") - stripped.count("}")

        depth += stripped.count("{") - stripped.count("}")

        if in_for and depth <= for_depth:
            in_for = False

        if in_for and _RE_SOQL_SELECT.search(stripped):
            issues.append(
                f"{path}:{i + 1}: SOQL query (SELECT) detected inside a for loop. "
                "Collect all IDs before the loop and run one aggregate query outside."
            )

    return issues


def check_dml_inside_loop(path: Path, source: str) -> list[str]:
    """Heuristic: flag DML statements inside for-loop blocks."""
    issues: list[str] = []
    lines = source.splitlines()
    depth = 0
    in_for = False
    for_depth = 0

    for i, line in enumerate(lines):
        stripped = line.strip()

        if _RE_FOR_LOOP.search(stripped):
            in_for = True
            for_depth = depth + stripped.count("{") - stripped.count("}")

        depth += stripped.count("{") - stripped.count("}")

        if in_for and depth <= for_depth:
            in_for = False

        if in_for and _RE_DML_STMT.search(stripped):
            if not stripped.startswith("//") and not stripped.startswith("*"):
                issues.append(
                    f"{path}:{i + 1}: DML statement detected inside a for loop. "
                    "Collect records into a list and DML once outside the loop."
                )

    return issues


def check_oldmap_access_without_guard(path: Path, source: str) -> list[str]:
    """Flag Trigger.oldMap.get() calls without a visible null/isUpdate guard."""
    issues: list[str] = []
    if not _RE_OLDMAP_ACCESS.search(source):
        return issues
    if not _RE_OLDMAP_NULL_GUARD.search(source):
        issues.append(
            f"{path}: Trigger.oldMap.get() used without a visible isUpdate or "
            "null guard. This causes a NullPointerException in insert contexts."
        )
    return issues


def check_opportunity_trigger_patterns(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    apex_files = _find_apex_files(manifest_dir)
    if not apex_files:
        return issues

    for path in apex_files:
        source = _file_source(path)
        if not source:
            continue

        issues.extend(check_split_dml_in_before_context(path, source))
        issues.extend(check_stage_comparison_missing_delta(path, source))
        issues.extend(check_soql_inside_loop(path, source))
        issues.extend(check_dml_inside_loop(path, source))
        issues.extend(check_oldmap_access_without_guard(path, source))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Apex metadata for Opportunity trigger anti-patterns: "
            "missing stage-change delta guards, OpportunitySplit DML in before contexts, "
            "SOQL/DML inside loops, and unguarded Trigger.oldMap access."
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
    issues = check_opportunity_trigger_patterns(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
