#!/usr/bin/env python3
"""Checker script for LWC Security skill."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check LWC Security configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_lwc_security(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    for html_path in sorted(manifest_dir.rglob("*.html")):
        text = html_path.read_text(encoding="utf-8", errors="ignore")
        if 'lwc:dom="manual"' in text:
            issues.append(f"{html_path}: uses `lwc:dom=\"manual\"`; review DOM ownership and sanitization carefully.")
        if 'lwc:render-mode="light"' in text:
            issues.append(f"{html_path}: uses light DOM; confirm the component hierarchy and security tradeoff are intentional.")

    for js_path in sorted(manifest_dir.rglob("*.js")):
        text = js_path.read_text(encoding="utf-8", errors="ignore")
        if "innerHTML" in text or "outerHTML" in text:
            issues.append(f"{js_path}: uses innerHTML/outerHTML; review for unsafe manual DOM rendering.")
        if "document.querySelector" in text or "window.document" in text:
            issues.append(f"{js_path}: queries the global document; use component-owned DOM access instead.")

    for cls_path in sorted(manifest_dir.rglob("*.cls")):
        text = cls_path.read_text(encoding="utf-8", errors="ignore")
        if "@AuraEnabled" in text and not re.search(r"\b(with|without|inherited)\s+sharing\b", text):
            issues.append(f"{cls_path}: exposes @AuraEnabled Apex without an explicit sharing declaration; review the controller boundary.")

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_lwc_security(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
