#!/usr/bin/env python3
"""Checker script for Embedded Analytics Architecture skill.

Checks org metadata or configuration relevant to Embedded Analytics Architecture.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_embedded_analytics_architecture.py [--help]
    python3 check_embedded_analytics_architecture.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Embedded Analytics Architecture configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_lwc_source(file_path: Path) -> list[str]:
    """Check an LWC HTML file for embedded analytics anti-patterns."""
    issues: list[str] = []

    content = file_path.read_text(encoding="utf-8", errors="ignore")

    # Check for filter attribute on wave-wave-dashboard (anti-pattern)
    import re
    if re.search(r'wave-wave-dashboard[^>]*filter\s*=', content, re.IGNORECASE):
        issues.append(
            f"{file_path.name}: wave-wave-dashboard component uses 'filter' attribute. "
            "The LWC wave-wave-dashboard component uses 'state' (not 'filter'). "
            "The 'filter' attribute is for the Aura wave:waveDashboard component only. "
            "Using 'filter' on the LWC component silently has no effect."
        )

    # Check for hard-coded dashboardDevName value
    if re.search(r'dashboard-dev-name\s*=\s*"[a-zA-Z]', content):
        issues.append(
            f"{file_path.name}: wave-wave-dashboard has a hard-coded dashboard-dev-name. "
            "Hard-coded dev names break when the dashboard is renamed or across environments. "
            "Resolve dashboardDevName at runtime from Custom Metadata or Apex."
        )

    return issues


def check_embedded_analytics_architecture(manifest_dir: Path) -> list[str]:
    """Check LWC metadata for embedded analytics anti-patterns."""
    import re

    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Scan LWC HTML files for anti-patterns
    html_files = list(manifest_dir.rglob("*.html"))
    for html_file in html_files:
        content = html_file.read_text(encoding="utf-8", errors="ignore")
        if "wave-wave-dashboard" in content or "waveDashboard" in content:
            issues.extend(check_lwc_source(html_file))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_embedded_analytics_architecture(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
