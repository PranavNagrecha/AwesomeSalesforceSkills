#!/usr/bin/env python3
"""Checker for the feature-flag-custom-metadata skill.

Scans a source directory (SFDX package directory or Metadata API retrieve) for
feature-flag mistakes the skill warns about.

Flag records (customMetadata/<FlagType>.<Name>.md[-meta.xml], default type Feature_Flag):
  ERROR  Is_Enabled__c committed as true (the feature goes live at deploy time)
  ERROR  Percent_Rollout__c outside 0..100 or not a number
  WARN   no Is_Enabled__c value in the record (an updated record keeps the org's value)
  WARN   Is_Enabled__c set with xsi:nil (clears the value instead of setting false)
Flag type definition (objects/<FlagType>__mdt):
  ERROR  a MultiselectPicklist field (not a valid custom metadata value type)
  WARN   a TextArea / LongTextArea field (getAll()/getInstance() return 255 characters)
Apex (.cls, comments and strings ignored):
  ERROR  DML (insert/update/upsert/delete) on a variable typed as an __mdt
  WARN   Math.random() in a class that reads custom metadata (non-deterministic rollout)

Exit 1 on ERROR (or WARN with --strict) and when --manifest-dir is missing.
Stdlib only.

Usage:
    python3 check_feature_flag_custom_metadata.py --manifest-dir force-app
    python3 check_feature_flag_custom_metadata.py --manifest-dir force-app --flag-type Feature_Flag --strict
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{http://soap.sforce.com/2006/04/metadata}"
XSI_NIL = "{http://www.w3.org/2001/XMLSchema-instance}nil"


def _child(elem: ET.Element, tag: str) -> ET.Element | None:
    found = elem.find(NS + tag)
    if found is not None:
        return found
    return elem.find(tag)


def _children(elem: ET.Element, tag: str) -> list[ET.Element]:
    return elem.findall(NS + tag) + elem.findall(tag)


def strip_code(src: str) -> str:
    src = re.sub(r"/\*.*?\*/", lambda m: re.sub(r"[^\n]", " ", m.group(0)), src, flags=re.S)
    src = re.sub(r"//[^\n]*", "", src)
    return re.sub(r"'(?:\\.|[^'\\])*'", "''", src)


def check_records(root: Path, flag_type: str, out: list[tuple[str, str]]) -> int:
    n = 0
    for path in sorted(root.rglob(f"{flag_type}.*")):
        if not (path.name.endswith(".md-meta.xml") or path.name.endswith(".md")) or "customMetadata" not in path.parts:
            continue
        n += 1
        try:
            rec = ET.parse(path).getroot()
        except ET.ParseError as exc:
            out.append(("ERROR", f"{path}: not well-formed XML ({exc})"))
            continue
        values = {}
        for v in _children(rec, "values"):
            field = _child(v, "field")
            value = _child(v, "value")
            if field is not None:
                values[(field.text or "").strip()] = value
        enabled = values.get("Is_Enabled__c")
        if "Is_Enabled__c" not in values:
            out.append(("WARN", f"{path}: no Is_Enabled__c value; an updated record keeps whatever the org has"))
        elif enabled is not None and enabled.get(XSI_NIL) == "true":
            out.append(("WARN", f"{path}: Is_Enabled__c is xsi:nil; commit an explicit false"))
        elif enabled is not None and (enabled.text or "").strip().lower() == "true":
            out.append(("ERROR", f"{path}: Is_Enabled__c committed as true; the feature goes live at deploy time"))
        pct = values.get("Percent_Rollout__c")
        if pct is not None and pct.get(XSI_NIL) != "true" and (pct.text or "").strip():
            try:
                num = float(pct.text.strip())
                if not 0 <= num <= 100:
                    out.append(("ERROR", f"{path}: Percent_Rollout__c {num} is outside 0..100"))
            except ValueError:
                out.append(("ERROR", f"{path}: Percent_Rollout__c '{pct.text.strip()}' is not a number"))
    return n


def check_type(root: Path, flag_type: str, out: list[tuple[str, str]]) -> int:
    n = 0
    files = [p for p in root.rglob("*") if p.is_file() and f"{flag_type}__mdt" in str(p)
             and (p.name.endswith(".field-meta.xml") or p.name.endswith(".object") or p.name.endswith(".object-meta.xml"))]
    for path in sorted(files):
        n += 1
        try:
            xml = ET.parse(path).getroot()
        except ET.ParseError as exc:
            out.append(("ERROR", f"{path}: not well-formed XML ({exc})"))
            continue
        fields = [xml] if xml.tag.endswith("CustomField") else _children(xml, "fields")
        for f in fields:
            ftype = _child(f, "type")
            name = _child(f, "fullName")
            label = (name.text if name is not None else path.name) or path.name
            kind = (ftype.text or "").strip() if ftype is not None else ""
            if kind == "MultiselectPicklist":
                out.append(("ERROR", f"{path}: field {label} is MultiselectPicklist, not a valid custom metadata value type"))
            elif kind in ("TextArea", "LongTextArea"):
                out.append(("WARN", f"{path}: field {label} is {kind}; getAll()/getInstance() return only 255 characters"))
    return n


def check_apex(root: Path, out: list[tuple[str, str]]) -> int:
    n = 0
    for path in sorted(root.rglob("*.cls")):
        code = strip_code(path.read_text(encoding="utf-8", errors="ignore"))
        if "__mdt" not in code:
            continue
        n += 1
        mdt_vars = set(re.findall(r"\b\w+__mdt\s*(?:>\s*)?\s+(\w+)\s*[=;]", code))
        mdt_vars |= set(re.findall(r"List<\s*\w+__mdt\s*>\s+(\w+)", code))
        for var in sorted(mdt_vars):
            if re.search(rf"\b(insert|update|upsert|delete)\s+{re.escape(var)}\s*;", code, re.I):
                out.append(("ERROR", f"{path}: DML on custom metadata variable '{var}'; deploy with Metadata.Operations.enqueueDeployment"))
        if re.search(r"\bMath\.random\s*\(", code):
            out.append(("WARN", f"{path}: Math.random() in a class that reads custom metadata; rollout must be deterministic per user"))
    return n


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check feature flags built on Custom Metadata Types.")
    parser.add_argument("--manifest-dir", required=True, type=Path, help="Source directory to scan (e.g. force-app).")
    parser.add_argument("--flag-type", default="Feature_Flag", help="Custom metadata type name without __mdt (default Feature_Flag).")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on WARN as well as ERROR.")
    args = parser.parse_args(argv)

    root = args.manifest_dir
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)

    out: list[tuple[str, str]] = []
    checked = check_records(root, args.flag_type, out) + check_type(root, args.flag_type, out) + check_apex(root, out)
    if not checked:
        print(f"WARN: no {args.flag_type} records, {args.flag_type}__mdt definition, or Apex reading __mdt under {root}")
        return 0
    for level, msg in out:
        print(f"{level}: {msg}")
    errors = sum(1 for lvl, _ in out if lvl == "ERROR")
    warns = len(out) - errors
    print(f"Checked {checked} file(s): {errors} error(s), {warns} warning(s).")
    return 1 if errors or (args.strict and warns) else 0


if __name__ == "__main__":
    sys.exit(main())
