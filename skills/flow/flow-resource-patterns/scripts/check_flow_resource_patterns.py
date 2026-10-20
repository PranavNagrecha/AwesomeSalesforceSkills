#!/usr/bin/env python3
"""Checker for Flow Resource Patterns skill.

Scans *.flow-meta.xml under --manifest-dir. Stdlib only; reads metadata, never runs a
flow. Grounding is the Metadata API Developer Guide 264 ("api_meta"); line numbers
come from `grep -n`.

ERROR (exit 1 always)
  * A flow file that does not parse.
  * A constants element whose value holds a merge field. The guide: the value "can't
    have merge fields, nor can it reference another resource besides
    $GlobalConstant.EmptyString" (api_meta 264 L72921-72923).
WARN / REVIEW (exit 0 unless --strict)
  * A record choice set (a dynamicChoiceSets element with no picklistField and no
    picklistObject, and no collectionReference) with no filters: it loads the first
    records of the object up to the limit. A choice set built from a collection
    (collectionReference, api_meta 264 L72976-72977) is skipped. A picklist choice set is skipped, because filters are "Not supported
    for picklist choices" (api_meta 264 L73012-73015).
  * A record choice set with no limit element. The default and the maximum are both
    200 (api_meta 264 L73017-73018), so this is a REVIEW of the 200-row list, not an
    unbounded load.
  * The same string literal used four or more times in one flow (promote-to-Constant
    candidate; SKILL.md Recommended Workflow step 6).
  * An assignment with four or more `Add` items. REVIEW only: `Add` appends text to a
    string variable but also appends to a collection variable and adds numbers
    (api_meta 264 L72353-72367), so this may be a collection build, not concatenation.

An empty tree prints one WARN and exits 0 (1 with --strict). A missing path prints an
ERROR and exits 1.

Usage:
    python3 check_flow_resource_patterns.py --manifest-dir path/to/metadata [--strict]
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

STRING_LITERAL = re.compile(r"<stringValue>([^<]{3,})</stringValue>")


def local(el: ET.Element) -> str:
    return el.tag.split("}")[-1]


def kids(parent: ET.Element, name: str) -> list[ET.Element]:
    return [c for c in parent if local(c) == name]


def text(parent: ET.Element, name: str) -> str:
    for c in kids(parent, name):
        return (c.text or "").strip()
    return ""


def check_flow(path: Path, root: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warns: list[str] = []
    rel = path.relative_to(root)
    try:
        r = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [f"{rel}: XML does not parse ({exc})"], warns
    for dcs in kids(r, "dynamicChoiceSets"):
        name = text(dcs, "name") or "unknown"
        if text(dcs, "picklistField") or text(dcs, "picklistObject") or text(dcs, "collectionReference"):
            continue
        if not kids(dcs, "filters"):
            warns.append(f"{rel}: record choice set '{name}' has no filter; it loads records up to its limit (api_meta 264 L73012-73018)")
        if not kids(dcs, "limit"):
            warns.append(f"{rel}: REVIEW record choice set '{name}' has no limit; the default and maximum are both 200 (api_meta 264 L73017-73018)")
    for const in kids(r, "constants"):
        name = text(const, "name") or "unknown"
        for value in kids(const, "value"):
            for el in value.iter():
                bad_ref = local(el) == "elementReference" and (el.text or "").strip() != "$GlobalConstant.EmptyString"
                if bad_ref or (el.text and "{!" in el.text):
                    errors.append(f"{rel}: constant '{name}' holds a merge field or resource reference; constants cannot (api_meta 264 L72921-72923)")
                    break
    literals = Counter(m.group(1) for m in STRING_LITERAL.finditer(path.read_text(encoding="utf-8", errors="ignore")))
    for literal, count in literals.items():
        if count >= 4 and not literal.startswith("{!") and len(literal) <= 40:
            warns.append(f"{rel}: literal '{literal}' used {count}x; promote to a Constant")
    for asg in kids(r, "assignments"):
        name = text(asg, "name") or "unknown"
        adds = sum(1 for item in kids(asg, "assignmentItems") if text(item, "operator") in ("Add", "AddItem"))
        if adds >= 4:
            warns.append(f"{rel}: REVIEW assignment '{name}' has {adds} Add items; a Text Template may fit if this builds a string (api_meta 264 L72353-72367)")
    return errors, warns


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Flow resource anti-patterns.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of metadata (default: current directory).")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on WARN findings too.")
    args = parser.parse_args()
    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)
    files = sorted(root.rglob("*.flow-meta.xml"))
    if not files:
        print(f"WARN: no *.flow-meta.xml files found under {root}")
        return 1 if args.strict else 0
    errors: list[str] = []
    warns: list[str] = []
    for f in files:
        e, w = check_flow(f, root)
        errors += e
        warns += w
    for e in errors:
        print(f"ERROR: {e}")
    for w in warns:
        print(f"WARN: {w}")
    if not errors and not warns:
        print("No Flow resource anti-patterns detected.")
    if errors:
        sys.exit(1)
    return 1 if (warns and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
