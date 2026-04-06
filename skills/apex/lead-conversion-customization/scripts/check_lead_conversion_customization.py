#!/usr/bin/env python3
"""Checker script for Lead Conversion Customization skill.

Scans Apex source files for common lead conversion anti-patterns documented
in references/gotchas.md and references/llm-anti-patterns.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_lead_conversion_customization.py [--help]
    python3 check_lead_conversion_customization.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex metadata for lead conversion anti-patterns.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata or force-app source (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Compiled patterns
# ---------------------------------------------------------------------------

_HARDCODED_STATUS_RE = re.compile(
    r"""setConvertedStatus\s*\(\s*['"][^'"]+['"]\s*\)""",
    re.IGNORECASE,
)

_NEW_CONVERT_RESULT_RE = re.compile(
    r"""new\s+Database\.LeadConvertResult\s*\(""",
    re.IGNORECASE,
)

_CONVERT_LEAD_CALL_RE = re.compile(
    r"""Database\.convertLead\s*\(""",
    re.IGNORECASE,
)

_FOR_LOOP_RE = re.compile(r"""\bfor\s*\(""", re.IGNORECASE)

_CONVERTED_ID_FIELDS_RE = re.compile(
    r"""ConvertedContactId|ConvertedAccountId|ConvertedOpportunityId""",
    re.IGNORECASE,
)

_BEFORE_UPDATE_LEAD_TRIGGER_RE = re.compile(
    r"""on\s+Lead\s*\([^)]*before\s+update""",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Individual check functions
# ---------------------------------------------------------------------------

def check_hardcoded_converted_status(content: str, path: Path) -> list[str]:
    """Warn when setConvertedStatus() uses a hardcoded string literal."""
    issues: list[str] = []
    for i, line in enumerate(content.splitlines(), start=1):
        if _HARDCODED_STATUS_RE.search(line):
            issues.append(
                f"{path}:{i} — setConvertedStatus() called with a hardcoded string literal. "
                "Query [SELECT MasterLabel FROM LeadStatus WHERE IsConverted = true] dynamically instead."
            )
    return issues


def check_instantiated_lead_convert_result(content: str, path: Path) -> list[str]:
    """Detect attempts to instantiate Database.LeadConvertResult directly."""
    issues: list[str] = []
    for i, line in enumerate(content.splitlines(), start=1):
        if _NEW_CONVERT_RESULT_RE.search(line):
            issues.append(
                f"{path}:{i} — 'new Database.LeadConvertResult()' will not compile. "
                "Use the result returned by Database.convertLead(), or JSON.deserialize() for mocks."
            )
    return issues


def check_convert_lead_in_loop(content: str, path: Path) -> list[str]:
    """Warn if Database.convertLead() appears to be called inside a for loop."""
    issues: list[str] = []
    lines = content.splitlines()

    # Track open brace depth and the depth at which each for-loop opened
    brace_depth = 0
    loop_open_depths: list[int] = []

    for i, line in enumerate(lines, start=1):
        # Detect new for-loop — record the current brace depth before this line's braces
        if _FOR_LOOP_RE.search(line):
            loop_open_depths.append(brace_depth)

        # Update brace depth after scanning for loops on this line
        brace_depth += line.count("{") - line.count("}")

        # Pop any loops whose body has been fully closed
        while loop_open_depths and brace_depth <= loop_open_depths[-1]:
            loop_open_depths.pop()

        # If we are inside at least one for-loop and convertLead is called, flag it
        if loop_open_depths and _CONVERT_LEAD_CALL_RE.search(line):
            issues.append(
                f"{path}:{i} — Database.convertLead() called inside a for loop. "
                "Build a List<Database.LeadConvert> outside the loop and call convertLead() "
                "once per chunk of 100 records."
            )

    return issues


def check_converted_id_in_before_trigger(content: str, path: Path) -> list[str]:
    """Warn if ConvertedContactId/AccountId/OpportunityId appears in a before update Lead trigger."""
    issues: list[str] = []
    if path.suffix != ".trigger":
        return issues
    if not _BEFORE_UPDATE_LEAD_TRIGGER_RE.search(content):
        return issues
    for i, line in enumerate(content.splitlines(), start=1):
        if _CONVERTED_ID_FIELDS_RE.search(line):
            issues.append(
                f"{path}:{i} — ConvertedContactId/AccountId/OpportunityId referenced in a "
                "'before update' Lead trigger. These fields are null until after "
                "conversion DML completes — move this logic to 'after update'."
            )
    return issues


def check_missing_chunk_guard(content: str, path: Path) -> list[str]:
    """Warn if convertLead() is used but no subList() chunking is visible in the same file."""
    issues: list[str] = []
    if "convertLead" not in content:
        return issues
    if "subList" not in content:
        issues.append(
            f"{path} — Database.convertLead() is present but no subList() chunking is visible. "
            "convertLead() has a hard limit of 100 records per call. "
            "Add: subList(i, Math.min(i + 100, list.size()))."
        )
    return issues


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def _find_apex_files(manifest_dir: Path) -> list[Path]:
    """Return all .cls and .trigger files under manifest_dir."""
    apex_files: list[Path] = []
    for ext in ("*.cls", "*.trigger"):
        apex_files.extend(manifest_dir.rglob(ext))
    return apex_files


def check_lead_conversion_customization(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found across Apex files in manifest_dir."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    apex_files = _find_apex_files(manifest_dir)
    if not apex_files:
        # No Apex files to check — not an error
        return issues

    for apex_file in sorted(apex_files):
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            issues.append(f"Could not read {apex_file}: {exc}")
            continue

        # Only run conversion-specific checks on files that mention lead conversion concepts
        lower = content.lower()
        is_conversion_related = any(
            kw in lower for kw in (
                "database.leadconvert",
                "convertlead",
                "isconverted",
                "leadconvertresult",
                "setconvertedstatus",
            )
        )
        if not is_conversion_related:
            continue

        issues.extend(check_hardcoded_converted_status(content, apex_file))
        issues.extend(check_instantiated_lead_convert_result(content, apex_file))
        issues.extend(check_convert_lead_in_loop(content, apex_file))
        issues.extend(check_converted_id_in_before_trigger(content, apex_file))
        issues.extend(check_missing_chunk_guard(content, apex_file))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_lead_conversion_customization(manifest_dir)

    if not issues:
        print("No lead conversion issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
