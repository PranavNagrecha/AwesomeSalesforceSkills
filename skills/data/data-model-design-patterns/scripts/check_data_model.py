#!/usr/bin/env python3
"""Data model checker for the data-model-design-patterns skill.

Reads object and field metadata in source format (objects/<Obj>/<Obj>.object-meta.xml
plus objects/<Obj>/fields/*.field-meta.xml) or Metadata API format (*.object).

Rules (Object Reference "Relationships Among Objects"; Metadata API CustomField;
Limits Quick Reference):
  ERROR  a MasterDetail field whose master is BusinessHours, Idea, Lead,
         OrderItem, Pricebook2, Product2, QuoteLineItem, or User (these can't be
         the primary object); a MasterDetail field on a standard object that
         points at a custom object (a standard object can't be the detail of a
         custom object).
  WARN   a custom object whose only relationship fields are two lookups (a
         lookup-only junction: no native roll-ups, rows survive parent deletes);
         a master-detail chain deeper than two levels; 35 or more relationship
         fields on one object (a custom object allows up to 40 relationships);
         a lookup with deleteConstraint Cascade (review access implications);
         a Text field whose label suggests phone or email data.

Exit codes: 0 clean or WARN only; 1 on ERROR, missing directory, or WARN with
--strict. An empty directory prints a WARN and exits 0. Stdlib only.

Usage:
    python3 check_data_model.py --manifest-dir force-app/main/default [--strict]
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{http://soap.sforce.com/2006/04/metadata}"
NEVER_MASTER = {"businesshours", "idea", "lead", "orderitem", "pricebook2", "product2", "quotelineitem", "user"}
RELATIONSHIP_WARN = 35
PHONE_WORDS = ("phone", "mobile", "fax")
EMAIL_WORDS = ("email", "e-mail")


def text(elem: ET.Element, tag: str) -> str:
    node = elem.find(NS + tag)
    if node is None:
        node = elem.find(tag)
    return node.text.strip() if node is not None and node.text is not None else ""


def parse(path: Path) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as exc:
        print(f"WARN: {path}: cannot parse ({exc})")
        return None


def load(root: Path) -> dict[str, list[tuple[Path, ET.Element]]]:
    """Map object API name -> list of (file, CustomField element)."""
    objects: dict[str, list[tuple[Path, ET.Element]]] = {}
    for f in root.rglob("*.object-meta.xml"):
        name = f.name[: -len(".object-meta.xml")]
        objects.setdefault(name, [])
        node = parse(f)
        if node is not None:
            for fld in node.findall(NS + "fields") + node.findall("fields"):
                objects[name].append((f, fld))
    for f in root.rglob("*.field-meta.xml"):
        name = f.parent.parent.name if f.parent.name == "fields" else f.parent.name
        node = parse(f)
        if node is not None:
            objects.setdefault(name, []).append((f, node))
    for f in root.rglob("*.object"):
        node = parse(f)
        if node is not None:
            objects.setdefault(f.stem, [])
            for fld in node.findall(NS + "fields") + node.findall("fields"):
                objects[f.stem].append((f, fld))
    return objects


def check(objects: dict[str, list[tuple[Path, ET.Element]]]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    md_parent: dict[str, str] = {}
    for obj, fields in sorted(objects.items()):
        rels = [(p, f) for p, f in fields if text(f, "type") in ("Lookup", "MasterDetail")]
        for path, f in rels:
            ftype, target, name = text(f, "type"), text(f, "referenceTo"), text(f, "fullName")
            if ftype == "MasterDetail":
                if target.lower() in NEVER_MASTER:
                    out.append(("ERROR", f"{path}: {obj}.{name} is master-detail to {target}, which can't be the master object; use a lookup"))
                if not obj.endswith("__c") and target.endswith("__c"):
                    out.append(("ERROR", f"{path}: {obj}.{name} makes standard object {obj} the detail of custom object {target}, which isn't allowed"))
                md_parent[obj] = target
            if ftype == "Lookup" and text(f, "deleteConstraint") == "Cascade":
                out.append(("WARN", f"{path}: {obj}.{name} lookup uses deleteConstraint Cascade; confirm availability and access implications"))
        if obj.endswith("__c") and len(rels) == 2 and all(text(f, "type") == "Lookup" for _, f in rels):
            out.append(("WARN", f"{rels[0][0]}: {obj} has exactly two lookups and no master-detail; if it is a junction, it gets no native roll-ups and its rows survive parent deletes"))
        if len(rels) >= RELATIONSHIP_WARN:
            out.append(("WARN", f"{obj}: {len(rels)} relationship fields; a custom object allows up to 40 relationships"))
        for path, f in fields:
            if text(f, "type") != "Text":
                continue
            label = (text(f, "label") or text(f, "fullName")).lower()
            if any(w in label for w in PHONE_WORDS):
                out.append(("WARN", f"{path}: {obj}.{text(f, 'fullName')} stores phone-like data as Text; use the Phone type"))
            elif any(w in label for w in EMAIL_WORDS):
                out.append(("WARN", f"{path}: {obj}.{text(f, 'fullName')} stores email-like data as Text; use the Email type"))
    for obj in sorted(md_parent):
        depth, cur, seen = 1, md_parent[obj], {obj}
        while cur in md_parent and cur not in seen:
            seen.add(cur)
            depth += 1
            cur = md_parent[cur]
        if depth > 2:
            out.append(("WARN", f"{obj}: master-detail chain {depth} levels deep; one top-level delete cascades through every level"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Check relationship and field-type metadata (data-model-design-patterns skill).")
    ap.add_argument("--manifest-dir", default=".", help="Root of the metadata tree")
    ap.add_argument("--strict", action="store_true", help="Treat WARN as failure")
    args = ap.parse_args()

    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)

    objects = load(root)
    if not objects:
        print(f"WARN: no object or field metadata under {root}; nothing to check")
        return 0

    findings = check(objects)
    errors = sum(1 for s, _ in findings if s == "ERROR")
    warns = len(findings) - errors
    for sev, msg in findings:
        print(f"{sev}: {msg}")
    print(f"Scanned {len(objects)} object(s): {errors} ERROR, {warns} WARN")
    if errors or (args.strict and warns):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
