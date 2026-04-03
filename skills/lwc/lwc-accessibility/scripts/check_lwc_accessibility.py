#!/usr/bin/env python3
"""Check LWC source files for common accessibility anti-patterns."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


CLICKABLE_CONTAINER_RE = re.compile(r"<(?:div|span)\b[^>]*\bonclick\s*=", re.IGNORECASE)
LIGHTNING_ICON_RE = re.compile(r"<lightning-icon\b", re.IGNORECASE)
ALT_TEXT_RE = re.compile(r"\balternative-text\s*=", re.IGNORECASE)
IMG_RE = re.compile(r"<img\b", re.IGNORECASE)
IMG_ALT_RE = re.compile(r"\balt\s*=", re.IGNORECASE)
NON_BUTTON_TABINDEX_RE = re.compile(r"<(?:div|span)\b[^>]*\btabindex\s*=\s*['\"]0['\"]", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Lightning Web Components for common accessibility issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata or source tree (default: current directory).",
    )
    return parser.parse_args()


def check_lwc_accessibility(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    for html_path in sorted(manifest_dir.rglob("*.html")):
        text = html_path.read_text(encoding="utf-8", errors="ignore")
        if CLICKABLE_CONTAINER_RE.search(text):
            issues.append(
                f"{html_path}: clickable `div` or `span` found; prefer semantic buttons or links instead of custom keyboard wiring."
            )
        if NON_BUTTON_TABINDEX_RE.search(text):
            issues.append(
                f"{html_path}: non-semantic element with `tabindex=\"0\"` found; confirm this is a deliberate composite-widget pattern."
            )
        if IMG_RE.search(text) and not IMG_ALT_RE.search(text):
            issues.append(
                f"{html_path}: `<img>` found without `alt`; provide alt text or an empty alt for decorative imagery."
            )
        for match in LIGHTNING_ICON_RE.finditer(text):
            tail = text[match.start():match.start() + 300]
            if not ALT_TEXT_RE.search(tail):
                issues.append(
                    f"{html_path}: `lightning-icon` appears without `alternative-text`; confirm the icon is decorative or add a text equivalent."
                )
                break

    return issues


def main() -> int:
    args = parse_args()
    issues = check_lwc_accessibility(Path(args.manifest_dir))

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
