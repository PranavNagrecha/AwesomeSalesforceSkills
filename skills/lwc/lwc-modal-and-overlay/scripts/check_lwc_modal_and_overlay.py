#!/usr/bin/env python3
"""Check LWC overlay patterns for common modal anti-patterns."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


EXTENDS_MODAL_RE = re.compile(r"class\s+\w+\s+extends\s+LightningModal", re.IGNORECASE)
CLOSE_CALL_RE = re.compile(r"\bclose\s*\(", re.IGNORECASE)
WINDOW_DIALOG_RE = re.compile(r"\bwindow\.(?:alert|confirm|prompt)\s*\(", re.IGNORECASE)
SLDS_MODAL_RE = re.compile(r"slds-modal", re.IGNORECASE)
ARIA_MODAL_RE = re.compile(r'aria-modal\s*=\s*["\']true["\']', re.IGNORECASE)
ARIA_LABEL_RE = re.compile(r"aria-labelledby\s*=|aria-label\s*=", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check LWC overlay code for common modal and dialog issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata or source tree (default: current directory).",
    )
    return parser.parse_args()


def check_lwc_modal_and_overlay(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    for js_path in sorted(manifest_dir.rglob("*.js")):
        text = js_path.read_text(encoding="utf-8", errors="ignore")
        if WINDOW_DIALOG_RE.search(text):
            issues.append(
                f"{js_path}: browser alert/confirm/prompt detected; review whether a supported Salesforce overlay pattern should be used instead."
            )
        if EXTENDS_MODAL_RE.search(text) and not CLOSE_CALL_RE.search(text):
            issues.append(
                f"{js_path}: component extends `LightningModal` but no `close()` call was found; confirm the modal has a clear completion path."
            )

    for html_path in sorted(manifest_dir.rglob("*.html")):
        text = html_path.read_text(encoding="utf-8", errors="ignore")
        if SLDS_MODAL_RE.search(text):
            if not ARIA_MODAL_RE.search(text):
                issues.append(
                    f"{html_path}: custom SLDS modal markup found without `aria-modal=\"true\"`."
                )
            if not ARIA_LABEL_RE.search(text):
                issues.append(
                    f"{html_path}: custom SLDS modal markup found without an obvious accessible label."
                )

    return issues


def main() -> int:
    args = parse_args()
    issues = check_lwc_modal_and_overlay(Path(args.manifest_dir))

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
