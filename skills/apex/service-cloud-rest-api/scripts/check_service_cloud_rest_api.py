#!/usr/bin/env python3
"""Checker script for Service Cloud REST API skill.

Scans Apex source files and metadata in a Salesforce project directory for
common Service Cloud REST API anti-patterns:

  1. Legacy Chat REST API usage (retired Feb 14, 2026)
  2. Knowledge authoring endpoint used in guest/Experience Cloud contexts
  3. Missing URL-encoding on Knowledge API category parameters
  4. Hardcoded Knowledge article record IDs in URLs
  5. Missing empty-array handling after Knowledge REST API calls

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_service_cloud_rest_api.py [--help]
    python3 check_service_cloud_rest_api.py --manifest-dir path/to/metadata
    python3 check_service_cloud_rest_api.py --manifest-dir . --verbose
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Legacy Chat REST API indicators
LEGACY_CHAT_PATTERNS: list[tuple[str, str]] = [
    (r"/chat/rest/", "Legacy Chat REST API path `/chat/rest/` (retired Feb 14, 2026)"),
    (r"X-LIVEAGENT-API-VERSION", "Legacy Chat REST API header `X-LIVEAGENT-API-VERSION` (retired)"),
    (r"X-LIVEAGENT-SESSION-KEY", "Legacy Chat REST API header `X-LIVEAGENT-SESSION-KEY` (retired)"),
    (r"X-LIVEAGENT-AFFINITY", "Legacy Chat REST API header `X-LIVEAGENT-AFFINITY` (retired)"),
    (r"ChasitorInit", "Legacy Chat REST API endpoint `ChasitorInit` (retired)"),
    (r"/System/SessionId", "Legacy Chat REST API path `/System/SessionId` (retired)"),
    (r"/System/Messages", "Legacy Chat REST API long-poll path `/System/Messages` (retired)"),
]

# Knowledge authoring endpoint used — check if it appears near 'without sharing' or 'AuraEnabled'
# or in classes that look like they serve Experience Cloud guests
KNOWLEDGE_AUTHORING_IN_GUEST_CONTEXT = re.compile(
    r"knowledgeManagement/articles",
    re.IGNORECASE,
)

GUEST_CONTEXT_INDICATORS = re.compile(
    r"(without\s+sharing|@AuraEnabled.*cacheable\s*=\s*true|ExperienceCloud|Site\.getBaseUrl|Network\.getNetworkId)",
    re.IGNORECASE | re.DOTALL,
)

# URL encoding check: categoryGroup= or category= in string concat without EncodingUtil
CATEGORY_WITHOUT_ENCODING = re.compile(
    r"""(?:categoryGroup|category)\s*=\s*["']?\s*\+""",
    re.IGNORECASE,
)

ENCODING_UTIL_PRESENT = re.compile(
    r"EncodingUtil\.urlEncode",
    re.IGNORECASE,
)

# Hardcoded Knowledge article record IDs (kA0... or kA1... patterns) in strings
HARDCODED_ARTICLE_ID = re.compile(
    r"""["'](kA[0-9][a-zA-Z0-9]{12,15})["']""",
)

# Empty array check: body.get('articles') without isEmpty() or == null nearby
ARTICLES_GET = re.compile(r"""body\.get\(['"]articles['"]\)""", re.IGNORECASE)
EMPTY_CHECK = re.compile(r"(isEmpty\s*\(\s*\)|==\s*null|!= null)", re.IGNORECASE)


# ---------------------------------------------------------------------------
# File scanners
# ---------------------------------------------------------------------------

def _apex_files(manifest_dir: Path) -> list[Path]:
    """Return all .cls and .trigger files under manifest_dir."""
    return list(manifest_dir.rglob("*.cls")) + list(manifest_dir.rglob("*.trigger"))


def check_legacy_chat_rest(files: list[Path], verbose: bool) -> list[str]:
    issues: list[str] = []
    for pattern_str, description in LEGACY_CHAT_PATTERNS:
        compiled = re.compile(pattern_str, re.IGNORECASE)
        for f in files:
            try:
                content = f.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for i, line in enumerate(content.splitlines(), 1):
                if compiled.search(line):
                    issues.append(
                        f"{f.name}:{i} — {description}"
                    )
                    if verbose:
                        issues.append(f"    context: {line.strip()}")
    return issues


def check_knowledge_authoring_in_guest_context(files: list[Path], verbose: bool) -> list[str]:
    """Flag Apex files that use /knowledgeManagement/ AND contain guest-context indicators."""
    issues: list[str] = []
    for f in files:
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if KNOWLEDGE_AUTHORING_IN_GUEST_CONTEXT.search(content) and GUEST_CONTEXT_INDICATORS.search(content):
            issues.append(
                f"{f.name} — uses `/knowledgeManagement/` (authoring endpoint) "
                "alongside guest-context indicators (`without sharing`, `@AuraEnabled cacheable`, "
                "Experience Cloud APIs). Consider `/support/knowledgeWithSEO/` for guest contexts."
            )
    return issues


def check_category_url_encoding(files: list[Path], verbose: bool) -> list[str]:
    """Flag files that build categoryGroup/category query params without EncodingUtil.urlEncode."""
    issues: list[str] = []
    for f in files:
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if CATEGORY_WITHOUT_ENCODING.search(content) and not ENCODING_UTIL_PRESENT.search(content):
            issues.append(
                f"{f.name} — builds `categoryGroup=` or `category=` query parameter via string "
                "concatenation without `EncodingUtil.urlEncode()`. Category developer names with "
                "special characters will produce malformed URLs."
            )
    return issues


def check_hardcoded_article_ids(files: list[Path], verbose: bool) -> list[str]:
    """Flag hardcoded Knowledge article record IDs (kA0.../kA1...) in source files."""
    issues: list[str] = []
    for f in files:
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for match in HARDCODED_ARTICLE_ID.finditer(content):
            line_num = content[: match.start()].count("\n") + 1
            issues.append(
                f"{f.name}:{line_num} — hardcoded Knowledge article ID `{match.group(1)}`. "
                "Article IDs change on re-publication. Use URL-name lookup via "
                "`/support/knowledgeWithSEO/articles?urlName=<slug>` for stable references."
            )
    return issues


def check_missing_empty_array_handling(files: list[Path], verbose: bool) -> list[str]:
    """Flag files that call body.get('articles') without a nearby null/isEmpty check."""
    issues: list[str] = []
    for f in files:
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if not ARTICLES_GET.search(content):
            continue
        # Check a 5-line window around each match for empty handling
        lines = content.splitlines()
        for i, line in enumerate(lines):
            if ARTICLES_GET.search(line):
                window_start = max(0, i - 1)
                window_end = min(len(lines), i + 6)
                window = "\n".join(lines[window_start:window_end])
                if not EMPTY_CHECK.search(window):
                    issues.append(
                        f"{f.name}:{i + 1} — `body.get('articles')` found without a nearby "
                        "`isEmpty()` or null check. The Knowledge REST API returns HTTP 200 with "
                        "`articles: []` for invalid category names — handle this case explicitly."
                    )
    return issues


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def check_service_cloud_rest_api(manifest_dir: Path, verbose: bool = False) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    apex_files = _apex_files(manifest_dir)

    if not apex_files:
        # No Apex files to scan — not necessarily an error; report if verbose
        if verbose:
            issues.append(
                f"No Apex (.cls/.trigger) files found under {manifest_dir}. "
                "Nothing to check for Service Cloud REST API patterns."
            )
        return issues

    issues += check_legacy_chat_rest(apex_files, verbose)
    issues += check_knowledge_authoring_in_guest_context(apex_files, verbose)
    issues += check_category_url_encoding(apex_files, verbose)
    issues += check_hardcoded_article_ids(apex_files, verbose)
    issues += check_missing_empty_array_handling(apex_files, verbose)

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Apex source files for Service Cloud REST API anti-patterns: "
            "legacy Chat REST API usage, wrong Knowledge endpoint for guest context, "
            "missing URL encoding, hardcoded article IDs, and missing empty-array handling."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce project/metadata (default: current directory).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Include additional context in issue output.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_service_cloud_rest_api(manifest_dir, verbose=args.verbose)

    if not issues:
        print("No Service Cloud REST API issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
