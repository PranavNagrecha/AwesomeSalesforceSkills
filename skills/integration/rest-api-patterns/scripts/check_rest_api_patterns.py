#!/usr/bin/env python3
"""Checker script for REST API Patterns skill.

Inspects Salesforce project metadata to surface common REST API integration
anti-patterns: hard-coded old API versions, missing error handling markers,
and composite usage without subrequest result inspection.

Rules added 2026-10-03, grounded on the REST API Developer Guide v67.0
(API End-of-Life Policy; Status Codes and Error Responses):
  * A version at or below 30.0 is retired and returns 410 GONE.
  * Retry logic keyed on HTTP 429 or Retry-After without any REQUEST_LIMIT_EXCEEDED
    handling: the REST guide documents 403 with errorCode REQUEST_LIMIT_EXCEEDED
    for exceeded request limits and lists no 429.

Uses stdlib only; no pip dependencies.

Usage:
    python3 check_rest_api_patterns.py [--help]
    python3 check_rest_api_patterns.py --manifest-dir path/to/force-app
    python3 check_rest_api_patterns.py --self-test
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Minimum acceptable API version (roughly last 4 major releases from Spring '25)
MIN_API_VERSION = 56
# Versions 7.0 through 30.0 are retired (REST guide, API End-of-Life Policy)
RETIRED_MAX_VERSION = 30
_RE_429 = re.compile(r"\b429\b|Retry-After", re.IGNORECASE)
_RE_LIMIT_CODE = re.compile(r"REQUEST_LIMIT_EXCEEDED")

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
_RE_DONE_FLAG = re.compile(r'"done"\s*:|\.done\b|\[\s*[\'"]done[\'"]\s*\]', re.IGNORECASE)


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
        if version <= RETIRED_MAX_VERSION:
            line_num = text[: match.start()].count("\n") + 1
            issues.append(
                f"{path}:{line_num}: REST API version v{version_str}.0 is retired; requests "
                f"return 410 GONE (versions 7.0 through 30.0 are retired). Upgrade the version."
            )
        elif version < MIN_API_VERSION:
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


def _scan_file_for_limit_handling(path: Path) -> list[str]:
    """Flag retry logic that waits for 429/Retry-After but never handles REQUEST_LIMIT_EXCEEDED."""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    if "/services/data/" not in text:
        return []
    if _RE_429.search(text) and not _RE_LIMIT_CODE.search(text):
        return [
            f"{path}: Retry logic keys on HTTP 429 or Retry-After. Salesforce REST API returns 403 "
            f"with errorCode REQUEST_LIMIT_EXCEEDED when request limits are exceeded; handle that code."
        ]
    return []


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
        issues.extend(_scan_file_for_limit_handling(source_file))

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
    parser.add_argument("--self-test", action="store_true", help="Run the bundled fixtures and exit.")
    args = parser.parse_args()
    if args.self_test:
        here = Path(__file__).resolve().parent / "fixtures"
        good = check_rest_api_patterns(here / "good")
        bad = check_rest_api_patterns(here / "bad")
        expected = ["is retired", "below the recommended minimum", "no inspection of 'compositeResponse'",
                    "missing pagination handling", "REQUEST_LIMIT_EXCEEDED"]
        missing = [e for e in expected if not any(e in issue for issue in bad)]
        print(f"good fixtures: {len(good)} issue(s) (expected 0)")
        for g in good:
            print(f"  unexpected: {g}")
        print(f"bad fixtures: {len(bad)} issue(s); missing expected: {missing or 'none'}")
        return 0 if not good and not missing else 1
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
