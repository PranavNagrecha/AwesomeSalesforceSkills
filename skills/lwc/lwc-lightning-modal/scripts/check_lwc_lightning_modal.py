#!/usr/bin/env python3
"""Checker for LWC LightningModal skill.

Scans LWC for:
- Component name contains "modal" but extends LightningElement
- Hand-rolled slds-modal overlay without LightningModal import

Usage:
    python3 check_lwc_lightning_modal.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


EXTENDS_ELEMENT = re.compile(r"extends\s+LightningElement\b")
IMPORT_MODAL = re.compile(r"from\s+['\"]lightning/modal['\"]")
SLDS_MODAL_DIV = re.compile(r"class\s*=\s*['\"][^'\"]*\bslds-modal\b")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check LightningModal anti-patterns.")
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
        name_has_modal = "modal" in comp.name.lower() or "dialog" in comp.name.lower()
        for path in comp.glob("*.js"):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if name_has_modal and EXTENDS_ELEMENT.search(text) and not IMPORT_MODAL.search(text):
                issues.append(
                    f"{path.relative_to(root)}: component named like a modal extends LightningElement; use LightningModal"
                )
        for path in comp.glob("*.html"):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if SLDS_MODAL_DIV.search(text):
                # Check if any JS file in the component imports LightningModal
                js_files = list(comp.glob("*.js"))
                any_import = any(
                    IMPORT_MODAL.search(f.read_text(encoding="utf-8", errors="ignore"))
                    for f in js_files
                )
                if not any_import:
                    issues.append(
                        f"{path.relative_to(root)}: hand-rolled slds-modal div without LightningModal import"
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
        print("No LightningModal anti-patterns detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
