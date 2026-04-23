#!/usr/bin/env python3
"""Checker script for the lwc-quick-actions skill.

Scans LWC bundles under --manifest-dir and flags common quick-action mistakes:

1. `<template>` markup present in a bundle whose meta.xml declares
   `actionType="Action"` (headless actions render nothing).
2. Missing `@api recordId` declaration in a bundle whose meta.xml declares
   the `lightning__RecordAction` target.
3. Any `window.location` usage in the same bundle (breaks SPA navigation —
   use `getRecordNotifyChange`, `refreshApex`, or `NavigationMixin`).
4. Dispatch of `CloseActionScreenEvent` before any `await`/`.then(` on the
   save path inside the same function (heuristic — pre-save close race).

Stdlib only.

Usage:
    python3 check_lwc_quick_actions.py [--manifest-dir PATH]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


META_RECORD_ACTION = "lightning__RecordAction"
META_HEADLESS_ATTR_RE = re.compile(r'actionType\s*=\s*"Action"', re.IGNORECASE)
META_SCREEN_ATTR_RE = re.compile(r'actionType\s*=\s*"ScreenAction"', re.IGNORECASE)

API_RECORDID_RE = re.compile(r"@api\s+recordId\b")
WINDOW_LOCATION_RE = re.compile(r"\bwindow\.location\b|\blocation\.href\b")
CLOSE_EVENT_RE = re.compile(r"CloseActionScreenEvent\s*\(\s*\)")
AWAIT_OR_THEN_RE = re.compile(r"\bawait\b|\.then\s*\(")
FUNCTION_START_RE = re.compile(
    r"(^|\s)(async\s+)?([A-Za-z_$][\w$]*)\s*\([^)]*\)\s*\{"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check LWC quick-action bundles for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def find_lwc_bundles(root: Path) -> list[Path]:
    """Return every directory under root that contains a `.js-meta.xml` file.

    A bundle directory is one whose immediate children include a `*.js-meta.xml`.
    """
    bundles: list[Path] = []
    for meta in root.rglob("*.js-meta.xml"):
        if meta.is_file():
            bundles.append(meta.parent)
    # Deduplicate while preserving order.
    seen: set[Path] = set()
    unique: list[Path] = []
    for b in bundles:
        if b not in seen:
            seen.add(b)
            unique.append(b)
    return unique


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def classify_meta(meta_text: str) -> tuple[bool, bool, bool]:
    """Return (is_record_action, is_headless, is_screen) for a meta.xml text."""
    is_record_action = META_RECORD_ACTION in meta_text
    is_headless = bool(META_HEADLESS_ATTR_RE.search(meta_text))
    is_screen = bool(META_SCREEN_ATTR_RE.search(meta_text))
    return is_record_action, is_headless, is_screen


def has_template_markup(html_path: Path) -> bool:
    if not html_path.exists():
        return False
    text = read_text(html_path)
    # Strip simple whitespace/comments to decide "meaningful" markup.
    stripped = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    # A truly empty template file is still "markup present" if it has a <template> tag,
    # but the real concern for headless is any renderable content.
    return bool(re.search(r"<template[^>]*>[\s\S]*?<\/template>", stripped))


def check_close_before_await(js_text: str) -> list[tuple[int, str]]:
    """Heuristic — flag when `CloseActionScreenEvent` is dispatched in a function
    before any `await` or `.then(` on a preceding line in the same function body.

    The heuristic walks the file line by line, tracking brace depth to find the
    end of the function, and looks at whether a `CloseActionScreenEvent` is seen
    before the first `await`/`.then(` in that same function.
    """
    findings: list[tuple[int, str]] = []
    lines = js_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        match = FUNCTION_START_RE.search(line)
        if not match:
            i += 1
            continue
        # Found a function opener. Walk until matching closing brace.
        depth = line.count("{") - line.count("}")
        body_start = i
        j = i + 1
        seen_await_or_then = False
        close_line: int | None = None
        while j < len(lines) and depth > 0:
            cur = lines[j]
            # Order of checks matters — detect await/then on this line first.
            if AWAIT_OR_THEN_RE.search(cur):
                seen_await_or_then = True
            if (
                not seen_await_or_then
                and CLOSE_EVENT_RE.search(cur)
                and close_line is None
            ):
                close_line = j + 1  # 1-based
            depth += cur.count("{") - cur.count("}")
            j += 1
        if close_line is not None and not seen_await_or_then:
            findings.append(
                (
                    close_line,
                    "CloseActionScreenEvent dispatched before any await/.then in the same function "
                    f"(function starts at line {body_start + 1})",
                )
            )
        i = j if j > i else i + 1
    return findings


def scan_bundle(bundle_dir: Path) -> list[str]:
    """Return formatted findings for a single LWC bundle."""
    findings: list[str] = []
    meta_files = list(bundle_dir.glob("*.js-meta.xml"))
    if not meta_files:
        return findings
    meta_path = meta_files[0]
    meta_text = read_text(meta_path)
    is_record_action, is_headless, _is_screen = classify_meta(meta_text)

    if not is_record_action:
        return findings  # not a quick action — ignore

    # Locate primary JS and HTML files (same base name as meta).
    base = meta_path.name[: -len(".js-meta.xml")]
    js_path = bundle_dir / f"{base}.js"
    html_path = bundle_dir / f"{base}.html"
    js_text = read_text(js_path) if js_path.exists() else ""

    # 1. Headless with <template> markup.
    if is_headless and has_template_markup(html_path):
        findings.append(
            f"{html_path}:1: headless quick action (actionType=\"Action\") should not "
            f"ship renderable <template> markup — remove the HTML file or switch to ScreenAction"
        )

    # 2. Missing @api recordId when target is lightning__RecordAction.
    if js_text and not API_RECORDID_RE.search(js_text):
        findings.append(
            f"{js_path}:1: lightning__RecordAction target requires `@api recordId` "
            f"declaration — the platform injects recordId only when the decorator is present"
        )

    # 3. window.location usage in any JS under the bundle.
    for js_file in bundle_dir.rglob("*.js"):
        text = read_text(js_file)
        for lineno, line in enumerate(text.splitlines(), start=1):
            if WINDOW_LOCATION_RE.search(line):
                findings.append(
                    f"{js_file}:{lineno}: avoid `window.location` / `location.href` "
                    f"in quick actions — use NavigationMixin, getRecordNotifyChange, or refreshApex"
                )

    # 4. CloseActionScreenEvent dispatched before any await/.then in the same function.
    if js_text and not is_headless:
        for lineno, msg in check_close_before_await(js_text):
            findings.append(f"{js_path}:{lineno}: {msg}")

    return findings


def check_lwc_quick_actions(manifest_dir: Path) -> list[str]:
    issues: list[str] = []
    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]
    bundles = find_lwc_bundles(manifest_dir)
    if not bundles:
        return issues
    for bundle in bundles:
        issues.extend(scan_bundle(bundle))
    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_lwc_quick_actions(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
