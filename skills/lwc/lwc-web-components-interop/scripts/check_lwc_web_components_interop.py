#!/usr/bin/env python3
"""Checker script for LWC Web Components Interop skill.

Scans LWC metadata for interop hygiene issues:
- Multiple LWCs calling customElements.define() on the same tag
- LWC templates listening for dashed event names via onX syntax
- Static Resources carrying React/Vue bundles masquerading as web components

Usage:
    python3 check_lwc_web_components_interop.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path


DEFINE_PAT = re.compile(r"customElements\.define\s*\(\s*['\"]([a-z][a-z0-9-]*)['\"]")
DASHED_EVENT_PAT = re.compile(r"on([a-z0-9]+-[a-z0-9-]+)\s*=\s*\{")
FRAMEWORK_MARKER_PAT = re.compile(
    r"(?i)(react-dom|createReactClass|__REACT_DEVTOOLS|Vue\.createApp|new\s+Vue\s*\()"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check LWC web-components interop hygiene.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of Salesforce metadata.")
    return parser.parse_args()


def check_duplicate_defines(root: Path) -> list[str]:
    issues: list[str] = []
    tag_to_files: dict[str, list[str]] = defaultdict(list)
    lwc_dir = root / "lwc"
    if not lwc_dir.exists():
        return issues
    for path in lwc_dir.rglob("*.js"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for tag in DEFINE_PAT.findall(text):
            tag_to_files[tag].append(str(path.relative_to(root)))
    for tag, files in tag_to_files.items():
        if len(files) > 1:
            issues.append(
                f"tag '{tag}' defined in {len(files)} LWCs: {', '.join(files[:3])} — centralize define()"
            )
    return issues


def check_dashed_event_handlers(root: Path) -> list[str]:
    issues: list[str] = []
    lwc_dir = root / "lwc"
    if not lwc_dir.exists():
        return issues
    for path in lwc_dir.rglob("*.html"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for match in DASHED_EVENT_PAT.findall(text):
            issues.append(
                f"{path.relative_to(root)}: dashed event 'on{match}' — won't fire; use addEventListener"
            )
    return issues


def check_framework_static_resources(root: Path) -> list[str]:
    issues: list[str] = []
    sr_dir = root / "staticresources"
    if not sr_dir.exists():
        return issues
    for path in sr_dir.rglob("*.js"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")[:50000]
        except OSError:
            continue
        if FRAMEWORK_MARKER_PAT.search(text):
            issues.append(
                f"{path.relative_to(root)}: Static Resource contains React/Vue; not a standard web component"
            )
    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}", file=sys.stderr)
        return 1

    issues: list[str] = []
    issues.extend(check_duplicate_defines(root))
    issues.extend(check_dashed_event_handlers(root))
    issues.extend(check_framework_static_resources(root))

    if not issues:
        print("No LWC web-components interop issues detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
