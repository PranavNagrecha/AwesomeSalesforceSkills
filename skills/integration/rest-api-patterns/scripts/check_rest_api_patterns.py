#!/usr/bin/env python3
"""Checker script for REST API Patterns skill.

Inspects Salesforce project metadata to surface common REST API integration
anti-patterns: hard-coded old API versions, missing error handling markers,
and composite usage without subrequest result inspection.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_rest_api_patterns.py [--help]
    python3 check_rest_api_patterns.py --manifest-dir path/to/force-app
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Minimum acceptable API version (roughly last 4 major releases from Spring '25)
MIN_API_VERSION = 56

# Regex patterns for source scan
_RE_OLD_API_VERSION = re.compile(r"/services/data/v(\d+)(?:\.\d+)?/")
_RE_COMPOSITE_CALL = re.compile(r"/composite(?:/batch|/tree)?[/\"']")
_RE_OUTER_STATUS_ONLY = re.compile(
    r"(?:status_code|statusCode|http_status|httpStatus)\s*(?:==|===|!=|!==)\s*['\"]?200['\"]?",
    re.IGNORECASE,
)
_RE_COMPOSITE_RESPONSE_CHECK = re.compile(
    r"compositeResponse|httpStatusCode|subrequest",
    re.IGNORECASE,
)
_RE_NEXT_RECORDS_URL = re.compile(r"nextRecordsUrl", re.IGNORECASE)
_RE_DONE_FLAG = re.compile(r'"done"\s*:|\.done\b', re.IGNORECASE)


def _scan_file_for_api_version_issues(path: Path) -> list[str]:
    """Return issues related to old/pinned API versions in a source file."""
    issues: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return issues

    for match in _RE_OLD_API_VERSION.finditer(text):
        version_str = match.group(1)
        try:
            version = int(version_str)
        except ValueError:
            continue
        if version < MIN_API_VERSION:
            line_num = text[: match.start()].count("\n") + 1
            issues.append(
                f"{path}:{line_num} — REST API version v{version_str}.0 is below "
                f"the recommended minimum (v{MIN_API_VERSION}.0). Update to a "
                f"recent version (v60.0+ recommended)."
            )
    return issues


def _scan_file_for_composite_issues(path: Path) -> list[str]:
    """Check that files using Composite resources also inspect subrequest results."""
    issues: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return issues

    if not _RE_COMPOSITE_CALL.search(text):
        return issues  # File does not use Composite — skip

    # Flag files that check outer HTTP 200 but do not appear to inspect
    # per-subrequest httpStatusCode or compositeResponse entries.
    has_outer_status_check = bool(_RE_OUTER_STATUS_ONLY.search(text))
    has_subrequest_check = bool(_RE_COMPOSITE_RESPONSE_CHECK.search(text))

    if has_outer_status_check and not has_subrequest_check:
        issues.append(
            f"{path} — Uses a Composite resource and checks outer HTTP 200 but "
            f"no inspection of 'compositeResponse' or per-subrequest "
            f"'httpStatusCode' was detected. Outer HTTP 200 does not guarantee "
            f"subrequest success; inspect each subrequest result."
        )
    return issues


def _scan_file_for_pagination_issues(path: Path) -> list[str]:
    """Check that files issuing SOQL queries also handle nextRecordsUrl."""
    issues: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return issues

    # Look for files that reference the /query/ endpoint
    if "/query/" not in text and "query?q=" not in text.lower():
        return issues

    has_next_records = bool(_RE_NEXT_RECORDS_URL.search(text))
    has_done_flag = bool(_RE_DONE_FLAG.search(text))

    if not has_next_records or not has_done_flag:
        missing = []
        if not has_next_records:
            missing.append("'nextRecordsUrl'")
        if not has_done_flag:
            missing.append("'done' flag check")
        issues.append(
            f"{path} — References the SOQL /query/ endpoint but is missing "
            f"pagination handling: {', '.join(missing)}. Queries returning "
            f">2,000 records require following nextRecordsUrl until done=true."
        )
    return issues


def check_rest_api_patterns(manifest_dir: Path) -> list[str]:
    """Scan manifest_dir for REST API integration issues.

    Returns a list of actionable issue strings.
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Scan source files: Apex (.cls), JavaScript (.js), Python (.py), JSON (.json)
    extensions = {".cls", ".js", ".py", ".json", ".ts"}
    source_files = [
        f
        for f in manifest_dir.rglob("*")
        if f.is_file() and f.suffix in extensions
        # Skip generated and dependency directories
        and not any(part in f.parts for part in ("node_modules", ".sfdx", "__pycache__"))
    ]

    for source_file in source_files:
        issues.extend(_scan_file_for_api_version_issues(source_file))
        issues.extend(_scan_file_for_composite_issues(source_file))
        issues.extend(_scan_file_for_pagination_issues(source_file))

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce project metadata and source for REST API "
            "integration anti-patterns (old API versions, composite error "
            "handling gaps, missing pagination)."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce project metadata (default: current directory).",
    )
    args = parser.parse_args()
    manifest_dir = Path(args.manifest_dir)

    issues = check_rest_api_patterns(manifest_dir)

    if not issues:
        print("No REST API pattern issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
