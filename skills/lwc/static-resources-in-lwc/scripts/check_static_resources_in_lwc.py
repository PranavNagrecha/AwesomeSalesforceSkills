#!/usr/bin/env python3
"""Check LWC static-resource loading patterns for common anti-patterns."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REMOTE_URL_RE = re.compile(r"https?://", re.IGNORECASE)
RESOURCE_URL_IMPORT_RE = re.compile(r"@salesforce/resourceUrl/", re.IGNORECASE)
LOAD_SCRIPT_RE = re.compile(r"\bloadScript\s*\(", re.IGNORECASE)
LOAD_STYLE_RE = re.compile(r"\bloadStyle\s*\(", re.IGNORECASE)
RENDERED_CALLBACK_RE = re.compile(r"\brenderedCallback\s*\(", re.IGNORECASE)
GUARD_HINT_RE = re.compile(r"\b(?:initialized|isLoaded|hasLoaded|resourcesLoaded|scriptLoaded)\b", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check LWC source for common static-resource loading issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata or source tree (default: current directory).",
    )
    return parser.parse_args()


def check_static_resources_in_lwc(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    for html_path in sorted(manifest_dir.rglob("*.html")):
        text = html_path.read_text(encoding="utf-8", errors="ignore")
        if "<script" in text.lower() and REMOTE_URL_RE.search(text):
            issues.append(
                f"{html_path}: remote script or stylesheet URL found in markup; prefer packaged static resources instead of CDN loading."
            )

    for js_path in sorted(manifest_dir.rglob("*.js")):
        text = js_path.read_text(encoding="utf-8", errors="ignore")
        if REMOTE_URL_RE.search(text) and not RESOURCE_URL_IMPORT_RE.search(text):
            issues.append(
                f"{js_path}: remote URL found in JS; confirm third-party assets are packaged as static resources rather than loaded from the public internet."
            )
        if (LOAD_SCRIPT_RE.search(text) or LOAD_STYLE_RE.search(text)) and not RESOURCE_URL_IMPORT_RE.search(text):
            issues.append(
                f"{js_path}: resource loader usage found without an `@salesforce/resourceUrl` import; verify the loaded asset path is deployable."
            )
        if RENDERED_CALLBACK_RE.search(text) and (LOAD_SCRIPT_RE.search(text) or LOAD_STYLE_RE.search(text)) and not GUARD_HINT_RE.search(text):
            issues.append(
                f"{js_path}: resource loading inside `renderedCallback()` found without an obvious one-time guard."
            )

    return issues


def main() -> int:
    args = parse_args()
    issues = check_static_resources_in_lwc(Path(args.manifest_dir))

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
