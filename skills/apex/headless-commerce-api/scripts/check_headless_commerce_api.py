#!/usr/bin/env python3
"""Checker script for Headless Commerce API (SCAPI) skill.

Scans JavaScript/TypeScript source files for SCAPI integration anti-patterns:
  - OCAPI endpoint URL patterns used where SCAPI is expected
  - Missing Retry-After handling on HTTP 503 responses
  - Access token stored in localStorage (XSS risk)
  - Client secret present in browser-side code
  - Basket merge endpoint absent from login flows

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_headless_commerce_api.py [--help]
    python3 check_headless_commerce_api.py --src-dir path/to/frontend/src
    python3 check_headless_commerce_api.py --src-dir . --verbose
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Pattern definitions — each entry is (name, regex, advice)
# ---------------------------------------------------------------------------

OCAPI_URL_PATTERN = re.compile(
    r"/dw/shop/v|/dw/data/v|demandware\.net/s/[^/]+/dw/",
    re.IGNORECASE,
)

OCAPI_SESSION_HEADER = re.compile(
    r"x-dw-client-id|dwsid|dwtoken",
    re.IGNORECASE,
)

# Detect 503 handling that does NOT read Retry-After
# Heuristic: a catch/if block referencing 503 without nearby Retry-After
STATUS_503_BLOCK = re.compile(r"503", re.IGNORECASE)
RETRY_AFTER_READ = re.compile(r"[Rr]etry[-_]?[Aa]fter", re.IGNORECASE)

# Access token stored in localStorage
LOCALSTORAGE_TOKEN = re.compile(
    r"localStorage\s*\.\s*setItem\s*\([^)]*(?:access_token|accessToken|token)[^)]*\)",
    re.IGNORECASE,
)

# Client secret in client-side environment variable (NEXT_PUBLIC_ exposes it)
CLIENT_SECRET_PUBLIC = re.compile(
    r"NEXT_PUBLIC_[A-Z_]*(?:CLIENT_SECRET|SECRET)",
    re.IGNORECASE,
)

# client_secret sent in a fetch/axios POST body
CLIENT_SECRET_IN_BODY = re.compile(
    r"client_secret\s*:",
    re.IGNORECASE,
)

# PKCE code verifier generated with too few bytes (< 48 bytes produces < 64 chars,
# and some libraries produce well under 43)
PKCE_SHORT_VERIFIER = re.compile(
    r"randomBytes\s*\(\s*([0-9]+)\s*\)",
    re.IGNORECASE,
)

# Presence of SLAS token endpoint usage
SLAS_TOKEN_ENDPOINT = re.compile(
    r"shopper/auth/v\d+/organizations/[^/]*/oauth2/token",
    re.IGNORECASE,
)

# Basket merge endpoint
BASKET_MERGE_ENDPOINT = re.compile(
    r"baskets/actions/merge",
    re.IGNORECASE,
)

# Login / token exchange that should be followed by a basket merge
# Heuristic: function/method that includes "login" or "signIn" and exchanges a token
LOGIN_FUNCTION = re.compile(
    r"(?:function|const|async\s+function)\s+\w*[Ll]og[Ii]n\w*|"
    r"(?:function|const|async\s+function)\s+\w*[Ss]ign[Ii]n\w*|"
    r"handleLogin|onLogin|loginUser|userLogin",
    re.IGNORECASE,
)


def _source_files(src_dir: Path) -> list[Path]:
    """Return all .js, .jsx, .ts, .tsx files under src_dir."""
    extensions = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}
    return [f for f in src_dir.rglob("*") if f.suffix in extensions]


def check_ocapi_patterns(src_dir: Path) -> list[str]:
    """Detect OCAPI URL patterns and session headers in source files."""
    issues: list[str] = []
    for f in _source_files(src_dir):
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for lineno, line in enumerate(content.splitlines(), start=1):
            if OCAPI_URL_PATTERN.search(line):
                issues.append(
                    f"{f}:{lineno} — OCAPI URL pattern detected (`/dw/shop/v` or `demandware.net`). "
                    "SCAPI uses `https://{{shortCode}}.api.commercecloud.salesforce.com/...` instead."
                )
            if OCAPI_SESSION_HEADER.search(line):
                issues.append(
                    f"{f}:{lineno} — OCAPI session header detected (`x-dw-client-id`, `dwsid`, or `dwtoken`). "
                    "SCAPI uses `Authorization: Bearer <slas_access_token>` — no session cookies or OCAPI headers."
                )
    return issues


def check_503_without_retry_after(src_dir: Path) -> list[str]:
    """Warn when a file references HTTP 503 but does not read Retry-After."""
    issues: list[str] = []
    for f in _source_files(src_dir):
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if STATUS_503_BLOCK.search(content) and not RETRY_AFTER_READ.search(content):
            issues.append(
                f"{f} — HTTP 503 handling detected but `Retry-After` header is not read. "
                "SCAPI uses load-shedding at 90% capacity: read the `Retry-After` header value "
                "and wait that many seconds (plus jitter) before retrying."
            )
    return issues


def check_token_in_localstorage(src_dir: Path) -> list[str]:
    """Detect access tokens stored in localStorage."""
    issues: list[str] = []
    for f in _source_files(src_dir):
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for lineno, line in enumerate(content.splitlines(), start=1):
            if LOCALSTORAGE_TOKEN.search(line):
                issues.append(
                    f"{f}:{lineno} — SLAS access token stored in `localStorage`. "
                    "Store access tokens in memory only; store refresh tokens in `httpOnly` cookies "
                    "to prevent XSS theft."
                )
    return issues


def check_client_secret_exposed(src_dir: Path) -> list[str]:
    """Detect client_secret in browser-accessible code."""
    issues: list[str] = []
    for f in _source_files(src_dir):
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for lineno, line in enumerate(content.splitlines(), start=1):
            if CLIENT_SECRET_PUBLIC.search(line):
                issues.append(
                    f"{f}:{lineno} — `NEXT_PUBLIC_*SECRET` variable detected. "
                    "`NEXT_PUBLIC_` variables are bundled into the browser. "
                    "SLAS PKCE does not require a client secret for public clients — remove it."
                )
            if CLIENT_SECRET_IN_BODY.search(line):
                issues.append(
                    f"{f}:{lineno} — `client_secret` found in what appears to be a request body. "
                    "SCAPI Shopper SLAS PKCE flows do not use a client secret. "
                    "If this is a server-side Admin API call, ensure it is never exposed client-side."
                )
    return issues


def check_pkce_verifier_length(src_dir: Path) -> list[str]:
    """Warn when randomBytes() is called with fewer than 48 bytes for PKCE."""
    issues: list[str] = []
    for f in _source_files(src_dir):
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        # Only flag files that also reference SLAS token endpoints — avoids false positives
        if not SLAS_TOKEN_ENDPOINT.search(content):
            continue
        for lineno, line in enumerate(content.splitlines(), start=1):
            match = PKCE_SHORT_VERIFIER.search(line)
            if match:
                byte_count = int(match.group(1))
                if byte_count < 48:
                    # base64url encoding: ~1.33 chars per byte; 48 bytes → ~64 chars (> 43 min)
                    issues.append(
                        f"{f}:{lineno} — `randomBytes({byte_count})` used near SLAS token endpoint. "
                        f"SLAS enforces RFC 7636: PKCE code verifier must be 43–128 URL-safe Base64 chars. "
                        f"{byte_count} bytes in base64url produces ~{int(byte_count * 1.33)} chars — "
                        "below the safe threshold. Use `randomBytes(64)` (produces ~86 chars) instead."
                    )
    return issues


def check_login_without_basket_merge(src_dir: Path) -> list[str]:
    """Warn when a login function exists but basket merge endpoint is absent from the file."""
    issues: list[str] = []
    for f in _source_files(src_dir):
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if LOGIN_FUNCTION.search(content) and SLAS_TOKEN_ENDPOINT.search(content):
            if not BASKET_MERGE_ENDPOINT.search(content):
                issues.append(
                    f"{f} — Login function with SLAS token exchange detected, but "
                    "`baskets/actions/merge` endpoint not found in this file. "
                    "If guest shoppers can add to cart before logging in, the guest basket must be "
                    "merged into the registered session using `POST baskets/actions/merge` before "
                    "the guest basket ID is discarded."
                )
    return issues


def check_headless_commerce_api(src_dir: Path, verbose: bool = False) -> list[str]:
    """Run all SCAPI integration checks and return a combined issue list."""
    all_issues: list[str] = []

    checks = [
        ("OCAPI patterns", check_ocapi_patterns),
        ("503 without Retry-After", check_503_without_retry_after),
        ("Token in localStorage", check_token_in_localstorage),
        ("Client secret exposed", check_client_secret_exposed),
        ("PKCE verifier length", check_pkce_verifier_length),
        ("Login without basket merge", check_login_without_basket_merge),
    ]

    for name, fn in checks:
        results = fn(src_dir)
        if verbose and results:
            print(f"\n[{name}] {len(results)} issue(s):")
        all_issues.extend(results)

    return all_issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check JavaScript/TypeScript source files for SCAPI headless Commerce "
            "integration anti-patterns (OCAPI patterns, missing Retry-After, "
            "unsafe token storage, exposed client secrets, short PKCE verifiers, "
            "missing basket merge)."
        ),
    )
    parser.add_argument(
        "--src-dir",
        "--manifest-dir",  # alias for compatibility with skill runner conventions
        dest="src_dir",
        default=".",
        help="Root directory of JavaScript/TypeScript source files to scan (default: current directory).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print check names and counts as each check runs.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    src_dir = Path(args.src_dir)

    if not src_dir.exists():
        print(f"ERROR: source directory not found: {src_dir}", file=sys.stderr)
        return 2

    source_files = _source_files(src_dir)
    if args.verbose:
        print(f"Scanning {len(source_files)} JS/TS file(s) in {src_dir} …")

    issues = check_headless_commerce_api(src_dir, verbose=args.verbose)

    if not issues:
        print("No SCAPI integration issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    print(f"\n{len(issues)} issue(s) found.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
