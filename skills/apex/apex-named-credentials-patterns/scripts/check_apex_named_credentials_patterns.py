#!/usr/bin/env python3
"""Checker script for Apex Named Credentials Patterns skill.

Scans Apex source files (.cls) and Named Credential metadata (.namedCredential,
.externalCredential) for common anti-patterns documented in this skill.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_apex_named_credentials_patterns.py [--help]
    python3 check_apex_named_credentials_patterns.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Patterns that indicate anti-patterns in Apex code
# ---------------------------------------------------------------------------

# Hard-coded HTTPS endpoint in setEndpoint (should use callout: prefix)
HARDCODED_ENDPOINT_PATTERN = re.compile(
    r'setEndpoint\s*\(\s*["\']https?://',
    re.IGNORECASE,
)

# setHeader for Authorization — credentials injected manually
AUTH_HEADER_PATTERN = re.compile(
    r'setHeader\s*\(\s*["\']Authorization["\']',
    re.IGNORECASE,
)

# {!$Credential.*} in Apex string literals (inside double-quoted strings)
FORMULA_TOKEN_IN_APEX_PATTERN = re.compile(
    r'"[^"]*\{\s*!\s*\$Credential\.[^}]+\}[^"]*"',
)

# Continuation with callout: prefix — not supported
CONTINUATION_WITH_CALLOUT_PATTERN = re.compile(
    r'new\s+Continuation\s*\(.*?\).*?setEndpoint\s*\(\s*["\']callout:',
    re.IGNORECASE | re.DOTALL,
)

# Missing timeout: setEndpoint used without setTimeout in the same file
# (heuristic — check if setTimeout is absent in files that do callouts)
SET_ENDPOINT_PATTERN = re.compile(r'setEndpoint\s*\(', re.IGNORECASE)
SET_TIMEOUT_PATTERN = re.compile(r'setTimeout\s*\(', re.IGNORECASE)

# Credential-like values in Custom Label / Custom Setting reads near setHeader
CUSTOM_LABEL_IN_HEADER = re.compile(
    r'setHeader\s*\([^)]+System\.Label\.',
    re.IGNORECASE,
)


def check_apex_files(manifest_dir: Path) -> list[str]:
    """Check Apex .cls files for Named Credential anti-patterns."""
    issues: list[str] = []

    cls_files = list(manifest_dir.rglob("*.cls"))
    if not cls_files:
        return issues

    for cls_file in cls_files:
        try:
            source = cls_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        rel = cls_file.relative_to(manifest_dir)

        # Anti-pattern 1: hardcoded HTTPS endpoint
        if HARDCODED_ENDPOINT_PATTERN.search(source):
            issues.append(
                f"{rel}: setEndpoint() uses a hardcoded HTTPS URL. "
                "Use 'callout:<NamedCredentialApiName>/path' instead."
            )

        # Anti-pattern 2: manual Authorization header
        if AUTH_HEADER_PATTERN.search(source):
            issues.append(
                f"{rel}: setHeader('Authorization', ...) found. "
                "Auth headers should be injected via Named Credential custom header formulas, "
                "not set manually in Apex."
            )

        # Anti-pattern 3: Custom Label credential in header
        if CUSTOM_LABEL_IN_HEADER.search(source):
            issues.append(
                f"{rel}: setHeader() uses a System.Label value. "
                "Credentials stored in Custom Labels are not encrypted. "
                "Use a Named Credential instead."
            )

        # Anti-pattern 4: formula token in Apex string literal
        if FORMULA_TOKEN_IN_APEX_PATTERN.search(source):
            issues.append(
                f"{rel}: {{!$Credential.*}} formula token found in an Apex string literal. "
                "These tokens only resolve inside Named Credential custom header fields "
                "configured in the Setup UI, not in Apex code."
            )

        # Anti-pattern 5: Continuation with callout: prefix
        if CONTINUATION_WITH_CALLOUT_PATTERN.search(source):
            issues.append(
                f"{rel}: Continuation framework used with 'callout:' endpoint prefix. "
                "The callout: prefix is not supported by the Continuation framework. "
                "Use a Queueable (Database.AllowsCallouts) for async Named Credential callouts."
            )

        # Warning: callout without explicit timeout
        if SET_ENDPOINT_PATTERN.search(source) and not SET_TIMEOUT_PATTERN.search(source):
            issues.append(
                f"{rel}: callout endpoint is set but no setTimeout() found in this file. "
                "The default callout timeout is 10 seconds. "
                "Consider setting an explicit timeout (max 120 000 ms)."
            )

    return issues


def check_named_credential_metadata(manifest_dir: Path) -> list[str]:
    """Check Named Credential XML metadata for common issues."""
    issues: list[str] = []

    nc_files = (
        list(manifest_dir.rglob("*.namedCredential"))
        + list(manifest_dir.rglob("*.namedCredential-meta.xml"))
    )

    for nc_file in nc_files:
        try:
            content = nc_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        rel = nc_file.relative_to(manifest_dir)

        # Flag Named Credentials that have allowFormula disabled (blocks formula tokens)
        if "<allowFormula>false</allowFormula>" in content:
            issues.append(
                f"{rel}: Named Credential has allowFormula=false. "
                "Custom header formula tokens such as {{!$Credential.OAuthToken}} "
                "will not be evaluated. Enable formula support if custom headers are needed."
            )

        # Warn if endpoint is plain HTTP (not HTTPS) — security concern
        endpoint_match = re.search(r"<endpoint>(http://[^<]+)</endpoint>", content)
        if endpoint_match:
            issues.append(
                f"{rel}: Named Credential endpoint uses plain HTTP: "
                f"{endpoint_match.group(1)}. "
                "All external endpoints should use HTTPS."
            )

    return issues


def check_apex_named_credentials_patterns(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_apex_files(manifest_dir))
    issues.extend(check_named_credential_metadata(manifest_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Apex source files and Named Credential metadata for "
            "anti-patterns documented in the apex-named-credentials-patterns skill."
        ),
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
    issues = check_apex_named_credentials_patterns(manifest_dir)

    if not issues:
        print("No Named Credential anti-patterns found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
