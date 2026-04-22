#!/usr/bin/env python3
"""Checker script for LWC Chart and Visualization skill.

Scans LWC metadata for chart anti-patterns:
- `new Chart(` in renderedCallback without a guard
- External CDN script URLs in LWC files
- Canvas-based charts without adjacent accessible table or aria attributes

Usage:
    python3 check_lwc_chart_and_visualization.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


NEW_CHART_PAT = re.compile(r"new\s+Chart\s*\(")
GUARD_PAT = re.compile(r"if\s*\(\s*!\s*this\._chart\s*\)")
CDN_PAT = re.compile(r"(?i)https?://[^'\"\s]*(cdn|unpkg|jsdelivr)[^'\"\s]*\.js")
CANVAS_PAT = re.compile(r"<canvas[^>]*>")
ARIA_OR_TABLE_PAT = re.compile(r"(?i)(aria-describedby|<table[^>]*>|role\s*=\s*['\"]img['\"])")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check LWC chart/visualization hygiene.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of Salesforce metadata.")
    return parser.parse_args()


def iter_lwc_components(root: Path):
    lwc_dir = root / "lwc"
    if not lwc_dir.exists():
        return
    for comp_dir in lwc_dir.iterdir():
        if comp_dir.is_dir():
            yield comp_dir


def check_unguarded_new_chart(root: Path) -> list[str]:
    issues: list[str] = []
    for comp in iter_lwc_components(root):
        for path in comp.glob("*.js"):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if not NEW_CHART_PAT.search(text):
                continue
            if "renderedCallback" in text and not GUARD_PAT.search(text):
                issues.append(
                    f"{path.relative_to(root)}: new Chart() in renderedCallback without _chart guard"
                )
    return issues


def check_cdn_references(root: Path) -> list[str]:
    issues: list[str] = []
    for comp in iter_lwc_components(root):
        for path in list(comp.glob("*.js")) + list(comp.glob("*.html")):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if CDN_PAT.search(text):
                issues.append(
                    f"{path.relative_to(root)}: CDN script URL; bundle as Static Resource instead"
                )
    return issues


def check_canvas_accessibility(root: Path) -> list[str]:
    issues: list[str] = []
    for comp in iter_lwc_components(root):
        html_files = list(comp.glob("*.html"))
        if not html_files:
            continue
        combined = ""
        for h in html_files:
            try:
                combined += h.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
        if CANVAS_PAT.search(combined) and not ARIA_OR_TABLE_PAT.search(combined):
            issues.append(
                f"{comp.relative_to(root)}: canvas chart without aria/table accessibility fallback"
            )
    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}", file=sys.stderr)
        return 1

    issues: list[str] = []
    issues.extend(check_unguarded_new_chart(root))
    issues.extend(check_cdn_references(root))
    issues.extend(check_canvas_accessibility(root))

    if not issues:
        print("No LWC chart/visualization issues detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
