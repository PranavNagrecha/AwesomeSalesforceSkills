#!/usr/bin/env python3
"""Check LWC datatable usage for common state and loading issues."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


DATATABLE_RE = re.compile(r"<lightning-datatable\b", re.IGNORECASE)
KEY_FIELD_RE = re.compile(r"\bkey-field\s*=", re.IGNORECASE)
INFINITE_LOADING_RE = re.compile(r"\benable-infinite-loading\b", re.IGNORECASE)
LOAD_MORE_RE = re.compile(r"\bonloadmore\s*=", re.IGNORECASE)
DRAFT_VALUES_RE = re.compile(r"\bdraft-values\s*=", re.IGNORECASE)
ONSAVE_RE = re.compile(r"\bonsave\s*=", re.IGNORECASE)
SELECTED_ROWS_RE = re.compile(r"\bselected-rows\s*=", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Lightning datatable markup for common identity and loading issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata or source tree (default: current directory).",
    )
    return parser.parse_args()


def check_lwc_data_table(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    for html_path in sorted(manifest_dir.rglob("*.html")):
        text = html_path.read_text(encoding="utf-8", errors="ignore")
        if not DATATABLE_RE.search(text):
            continue
        if not KEY_FIELD_RE.search(text):
            issues.append(f"{html_path}: `lightning-datatable` found without `key-field`.")
        if INFINITE_LOADING_RE.search(text) and not LOAD_MORE_RE.search(text):
            issues.append(
                f"{html_path}: infinite loading is enabled but no `onloadmore` handler was found."
            )
        if DRAFT_VALUES_RE.search(text) and not ONSAVE_RE.search(text):
            issues.append(
                f"{html_path}: draft values are configured but no `onsave` handler was found."
            )
        if SELECTED_ROWS_RE.search(text) and not KEY_FIELD_RE.search(text):
            issues.append(
                f"{html_path}: selected rows are configured without an explicit `key-field`; selection may be unstable."
            )

    return issues


def main() -> int:
    args = parse_args()
    issues = check_lwc_data_table(Path(args.manifest_dir))

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
