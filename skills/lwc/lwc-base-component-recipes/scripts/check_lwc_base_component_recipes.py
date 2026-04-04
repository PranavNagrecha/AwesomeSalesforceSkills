#!/usr/bin/env python3
"""Checker script for LWC Base Component Recipes skill.

Scans LWC component source files for common base component anti-patterns:
- lightning-datatable without draft-values binding
- lightning-record-edit-form without lightning-messages
- if:true/if:false wrapping a lightning-record-edit-form (destroys unsaved state)
- lightning-datatable onsave handler that does not reset draftValues

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_lwc_base_component_recipes.py [--help]
    python3 check_lwc_base_component_recipes.py --manifest-dir path/to/force-app
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check LWC component source for base component anti-patterns "
            "(lightning-datatable, lightning-record-edit-form, lightning-record-form)."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata or LWC source (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_lwc_files(root: Path, extension: str) -> list[Path]:
    """Recursively collect LWC source files with the given extension."""
    return list(root.rglob(f"*.{extension}"))


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_datatable_missing_draft_values(html_files: list[Path]) -> list[str]:
    """Warn when lightning-datatable has editable columns but no draft-values binding."""
    issues: list[str] = []
    datatable_re = re.compile(
        r"<lightning-datatable\b([^>]*(?:>(?!<\/lightning-datatable)[\s\S]*?)?)",
        re.IGNORECASE,
    )
    for path in html_files:
        content = _read(path)
        if "lightning-datatable" not in content.lower():
            continue
        # Simple heuristic: editable:true present in columns JS or editable attribute in HTML
        has_editable = bool(re.search(r"editable\s*:\s*true", content, re.IGNORECASE))
        has_draft_values = bool(re.search(r"draft-values", content, re.IGNORECASE))
        if has_editable and not has_draft_values:
            issues.append(
                f"{path}: lightning-datatable appears to have editable columns but "
                f"'draft-values' binding is missing. Inline edits will be lost on save."
            )
    return issues


def check_datatable_draft_values_not_reset(js_files: list[Path]) -> list[str]:
    """Warn when onsave handler exists but draftValues is never reset to []."""
    issues: list[str] = []
    for path in js_files:
        content = _read(path)
        if "handleSave" not in content and "onsave" not in content.lower():
            continue
        # Look for a handleSave function
        if not re.search(r"handleSave\s*\(", content):
            continue
        # Check if draftValues is reset within the file
        if not re.search(r"draftValues\s*=\s*\[\s*\]", content):
            issues.append(
                f"{path}: onsave / handleSave found but 'draftValues = []' reset is missing. "
                f"The inline edit toolbar will remain visible after save."
            )
    return issues


def check_record_edit_form_missing_messages(html_files: list[Path]) -> list[str]:
    """Warn when lightning-record-edit-form is present but lightning-messages is absent."""
    issues: list[str] = []
    for path in html_files:
        content = _read(path)
        if "lightning-record-edit-form" not in content.lower():
            continue
        if "lightning-messages" not in content.lower():
            issues.append(
                f"{path}: lightning-record-edit-form found without lightning-messages. "
                f"Server-side save errors will not be displayed to the user."
            )
    return issues


def check_record_edit_form_wrapped_in_if_true(html_files: list[Path]) -> list[str]:
    """Warn when lightning-record-edit-form is inside an if:true block.

    Toggling if:true destroys the form element, discarding unsaved field values.
    """
    issues: list[str] = []
    # Pattern: if:true or lwc:if before lightning-record-edit-form in the same template block
    if_pattern = re.compile(r'\bif:true\b|\blwc:if\b', re.IGNORECASE)
    form_pattern = re.compile(r'<lightning-record-edit-form', re.IGNORECASE)
    for path in html_files:
        content = _read(path)
        if not form_pattern.search(content):
            continue
        # Find position of form and look back for if:true within 300 chars
        for m in form_pattern.finditer(content):
            preceding = content[max(0, m.start() - 300): m.start()]
            if if_pattern.search(preceding):
                issues.append(
                    f"{path}: lightning-record-edit-form appears to be inside an if:true / lwc:if "
                    f"block. Toggling this condition destroys the form and discards unsaved values. "
                    f"Use an slds-hide CSS class toggle instead."
                )
                break  # one warning per file
    return issues


def check_datatable_missing_key_field(html_files: list[Path]) -> list[str]:
    """Warn when lightning-datatable is present but key-field attribute is not set."""
    issues: list[str] = []
    for path in html_files:
        content = _read(path)
        if "lightning-datatable" not in content.lower():
            continue
        if not re.search(r'key-field\s*=', content, re.IGNORECASE):
            issues.append(
                f"{path}: lightning-datatable found without a 'key-field' attribute. "
                f"This is required and will cause a runtime error."
            )
    return issues


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def check_lwc_base_component_recipes(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found under manifest_dir."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    html_files = _find_lwc_files(manifest_dir, "html")
    js_files = _find_lwc_files(manifest_dir, "js")

    if not html_files and not js_files:
        # No LWC source found — not an error for this checker
        return issues

    issues.extend(check_datatable_missing_draft_values(html_files))
    issues.extend(check_datatable_draft_values_not_reset(js_files))
    issues.extend(check_record_edit_form_missing_messages(html_files))
    issues.extend(check_record_edit_form_wrapped_in_if_true(html_files))
    issues.extend(check_datatable_missing_key_field(html_files))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_lwc_base_component_recipes(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
