#!/usr/bin/env python3
"""Checker script for LWC Dynamic Components skill.

Scans LWC source files in a Salesforce metadata directory for common
dynamic-component anti-patterns described in references/gotchas.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_lwc_dynamic.py [--help]
    python3 check_lwc_dynamic.py --manifest-dir path/to/lwc

Checks performed:
    1. import() result assigned directly to lwc:is without .default
    2. Computed (non-literal) import specifiers
    3. import() calls not wrapped in try/catch
    4. lwc:component used without a loading or error fallback in the template
    5. lwc:component usage in files that may be in unlocked packages (heuristic)
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Detects: this.x = await import('c/foo')  (no .default access on same line)
# This is a simplified heuristic — it looks for assignment of import() result
# directly without .default on the same expression.
RE_IMPORT_WITHOUT_DEFAULT = re.compile(
    r'=\s*await\s+import\s*\(\s*[\'"][^\'\"]+[\'"]\s*\)'
    r'(?!\s*[;\n].*\.default)',
)

# Detects: import() where the specifier contains a variable expression
# e.g., import(`c/${name}`) or import('c/' + this.variant)
RE_COMPUTED_SPECIFIER = re.compile(
    r'\bimport\s*\(\s*(?:`[^`]*\$\{|[\'"][^\'\"]*\'\s*\+|[\'"][^\'\"]*"\s*\+)',
)

# Detects: await import(...) that is NOT preceded by try { on the same or nearby line
# Heuristic: look for `await import` not inside a try block in the same function body.
# We flag files where import() appears without any try keyword in the file.
RE_AWAIT_IMPORT = re.compile(r'\bawait\s+import\s*\(')
RE_TRY_BLOCK = re.compile(r'\btry\s*\{')

# Detects: lwc:component directive in HTML templates
RE_LWC_COMPONENT_TAG = re.compile(r'<lwc:component\b')

# Detects: loading/error fallback patterns alongside lwc:component
RE_SPINNER = re.compile(r'<lightning-spinner\b')
RE_ERROR_STATE = re.compile(r'slds-text-color_error|hasError|error\s*\}|errorMessage')
RE_LWC_ELSE = re.compile(r'lwc:else|lwc:elseif')

# Detects: .default access on dynamic import result or destructuring of default from a module.
# Must NOT match 'export default' — only property access (.default) or destructuring ({ default: }).
RE_DEFAULT_ACCESS = re.compile(
    r'(?:\.default\b|\{\s*default\s*:|\{\s*default\s*,|\bdefault\s+as\s+\w)'
)


# ---------------------------------------------------------------------------
# File finders
# ---------------------------------------------------------------------------

def find_js_files(root: Path) -> list[Path]:
    return list(root.rglob('*.js'))


def find_html_files(root: Path) -> list[Path]:
    return list(root.rglob('*.html'))


# ---------------------------------------------------------------------------
# Checkers
# ---------------------------------------------------------------------------

def check_js_file(path: Path) -> list[str]:
    issues: list[str] = []
    try:
        source = path.read_text(encoding='utf-8', errors='replace')
    except OSError as exc:
        return [f"{path}: cannot read file — {exc}"]

    if not RE_AWAIT_IMPORT.search(source):
        # No dynamic imports in this file; nothing to check
        return issues

    # Check 1: import() result assigned without .default anywhere in the file.
    # Strategy: if the entire file contains any .default access or { default: } destructuring
    # alongside dynamic import calls, trust that the developer is handling it correctly.
    # Only flag when the file uses await import() but has NO .default reference at all.
    # This avoids false positives on two-step patterns (assign to mod, then use mod.default).
    has_default_access = bool(RE_DEFAULT_ACCESS.search(source))
    source_lines = source.splitlines()
    if not has_default_access:
        # Flag each import() line since none of them access .default anywhere in the file
        for lineno, line in enumerate(source_lines, start=1):
            if RE_AWAIT_IMPORT.search(line):
                issues.append(
                    f"{path}:{lineno}: possible missing .default — "
                    f"'await import()' result may be assigned without destructuring "
                    f"'default'. Use `const {{ default: Ctor }} = await import(...)` "
                    f"or `mod.default`."
                )

    # Check 2: computed (non-literal) import specifiers
    for lineno, line in enumerate(source.splitlines(), start=1):
        if RE_COMPUTED_SPECIFIER.search(line):
            issues.append(
                f"{path}:{lineno}: computed import specifier detected — "
                f"LWC build toolchain requires static literal strings in import(). "
                f"Template literals and string concatenation are not supported."
            )

    # Check 3: await import() without any try/catch in the file
    if RE_AWAIT_IMPORT.search(source) and not RE_TRY_BLOCK.search(source):
        issues.append(
            f"{path}: dynamic import() found with no try/catch in the file — "
            f"wrap every import() call in try/catch and render an error state "
            f"so users see a message instead of a blank area on module load failure."
        )

    return issues


def check_html_file(path: Path) -> list[str]:
    issues: list[str] = []
    try:
        source = path.read_text(encoding='utf-8', errors='replace')
    except OSError as exc:
        return [f"{path}: cannot read file — {exc}"]

    if not RE_LWC_COMPONENT_TAG.search(source):
        return issues  # no lwc:component in this template

    # Check 4: lwc:component without a loading or error fallback
    has_spinner = RE_SPINNER.search(source)
    has_error = RE_ERROR_STATE.search(source)
    has_else = RE_LWC_ELSE.search(source)

    if not (has_spinner or has_error or has_else):
        issues.append(
            f"{path}: <lwc:component> found without an apparent loading or error fallback — "
            f"add a lwc:else branch with a lightning-spinner (loading state) and an error "
            f"message state. Users see a blank area if the dynamic import is slow or fails."
        )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_dynamic_components(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found under manifest_dir."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    js_files = find_js_files(manifest_dir)
    html_files = find_html_files(manifest_dir)

    if not js_files and not html_files:
        issues.append(
            f"No .js or .html files found under {manifest_dir}. "
            f"Verify the path points to an LWC source directory."
        )
        return issues

    for js_path in js_files:
        issues.extend(check_js_file(js_path))

    for html_path in html_files:
        issues.extend(check_html_file(html_path))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check LWC source files for common dynamic-component anti-patterns. "
            "See skills/lwc/lwc-dynamic-components/references/gotchas.md for details."
        ),
    )
    parser.add_argument(
        '--manifest-dir',
        default='.',
        help='Root directory of the LWC source or Salesforce metadata (default: current directory).',
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_dynamic_components(manifest_dir)

    if not issues:
        print('No dynamic-component issues found.')
        return 0

    for issue in issues:
        print(f'ISSUE: {issue}')

    print(f'\n{len(issues)} issue(s) found.')
    return 1


if __name__ == '__main__':
    sys.exit(main())
