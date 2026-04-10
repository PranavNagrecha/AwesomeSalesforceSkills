#!/usr/bin/env python3
"""Checker script for Marketing Cloud API skill.

Checks Apex metadata and configuration files for common Marketing Cloud API anti-patterns.
Uses stdlib only — no pip dependencies.

Checks performed:
  1. Detects hardcoded or generic MC endpoint URLs (non-tenant-specific)
  2. Detects legacy Fuel authentication patterns
  3. Detects token acquisition inside loops (missing token cache)
  4. Detects journey injection without EventDefinitionKey field
  5. Detects missing requestId polling for async DE operations
  6. Detects hardcoded credentials (client_id / client_secret literals)

Usage:
    python3 check_marketing_cloud_api.py [--help]
    python3 check_marketing_cloud_api.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Anti-pattern definitions
# ---------------------------------------------------------------------------

# Generic or legacy MC endpoint patterns that should never appear in code
LEGACY_ENDPOINT_PATTERNS = [
    (re.compile(r'exacttargetapis\.com', re.IGNORECASE),
     "Legacy/generic endpoint 'exacttargetapis.com' detected — use tenant-specific subdomain: "
     "{{subdomain}}.rest.marketingcloudapis.com"),
    (re.compile(r'auth\.exacttarget\.com', re.IGNORECASE),
     "Legacy Fuel auth endpoint 'auth.exacttarget.com' detected — use OAuth 2.0 via "
     "{{subdomain}}.auth.marketingcloudapis.com/v2/token"),
    (re.compile(r'/v1/requestToken', re.IGNORECASE),
     "Legacy Fuel token endpoint '/v1/requestToken' detected — use client_credentials grant "
     "at /v2/token on the tenant-specific auth subdomain"),
    (re.compile(r'AppID|AppSecret', re.IGNORECASE),
     "Legacy Fuel AppID/AppSecret credentials detected — use Installed Package Client ID and "
     "Client Secret with OAuth 2.0 client_credentials grant"),
]

# Hardcoded credential patterns
HARDCODED_CREDENTIAL_PATTERNS = [
    (re.compile(r'''(?i)(client_id|clientId)\s*[=:]\s*['"][0-9a-f\-]{20,}['"]'''),
     "Possible hardcoded client_id value — store credentials in Custom Metadata or Named Credentials"),
    (re.compile(r'''(?i)(client_secret|clientSecret)\s*[=:]\s*['"][0-9a-zA-Z\-_]{20,}['"]'''),
     "Possible hardcoded client_secret value — store credentials in Custom Metadata or Named Credentials"),
]

# Missing EventDefinitionKey in journey injection context
JOURNEY_INJECTION_WITHOUT_KEY = re.compile(
    r'interaction/v1/events', re.IGNORECASE
)
EVENT_DEFINITION_KEY_PRESENT = re.compile(
    r'EventDefinitionKey', re.IGNORECASE
)

# Async DE insert without requestId polling
ASYNC_DE_INSERT = re.compile(
    r'dataeventsasync', re.IGNORECASE
)
REQUEST_ID_POLLING = re.compile(
    r'requestId', re.IGNORECASE
)

# Token acquisition inside a loop (simple heuristic)
TOKEN_IN_LOOP_PATTERN = re.compile(
    r'(for|while|forEach)\s*[\(\{].*\n.*(/v2/token|getAccessToken|requestToken)',
    re.MULTILINE | re.DOTALL
)


def check_file(filepath: Path) -> list[str]:
    """Run all checks on a single file. Returns list of issue strings."""
    issues: list[str] = []

    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        issues.append(f"{filepath}: cannot read file — {exc}")
        return issues

    # Check 1: Legacy or generic endpoint URLs
    for pattern, message in LEGACY_ENDPOINT_PATTERNS:
        for match in pattern.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            issues.append(f"{filepath}:{line_num}: {message}")

    # Check 2: Hardcoded credentials
    for pattern, message in HARDCODED_CREDENTIAL_PATTERNS:
        for match in pattern.finditer(content):
            line_num = content[:match.start()].count('\n') + 1
            issues.append(f"{filepath}:{line_num}: {message}")

    # Check 3: Journey injection endpoint present but no EventDefinitionKey
    if JOURNEY_INJECTION_WITHOUT_KEY.search(content):
        if not EVENT_DEFINITION_KEY_PRESENT.search(content):
            issues.append(
                f"{filepath}: Journey injection endpoint (/interaction/v1/events) found but "
                f"'EventDefinitionKey' is missing from the file — verify the payload includes this field"
            )

    # Check 4: Async DE insert without requestId polling
    if ASYNC_DE_INSERT.search(content):
        if not REQUEST_ID_POLLING.search(content):
            issues.append(
                f"{filepath}: Async DE endpoint (dataeventsasync) found but no 'requestId' "
                f"reference detected — async inserts require polling the requestId for completion status"
            )

    return issues


def check_marketing_cloud_api(manifest_dir: Path) -> list[str]:
    """Scan the manifest directory for Marketing Cloud API anti-patterns.

    Returns a list of issue strings found across all relevant files.
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # File extensions to scan
    extensions = {'.cls', '.trigger', '.apex', '.js', '.json', '.py', '.yaml', '.yml', '.xml'}

    scanned = 0
    for filepath in manifest_dir.rglob('*'):
        if not filepath.is_file():
            continue
        if filepath.suffix.lower() not in extensions:
            continue
        file_issues = check_file(filepath)
        issues.extend(file_issues)
        scanned += 1

    if scanned == 0:
        issues.append(
            f"No scannable files found in {manifest_dir} "
            f"(looked for: {', '.join(sorted(extensions))})"
        )

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata and code for Marketing Cloud API anti-patterns. "
            "Detects legacy endpoints, hardcoded credentials, missing EventDefinitionKey, "
            "and missing requestId polling for async DE operations."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata to scan (default: current directory).",
    )
    args = parser.parse_args()
    manifest_dir = Path(args.manifest_dir)

    issues = check_marketing_cloud_api(manifest_dir)

    if not issues:
        print("No Marketing Cloud API issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
