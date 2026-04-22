#!/usr/bin/env python3
"""Checker for Flow Resource Patterns skill.

Scans .flow-meta.xml for:
- Record Choice Sets without a filter or limit
- Repeated literal strings across decisions/assignments (promote-to-Constant candidates)
- Assignments doing long string concatenation (promote-to-Text-Template candidates)

Usage:
    python3 check_flow_resource_patterns.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


NS = {"sf": "http://soap.sforce.com/2006/04/metadata"}
STRING_LITERAL = re.compile(r"<stringValue>([^<]{3,})</stringValue>")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Flow resource anti-patterns.")
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

        # Record Choice Sets without filters/limit
        for dcs in r.findall("sf:dynamicChoiceSets", NS):
            name = dcs.findtext("sf:name", default="unknown", namespaces=NS)
            if dcs.find("sf:filters", NS) is None:
                issues.append(
                    f"{path.relative_to(root)}: dynamicChoiceSet '{name}' has no filter — may load all records"
                )
            if dcs.find("sf:limit", NS) is None:
                issues.append(
                    f"{path.relative_to(root)}: dynamicChoiceSet '{name}' has no limit — set 10–200 for UX"
                )

        # Repeated string literals (4+ identical) across the flow
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        literals = Counter(m.group(1) for m in STRING_LITERAL.finditer(text))
        for literal, count in literals.items():
            if count >= 4 and not literal.startswith("{!") and len(literal) <= 40:
                issues.append(
                    f"{path.relative_to(root)}: literal '{literal}' used {count}× — promote to Constant"
                )

        # Assignments doing long string concatenation
        for asg in r.findall("sf:assignments", NS):
            name = asg.findtext("sf:name", default="unknown", namespaces=NS)
            concats = 0
            for item in asg.findall("sf:assignmentItems", NS):
                op = item.findtext("sf:operator", default="", namespaces=NS)
                if op in ("Add", "AddItem"):
                    concats += 1
            if concats >= 4:
                issues.append(
                    f"{path.relative_to(root)}: assignment '{name}' concatenates {concats}× — consider a Text Template"
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
        print("No Flow resource anti-patterns detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
