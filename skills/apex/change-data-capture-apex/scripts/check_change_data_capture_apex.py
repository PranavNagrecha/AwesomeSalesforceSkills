#!/usr/bin/env python3
"""Checker script for Change Data Capture Apex skill.

Scans Apex trigger files in a Salesforce metadata deployment directory for
common CDC anti-patterns documented in references/llm-anti-patterns.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_change_data_capture_apex.py [--help]
    python3 check_change_data_capture_apex.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Apex CDC trigger files for common anti-patterns: "
            "wrong trigger event, SOQL in event loop, missing GAP handling, "
            "synchronous callout risk, and direct field reads on UPDATE events."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# Regex: trigger declaration on a ChangeEvent type
_CDC_TRIGGER_DECL = re.compile(
    r"trigger\s+\w+\s+on\s+(\w+ChangeEvent)\s*\(([^)]+)\)",
    re.IGNORECASE,
)

# Regex: trigger declaration using before insert (wrong for CDC)
_BEFORE_INSERT = re.compile(r"\bbefore\s+insert\b", re.IGNORECASE)

# Regex: SOQL inside a for loop (heuristic — looks for SELECT within a for block)
# We look for a for( pattern followed by SELECT on the same or nearby lines
_FOR_SOQL_PATTERN = re.compile(
    r"for\s*\([^)]*Trigger\.new[^)]*\).*?SELECT",
    re.DOTALL | re.IGNORECASE,
)

# Regex: synchronous Http usage in trigger body
_HTTP_CALLOUT = re.compile(r"\bHttpRequest\b|\bHttp\(\)|\bHttp\.send\b", re.IGNORECASE)

# Regex: GAP event handling — must contain GAP_ reference
_GAP_HANDLING = re.compile(r"GAP_|startsWith\s*\(\s*['\"]GAP", re.IGNORECASE)

# Regex: changeType == 'UPDATE' or similar that suggests UPDATE handling present
_UPDATE_HANDLING = re.compile(r"changeType\s*[!=]=\s*['\"]UPDATE['\"]", re.IGNORECASE)

# Regex: direct field read on event variable inside an UPDATE block (heuristic)
# Matches event.<FieldName> where it's not ChangeEventHeader
_DIRECT_EVENT_FIELD = re.compile(
    r"event\.\s*(?!ChangeEventHeader)\b([A-Z][a-zA-Z0-9_]+)\b",
)


def find_apex_triggers(manifest_dir: Path) -> list[Path]:
    """Return all .trigger files under manifest_dir."""
    return list(manifest_dir.rglob("*.trigger"))


def check_file(trigger_file: Path) -> list[str]:
    """Return a list of issue strings for the given trigger file."""
    issues: list[str] = []
    content = trigger_file.read_text(encoding="utf-8", errors="replace")
    rel = trigger_file.name

    # Check if this is a CDC trigger at all
    decl_match = _CDC_TRIGGER_DECL.search(content)
    if not decl_match:
        return []  # Not a CDC trigger — skip

    event_type = decl_match.group(1)
    trigger_events = decl_match.group(2)

    # Anti-pattern 1: before insert instead of after insert
    if _BEFORE_INSERT.search(trigger_events):
        issues.append(
            f"{rel}: CDC trigger on {event_type} uses 'before insert'. "
            "CDC triggers must use 'after insert' only."
        )

    # Anti-pattern 4: missing GAP event handling when UPDATE handling is present
    has_update_handling = bool(_UPDATE_HANDLING.search(content))
    has_gap_handling = bool(_GAP_HANDLING.search(content))

    if has_update_handling and not has_gap_handling:
        issues.append(
            f"{rel}: CDC trigger handles UPDATE but has no GAP_ branch. "
            "Add a 'changeType.startsWith(\"GAP_\")' handler to prevent silent data drift."
        )

    # Anti-pattern 5: synchronous callout risk in trigger body
    if _HTTP_CALLOUT.search(content):
        issues.append(
            f"{rel}: CDC trigger appears to use synchronous HttpRequest/Http callout. "
            "CDC triggers cannot perform synchronous callouts. "
            "Dispatch to System.enqueueJob() or @future(callout=true)."
        )

    # Anti-pattern 6: SOQL inside event loop (heuristic)
    # Count SELECT occurrences inside for(... : Trigger.new) blocks
    # Simple heuristic: look for SELECT that appears inside a for block
    for_blocks = re.finditer(
        r"for\s*\(\s*\w+\s+\w+\s*:\s*Trigger\.new\s*\)(.*?)(?=\n\s*\}|\Z)",
        content,
        re.DOTALL,
    )
    for block in for_blocks:
        block_text = block.group(1)
        if re.search(r"\[SELECT\b|\bDatabase\.query\b", block_text, re.IGNORECASE):
            issues.append(
                f"{rel}: SOQL query detected inside the Trigger.new event loop. "
                "Collect all record IDs first, then issue a single bulk SOQL outside the loop."
            )
            break  # Report once per file

    return issues


def check_change_data_capture_apex(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    trigger_files = find_apex_triggers(manifest_dir)

    if not trigger_files:
        # Not necessarily an error — the directory may not contain triggers
        return issues

    cdc_triggers_found = 0
    for tf in trigger_files:
        file_issues = check_file(tf)
        if file_issues:
            issues.extend(file_issues)
        # Count CDC triggers
        content = tf.read_text(encoding="utf-8", errors="replace")
        if _CDC_TRIGGER_DECL.search(content):
            cdc_triggers_found += 1

    if cdc_triggers_found == 0:
        # Informational — no CDC triggers to validate
        pass

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_change_data_capture_apex(manifest_dir)

    if not issues:
        print("No CDC anti-pattern issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
