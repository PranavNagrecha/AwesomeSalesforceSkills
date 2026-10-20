#!/usr/bin/env python3
"""Checker script for Lookup and Relationship Design skill.

Scans custom object metadata for relationship-design smells:
- Objects approaching or exceeding the 40-relationship limit
- SOQL queries traversing 5+ levels of parent relationships

Limits: 40 relationships per custom object and five child-to-parent levels
(salesforce_app_limits_cheatsheet 264 L688-L689, L708-L712).

Exit contract: a custom object over 40 relationships is an ERROR and exits 1
(the platform allows up to 40); every other finding prints as WARN and exits 0
(exit 1 with --strict); a
directory with no objects/ and no .cls files prints one WARN and exits 0; a
missing directory prints ERROR and exits 1.

Usage:
    python3 check_lookup_and_relationship_design.py [--manifest-dir path/to/metadata] [--strict]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET


NS = {"sf": "http://soap.sforce.com/2006/04/metadata"}
DEEP_SOQL = re.compile(r"\b\w+(?:\.\w+){5,}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check relationship design smells.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of metadata.")
    parser.add_argument("--limit", type=int, default=35, help="Warn at this relationship count (default 35).")
    parser.add_argument("--strict", action="store_true", help="Exit 1 when any WARN finding is reported.")
    return parser.parse_args()


def count_relationships(object_dir: Path) -> int:
    fields_dir = object_dir / "fields"
    if not fields_dir.exists():
        return 0
    count = 0
    for field in fields_dir.glob("*.field-meta.xml"):
        try:
            tree = ET.parse(field)
        except (ET.ParseError, OSError):
            continue
        type_el = tree.find("sf:type", NS)
        if type_el is not None and type_el.text in ("Lookup", "MasterDetail", "Hierarchy"):
            count += 1
    return count


def check_relationship_counts(root: Path, limit: int) -> list[str]:
    issues: list[str] = []
    objects_dir = root / "objects"
    if not objects_dir.exists():
        return issues
    for obj in objects_dir.iterdir():
        if not obj.is_dir():
            continue
        count = count_relationships(obj)
        if count > 40 and obj.name.endswith("__c"):
            issues.append(f"ERROR|{obj.name}: {count} relationship fields — over the 40 a custom object allows")
        elif count >= 40:
            issues.append(f"{obj.name}: {count} relationship fields — at/over the 40-relationship limit")
        elif count >= limit:
            issues.append(f"{obj.name}: {count} relationship fields — approaching 40-field limit")
    return issues


def check_deep_soql(root: Path) -> list[str]:
    issues: list[str] = []
    for path in root.rglob("*.cls"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for m in DEEP_SOQL.finditer(text):
            if "SELECT" in text[max(0, m.start() - 200) : m.start()].upper():
                line_no = text[: m.start()].count("\n") + 1
                issues.append(
                    f"{path.relative_to(root)}:{line_no}: deep relationship traversal {m.group(0)!r} — SOQL caps at 5 levels"
                )
                break
    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: directory not found: {root}")
        return 1
    if not (root / "objects").is_dir() and not any(root.rglob("*.cls")):
        print(f"WARN: no objects/ directory and no .cls files under {root} — nothing to check.")
        return 0

    issues: list[str] = []
    issues.extend(check_relationship_counts(root, args.limit))
    issues.extend(check_deep_soql(root))

    if not issues:
        print("No relationship-design issues detected.")
        return 0
    errors = [i[len("ERROR|"):] for i in issues if i.startswith("ERROR|")]
    for issue in errors:
        print(f"ERROR: {issue}")
    for issue in issues:
        if not issue.startswith("ERROR|"):
            print(f"WARN: {issue}")
    if errors:
        return 1
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
