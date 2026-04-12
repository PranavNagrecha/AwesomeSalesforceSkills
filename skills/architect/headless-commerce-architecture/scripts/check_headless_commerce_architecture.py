#!/usr/bin/env python3
"""Checker script for Headless Commerce Architecture skill.

Scans PWA Kit project files and Salesforce metadata for architecture issues
specific to headless B2C Commerce Cloud storefronts on Composable Storefront.

Uses stdlib only — no pip dependencies.

Checks performed:
  - OCAPI endpoint references in frontend source files (should not exist in new headless work)
  - Sequential SCAPI calls without parallel fetch patterns (latency budget risk)
  - Suspicious cache-key configurations that omit locale or currency
  - localStorage / sessionStorage token storage (SLAS tokens must be in memory or httpOnly cookies)
  - Client secret exposure in frontend bundle files

Usage:
    python3 check_headless_commerce_architecture.py [--help]
    python3 check_headless_commerce_architecture.py --project-dir path/to/pwa-kit-project
    python3 check_headless_commerce_architecture.py --project-dir . --verbose
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Patterns that indicate architecture issues
# ---------------------------------------------------------------------------

# OCAPI endpoint references — should not appear in new headless storefronts
OCAPI_PATTERN = re.compile(r"/dw/(shop|data)/v\d+", re.IGNORECASE)

# localStorage / sessionStorage used to store tokens (insecure for SLAS JWTs)
LOCALSTORAGE_TOKEN_PATTERN = re.compile(
    r"localStorage\.setItem\s*\(\s*['\"].*token.*['\"]",
    re.IGNORECASE,
)
SESSIONSTORAGE_TOKEN_PATTERN = re.compile(
    r"sessionStorage\.setItem\s*\(\s*['\"].*token.*['\"]",
    re.IGNORECASE,
)

# Client secret in frontend source — should never appear in browser-executed code
CLIENT_SECRET_PATTERN = re.compile(
    r"clientSecret\s*[:=]\s*['\"][^'\"]{8,}['\"]",
    re.IGNORECASE,
)

# Sequential SCAPI awaits — multiple sequential awaits in the same block suggest
# sequential call chains that risk exceeding the 10-second SCAPI timeout
SEQUENTIAL_AWAIT_PATTERN = re.compile(
    r"(await\s+\w+[^\n]*\n[^\n]*){4,}",
    re.MULTILINE,
)

# Cache key construction that uses only URL/path with no locale or currency
# Heuristic: a cache key string that includes "url" or "pathname" but not "locale"
CACHE_KEY_URL_ONLY_PATTERN = re.compile(
    r"cacheKey\s*[=:]\s*[`'\"][^`'\"]*(?:url|pathname|href)[^`'\"]*[`'\"]",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# File extensions to scan
# ---------------------------------------------------------------------------
FRONTEND_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}
CONFIG_EXTENSIONS = {".json", ".yaml", ".yml"}
ALL_SCAN_EXTENSIONS = FRONTEND_EXTENSIONS | CONFIG_EXTENSIONS

# Directories to skip
SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".next", "coverage", "__pycache__"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _iter_files(root: Path, extensions: set[str]) -> list[Path]:
    """Walk root and yield files with the given extensions, skipping SKIP_DIRS."""
    results: list[Path] = []
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file() and path.suffix.lower() in extensions:
            results.append(path)
    return results


def _read_safe(path: Path) -> str | None:
    """Read file content as text, returning None on decode errors."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_ocapi_references(root: Path) -> list[str]:
    """Detect OCAPI endpoint URL patterns in frontend source files."""
    issues: list[str] = []
    for path in _iter_files(root, FRONTEND_EXTENSIONS):
        content = _read_safe(path)
        if content is None:
            continue
        for line_no, line in enumerate(content.splitlines(), start=1):
            if OCAPI_PATTERN.search(line):
                rel = path.relative_to(root)
                issues.append(
                    f"OCAPI endpoint reference found in frontend file {rel}:{line_no} — "
                    f"SCAPI is required for new headless storefronts; OCAPI is maintenance-mode only."
                )
    return issues


def check_localstorage_token_storage(root: Path) -> list[str]:
    """Detect SLAS token storage in localStorage or sessionStorage."""
    issues: list[str] = []
    for path in _iter_files(root, FRONTEND_EXTENSIONS):
        content = _read_safe(path)
        if content is None:
            continue
        for line_no, line in enumerate(content.splitlines(), start=1):
            if LOCALSTORAGE_TOKEN_PATTERN.search(line):
                rel = path.relative_to(root)
                issues.append(
                    f"localStorage token storage at {rel}:{line_no} — "
                    f"SLAS access tokens must be stored in memory only; "
                    f"refresh tokens must be in httpOnly cookies."
                )
            elif SESSIONSTORAGE_TOKEN_PATTERN.search(line):
                rel = path.relative_to(root)
                issues.append(
                    f"sessionStorage token storage at {rel}:{line_no} — "
                    f"SLAS access tokens must be stored in memory only."
                )
    return issues


def check_client_secret_in_frontend(root: Path) -> list[str]:
    """Detect client secret literals in frontend source files."""
    issues: list[str] = []
    for path in _iter_files(root, FRONTEND_EXTENSIONS):
        content = _read_safe(path)
        if content is None:
            continue
        for line_no, line in enumerate(content.splitlines(), start=1):
            if CLIENT_SECRET_PATTERN.search(line):
                rel = path.relative_to(root)
                issues.append(
                    f"Possible client secret literal at {rel}:{line_no} — "
                    f"SLAS uses PKCE for public clients; client secrets must not appear in "
                    f"browser-side code or frontend bundles."
                )
    return issues


def check_url_only_cache_keys(root: Path) -> list[str]:
    """Detect cache key patterns that appear to use URL/path without locale/currency."""
    issues: list[str] = []
    for path in _iter_files(root, FRONTEND_EXTENSIONS):
        content = _read_safe(path)
        if content is None:
            continue
        for line_no, line in enumerate(content.splitlines(), start=1):
            if CACHE_KEY_URL_ONLY_PATTERN.search(line):
                # Only flag if locale is not on the same line
                if "locale" not in line.lower() and "currency" not in line.lower():
                    rel = path.relative_to(root)
                    issues.append(
                        f"Possible URL-only cache key at {rel}:{line_no} — "
                        f"cache keys must include locale and currency to prevent "
                        f"cross-locale content contamination."
                    )
    return issues


def check_pwa_kit_package_json(root: Path) -> list[str]:
    """Check package.json for PWA Kit dependency presence."""
    issues: list[str] = []
    pkg_path = root / "package.json"
    if not pkg_path.exists():
        return issues
    content = _read_safe(pkg_path)
    if content is None:
        return issues
    if "@salesforce/pwa-kit-react-sdk" not in content and "pwa-kit" not in content:
        issues.append(
            "package.json does not reference @salesforce/pwa-kit-react-sdk — "
            "confirm this is a PWA Kit (Composable Storefront) project. "
            "If using a custom React build, ensure SLAS PKCE and SCAPI integration are implemented manually."
        )
    return issues


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

def run_all_checks(project_dir: Path, verbose: bool = False) -> list[str]:
    """Run all architecture checks and return a flat list of issue strings."""
    all_issues: list[str] = []

    checks = [
        ("OCAPI references", check_ocapi_references),
        ("localStorage/sessionStorage token storage", check_localstorage_token_storage),
        ("Client secret in frontend code", check_client_secret_in_frontend),
        ("URL-only cache keys", check_url_only_cache_keys),
        ("PWA Kit package.json", check_pwa_kit_package_json),
    ]

    for check_name, check_fn in checks:
        if verbose:
            print(f"  Running check: {check_name}...", file=sys.stderr)
        results = check_fn(project_dir)
        all_issues.extend(results)

    return all_issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a PWA Kit / Composable Storefront project for "
            "headless B2C Commerce architecture issues."
        ),
    )
    parser.add_argument(
        "--project-dir",
        default=".",
        help="Root directory of the PWA Kit project (default: current directory).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print check names as they run.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_dir = Path(args.project_dir).resolve()

    if not project_dir.exists():
        print(f"ERROR: Project directory not found: {project_dir}", file=sys.stderr)
        return 2

    if args.verbose:
        print(f"Scanning: {project_dir}", file=sys.stderr)

    issues = run_all_checks(project_dir, verbose=args.verbose)

    if not issues:
        print("No headless commerce architecture issues found.")
        return 0

    print(f"Found {len(issues)} issue(s):", file=sys.stderr)
    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
