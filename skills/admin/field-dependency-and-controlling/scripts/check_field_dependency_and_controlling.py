#!/usr/bin/env python3
"""Checker for Field Dependency and Controlling skill.

Scans custom field XML for:
- Dependent picklists (valueSet.controllingField) without a Validation Rule
  on the same object mentioning both field names
- Dependent picklists where valueSettings is empty (matrix unpopulated)

Usage:
    python3 check_field_dependency_and_controlling.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


NS = {"sf": "http://soap.sforce.com/2006/04/metadata"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check dependent-picklist anti-patterns.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of metadata.")
    return parser.parse_args()


def _strip_ns(tag: str) -> str:
    return tag.split("}", 1)[1] if "}" in tag else tag


def check_metadata(root: Path) -> list[str]:
    issues: list[str] = []

    # Walk objects dir for field XMLs (both SFDX format and mdapi format)
    for field_xml in list(root.rglob("*.field-meta.xml")) + list(root.rglob("*.object-meta.xml")):
        try:
            tree = ET.parse(field_xml)
        except ET.ParseError:
            continue
        r = tree.getroot()
        # For object-meta.xml, iterate <fields>; for field-meta.xml, root is CustomField
        field_nodes = r.findall("sf:fields", NS) if _strip_ns(r.tag) == "CustomObject" else [r]

        for fn in field_nodes:
            vs = fn.find("sf:valueSet", NS)
            if vs is None:
                continue
            controlling = vs.findtext("sf:controllingField", default="", namespaces=NS)
            if not controlling:
                continue
            field_name = fn.findtext("sf:fullName", default="unknown", namespaces=NS)

            settings = vs.findall("sf:valueSettings", NS)
            if not settings:
                issues.append(
                    f"{field_xml.relative_to(root)}: dependent field '{field_name}' has controllingField '{controlling}' but no valueSettings — matrix unpopulated"
                )

            # Look for a validation rule on this object that references both fields
            # Object folder: parent of the fields folder OR same folder for mdapi
            obj_dir = field_xml.parent
            if obj_dir.name == "fields":
                obj_dir = obj_dir.parent
            vr_dir = obj_dir / "validationRules"
            has_guard = False
            if vr_dir.exists():
                for vr in vr_dir.glob("*.validationRule-meta.xml"):
                    try:
                        txt = vr.read_text(encoding="utf-8", errors="ignore")
                    except OSError:
                        continue
                    if field_name in txt and controlling in txt:
                        has_guard = True
                        break
            if not has_guard:
                issues.append(
                    f"{field_xml.relative_to(root)}: dependent picklist '{field_name}' has no Validation Rule referencing both '{field_name}' and '{controlling}' — API writes bypass matrix"
                )
    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}", file=sys.stderr)
        return 1

    issues = check_metadata(root)
    if not issues:
        print("No dependent-picklist anti-patterns detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
