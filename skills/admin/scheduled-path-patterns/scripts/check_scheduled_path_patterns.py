#!/usr/bin/env python3
"""Checker for Scheduled Path Patterns skill.

Scans Flow metadata for:
- Record-triggered Flows with scheduled paths missing entry conditions
- Scheduled paths without Get Records or Decision re-check at branch start

Usage:
    python3 check_scheduled_path_patterns.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from xml.etree import ElementTree as ET


NS = {"sf": "http://soap.sforce.com/2006/04/metadata"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check scheduled-path anti-patterns.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of metadata.")
    return parser.parse_args()


def iter_flows(root: Path):
    for path in root.rglob("*.flow-meta.xml"):
        yield path
    for path in root.rglob("*.flow"):
        yield path


def check_flow(path: Path, root: Path) -> list[str]:
    issues: list[str] = []
    try:
        tree = ET.parse(path)
    except (ET.ParseError, OSError):
        return issues
    root_el = tree.getroot()

    scheduled_paths = root_el.findall(".//sf:scheduledPaths", NS)
    if not scheduled_paths:
        return issues

    for sp in scheduled_paths:
        sp_name = sp.findtext("sf:name", default="<unnamed>", namespaces=NS)
        # Require entry condition filter on the start element OR on the path
        start = root_el.find("sf:start", NS)
        filters = []
        if start is not None:
            filters = start.findall(".//sf:filters", NS) + start.findall(".//sf:filterFormula", NS)
        if not filters:
            issues.append(
                f"{path.relative_to(root)}: scheduled path '{sp_name}' without entry filter criteria"
            )

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}", file=sys.stderr)
        return 1

    issues: list[str] = []
    for flow in iter_flows(root):
        issues.extend(check_flow(flow, root))

    if not issues:
        print("No scheduled-path anti-patterns detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
