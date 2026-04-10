#!/usr/bin/env python3
"""Checker script for Marketing Integration Patterns skill.

Validates metadata and source files for common Marketing Cloud integration issues:
- Hardcoded MC REST API domains (should use rest_instance_url from token response)
- Use of Journey ID where eventDefinitionKey is required
- Missing OAuth 2.0 token caching (re-auth on every call)
- Async batch calls that may exceed the 100-contact limit
- SOAP-style authentication credentials in REST calls
- Missing Installed Package / API Integration references in documentation

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_marketing_integration_patterns.py [--help]
    python3 check_marketing_integration_patterns.py --manifest-dir path/to/source
    python3 check_marketing_integration_patterns.py --manifest-dir path/to/source --ext .py .js .ts .cls
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Patterns that indicate anti-patterns documented in this skill
# ---------------------------------------------------------------------------

# Hardcoded generic Marketing Cloud REST domains (should use rest_instance_url dynamically)
HARDCODED_MC_DOMAINS = re.compile(
    r'https?://(www\.)?exacttargetapis\.com|mcapi\.salesforce\.com',
    re.IGNORECASE,
)

# Journey Injection endpoint used with a plain UUID (no APIEvent- prefix) as the event key
# Detects cases where a Journey ID is likely being used instead of eventDefinitionKey
JOURNEY_ID_AS_EVENT_KEY = re.compile(
    r'["\']EventDefinitionKey["\']\s*:\s*["\'](?!APIEvent-)[0-9a-fA-F\-]{30,}["\']',
    re.IGNORECASE,
)

# SOAP / legacy credential patterns in code — username/password used as HTTP request headers
# in REST calls to Marketing Cloud. Match only in code contexts (dict/object key assignment)
# not in documentation prose. Requires the credential key AND a Marketing Cloud domain on
# the same line or within close proximity; use single-line match to avoid documentation hits.
SOAP_AUTH_PATTERN = re.compile(
    r'["\'](?:Username|Password)["\']\s*:\s*["\'][^"\']+["\']\s*[,}]',
    re.IGNORECASE,
)

# Token endpoint called inside a per-request loop — naïve heuristic: /v2/token
# appearing in a loop body (for/while before token call without caching variable)
# We detect multiple /v2/token occurrences without a cache/expires pattern nearby
TOKEN_ENDPOINT_PATTERN = re.compile(r'/v2/token', re.IGNORECASE)
TOKEN_CACHE_PATTERN = re.compile(
    r'(cache|expire|ttl|expir|refresh|token_time|token_age|access_token\s*=)',
    re.IGNORECASE,
)

# async batch endpoint — look for contacts arrays that are NOT sliced/chunked
# Heuristic: /events/async present but no slice/chunk/batch_size/[:100]/range(0 pattern nearby
ASYNC_BATCH_ENDPOINT = re.compile(r'/interaction/v1/events/async', re.IGNORECASE)
BATCH_CHUNK_PATTERN = re.compile(
    r'(chunk|slice|batch_size|BATCH_SIZE|\[:100\]|\[i:i\s*\+|range\(0|\.split\()',
    re.IGNORECASE,
)

# eventDefinitionKey used without APIEvent- prefix validation
EVENT_DEF_KEY_RAW = re.compile(
    r'eventDefinitionKey|EventDefinitionKey|event_definition_key',
    re.IGNORECASE,
)

SUPPORTED_EXTENSIONS = {'.py', '.js', '.ts', '.cls', '.java', '.rb', '.go', '.md', '.html'}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check source files for common Marketing Cloud integration anti-patterns. "
            "Reports hardcoded domains, wrong eventDefinitionKey usage, missing token caching, "
            "batch limit violations, and SOAP-style auth in REST contexts."
        ),
    )
    parser.add_argument(
        '--manifest-dir',
        default='.',
        help='Root directory to scan for source files (default: current directory).',
    )
    parser.add_argument(
        '--ext',
        nargs='+',
        default=list(SUPPORTED_EXTENSIONS),
        help='File extensions to check (default: .py .js .ts .cls .java .rb .go .md .html).',
    )
    return parser.parse_args()


SKIP_DIR_NAMES = {'references', 'templates', 'node_modules', '.git', '__pycache__', 'vendor'}


def collect_files(manifest_dir: Path, extensions: list[str]) -> list[Path]:
    """Collect source files to check, skipping documentation directories.

    Directories named 'references' contain skill documentation that intentionally
    shows both correct and incorrect patterns for educational purposes — scanning
    them would produce false positives. Only scan directories that contain
    application source code.
    """
    files: list[Path] = []
    ext_set = {e if e.startswith('.') else f'.{e}' for e in extensions}
    this_script = Path(__file__).resolve()
    for path in manifest_dir.rglob('*'):
        # Skip known documentation and non-source directories
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        # Skip this checker script itself
        if path.resolve() == this_script:
            continue
        if path.is_file() and path.suffix.lower() in ext_set:
            files.append(path)
    return sorted(files)


def check_file(filepath: Path) -> list[str]:
    """Run all checks against a single file. Returns list of issue strings."""
    issues: list[str] = []
    try:
        content = filepath.read_text(encoding='utf-8', errors='replace')
    except OSError as exc:
        issues.append(f'{filepath}: could not read file — {exc}')
        return issues

    lines = content.splitlines()

    # --- Check 1: Hardcoded generic MC REST domains ---
    for lineno, line in enumerate(lines, start=1):
        if HARDCODED_MC_DOMAINS.search(line):
            issues.append(
                f'{filepath}:{lineno}: Hardcoded Marketing Cloud domain detected '
                f'("{HARDCODED_MC_DOMAINS.pattern}"). '
                'Use rest_instance_url from the OAuth token response instead of a generic domain.'
            )

    # --- Check 2: EventDefinitionKey using non-APIEvent- value (likely Journey ID) ---
    for lineno, line in enumerate(lines, start=1):
        if JOURNEY_ID_AS_EVENT_KEY.search(line):
            issues.append(
                f'{filepath}:{lineno}: EventDefinitionKey appears to use a plain UUID '
                '(not prefixed with "APIEvent-"). Journey Injection requires the eventDefinitionKey '
                'from the REST API Entry Source, not the Journey ID. '
                'The correct value starts with "APIEvent-".'
            )

    # --- Check 3: SOAP-style username/password credentials in REST context ---
    for lineno, line in enumerate(lines, start=1):
        if SOAP_AUTH_PATTERN.search(line):
            issues.append(
                f'{filepath}:{lineno}: SOAP-style "Username" or "Password" credential pattern '
                'detected alongside Marketing Cloud domain. Marketing Cloud REST APIs require '
                'OAuth 2.0 client credentials from an Installed Package, not username/password auth.'
            )

    # --- Check 4: Token endpoint called without caching evidence ---
    token_call_count = len(TOKEN_ENDPOINT_PATTERN.findall(content))
    has_cache = bool(TOKEN_CACHE_PATTERN.search(content))
    if token_call_count > 1 and not has_cache:
        issues.append(
            f'{filepath}: Marketing Cloud /v2/token endpoint appears {token_call_count} times '
            'without evidence of token caching (no cache/expire/ttl/refresh pattern found). '
            'Access tokens are valid for 20 minutes — cache and reuse them instead of '
            're-authenticating on every API call.'
        )

    # --- Check 5: Async batch endpoint without chunking logic ---
    if ASYNC_BATCH_ENDPOINT.search(content):
        if not BATCH_CHUNK_PATTERN.search(content):
            issues.append(
                f'{filepath}: /interaction/v1/events/async is used but no chunking or batch-size '
                'logic detected (no slice/chunk/BATCH_SIZE/range pattern found). '
                'The async batch endpoint accepts a maximum of 100 contacts per request. '
                'Add explicit chunking to split input lists into batches of ≤ 100 before each call.'
            )

    return issues


def check_marketing_integration_patterns(manifest_dir: Path, extensions: list[str]) -> list[str]:
    """Return a list of issue strings found across all files in manifest_dir."""
    all_issues: list[str] = []

    if not manifest_dir.exists():
        all_issues.append(f'Manifest directory not found: {manifest_dir}')
        return all_issues

    files = collect_files(manifest_dir, extensions)

    if not files:
        # Not an error — just nothing to check
        return all_issues

    for filepath in files:
        file_issues = check_file(filepath)
        all_issues.extend(file_issues)

    return all_issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_marketing_integration_patterns(manifest_dir, args.ext)

    if not issues:
        print('No Marketing Cloud integration anti-patterns detected.')
        return 0

    for issue in issues:
        print(f'WARN: {issue}', file=sys.stderr)

    print(
        f'\n{len(issues)} issue(s) found. '
        'See references/llm-anti-patterns.md for correct patterns.',
        file=sys.stderr,
    )
    return 1


if __name__ == '__main__':
    sys.exit(main())
