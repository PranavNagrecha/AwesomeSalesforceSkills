#!/usr/bin/env python3
"""Checker script for MCAE (Pardot) API v5 skill.

Scans source files in a project directory for common MCAE API v5 integration
anti-patterns: deprecated API versions, missing required headers, offset
pagination instead of nextPageMark, and standalone Pardot authentication.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_mcae_pardot_api.py [--help]
    python3 check_mcae_pardot_api.py --manifest-dir path/to/project
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Patterns that signal anti-patterns in source code
# ---------------------------------------------------------------------------

# Deprecated v3/v4 API URL patterns
DEPRECATED_API_PATTERN = re.compile(
    r"pi\.pardot\.com/api/[34]/",
    re.IGNORECASE,
)

# Legacy Pardot login endpoint
LEGACY_AUTH_PATTERN = re.compile(
    r"pi\.pardot\.com/api/login",
    re.IGNORECASE,
)

# v5 API calls that are missing the required header (heuristic: pi.pardot.com
# present but Pardot-Business-Unit-Id not in same file — reported as warning)
PARDOT_API_V5_CALL = re.compile(
    r"pi\.pardot\.com/api/v5",
    re.IGNORECASE,
)
REQUIRED_HEADER = re.compile(
    r"Pardot-Business-Unit-Id",
    re.IGNORECASE,
)

# Offset pagination patterns in v5 context
OFFSET_PAGINATION_IN_V5 = re.compile(
    r'(?:page=|offset=|["\']page["\']:)',
    re.IGNORECASE,
)

# Visitor email query anti-pattern
VISITOR_EMAIL_QUERY = re.compile(
    r"/visitors\?[^\"'\s]*email=",
    re.IGNORECASE,
)

# Standalone Pardot credentials (user_key is a v3/v4 credential)
PARDOT_USER_KEY = re.compile(
    r"\buser_key\b",
    re.IGNORECASE,
)

# Source file extensions to scan
SOURCE_EXTENSIONS = {
    ".py", ".js", ".ts", ".cls", ".java", ".go",
    ".rb", ".php", ".cs", ".sh", ".http",
}


def scan_file(file_path: Path) -> list[str]:
    """Scan a single source file for MCAE API v5 anti-patterns.

    Returns a list of issue strings (empty if no issues found).
    """
    issues: list[str] = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return issues

    rel = file_path.name

    # Check 1: deprecated v3/v4 API endpoints
    if DEPRECATED_API_PATTERN.search(content):
        issues.append(
            f"{rel}: uses deprecated Pardot API v3/v4 URL (pi.pardot.com/api/3/ or /api/4/). "
            "Migrate to https://pi.pardot.com/api/v5/objects/{{object}}"
        )

    # Check 2: legacy Pardot login authentication
    if LEGACY_AUTH_PATTERN.search(content):
        issues.append(
            f"{rel}: references legacy Pardot authentication endpoint (pi.pardot.com/api/login). "
            "API v5 requires Salesforce OAuth via login.salesforce.com — not standalone Pardot credentials."
        )

    # Check 3: v5 API calls present but required header absent
    if PARDOT_API_V5_CALL.search(content) and not REQUIRED_HEADER.search(content):
        issues.append(
            f"{rel}: calls MCAE API v5 but 'Pardot-Business-Unit-Id' header not found in file. "
            "This header is required on every request; omitting it returns 401."
        )

    # Check 4: offset pagination in files that also use v5
    if PARDOT_API_V5_CALL.search(content) and OFFSET_PAGINATION_IN_V5.search(content):
        issues.append(
            f"{rel}: may use offset/page pagination with MCAE API v5. "
            "v5 requires cursor-based pagination via 'nextPageMark'; offset parameters are silently ignored."
        )

    # Check 5: visitor query by email anti-pattern
    if VISITOR_EMAIL_QUERY.search(content):
        issues.append(
            f"{rel}: queries Visitor object by email (/visitors?...email=...). "
            "Visitors are anonymous; filter VisitorActivities by prospectId instead."
        )

    # Check 6: Pardot user_key credential (v3/v4 auth artifact)
    if PARDOT_USER_KEY.search(content):
        issues.append(
            f"{rel}: references 'user_key' — a v3/v4 Pardot credential. "
            "API v5 uses Salesforce OAuth only; remove user_key references."
        )

    return issues


def check_mcae_pardot_api(manifest_dir: Path) -> list[str]:
    """Scan the project directory for MCAE API v5 anti-patterns.

    Returns a list of issue strings found across all scanned files.
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    scanned = 0
    for file_path in manifest_dir.rglob("*"):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in SOURCE_EXTENSIONS:
            continue
        # Skip hidden directories and common non-source trees
        parts = file_path.parts
        if any(p.startswith(".") or p in ("node_modules", "__pycache__", "venv", ".venv") for p in parts):
            continue
        file_issues = scan_file(file_path)
        issues.extend(file_issues)
        scanned += 1

    if scanned == 0:
        issues.append(
            f"No source files found under {manifest_dir} "
            f"(looked for extensions: {', '.join(sorted(SOURCE_EXTENSIONS))}). "
            "Pass --manifest-dir pointing to your project root."
        )

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check source files for MCAE (Pardot) API v5 integration anti-patterns: "
            "deprecated API versions, missing required headers, offset pagination, "
            "visitor email queries, and legacy authentication."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the project to scan (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_mcae_pardot_api(manifest_dir)

    if not issues:
        print("No MCAE API v5 issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
