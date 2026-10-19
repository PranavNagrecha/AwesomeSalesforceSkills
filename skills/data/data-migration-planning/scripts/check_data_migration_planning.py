#!/usr/bin/env python3
"""Checker for the data-migration-planning skill.

Point --manifest-dir at a migration folder containing any of:
  * migration_sequence.csv (or *sequence*.csv) with columns object, depends_on,
    bypass_documented
  * load CSVs (one per object; file name starts with the object API name,
    e.g. Contact.csv or Contact_load.csv)
  * target metadata in source format (objects/<Object>/fields/*.field-meta.xml,
    objects/<Object>/validationRules/*.validationRule-meta.xml) or *.object files

Rules (Bulk API 2.0 guide "Relationship Fields in a Header Row"; LDV guide):
  ERROR  sequence file lists a child before a parent it depends on; a load CSV
         header that chains past one level (A.B.C), which Bulk API relationship
         headers don't allow; a relationship column whose parent field is a
         custom field in the scanned metadata without externalId=true (only
         indexed parent fields can be referenced).
  WARN   sequence row with bypass_documented not yes; a load CSV with no column
         that looks like an external ID key; an active validation rule whose
         formula has no $Permission bypass.

Exit codes: 0 clean or WARN only; 1 on ERROR, missing directory, or WARN with
--strict. An empty directory prints a WARN and exits 0. Stdlib only.

Usage:
    python3 check_data_migration_planning.py --manifest-dir path/to/migration [--strict]
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{http://soap.sforce.com/2006/04/metadata}"
KEY_HINTS = ("external_id", "externalid", "legacy", "source_id", "ext_id")


def find(elem: ET.Element, tag: str) -> ET.Element | None:
    node = elem.find(NS + tag)
    if node is None:
        node = elem.find(tag)
    return node


def text(elem: ET.Element, tag: str) -> str:
    node = find(elem, tag)
    return node.text.strip() if node is not None and node.text is not None else ""


def parse_xml(path: Path) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as exc:
        print(f"WARN: {path}: cannot parse ({exc})")
        return None


def load_metadata(root: Path) -> tuple[dict[tuple[str, str], ET.Element], list[tuple[Path, ET.Element]]]:
    fields: dict[tuple[str, str], ET.Element] = {}
    rules: list[tuple[Path, ET.Element]] = []
    for f in root.rglob("*.field-meta.xml"):
        node = parse_xml(f)
        if node is not None:
            fields[(f.parent.parent.name.lower(), text(node, "fullName").lower() or f.name.split(".")[0].lower())] = node
    for f in root.rglob("*.validationRule-meta.xml"):
        node = parse_xml(f)
        if node is not None:
            rules.append((f, node))
    for f in root.rglob("*.object"):
        node = parse_xml(f)
        if node is None:
            continue
        obj = f.stem.lower()
        for fld in node.findall(NS + "fields") + node.findall("fields"):
            fields[(obj, text(fld, "fullName").lower())] = fld
        for vr in node.findall(NS + "validationRules") + node.findall("validationRules"):
            rules.append((f, vr))
    return fields, rules


def check_sequence(path: Path) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        cols = {c.lower().strip() for c in (reader.fieldnames or [])}
        if not {"object", "depends_on"} <= cols:
            return [("ERROR", f"{path}: sequence file needs columns object, depends_on (bypass_documented recommended)")]
        seen: set[str] = set()
        for n, row in enumerate(reader, start=2):
            r = {k.lower().strip(): (v or "").strip() for k, v in row.items() if k}
            obj = r.get("object", "")
            if not obj:
                continue
            for parent in [p.strip() for p in r.get("depends_on", "").split(",") if p.strip()]:
                if parent.lower() != obj.lower() and parent.lower() not in seen:
                    out.append(("ERROR", f"{path}:{n}: {obj} depends on {parent}, which is not loaded earlier"))
            if r.get("bypass_documented", "").lower() not in {"yes", "y", "true", "1"}:
                out.append(("WARN", f"{path}:{n}: {obj} has no documented automation bypass"))
            seen.add(obj.lower())
    return out


def child_object(csv_path: Path, known: set[str]) -> str:
    stem = csv_path.stem.lower()
    for obj in sorted(known, key=len, reverse=True):
        if stem == obj or stem.startswith(obj + "_") or stem.startswith(obj + "-") or stem.startswith(obj + "."):
            return obj
    return re.split(r"[_.\-]", stem)[0]


def check_load_csv(path: Path, fields: dict[tuple[str, str], ET.Element]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    with path.open(newline="", encoding="utf-8-sig") as fh:
        try:
            header = next(csv.reader(fh))
        except StopIteration:
            return [("WARN", f"{path}: empty file")]
    known_objects = {o for o, _ in fields}
    child = child_object(path, known_objects)
    if not any(any(h in col.lower() for h in KEY_HINTS) for col in header):
        out.append(("WARN", f"{path}: no column looks like an external ID key; re-runs can't upsert safely"))
    for col in header:
        parts = col.strip().split(".")
        if len(parts) > 2:
            out.append(("ERROR", f"{path}: column '{col}' chains more than one level; Bulk API relationship headers allow child-to-parent only"))
            continue
        if len(parts) != 2:
            continue
        rel, parent_field = parts[0].lower(), parts[1].lower()
        if rel.endswith("__r"):
            lookup = fields.get((child, rel[:-3] + "__c"))
            parent = text(lookup, "referenceTo").lower() if lookup is not None else ""
        else:
            parent = rel
        if not parent or not parent_field.endswith("__c"):
            continue
        target = fields.get((parent, parent_field))
        if target is not None and text(target, "externalId").lower() != "true":
            out.append(("ERROR", f"{path}: column '{col}' references {parent}.{parts[1]}, which is not an External ID; only indexed parent fields can be used"))
    return out


def check_rule(path: Path, rule: ET.Element) -> list[tuple[str, str]]:
    if text(rule, "active").lower() != "true":
        return []
    formula = text(rule, "errorConditionFormula")
    if "$Permission" not in formula:
        name = text(rule, "fullName") or path.name
        return [("WARN", f"{path}: active validation rule {name} has no $Permission bypass; migration rows that break it will fail")]
    return []


def main() -> int:
    ap = argparse.ArgumentParser(description="Check a migration folder (data-migration-planning skill).")
    ap.add_argument("--manifest-dir", default=".", help="Migration folder: sequence CSV, load CSVs, target metadata")
    ap.add_argument("--strict", action="store_true", help="Treat WARN as failure")
    args = ap.parse_args()

    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)

    csvs = sorted(root.rglob("*.csv"))
    fields, rules = load_metadata(root)
    if not csvs and not fields and not rules:
        print(f"WARN: no sequence file, load CSVs, or metadata under {root}; nothing to check")
        return 0

    findings: list[tuple[str, str]] = []
    for c in csvs:
        if "sequence" in c.stem.lower():
            findings.extend(check_sequence(c))
        else:
            findings.extend(check_load_csv(c, fields))
    for path, rule in rules:
        findings.extend(check_rule(path, rule))

    errors = sum(1 for s, _ in findings if s == "ERROR")
    warns = len(findings) - errors
    for sev, msg in findings:
        print(f"{sev}: {msg}")
    print(f"Scanned {len(csvs)} CSV file(s), {len(fields)} field(s), {len(rules)} validation rule(s): {errors} ERROR, {warns} WARN")
    if errors or (args.strict and warns):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
