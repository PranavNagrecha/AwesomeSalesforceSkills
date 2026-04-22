#!/usr/bin/env python3
"""Checker for Flow Cross Object Updates skill.

Scans .flow-meta.xml for:
- recordUpdates / recordCreates element inside a loops body (DML-in-loop)
- recordLookups / recordUpdates missing a faultConnector

Usage:
    python3 check_flow_cross_object_updates.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


NS = {"sf": "http://soap.sforce.com/2006/04/metadata"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Flow cross-object anti-patterns.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of metadata.")
    return parser.parse_args()


def check_flows(root: Path) -> list[str]:
    issues: list[str] = []
    for path in root.rglob("*.flow-meta.xml"):
        try:
            tree = ET.parse(path)
        except ET.ParseError:
            continue
        r = tree.getroot()

        # Gather targetReferences inside loops
        loops = r.findall("sf:loops", NS)
        loop_next_refs: set[str] = set()
        for loop in loops:
            nvc = loop.find("sf:nextValueConnector", NS)
            if nvc is not None:
                tr = nvc.find("sf:targetReference", NS)
                if tr is not None and tr.text:
                    loop_next_refs.add(tr.text)

        # Elements whose name is reached inside a loop body
        updates = {u.findtext("sf:name", default="", namespaces=NS): u for u in r.findall("sf:recordUpdates", NS)}
        creates = {u.findtext("sf:name", default="", namespaces=NS): u for u in r.findall("sf:recordCreates", NS)}
        for nm in list(updates.keys()) + list(creates.keys()):
            if nm in loop_next_refs:
                issues.append(
                    f"{path.relative_to(root)}: DML element '{nm}' is the loop body — move Update/Create OUTSIDE the loop"
                )

        # Missing faultConnector on data elements
        for tag in ("recordLookups", "recordUpdates", "recordCreates", "recordDeletes"):
            for el in r.findall(f"sf:{tag}", NS):
                name = el.findtext("sf:name", default="unknown", namespaces=NS)
                if el.find("sf:faultConnector", NS) is None:
                    issues.append(
                        f"{path.relative_to(root)}: {tag} '{name}' has no faultConnector — errors will surface as raw stacktrace"
                    )
    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}", file=sys.stderr)
        return 1

    issues = check_flows(root)
    if not issues:
        print("No Flow cross-object anti-patterns detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
