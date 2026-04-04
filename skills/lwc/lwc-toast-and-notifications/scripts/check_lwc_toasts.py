#!/usr/bin/env python3
"""Checker script for LWC Toast And Notifications skill.

Scans JavaScript files under a given directory for ShowToastEvent usage patterns,
checks for improper variant values, flags sticky mode overuse on non-error toasts,
and detects messageData placeholder count mismatches.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_lwc_toasts.py [--help]
    python3 check_lwc_toasts.py --source-dir path/to/lwc/components
    python3 check_lwc_toasts.py --source-dir force-app/main/default/lwc
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_VARIANTS = {"info", "success", "warning", "error"}

# Matches variant: 'value' or variant: "value"
VARIANT_PATTERN = re.compile(r"variant\s*:\s*['\"]([^'\"]+)['\"]")

# Matches mode: 'value' or mode: "value"
MODE_PATTERN = re.compile(r"mode\s*:\s*['\"]([^'\"]+)['\"]")

# Matches {0}, {1}, {2}, ... placeholders inside a string
PLACEHOLDER_PATTERN = re.compile(r"\{(\d+)\}")

# Matches the message field value (single or double quoted, non-greedy)
MESSAGE_PATTERN = re.compile(r"message\s*:\s*['\"]([^'\"]*)['\"]")

# Matches messageData array opening
MESSAGEDATA_PATTERN = re.compile(r"messageData\s*:\s*\[")

# Detects the start of a ShowToastEvent construction (opening brace position)
TOAST_START_PATTERN = re.compile(r"new\s+ShowToastEvent\s*\(\s*\{")

# Detects import of ShowToastEvent
IMPORT_PATTERN = re.compile(
    r"import\s+\{[^}]*ShowToastEvent[^}]*\}\s+from\s+['\"]lightning/platformShowToastEvent['\"]"
)

# Detect window.alert or window.confirm usage (prohibited in LWC)
WINDOW_DIALOG_PATTERN = re.compile(r"\bwindow\.(alert|confirm|prompt)\s*\(")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def extract_toast_blocks(source: str) -> list[tuple[int, str]]:
    """
    Extract the inner content of each ShowToastEvent({...}) object literal.
    Uses brace-depth counting to handle {n} placeholders inside string values.

    Returns list of (line_number, block_content) tuples.
    """
    results = []
    for start_match in TOAST_START_PATTERN.finditer(source):
        # The opening brace is the last char of the match
        open_brace_pos = start_match.end() - 1
        lineno = source[:open_brace_pos].count("\n") + 1

        # Walk from the opening brace to find the matching closing brace,
        # skipping string contents so {0} inside a value doesn't confuse depth.
        depth = 0
        in_string = False
        string_char = None
        block_start = open_brace_pos + 1  # content after '{'
        i = open_brace_pos

        while i < len(source):
            ch = source[i]
            if in_string:
                if ch == "\\" and i + 1 < len(source):
                    i += 2
                    continue
                if ch == string_char:
                    in_string = False
            else:
                if ch in ("'", '"', "`"):
                    in_string = True
                    string_char = ch
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        results.append((lineno, source[block_start:i]))
                        break
            i += 1

    return results


def count_placeholders(message: str) -> int:
    """Return the highest placeholder index + 1 in a message string."""
    found = PLACEHOLDER_PATTERN.findall(message)
    if not found:
        return 0
    return max(int(i) for i in found) + 1


def count_messagedata_entries(block: str, start_pos: int) -> int | None:
    """
    Attempt to count array entries in messageData by walking characters after '['.
    Returns None if the array is not fully parsable (e.g. spans multiple lines beyond block).
    This is a best-effort heuristic for static analysis.
    """
    depth = 0
    in_string = False
    string_char = None
    entries = 0
    i = start_pos

    while i < len(block):
        ch = block[i]
        if in_string:
            if ch == "\\" and i + 1 < len(block):
                i += 2
                continue
            if ch == string_char:
                in_string = False
        else:
            if ch in ("'", '"', "`"):
                in_string = True
                string_char = ch
                if depth == 1:
                    entries += 1
            elif ch == "[":
                depth += 1
                if depth == 1:
                    i += 1
                    # Skip whitespace
                    while i < len(block) and block[i] in (" ", "\t", "\n", "\r"):
                        i += 1
                    if i < len(block) and block[i] == "]":
                        return 0  # empty array
                    continue
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    return entries
            elif ch == "{" and depth == 1:
                # Object entry (link object)
                entries += 1
                depth_inner = 0
                while i < len(block):
                    if block[i] == "{":
                        depth_inner += 1
                    elif block[i] == "}":
                        depth_inner -= 1
                        if depth_inner == 0:
                            break
                    i += 1
            elif ch == "," and depth == 1:
                pass  # separator; entries already counted on open
        i += 1

    return None  # could not determine


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def check_file(path: Path) -> list[str]:
    """Run all toast-related checks on a single .js file. Returns list of issue strings."""
    issues: list[str] = []
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        issues.append(f"{path}: could not read file — {exc}")
        return issues

    # Only check files that import ShowToastEvent
    has_toast_import = bool(IMPORT_PATTERN.search(source))

    if has_toast_import:
        # Check each ShowToastEvent construction block
        for lineno, block in extract_toast_blocks(source):

            # --- Variant check ---
            variant_match = VARIANT_PATTERN.search(block)
            if variant_match:
                variant = variant_match.group(1).strip()
                if variant not in VALID_VARIANTS:
                    issues.append(
                        f"{path}:{lineno}: invalid toast variant '{variant}' — "
                        f"must be one of {sorted(VALID_VARIANTS)}"
                    )
            else:
                # No explicit variant — defaults to 'info', which may be intentional
                pass

            # --- Sticky mode overuse check ---
            mode_match = MODE_PATTERN.search(block)
            if mode_match:
                mode = mode_match.group(1).strip()
                if mode == "sticky":
                    # Warn if variant is not error or warning
                    if variant_match:
                        variant = variant_match.group(1).strip()
                        if variant in ("success", "info"):
                            issues.append(
                                f"{path}:{lineno}: 'sticky' mode used with variant "
                                f"'{variant}' — sticky mode should be reserved for "
                                f"'error' or 'warning' toasts that require user action"
                            )
                    else:
                        # No variant specified, sticky on default 'info' variant
                        issues.append(
                            f"{path}:{lineno}: 'sticky' mode used without an explicit "
                            f"variant — this creates a dismissal burden for informational "
                            f"messages; consider using 'error' or 'warning' variant instead"
                        )

            # --- messageData placeholder mismatch check ---
            msg_match = MESSAGE_PATTERN.search(block)
            if msg_match:
                message_text = msg_match.group(1)
                required_count = count_placeholders(message_text)

                md_match = MESSAGEDATA_PATTERN.search(block)
                if required_count > 0 and not md_match:
                    issues.append(
                        f"{path}:{lineno}: message contains {required_count} placeholder(s) "
                        f"but no messageData array was found — placeholders will render as "
                        f"literal text (e.g. '{{0}}')"
                    )
                elif md_match and required_count > 0:
                    # Best-effort array entry count
                    entry_count = count_messagedata_entries(block, md_match.end() - 1)
                    if entry_count is not None and entry_count < required_count:
                        issues.append(
                            f"{path}:{lineno}: message has {required_count} placeholder(s) "
                            f"but messageData appears to have only {entry_count} entr(y/ies) "
                            f"— users will see raw '{{n}}' text"
                        )

    # --- window.alert / window.confirm detection (applies to all .js files) ---
    for wd_match in WINDOW_DIALOG_PATTERN.finditer(source):
        lineno = source[: wd_match.start()].count("\n") + 1
        func = wd_match.group(1)
        issues.append(
            f"{path}:{lineno}: window.{func}() is prohibited in LWC — "
            f"use ShowToastEvent, lightning-alert, or lightning-confirm instead"
        )

    return issues


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scan LWC JavaScript files for ShowToastEvent usage issues: "
            "invalid variants, sticky-mode overuse on non-error toasts, "
            "messageData placeholder mismatches, and prohibited window.alert usage."
        )
    )
    parser.add_argument(
        "--source-dir",
        default=".",
        help="Root directory to scan for .js files (default: current directory).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print file names as they are scanned.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_dir = Path(args.source_dir)

    if not source_dir.exists():
        print(f"ERROR: source directory not found: {source_dir}", file=sys.stderr)
        return 2

    js_files = sorted(source_dir.rglob("*.js"))
    if not js_files:
        print(f"No .js files found under {source_dir}")
        return 0

    all_issues: list[str] = []
    for js_file in js_files:
        if args.verbose:
            print(f"Scanning: {js_file}")
        file_issues = check_file(js_file)
        all_issues.extend(file_issues)

    if not all_issues:
        print(f"No toast issues found. ({len(js_files)} file(s) scanned)")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")

    print(f"\n{len(all_issues)} issue(s) found in {len(js_files)} file(s) scanned.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
