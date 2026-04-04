#!/usr/bin/env python3
"""Checker script for LWC Accessibility Patterns skill.

Scans LWC component files (HTML templates and JS) for common accessibility
anti-patterns described in references/gotchas.md and references/llm-anti-patterns.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_lwc_accessibility_patterns.py [--help]
    python3 check_lwc_accessibility_patterns.py --manifest-dir path/to/force-app
    python3 check_lwc_accessibility_patterns.py --manifest-dir . --verbose
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check LWC component files for accessibility anti-patterns "
            "related to ARIA attributes, keyboard navigation, and focus management."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory to scan for LWC HTML/JS files (default: current directory).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print files scanned even when no issues are found.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def _find_lwc_files(root: Path) -> tuple[list[Path], list[Path]]:
    """Return (html_files, js_files) found under root."""
    html_files = list(root.rglob("*.html"))
    js_files = list(root.rglob("*.js"))
    return html_files, js_files


def check_role_button_missing_tabindex(html_files: list[Path]) -> list[str]:
    """Detect role="button" on non-native elements that are missing tabindex="0"."""
    issues: list[str] = []
    pattern = re.compile(r'role=["\']button["\']', re.IGNORECASE)
    tabindex_pattern = re.compile(r'tabindex=["\']0["\']', re.IGNORECASE)
    native_tags = re.compile(r'^\s*<(button|a|input|select|textarea)\b', re.IGNORECASE)

    for path in html_files:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue

        lines = text.splitlines()
        for i, line in enumerate(lines, start=1):
            if not pattern.search(line):
                continue
            if native_tags.search(line):
                continue
            # Look in a 5-line window for tabindex="0"
            window_start = max(0, i - 3)
            window_end = min(len(lines), i + 3)
            window = "\n".join(lines[window_start:window_end])
            if not tabindex_pattern.search(window):
                issues.append(
                    f"{path}:{i} — role=\"button\" found without tabindex=\"0\" nearby. "
                    "Custom button elements must have tabindex=\"0\" to be keyboard reachable."
                )
    return issues


def check_role_button_missing_keydown(html_files: list[Path]) -> list[str]:
    """Detect role="button" elements that have onclick but no onkeydown."""
    issues: list[str] = []
    role_btn = re.compile(r'role=["\']button["\']', re.IGNORECASE)
    onclick = re.compile(r'\bonclick\b', re.IGNORECASE)
    onkeydown = re.compile(r'\bonkeydown\b', re.IGNORECASE)
    native_tags = re.compile(r'^\s*<(button|a|input|select|textarea)\b', re.IGNORECASE)

    for path in html_files:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue

        lines = text.splitlines()
        for i, line in enumerate(lines, start=1):
            if not role_btn.search(line):
                continue
            if native_tags.search(line):
                continue
            # Multi-line element: look in a 10-line window
            window_start = max(0, i - 2)
            window_end = min(len(lines), i + 8)
            window = "\n".join(lines[window_start:window_end])
            has_onclick = onclick.search(window)
            has_keydown = onkeydown.search(window)
            if has_onclick and not has_keydown:
                issues.append(
                    f"{path}:{i} — role=\"button\" with onclick but no onkeydown. "
                    "Space and Enter keys will not activate the control. "
                    "Add an onkeydown handler that responds to Enter and Space."
                )
    return issues


def check_aria_live_in_conditional(html_files: list[Path]) -> list[str]:
    """Detect aria-live inside a conditional template block."""
    issues: list[str] = []
    aria_live = re.compile(r'aria-live\s*=', re.IGNORECASE)
    if_template = re.compile(r'<template\s+if:', re.IGNORECASE)

    for path in html_files:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue

        lines = text.splitlines()
        # Track nesting depth of conditional <template if:> blocks
        depth_stack: list[int] = []
        conditional_depth = 0

        for i, line in enumerate(lines, start=1):
            if if_template.search(line):
                depth_stack.append(i)
                conditional_depth += 1

            # Check for closing </template> — simplistic: count opens vs closes
            close_count = line.count("</template>")
            if close_count and depth_stack:
                for _ in range(min(close_count, len(depth_stack))):
                    depth_stack.pop()
                conditional_depth = len(depth_stack)

            if aria_live.search(line) and conditional_depth > 0:
                issues.append(
                    f"{path}:{i} — aria-live found inside a conditional template block. "
                    "Live regions must be always present in the DOM. "
                    "Move aria-live outside the if:true/if:false template wrapper."
                )
    return issues


def check_both_aria_label_and_labelledby(html_files: list[Path]) -> list[str]:
    """Detect elements that have both aria-label and aria-labelledby."""
    issues: list[str] = []
    aria_label = re.compile(r'\baria-label\s*=', re.IGNORECASE)
    aria_labelledby = re.compile(r'\baria-labelledby\s*=', re.IGNORECASE)

    for path in html_files:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue

        lines = text.splitlines()
        for i, line in enumerate(lines, start=1):
            if aria_label.search(line) and aria_labelledby.search(line):
                issues.append(
                    f"{path}:{i} — Both aria-label and aria-labelledby on the same element. "
                    "aria-labelledby takes precedence; aria-label will be ignored. "
                    "Use one or the other."
                )
    return issues


def check_custom_table_missing_grid_role(html_files: list[Path]) -> list[str]:
    """Detect <table> elements that appear to be interactive but lack role='grid'."""
    issues: list[str] = []
    table_tag = re.compile(r'<table\b', re.IGNORECASE)
    has_onclick = re.compile(r'\bonclick\b', re.IGNORECASE)
    has_grid = re.compile(r'role=["\']grid["\']', re.IGNORECASE)

    for path in html_files:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue

        # Only check files that have onclick handlers in a table context
        if not has_onclick.search(text):
            continue

        lines = text.splitlines()
        for i, line in enumerate(lines, start=1):
            if not table_tag.search(line):
                continue
            # Look ahead 3 lines for role="grid"
            window_start = i - 1
            window_end = min(len(lines), i + 3)
            window = "\n".join(lines[window_start:window_end])
            if has_onclick.search(text) and not has_grid.search(window):
                issues.append(
                    f"{path}:{i} — <table> in a component with onclick handlers "
                    "but no role=\"grid\" found. Interactive tables should use "
                    "role=\"grid\" with aria-rowcount and aria-colcount, or use "
                    "lightning-datatable instead."
                )
                break  # one issue per file for this check
    return issues


def check_renderedcallback_focus_without_guard(js_files: list[Path]) -> list[str]:
    """Detect .focus() calls in renderedCallback without a boolean guard."""
    issues: list[str] = []
    in_rendered = re.compile(r'\brenderedCallback\s*\(', re.IGNORECASE)
    focus_call = re.compile(r'\.focus\s*\(')
    guard_pattern = re.compile(r'\bif\s*\(.*this\._?\w*[Ff]ocus\w*')

    for path in js_files:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue

        if not in_rendered.search(text):
            continue
        if not focus_call.search(text):
            continue

        # Find the renderedCallback block (simplified: look for focus after it)
        lines = text.splitlines()
        in_cb = False
        brace_depth = 0
        for i, line in enumerate(lines, start=1):
            if in_rendered.search(line):
                in_cb = True

            if in_cb:
                brace_depth += line.count('{') - line.count('}')
                if brace_depth < 0:
                    in_cb = False
                    brace_depth = 0
                    continue
                if focus_call.search(line):
                    # Look for a guard in the surrounding 5 lines
                    window_start = max(0, i - 4)
                    window_end = min(len(lines), i + 2)
                    window = "\n".join(lines[window_start:window_end])
                    if not guard_pattern.search(window) and "if (" not in window and "if(" not in window:
                        issues.append(
                            f"{path}:{i} — .focus() call inside renderedCallback "
                            "without an apparent boolean guard. This will steal focus "
                            "on every rerender. Use a flag (e.g. this._focusPending) "
                            "to limit focus to intentional transitions."
                        )
    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_lwc_accessibility_patterns(manifest_dir: Path, verbose: bool = False) -> list[str]:
    """Run all accessibility pattern checks and return a list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    html_files, js_files = _find_lwc_files(manifest_dir)

    if verbose:
        print(f"Scanning {len(html_files)} HTML files and {len(js_files)} JS files under {manifest_dir}")

    issues.extend(check_role_button_missing_tabindex(html_files))
    issues.extend(check_role_button_missing_keydown(html_files))
    issues.extend(check_aria_live_in_conditional(html_files))
    issues.extend(check_both_aria_label_and_labelledby(html_files))
    issues.extend(check_custom_table_missing_grid_role(html_files))
    issues.extend(check_renderedcallback_focus_without_guard(js_files))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_lwc_accessibility_patterns(manifest_dir, verbose=args.verbose)

    if not issues:
        print("No LWC accessibility pattern issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    print(f"\n{len(issues)} issue(s) found.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
