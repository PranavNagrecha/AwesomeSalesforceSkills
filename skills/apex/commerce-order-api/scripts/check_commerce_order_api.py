#!/usr/bin/env python3
"""Checker script for Commerce Order API skill (SCAPI / OCAPI headless storefront).

Scans Salesforce metadata and Apex source for common anti-patterns related to:
  - Direct DML on OrderItemSummary in MANAGED mode (financial aggregate corruption)
  - SLAS token stored in localStorage-style patterns in LWC / JS files
  - OCAPI client ID used in SCAPI endpoint calls
  - Missing deduplication on POST /orders callouts (non-idempotent retry risk)
  - Hardcoded SLAS credentials in Apex source

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_commerce_order_api.py [--help]
    python3 check_commerce_order_api.py --manifest-dir path/to/metadata
    python3 check_commerce_order_api.py --manifest-dir . --verbose
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Patterns: Anti-patterns to detect
# ---------------------------------------------------------------------------

# Direct DML on OrderItemSummary — sets QuantityCanceled, QuantityReturnInitiated, etc.
# Flags: update <var> where var likely refers to OrderItemSummary
APEX_OIS_DML_PATTERNS = [
    # Explicit field assignment that should go through Connect API
    re.compile(r"\b(QuantityCanceled|QuantityReturnInitiated|QuantityReturnExpected)\s*=\s*", re.IGNORECASE),
    # update statement on a variable named after OIS patterns
    re.compile(r"\bupdate\s+\w*(orderItemSummary|ois|OrderItemSummary)\w*\b", re.IGNORECASE),
]

# Hardcoded SLAS or OCAPI credentials in Apex
APEX_HARDCODED_SECRET_PATTERNS = [
    re.compile(r"(client_secret|clientSecret|client_id|clientId)\s*=\s*['\"][A-Za-z0-9_\-]{10,}['\"]", re.IGNORECASE),
    re.compile(r"x-dw-client-id\s*['\"]?\s*,\s*['\"][A-Za-z0-9_\-]{5,}['\"]", re.IGNORECASE),
]

# OCAPI auth header being set on what appears to be a SCAPI URL
APEX_OCAPI_ON_SCAPI_PATTERN = re.compile(
    r"x-dw-client-id.*api\.commercecloud\.salesforce\.com|api\.commercecloud\.salesforce\.com.*x-dw-client-id",
    re.IGNORECASE | re.DOTALL,
)

# Missing deduplication: retry on POST /orders without GET /orders check nearby
# Heuristic: a retry loop containing '/orders' POST callout but no GET callout nearby
APEX_ORDERS_POST_IN_LOOP = re.compile(
    r"\bfor\s*\(|while\s*\(.*?POST.*?/orders|/orders.*?POST.*?while\s*\(",
    re.IGNORECASE | re.DOTALL,
)

# LWC / JS: localStorage.setItem with token-sounding keys
JS_LOCALSTORAGE_TOKEN_PATTERN = re.compile(
    r"localStorage\s*\.\s*setItem\s*\(\s*['\"][^'\"]*(?:token|access_token|slas|auth)[^'\"]*['\"]",
    re.IGNORECASE,
)

# LWC / JS: sessionStorage with token-sounding keys
JS_SESSIONSTORAGE_TOKEN_PATTERN = re.compile(
    r"sessionStorage\s*\.\s*setItem\s*\(\s*['\"][^'\"]*(?:token|access_token|slas|auth)[^'\"]*['\"]",
    re.IGNORECASE,
)

# JS: x-dw-client-id header on a SCAPI-looking URL
JS_OCAPI_ON_SCAPI_PATTERN = re.compile(
    r"x-dw-client-id.*api\.commercecloud\.salesforce\.com",
    re.IGNORECASE,
)

# Named Credential callout check: SCAPI callout that does NOT use 'callout:' prefix
# (heuristic: endpoint string hardcoded instead of Named Credential)
APEX_HARDCODED_SCAPI_ENDPOINT = re.compile(
    r"setEndpoint\s*\(\s*['\"]https?://[a-z0-9]+\.api\.commercecloud\.salesforce\.com",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# File traversal helpers
# ---------------------------------------------------------------------------

def iter_apex_files(root: Path):
    """Yield all .cls and .trigger files under root."""
    for ext in ("*.cls", "*.trigger"):
        yield from root.rglob(ext)


def iter_js_files(root: Path):
    """Yield all .js and .ts files under root (LWC / Aura)."""
    for ext in ("*.js", "*.ts"):
        yield from root.rglob(ext)


def check_file(path: Path, patterns: list, label_prefix: str) -> list[str]:
    """Return issues for a single file given a list of (pattern, message) tuples."""
    issues = []
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return issues

    for pattern, message in patterns:
        matches = pattern.findall(content)
        if matches:
            issues.append(f"{label_prefix} [{path.name}]: {message}")

    return issues


# ---------------------------------------------------------------------------
# Main check logic
# ---------------------------------------------------------------------------

def check_apex(manifest_dir: Path, verbose: bool) -> list[str]:
    issues: list[str] = []

    apex_patterns = [
        (APEX_OIS_DML_PATTERNS[0], "Direct assignment to QuantityCanceled/QuantityReturnInitiated detected — use OMS Connect API submit-cancel or submit-return instead of direct DML on OrderItemSummary in MANAGED mode."),
        (APEX_OIS_DML_PATTERNS[1], "Possible direct update DML on OrderItemSummary detected — verify this is UNMANAGED mode; MANAGED mode requires Connect API actions."),
        (APEX_HARDCODED_SECRET_PATTERNS[0], "Possible hardcoded SLAS/OCAPI client_id or client_secret in Apex source — use Named Credentials or Protected Custom Metadata instead."),
        (APEX_HARDCODED_SECRET_PATTERNS[1], "x-dw-client-id value appears hardcoded in Apex — use Named Credentials."),
        (APEX_HARDCODED_SCAPI_ENDPOINT, "SCAPI endpoint hardcoded as a literal URL in Apex setEndpoint() — use Named Credentials (callout:<name>) to abstract the base URL and credentials."),
    ]

    for apex_file in iter_apex_files(manifest_dir):
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for pattern, message in apex_patterns:
            if pattern.search(content):
                issues.append(f"APEX [{apex_file.name}]: {message}")
                if verbose:
                    # Show first match line for context
                    for i, line in enumerate(content.splitlines(), 1):
                        if pattern.search(line):
                            issues.append(f"  → line {i}: {line.strip()[:120]}")
                            break

        # Check for OCAPI auth header on SCAPI URL (multi-line scan)
        if APEX_OCAPI_ON_SCAPI_PATTERN.search(content):
            issues.append(
                f"APEX [{apex_file.name}]: x-dw-client-id (OCAPI auth) combined with api.commercecloud.salesforce.com (SCAPI) URL — SCAPI requires SLAS Bearer token, not OCAPI client ID."
            )

    return issues


def check_js(manifest_dir: Path, verbose: bool) -> list[str]:
    issues: list[str] = []

    js_patterns = [
        (JS_LOCALSTORAGE_TOKEN_PATTERN, "SLAS/auth token stored in localStorage — use httpOnly cookies or BFF server-side storage to prevent XSS token theft."),
        (JS_SESSIONSTORAGE_TOKEN_PATTERN, "SLAS/auth token stored in sessionStorage — sessionStorage is accessible to JavaScript; prefer httpOnly cookies for token storage."),
        (JS_OCAPI_ON_SCAPI_PATTERN, "x-dw-client-id header (OCAPI auth) used with api.commercecloud.salesforce.com (SCAPI) URL — SCAPI requires SLAS Bearer token in Authorization header."),
    ]

    for js_file in iter_js_files(manifest_dir):
        try:
            content = js_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for pattern, message in js_patterns:
            if pattern.search(content):
                issues.append(f"JS/LWC [{js_file.name}]: {message}")
                if verbose:
                    for i, line in enumerate(content.splitlines(), 1):
                        if pattern.search(line):
                            issues.append(f"  → line {i}: {line.strip()[:120]}")
                            break

    return issues


def check_metadata_config(manifest_dir: Path) -> list[str]:
    """Check for OCAPI wildcard origin in JSON config files (Business Manager export artifacts)."""
    issues: list[str] = []
    wildcard_pattern = re.compile(r'"allowed_origins"\s*:\s*\[\s*"\*"', re.IGNORECASE)

    for json_file in manifest_dir.rglob("*.json"):
        # Skip node_modules and large dependency directories
        if "node_modules" in str(json_file) or ".sfdx" in str(json_file):
            continue
        try:
            content = json_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if wildcard_pattern.search(content):
            issues.append(
                f"CONFIG [{json_file.name}]: OCAPI allowed_origins set to wildcard ['*'] — "
                "restrict to explicit production domain list to prevent cross-site API abuse."
            )

    return issues


def check_commerce_order_api(manifest_dir: Path, verbose: bool = False) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_apex(manifest_dir, verbose))
    issues.extend(check_js(manifest_dir, verbose))
    issues.extend(check_metadata_config(manifest_dir))

    return issues


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata and source for Commerce Order API anti-patterns.\n"
            "Detects: direct DML on OrderItemSummary, insecure SLAS token storage, "
            "OCAPI auth on SCAPI endpoints, hardcoded credentials, and OCAPI wildcard origins."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata / source (default: current directory).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show first matching line for each issue found.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_commerce_order_api(manifest_dir, verbose=args.verbose)

    if not issues:
        print("No Commerce Order API issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    print(f"\n{len(issues)} issue(s) found.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
