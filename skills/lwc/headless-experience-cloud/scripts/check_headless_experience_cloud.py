#!/usr/bin/env python3
"""Checker script for Headless Experience Cloud skill.

Checks org metadata or source files for common misconfigurations related to
Salesforce CMS headless delivery API integrations.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_headless_experience_cloud.py [--help]
    python3 check_headless_experience_cloud.py --manifest-dir path/to/metadata
    python3 check_headless_experience_cloud.py --source-dir path/to/js/src
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Pattern: hardcoded Salesforce channel ID in source code
# Channel IDs are 15- or 18-character alphanumeric strings starting with '0ap'
_CHANNEL_ID_PATTERN = re.compile(r"['\"`]/channels/0ap[A-Za-z0-9]{12,15}/")

# Pattern: delivery API base path used without an environment variable reference
_DELIVERY_ENDPOINT_PATTERN = re.compile(
    r"['\"`]/services/data/v\d+\.\d+/connect/cms/delivery/channels/"
)

# Pattern: OAuth scope 'full' in a connected app metadata file (overly permissive)
_FULL_SCOPE_PATTERN = re.compile(r"<oauthScope>full</oauthScope>")

# Pattern: missing pageSize parameter in a delivery API fetch call
_FETCH_WITHOUT_PAGE_SIZE = re.compile(
    r"/connect/cms/delivery/channels/[^'\"]+/contents['\"`]",
)


def _check_source_files(source_dir: Path) -> list[str]:
    """Check JavaScript/TypeScript source files for headless delivery anti-patterns."""
    issues: list[str] = []

    js_files = list(source_dir.rglob("*.js")) + list(source_dir.rglob("*.ts")) + list(source_dir.rglob("*.jsx")) + list(source_dir.rglob("*.tsx"))

    for filepath in js_files:
        try:
            content = filepath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        rel = filepath.relative_to(source_dir)

        # Check for hardcoded channel IDs
        if _CHANNEL_ID_PATTERN.search(content):
            issues.append(
                f"{rel}: hardcoded CMS channel ID detected in delivery API URL. "
                "Channel IDs differ between orgs — externalize as an environment variable."
            )

        # Check for full OAuth scope in connected app XML
        if _FULL_SCOPE_PATTERN.search(content):
            issues.append(
                f"{rel}: OAuth scope 'full' detected. "
                "Use minimum required scope (api or chatter_api) for CMS delivery access."
            )

        # Check delivery API calls missing pageSize
        for match in _FETCH_WITHOUT_PAGE_SIZE.finditer(content):
            surrounding = content[max(0, match.start() - 200):match.end() + 50]
            if "pageSize" not in surrounding and "page_size" not in surrounding:
                issues.append(
                    f"{rel}: CMS delivery endpoint call may be missing 'pageSize' parameter. "
                    "Always paginate delivery API requests to avoid unbounded payloads."
                )
                break  # Report once per file

    return issues


def _check_metadata_files(manifest_dir: Path) -> list[str]:
    """Check Salesforce metadata XML files for connected app scope issues."""
    issues: list[str] = []

    xml_files = list(manifest_dir.rglob("*.connectedApp-meta.xml")) + list(
        manifest_dir.rglob("*.connectedApp")
    )

    for filepath in xml_files:
        try:
            content = filepath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        rel = filepath.relative_to(manifest_dir)

        if _FULL_SCOPE_PATTERN.search(content):
            issues.append(
                f"{rel}: Connected App uses OAuth scope 'full'. "
                "For CMS delivery API access, restrict to 'api' or 'chatter_api'."
            )

        if "chatter_api" not in content and "api" not in content:
            # Only flag if this connected app is plausibly related to CMS/Experience
            if re.search(r"(?i)(cms|experience|channel|content)", content):
                issues.append(
                    f"{rel}: Connected App related to CMS/Experience may be missing "
                    "'api' or 'chatter_api' OAuth scope required for authenticated channel access."
                )

    return issues


def check_headless_experience_cloud(
    manifest_dir: Path,
    source_dir: Path | None = None,
) -> list[str]:
    """Return a list of issue strings found in the project.

    Args:
        manifest_dir: Root directory of Salesforce metadata (for connected app checks).
        source_dir: Root directory of frontend source files (JS/TS checks).

    Returns:
        List of issue description strings. Empty list means no issues found.
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(_check_metadata_files(manifest_dir))

    if source_dir is not None:
        if not source_dir.exists():
            issues.append(f"Source directory not found: {source_dir}")
        else:
            issues.extend(_check_source_files(source_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata and frontend source files for common issues "
            "with Salesforce CMS headless delivery API integrations."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--source-dir",
        default=None,
        help="Root directory of frontend JS/TS source files (optional).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    source_dir = Path(args.source_dir) if args.source_dir else None

    issues = check_headless_experience_cloud(manifest_dir, source_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
