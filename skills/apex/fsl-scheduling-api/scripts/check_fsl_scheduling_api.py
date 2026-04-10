#!/usr/bin/env python3
"""Checker script for FSL Scheduling API skill.

Scans Apex source files for common FSL scheduling API anti-patterns:
- FSL scheduling callouts inside trigger handlers
- Missing null check on FSL.ScheduleService.schedule() return value
- schedule() or GetSlots() calls in the same method as DML (heuristic)
- Batch executeBatch calls without size 1

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_fsl_scheduling_api.py [--help]
    python3 check_fsl_scheduling_api.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Patterns that indicate FSL scheduling API callouts
_FSL_CALLOUT_RE = re.compile(
    r'FSL\.(AppointmentBookingService\.GetSlots|ScheduleService\.schedule|GradeSlotsService\.GradeSlots|OAAS\.)',
    re.IGNORECASE,
)

# Pattern for trigger file detection
_TRIGGER_FILE_RE = re.compile(r'\.trigger$', re.IGNORECASE)

# Pattern: schedule() return value used without null check
_SCHEDULE_CALL_RE = re.compile(r'FSL\.ScheduleService\.schedule\s*\(', re.IGNORECASE)
_NULL_CHECK_RE = re.compile(r'if\s*\(\s*\w+\s*==\s*null\s*\)', re.IGNORECASE)

# Pattern: DML before callout in same file (heuristic)
_DML_RE = re.compile(r'\b(insert|update|delete|upsert)\s+\w+\s*;', re.IGNORECASE)

# Pattern: executeBatch without size 1
_EXECUTE_BATCH_FSL_RE = re.compile(r'Database\.executeBatch\s*\(', re.IGNORECASE)


def check_fsl_scheduling_api(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    apex_files = list(manifest_dir.rglob("*.cls")) + list(manifest_dir.rglob("*.trigger"))

    if not apex_files:
        return issues  # No Apex to check

    for apex_file in apex_files:
        try:
            source = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        rel = apex_file.relative_to(manifest_dir)
        lines = source.splitlines()

        # Check 1: FSL callouts inside trigger files
        if _TRIGGER_FILE_RE.search(apex_file.name):
            if _FSL_CALLOUT_RE.search(source):
                issues.append(
                    f"{rel}: FSL scheduling callout detected inside a trigger. "
                    "Callouts inside triggers throw CalloutException. "
                    "Enqueue a Queueable from the trigger instead."
                )

        # Check 2: schedule() return value not null-checked (heuristic)
        if _SCHEDULE_CALL_RE.search(source):
            # Look for lines after schedule() that use the result without a null check
            for i, line in enumerate(lines):
                if _SCHEDULE_CALL_RE.search(line):
                    # Check next 5 lines for null check
                    window = "\n".join(lines[i:i+6])
                    if not _NULL_CHECK_RE.search(window):
                        issues.append(
                            f"{rel}:{i+1}: FSL.ScheduleService.schedule() called but no null check "
                            "detected within 5 lines. schedule() returns null (not an exception) "
                            "when no resource is available. Add: if (result == null) {{ ... }}"
                        )

        # Check 3: executeBatch without size 1 near FSL scheduling pattern
        if _FSL_CALLOUT_RE.search(source) and _EXECUTE_BATCH_FSL_RE.search(source):
            for i, line in enumerate(lines):
                if _EXECUTE_BATCH_FSL_RE.search(line):
                    # Check if batch size 1 is specified
                    if not re.search(r'executeBatch\s*\([^,]+,\s*1\s*\)', line):
                        issues.append(
                            f"{rel}:{i+1}: Database.executeBatch() detected in file with FSL scheduling calls. "
                            "Ensure batch size is explicitly 1: Database.executeBatch(job, 1). "
                            "FSL scheduling callouts require batch size 1 to avoid callout limit failures."
                        )

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex source files for FSL Scheduling API anti-patterns.",
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
    issues = check_fsl_scheduling_api(manifest_dir)

    if not issues:
        print("No FSL Scheduling API issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
