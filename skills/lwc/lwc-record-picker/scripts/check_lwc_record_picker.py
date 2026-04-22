#!/usr/bin/env python3
"""Checker for LWC Record Picker skill.

Scans LWC for:
- Custom combobox lookups that should use lightning-record-picker
- record-picker markup missing matching-info when display-info has multiple fields

Usage:
    python3 check_lwc_record_picker.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


COMBOBOX_LOOKUP = re.compile(r"<lightning-combobox[^>]*>", re.IGNORECASE)
RECORD_PICKER = re.compile(r"<lightning-record-picker[^>]*>", re.IGNORECASE | re.DOTALL)
DISPLAY_INFO = re.compile(r"display-info\s*=")
MATCHING_INFO = re.compile(r"matching-info\s*=")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check record-picker anti-patterns.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of metadata.")
    return parser.parse_args()


def check_lwc(root: Path) -> list[str]:
    issues: list[str] = []
    lwc_dir = root / "lwc"
    if not lwc_dir.exists():
        return issues
    for comp in lwc_dir.iterdir():
        if not comp.is_dir():
            continue
        comp_name = comp.name.lower()
        for path in comp.glob("*.html"):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            # Custom combobox-lookup smell when the component is named like a lookup
            if ("lookup" in comp_name or "picker" in comp_name) and COMBOBOX_LOOKUP.search(text):
                if not RECORD_PICKER.search(text):
                    issues.append(
                        f"{path.relative_to(root)}: lookup-like component uses lightning-combobox; consider lightning-record-picker"
                    )

            for m in RECORD_PICKER.finditer(text):
                tag = m.group(0)
                if DISPLAY_INFO.search(tag) and not MATCHING_INFO.search(tag):
                    line_no = text[: m.start()].count("\n") + 1
                    issues.append(
                        f"{path.relative_to(root)}:{line_no}: record-picker has display-info but no matching-info"
                    )
    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}", file=sys.stderr)
        return 1

    issues = check_lwc(root)
    if not issues:
        print("No record-picker anti-patterns detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
