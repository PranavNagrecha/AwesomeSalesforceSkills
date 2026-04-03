#!/usr/bin/env python3
"""Check LWC source for navigation and routing anti-patterns."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


WINDOW_LOCATION_RE = re.compile(r"\b(?:window\.)?location\.(?:href|assign|replace)\b|\bwindow\.open\s*\(")
HARDCODED_INTERNAL_URL_RE = re.compile(r"""['"]/(?:lightning|s|apex)/""")
PAGE_TYPE_RE = re.compile(r"""type\s*:\s*['"]([^'"]+)['"]""")
STATE_BLOCK_RE = re.compile(r"""state\s*:\s*\{(?P<body>[^}]*)\}""", re.DOTALL)
STATE_KEY_RE = re.compile(r"""([A-Za-z_][A-Za-z0-9_]*)\s*:""")

STANDARD_STATE_KEYS = {
    "defaultFieldValues",
    "filterName",
    "nooverride",
    "navigationLocation",
    "backgroundContext",
    "count",
    "recordTypeId",
    "uid",
    "useRecordTypeCheck",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Lightning Web Components for routing and navigation issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def line_number(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def check_navigation_and_routing(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    for path in sorted(p for p in manifest_dir.rglob("*") if p.suffix in {".js", ".ts"}):
        text = path.read_text(encoding="utf-8", errors="ignore")

        for match in WINDOW_LOCATION_RE.finditer(text):
            issues.append(
                f"{path}:{line_number(text, match.start())}: uses browser location APIs; review whether a PageReference should replace hardcoded navigation."
            )

        for match in HARDCODED_INTERNAL_URL_RE.finditer(text):
            issues.append(
                f"{path}:{line_number(text, match.start())}: contains a hardcoded internal Salesforce URL segment; prefer NavigationMixin or GenerateUrl."
            )

        for match in STATE_BLOCK_RE.finditer(text):
            body = match.group("body")
            for state_key_match in STATE_KEY_RE.finditer(body):
                key = state_key_match.group(1)
                if "__" not in key and key not in STANDARD_STATE_KEYS:
                    issues.append(
                        f"{path}:{line_number(text, match.start() + state_key_match.start())}: custom PageReference state key `{key}` is not namespaced."
                    )

        for match in PAGE_TYPE_RE.finditer(text):
            page_type = match.group(1)
            window = text[match.start() : match.start() + 240]
            if page_type in {"standard__recordPage", "standard__objectPage"} and "actionName" not in window:
                issues.append(
                    f"{path}:{line_number(text, match.start())}: `{page_type}` appears without a nearby `actionName`; review whether the page reference is complete."
                )

    return issues


def main() -> int:
    args = parse_args()
    issues = check_navigation_and_routing(Path(args.manifest_dir))

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
