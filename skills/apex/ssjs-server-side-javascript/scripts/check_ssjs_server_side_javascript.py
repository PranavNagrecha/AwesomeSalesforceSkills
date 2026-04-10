#!/usr/bin/env python3
"""Checker script for SSJS Server-Side JavaScript skill.

Statically analyzes SSJS script files (.js, .html, .ssjs) for common
Marketing Cloud SSJS anti-patterns documented in references/llm-anti-patterns.md
and references/gotchas.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_ssjs_server_side_javascript.py [--help]
    python3 check_ssjs_server_side_javascript.py --manifest-dir path/to/ssjs/files
    python3 check_ssjs_server_side_javascript.py --file path/to/script.js
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Pattern definitions
# ---------------------------------------------------------------------------

# Modern JS syntax unsupported in SSJS ES3 engine
MODERN_JS_PATTERNS = [
    (r'\blet\s+', "Use of 'let' — SSJS engine is ES3; use 'var' instead"),
    (r'\bconst\s+', "Use of 'const' — SSJS engine is ES3; use 'var' instead"),
    (r'=>\s*[\{\(]', "Arrow function syntax — SSJS engine is ES3; use 'function' keyword"),
    (r'`[^`]*`', "Template literal (backtick string) — not supported in SSJS ES3 engine"),
    (r'\bawait\b', "Use of 'await' — async/await not supported in SSJS ES3 engine"),
    (r'\basync\b', "Use of 'async' — async/await not supported in SSJS ES3 engine"),
    (r'\bnew Promise\b', "Use of 'Promise' — not supported in SSJS ES3 engine"),
    (r'\.\.\.[a-zA-Z_\$]', "Spread operator — not supported in SSJS ES3 engine"),
]

# Wrong JSON functions — must use MC equivalents
JSON_ANTI_PATTERNS = [
    (r'\bJSON\.stringify\s*\(', "JSON.stringify() not available in SSJS — use Stringify() instead"),
    (r'\bJSON\.parse\s*\(', "JSON.parse() not available in SSJS — use Platform.Function.ParseJSON() instead"),
]

# Raw SOAP HTTP calls instead of WSProxy
SOAP_HTTP_PATTERNS = [
    (r'SOAPAction', "Raw SOAP HTTP call detected — use Script.Util.WSProxy for Marketing Cloud SOAP API calls"),
    (r'webservice\.s\d+\.exacttarget\.com', "Direct SOAP endpoint URL — use WSProxy instead of raw HTTP for MC SOAP API"),
    (r'text/xml.*SOAPAction|SOAPAction.*text/xml', "Raw SOAP content-type header — use WSProxy for Marketing Cloud SOAP calls"),
]

# Missing Platform.Load — not a file-level error but warn if MC functions are used without it
PLATFORM_LOAD_PATTERN = r'Platform\.Load\s*\('
PLATFORM_FUNCTIONS_PATTERN = r'Platform\.Function\.|Script\.Util\.|WSProxy'

# WSProxy retrieve without HasMoreRows check
WSPROXY_RETRIEVE_PATTERN = r'\.retrieve\s*\('
HAS_MORE_ROWS_PATTERN = r'HasMoreRows'

# Missing try/catch around WSProxy or HttpRequest calls
TRY_CATCH_PATTERN = r'\btry\s*\{'
API_CALL_PATTERNS = [
    r'new Script\.Util\.WSProxy\s*\(',
    r'new Script\.Util\.HttpRequest\s*\(',
]

# runat="server" check
RUNAT_SERVER_PATTERN = r'runat\s*=\s*["\']server["\']'


def check_file(path: Path) -> list[str]:
    """Return a list of issue strings found in a single SSJS file."""
    issues: list[str] = []

    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        issues.append(f"{path}: Cannot read file — {exc}")
        return issues

    # Only analyze files that contain SSJS content (runat=server or .ssjs extension)
    is_ssjs_file = (
        path.suffix.lower() in {".ssjs", ".js"}
        or bool(re.search(RUNAT_SERVER_PATTERN, content, re.IGNORECASE))
    )
    if not is_ssjs_file:
        return issues

    lines = content.splitlines()

    def check_patterns(pattern_list: list[tuple[str, str]]) -> None:
        for pattern, message in pattern_list:
            for lineno, line in enumerate(lines, start=1):
                if re.search(pattern, line):
                    issues.append(f"{path}:{lineno}: {message}")

    # 1. Modern JS syntax
    check_patterns(MODERN_JS_PATTERNS)

    # 2. Wrong JSON functions
    check_patterns(JSON_ANTI_PATTERNS)

    # 3. Raw SOAP HTTP patterns
    check_patterns(SOAP_HTTP_PATTERNS)

    # 4. Platform.Load missing when MC functions are used
    uses_mc_functions = bool(re.search(PLATFORM_FUNCTIONS_PATTERN, content))
    has_platform_load = bool(re.search(PLATFORM_LOAD_PATTERN, content))
    if uses_mc_functions and not has_platform_load:
        issues.append(
            f"{path}: Missing Platform.Load('Core', '1.1.1') — required before using "
            "Platform.Function.*, Script.Util.*, or WSProxy"
        )

    # 5. WSProxy retrieve without HasMoreRows pagination check
    if re.search(WSPROXY_RETRIEVE_PATTERN, content):
        if not re.search(HAS_MORE_ROWS_PATTERN, content):
            issues.append(
                f"{path}: WSProxy .retrieve() found but no 'HasMoreRows' pagination check — "
                "results may be silently truncated at the first page (~2500 rows)"
            )

    # 6. API calls without try/catch
    has_api_calls = any(re.search(p, content) for p in API_CALL_PATTERNS)
    has_try_catch = bool(re.search(TRY_CATCH_PATTERN, content))
    if has_api_calls and not has_try_catch:
        issues.append(
            f"{path}: WSProxy or HttpRequest calls found without try/catch — "
            "uncaught exceptions cause Script Activity failure with no diagnostic output"
        )

    return issues


def check_ssjs_server_side_javascript(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    ssjs_extensions = {".ssjs", ".js", ".html", ".htm"}
    candidate_files = [
        f for f in manifest_dir.rglob("*")
        if f.is_file() and f.suffix.lower() in ssjs_extensions
    ]

    if not candidate_files:
        # Not an error — this checker is for SSJS files; other repos may not have any
        return issues

    for fpath in sorted(candidate_files):
        issues.extend(check_file(fpath))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check SSJS files for common Marketing Cloud anti-patterns: "
            "modern JS syntax, missing try/catch, raw SOAP calls, and pagination issues."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory to scan recursively for SSJS files (default: current directory).",
    )
    parser.add_argument(
        "--file",
        help="Check a single SSJS file instead of scanning a directory.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.file:
        fpath = Path(args.file)
        issues = check_file(fpath)
    else:
        manifest_dir = Path(args.manifest_dir)
        issues = check_ssjs_server_side_javascript(manifest_dir)

    if not issues:
        print("No SSJS anti-pattern issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
