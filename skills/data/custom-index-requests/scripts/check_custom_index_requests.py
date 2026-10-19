#!/usr/bin/env python3
"""Checker for the custom-index-requests skill.

Reads CustomField metadata (source-format *.field-meta.xml, or fields inside
Metadata API *.object files) and CustomIndex components (*.indx-meta*).

Severity:
  ERROR  externalId=true on a type other than AutoNumber, Email, Number, or Text
         (the LDV guide allows External IDs only on those types); a CustomIndex
         component whose allowNullValues is not true or false; a field, object,
         or CustomIndex file that does not parse.
  WARN   externalId=true on a formula field; externalId=true without
         unique=true on a field whose name looks
         categorical (status, type, region, ...): External ID makes it an upsert
         key and duplicates make upserts fail; unique=true on such a field
         (legitimate repeated values will be rejected).

Exit codes: 0 clean or WARN only; 1 on ERROR, missing directory, or WARN with
--strict. An empty directory prints a WARN and exits 0. Stdlib only.

Usage:
    python3 check_custom_index_requests.py --manifest-dir force-app/main/default [--strict]
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{http://soap.sforce.com/2006/04/metadata}"
EXTERNAL_ID_TYPES = {"AutoNumber", "Email", "Number", "Text"}
CATEGORICAL = re.compile(r"(status|type|category|segment|region|tier|level|priority|source|channel|stage|phase|group|class)", re.IGNORECASE)


def find(elem: ET.Element, tag: str) -> ET.Element | None:
    node = elem.find(NS + tag)
    if node is None:
        node = elem.find(tag)
    return node


def text(elem: ET.Element, tag: str) -> str:
    node = find(elem, tag)
    return node.text.strip() if node is not None and node.text is not None else ""


PARSE_ERRORS: list[tuple[str, str]] = []


def parse(path: Path) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as exc:
        PARSE_ERRORS.append(("ERROR", f"{path}: cannot parse ({exc}); not checked"))
        return None


def fields_in(path: Path) -> list[ET.Element]:
    root = parse(path)
    if root is None:
        return []
    if root.tag.endswith("CustomField"):
        return [root]
    return root.findall(NS + "fields") + root.findall("fields")


def check_field(path: Path, f: ET.Element) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    name = text(f, "fullName") or path.name
    ftype = text(f, "type")
    ext = text(f, "externalId").lower() == "true"
    uniq = text(f, "unique").lower() == "true"
    if ext and find(f, "formula") is not None:
        out.append(("WARN", f"{path}: {name} is a formula field marked externalId; the LDV guide lists External IDs only on Auto Number, Email, Number, and Text fields, so verify in a sandbox deploy"))
    elif ext and ftype and ftype not in EXTERNAL_ID_TYPES:
        out.append(("ERROR", f"{path}: {name} is {ftype} with externalId=true; External IDs are allowed only on AutoNumber, Email, Number, Text"))
    if CATEGORICAL.search(name) is not None:
        if ext and not uniq:
            out.append(("WARN", f"{path}: {name} looks categorical but is an External ID; it becomes an upsert key and duplicates make upserts fail. Prefer a Support-built index"))
        if uniq:
            out.append(("WARN", f"{path}: {name} looks categorical but is unique=true; repeated values will be rejected"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Check index-related field and CustomIndex metadata (custom-index-requests skill).")
    ap.add_argument("--manifest-dir", default=".", help="Root of the metadata tree")
    ap.add_argument("--strict", action="store_true", help="Treat WARN as failure")
    args = ap.parse_args()

    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)

    field_files = sorted(list(root.rglob("*.field-meta.xml")) + list(root.rglob("*.object")))
    index_files = sorted(p for p in root.rglob("*") if p.is_file() and ".indx-meta" in p.name)
    if not field_files and not index_files:
        print(f"WARN: no field or CustomIndex metadata under {root}; nothing to check")
        return 0

    findings: list[tuple[str, str]] = []
    for path in field_files:
        for f in fields_in(path):
            findings.extend(check_field(path, f))
    for path in index_files:
        node = parse(path)
        if node is None:
            continue
        value = text(node, "allowNullValues").lower()
        if value not in {"", "true", "false"}:
            findings.append(("ERROR", f"{path}: allowNullValues must be true or false, found '{value}'"))

    findings = PARSE_ERRORS + findings
    errors = sum(1 for s, _ in findings if s == "ERROR")
    warns = len(findings) - errors
    for sev, msg in findings:
        print(f"{sev}: {msg}")
    print(f"Scanned {len(field_files)} field/object file(s), {len(index_files)} CustomIndex file(s): {errors} ERROR, {warns} WARN")
    if errors or (args.strict and warns):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
