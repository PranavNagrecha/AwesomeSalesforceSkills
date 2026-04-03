#!/usr/bin/env python3
"""Check LWC form components for common validation and save-pattern issues."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


RECORD_EDIT_FORM_RE = re.compile(r"<lightning-record-edit-form\b", re.IGNORECASE)
LIGHTNING_MESSAGES_RE = re.compile(r"<lightning-messages\b", re.IGNORECASE)
LIGHTNING_INPUT_RE = re.compile(r"<lightning-input\b", re.IGNORECASE)
FILE_UPLOAD_RE = re.compile(r"<lightning-file-upload\b", re.IGNORECASE)
RECORD_ID_ATTR_RE = re.compile(r"\brecord-id\s*=", re.IGNORECASE)
SET_CUSTOM_VALIDITY_RE = re.compile(r"\bsetCustomValidity\s*\(", re.IGNORECASE)
REPORT_VALIDITY_RE = re.compile(r"\breportValidity\s*\(", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Lightning Web Components for common form and validation issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata or source tree (default: current directory).",
    )
    return parser.parse_args()


def check_lwc_forms_and_validation(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    input_form_files: set[Path] = set()

    for html_path in sorted(manifest_dir.rglob("*.html")):
        text = html_path.read_text(encoding="utf-8", errors="ignore")
        if RECORD_EDIT_FORM_RE.search(text) and not LIGHTNING_MESSAGES_RE.search(text):
            issues.append(
                f"{html_path}: `lightning-record-edit-form` found without `lightning-messages`; review how validation-rule and save errors are surfaced."
            )
        if FILE_UPLOAD_RE.search(text) and not RECORD_ID_ATTR_RE.search(text):
            issues.append(
                f"{html_path}: `lightning-file-upload` found without an obvious `record-id`; confirm the upload step runs after a record exists."
            )
        if LIGHTNING_INPUT_RE.search(text):
            input_form_files.add(html_path.with_suffix(".js"))

    for js_path in sorted(manifest_dir.rglob("*.js")):
        text = js_path.read_text(encoding="utf-8", errors="ignore")
        if SET_CUSTOM_VALIDITY_RE.search(text) and not REPORT_VALIDITY_RE.search(text):
            issues.append(
                f"{js_path}: uses `setCustomValidity()` without `reportValidity()`; custom error messages may never render."
            )
        if js_path in input_form_files and "handleSave" in text and not REPORT_VALIDITY_RE.search(text):
            issues.append(
                f"{js_path}: save handler detected for a component with `lightning-input` fields, but no `reportValidity()` call was found."
            )

    return issues


def main() -> int:
    args = parse_args()
    issues = check_lwc_forms_and_validation(Path(args.manifest_dir))

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
