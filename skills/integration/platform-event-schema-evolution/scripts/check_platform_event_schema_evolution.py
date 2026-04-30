#!/usr/bin/env python3
"""Static checker for Platform Event metadata changes.

For each Platform Event source object (`*__e/objects/<Name>__e`), validates:

- no field is marked required (Platform Event fields should usually be optional)
- field-name renames between two trees: pass --base and --head pointing at two
  retrieves; the script reports any field that exists in --base but not --head
  (likely rename or delete).

Stdlib only.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {"sf": "http://soap.sforce.com/2006/04/metadata"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Lint platform event metadata.")
    p.add_argument("--head", default=".", help="Repository root for current state.")
    p.add_argument("--base", default=None, help="Optional second tree to compare against.")
    return p.parse_args()


def event_field_files(root: Path) -> list[Path]:
    return list(root.rglob("objects/*__e/fields/*.field-meta.xml"))


def field_required(path: Path) -> bool:
    try:
        tree = ET.parse(path)
    except ET.ParseError:
        return False
    root = tree.getroot()
    req = root.find("sf:required", NS)
    return req is not None and (req.text or "").strip().lower() == "true"


def event_fields(root: Path) -> dict[str, set[str]]:
    by_event: dict[str, set[str]] = {}
    for f in event_field_files(root):
        event = f.parents[1].name
        by_event.setdefault(event, set()).add(f.stem.removesuffix(".field-meta"))
    return by_event


def main() -> int:
    args = parse_args()
    head = Path(args.head)
    issues: list[str] = []

    for f in event_field_files(head):
        if field_required(f):
            issues.append(f"{f}: Platform Event field marked required — risks publisher breakage")

    if args.base:
        base = Path(args.base)
        base_fields = event_fields(base)
        head_fields = event_fields(head)
        for event, fields in base_fields.items():
            missing = fields - head_fields.get(event, set())
            for m in missing:
                issues.append(
                    f"{event}: field '{m}' exists in base but not head — possible rename/delete (breaking)"
                )

    if not issues:
        print("[platform-event-schema-evolution] no issues found")
        return 0
    for i in issues:
        print(f"WARN: {i}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
