#!/usr/bin/env python3
"""Checker script for retry-and-backoff-patterns skill.

Scans Apex source files in a Salesforce metadata directory for common
retry anti-patterns documented in references/llm-anti-patterns.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_retry_patterns.py --manifest-dir path/to/force-app
    python3 check_retry_patterns.py --manifest-dir .
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Pattern definitions
# ---------------------------------------------------------------------------

# Each entry: (check_id, description, pattern, severity)
PATTERNS = [
    (
        "RETRY-001",
        "Thread.sleep() call detected — not available in Apex; use Queueable chaining instead",
        re.compile(r"\bThread\.sleep\s*\(", re.IGNORECASE),
        "ERROR",
    ),
    (
        "RETRY-002",
        "Retry on all non-200 responses without filtering 4xx — retrying 400/401/403/404 will never succeed",
        re.compile(r"getStatusCode\(\)\s*!=\s*200", re.IGNORECASE),
        "WARNING",
    ),
    (
        "RETRY-003",
        "Hardcoded MAX_RETRIES constant — consider extracting to Custom Metadata (Retry_Config__mdt) for operator control",
        re.compile(r"static\s+final\s+Integer\s+MAX_RETRIES\s*=", re.IGNORECASE),
        "WARNING",
    ),
    (
        "RETRY-004",
        "Hardcoded BASE_DELAY constant — consider extracting to Custom Metadata (Retry_Config__mdt)",
        re.compile(r"static\s+final\s+Integer\s+BASE_DELAY", re.IGNORECASE),
        "WARNING",
    ),
    (
        "RETRY-005",
        "No maxRetries guard found in retry Queueable — unbounded retry chains risk exhausting daily async Apex limit",
        re.compile(r"System\.enqueueJob\s*\(", re.IGNORECASE),
        "INFO",  # Presence of enqueueJob without maxRetries check flagged separately
    ),
    (
        "RETRY-006",
        "No idempotency key header detected on callout — POST/PUT/PATCH retries without idempotency may create duplicates",
        re.compile(r'setHeader\s*\(\s*["\']X-Idempotency-Key["\']', re.IGNORECASE),
        "INFO",
    ),
]

# Patterns that indicate safe retry implementations (used to suppress false positives)
SAFE_INDICATORS = {
    "RETRY-002": re.compile(r"(429|503|500|5\d\d)", re.IGNORECASE),  # status-specific retry
    "RETRY-005": re.compile(r"retryCount\s*[<>=]+\s*max", re.IGNORECASE),  # maxRetries guard present
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex metadata for retry and backoff anti-patterns.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--severity",
        choices=["ERROR", "WARNING", "INFO"],
        default="WARNING",
        help="Minimum severity level to report (default: WARNING). ERROR=compile failures, WARNING=design issues, INFO=best-practice checks.",
    )
    return parser.parse_args()


def severity_rank(s: str) -> int:
    return {"ERROR": 3, "WARNING": 2, "INFO": 1}.get(s, 0)


def check_apex_file(file_path: Path, min_severity: str) -> list[dict]:
    """Scan a single Apex file for retry anti-patterns."""
    issues = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return issues

    lines = content.splitlines()

    for check_id, description, pattern, severity in PATTERNS:
        if severity_rank(severity) < severity_rank(min_severity):
            continue

        # Check if this file contains the anti-pattern signal
        matches = list(pattern.finditer(content))
        if not matches:
            continue

        # For INFO-level patterns that require co-presence of a mitigating pattern
        if check_id == "RETRY-005":
            # enqueueJob present — check if there's a maxRetries guard nearby
            safe_pattern = SAFE_INDICATORS.get(check_id)
            if safe_pattern and safe_pattern.search(content):
                continue  # Has a guard — suppress

        if check_id == "RETRY-006":
            # Only flag if there are callouts (Http.send) but no idempotency header
            has_callout = re.search(r"http\.send\s*\(", content, re.IGNORECASE)
            has_idempotency = re.search(r"X-Idempotency-Key", content, re.IGNORECASE)
            if not has_callout or has_idempotency:
                continue

        # Report each matching line
        for match in matches:
            line_num = content[: match.start()].count("\n") + 1
            issues.append({
                "file": str(file_path),
                "line": line_num,
                "check_id": check_id,
                "severity": severity,
                "description": description,
                "snippet": lines[line_num - 1].strip() if line_num <= len(lines) else "",
            })

    return issues


def check_manifest(manifest_dir: Path, min_severity: str) -> list[dict]:
    """Walk the manifest directory and check all .cls and .trigger files."""
    issues: list[dict] = []

    if not manifest_dir.exists():
        return [{"file": str(manifest_dir), "line": 0, "check_id": "SETUP-001",
                 "severity": "ERROR", "description": f"Manifest directory not found: {manifest_dir}",
                 "snippet": ""}]

    apex_files = list(manifest_dir.rglob("*.cls")) + list(manifest_dir.rglob("*.trigger"))

    if not apex_files:
        return [{"file": str(manifest_dir), "line": 0, "check_id": "SETUP-002",
                 "severity": "INFO", "description": "No Apex .cls or .trigger files found in manifest directory.",
                 "snippet": ""}]

    for apex_file in sorted(apex_files):
        issues.extend(check_apex_file(apex_file, min_severity))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    min_severity = args.severity

    issues = check_manifest(manifest_dir, min_severity)

    if not issues:
        print(f"No retry anti-pattern issues found at or above severity '{min_severity}'.")
        return 0

    error_count = sum(1 for i in issues if i["severity"] == "ERROR")
    warning_count = sum(1 for i in issues if i["severity"] == "WARNING")
    info_count = sum(1 for i in issues if i["severity"] == "INFO")

    for issue in issues:
        print(
            f"[{issue['severity']}] {issue['check_id']} "
            f"{issue['file']}:{issue['line']} — {issue['description']}"
        )
        if issue["snippet"]:
            print(f"         Code: {issue['snippet']}")

    print(
        f"\nSummary: {error_count} error(s), {warning_count} warning(s), {info_count} info(s) "
        f"across {len(set(i['file'] for i in issues))} file(s)."
    )

    return 1 if error_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
