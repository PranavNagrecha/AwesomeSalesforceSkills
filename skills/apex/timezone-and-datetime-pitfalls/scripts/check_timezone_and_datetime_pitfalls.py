#!/usr/bin/env python3
"""Checker script for Timezone and Datetime Pitfalls skill.

Scans Apex (.cls, .trigger) files in a Salesforce metadata directory for
common timezone and datetime anti-patterns documented in this skill.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_timezone_and_datetime_pitfalls.py [--help]
    python3 check_timezone_and_datetime_pitfalls.py --manifest-dir path/to/metadata
    python3 check_timezone_and_datetime_pitfalls.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Detection patterns
# Each entry is (rule_id, description, regex_pattern, severity)
# severity: "WARNING" = worth reviewing but may be intentional
#           "ERROR"   = almost always wrong
# ---------------------------------------------------------------------------
PATTERNS: list[tuple[str, str, re.Pattern[str], str]] = [
    (
        "TZ001",
        "Date.today() used — may return server UTC date instead of user's local date. "
        "Replace with UserInfo.getTimeZone()-based local date extraction for user-facing logic.",
        re.compile(r"\bDate\.today\(\)", re.IGNORECASE),
        "WARNING",
    ),
    (
        "TZ002",
        "Datetime.newInstance() with integer arguments — prefers Datetime.newInstanceGmt() "
        "for UTC component construction to avoid server-local-time ambiguity.",
        re.compile(
            r"\bDatetime\.newInstance\s*\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*\d+",
            re.IGNORECASE,
        ),
        "WARNING",
    ),
    (
        "TZ003",
        "Datetime.valueOf() called — does NOT parse ISO 8601 timezone offsets. "
        "Use JSON.deserialize for strings with timezone offsets.",
        re.compile(r"\bDatetime\.valueOf\s*\(", re.IGNORECASE),
        "WARNING",
    ),
    (
        "TZ004",
        "Hardcoded timezone offset in addHours() — breaks at DST transitions. "
        "Use Datetime.format(pattern, timezoneId) or TimeZone.getOffset() instead.",
        re.compile(
            r"\b\.addHours\s*\(\s*-?\d+\s*\)",
            re.IGNORECASE,
        ),
        "WARNING",
    ),
    (
        "TZ005",
        "Hardcoded offset in addSeconds() that looks like a timezone offset "
        "(multiples of 900 or large values) — may be a fixed timezone offset. "
        "Use TimeZone.getOffset(instant) for DST-safe offset calculation.",
        re.compile(
            r"\b\.addSeconds\s*\(\s*-?\s*(?:3600|7200|10800|14400|18000|21600|25200|28800|32400|36000|39600|43200)\s*\)",
            re.IGNORECASE,
        ),
        "WARNING",
    ),
    (
        "TZ006",
        "UserInfo.getTimeZone() in a Schedulable or Batchable class — returns the "
        "scheduler/system user's timezone, not the record owners'. Consider querying "
        "User.TimeZoneSidKey for each record owner instead.",
        re.compile(r"\bUserInfo\.getTimeZone\s*\(", re.IGNORECASE),
        "WARNING",
    ),
    (
        "TZ007",
        "DAY_ONLY() in SOQL — extracts the UTC date, not the user's local date. "
        "If user-timezone bucketing is needed, query raw Datetime and bucket in Apex.",
        re.compile(r"\bDAY_ONLY\s*\(", re.IGNORECASE),
        "WARNING",
    ),
    (
        "TZ008",
        ".date() called on a Datetime — extracts the UTC calendar date, not the local date. "
        "If a user-visible Date field is being populated, apply getOffset() shift first.",
        re.compile(r"\b\.date\s*\(\s*\)", re.IGNORECASE),
        "WARNING",
    ),
]

# Patterns that indicate the developer has accounted for timezone handling nearby
# (used to suppress false positives in the vicinity of flagged lines)
MITIGATION_HINTS = re.compile(
    r"getTimeZone|getOffset|newInstanceGmt|TimeZoneSidKey|America/|Europe/|Asia/|UTC",
    re.IGNORECASE,
)

# Context window: number of lines before/after a flagged line to check for mitigation
CONTEXT_WINDOW = 5


def find_apex_files(root: Path) -> list[Path]:
    """Return all .cls and .trigger files under root."""
    apex_files: list[Path] = []
    for ext in ("*.cls", "*.trigger"):
        apex_files.extend(root.rglob(ext))
    return sorted(apex_files)


def check_file(
    file_path: Path,
) -> list[dict[str, object]]:
    """Return a list of issue dicts found in a single Apex file."""
    issues: list[dict[str, object]] = []
    try:
        lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        issues.append(
            {
                "file": str(file_path),
                "line": 0,
                "rule": "IO_ERROR",
                "severity": "ERROR",
                "message": f"Could not read file: {exc}",
                "matched_text": "",
            }
        )
        return issues

    for line_no, line in enumerate(lines, start=1):
        # Skip comment lines
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("*"):
            continue

        for rule_id, description, pattern, severity in PATTERNS:
            match = pattern.search(line)
            if not match:
                continue

            # Check surrounding context for mitigation hints
            context_start = max(0, line_no - 1 - CONTEXT_WINDOW)
            context_end = min(len(lines), line_no + CONTEXT_WINDOW)
            context_block = "\n".join(lines[context_start:context_end])

            # For TZ006 (UserInfo.getTimeZone), only flag if we see Batchable/Schedulable
            if rule_id == "TZ006":
                # Read more context — check the whole file for Batchable/Schedulable
                full_text = "\n".join(lines)
                if not re.search(
                    r"implements\s+(?:Database\.Batchable|Schedulable)",
                    full_text,
                    re.IGNORECASE,
                ):
                    continue

            # Suppress if mitigation is visible in context (except TZ001 which needs
            # the mitigation to be in the same method, not just in the file)
            if rule_id not in ("TZ001", "TZ003") and MITIGATION_HINTS.search(
                context_block
            ):
                continue

            issues.append(
                {
                    "file": str(file_path),
                    "line": line_no,
                    "rule": rule_id,
                    "severity": severity,
                    "message": description,
                    "matched_text": line.strip(),
                }
            )

    return issues


def check_timezone_and_datetime_pitfalls(manifest_dir: Path) -> list[str]:
    """Return a list of human-readable issue strings for the given manifest directory."""
    output: list[str] = []

    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    apex_files = find_apex_files(manifest_dir)
    if not apex_files:
        output.append(
            f"No Apex files (.cls, .trigger) found under {manifest_dir}. "
            "Pass the correct --manifest-dir pointing to your Salesforce source tree."
        )
        return output

    total_files = len(apex_files)
    all_issues: list[dict[str, object]] = []
    for apex_file in apex_files:
        all_issues.extend(check_file(apex_file))

    if not all_issues:
        output.append(
            f"Scanned {total_files} Apex file(s). No timezone anti-patterns detected."
        )
        return output

    # Group by file for readable output
    issues_by_file: dict[str, list[dict[str, object]]] = {}
    for issue in all_issues:
        key = issue["file"]  # type: ignore[assignment]
        issues_by_file.setdefault(str(key), []).append(issue)

    output.append(
        f"Scanned {total_files} Apex file(s). Found {len(all_issues)} potential timezone issue(s) "
        f"in {len(issues_by_file)} file(s):\n"
    )

    for file_path, file_issues in sorted(issues_by_file.items()):
        output.append(f"  {file_path}")
        for issue in file_issues:
            output.append(
                f"    [{issue['severity']}] Line {issue['line']} [{issue['rule']}]: "
                f"{issue['message']}"
            )
            output.append(f"      Code: {issue['matched_text']}")
        output.append("")

    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Salesforce Apex files for timezone and datetime anti-patterns.\n\n"
            "Rules checked:\n"
            "  TZ001 — Date.today() in user-facing logic\n"
            "  TZ002 — Datetime.newInstance() with integer args (prefer newInstanceGmt)\n"
            "  TZ003 — Datetime.valueOf() (does not parse ISO 8601 offsets)\n"
            "  TZ004 — addHours() with hardcoded integer (DST risk)\n"
            "  TZ005 — addSeconds() with hardcoded timezone-offset-like values\n"
            "  TZ006 — UserInfo.getTimeZone() in Batchable/Schedulable context\n"
            "  TZ007 — DAY_ONLY() in SOQL (returns UTC date, not local date)\n"
            "  TZ008 — .date() on Datetime (extracts UTC date)\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata source (default: current directory).",
    )
    parser.add_argument(
        "--no-context-suppression",
        action="store_true",
        default=False,
        help="Disable context-based suppression of false positives (show all matches).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)

    if args.no_context_suppression:
        # Disable suppression by making the mitigation pattern never match
        global MITIGATION_HINTS  # noqa: PLW0603
        MITIGATION_HINTS = re.compile(r"(?!)")  # Never matches

    issues = check_timezone_and_datetime_pitfalls(manifest_dir)

    for line in issues:
        print(line)

    # Return non-zero if any ERROR or WARNING with "ERROR" severity found
    has_errors = any(
        "ERROR" in line and "[WARNING]" not in line for line in issues
    )
    if has_errors:
        print(f"WARN: timezone/datetime issues detected", file=sys.stderr)
    return 1 if has_errors else 0


if __name__ == "__main__":
    sys.exit(main())
