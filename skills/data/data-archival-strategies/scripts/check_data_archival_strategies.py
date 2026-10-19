#!/usr/bin/env python3
"""Checker for the data-archival-strategies skill.

Reads custom big object definitions, field history settings, and Apex in a
metadata tree (Metadata API .object files or source-format object folders).

Rules (Big Objects Implementation Guide; Security guide, Field History Tracking):
  ERROR  big object with no index; index field not defined, not required, of
         type LongTextArea or URL, or without ASC/DESC sortDirection; text
         fields in an index totalling over 100 characters (Email counts 80,
         Phone 40); Database.insertImmediate(...) called as a bare statement,
         because failures come back in SaveResults instead of an exception.
  WARN   more than 20 fields with trackHistory=true on one object (the limit
         without Field Audit Trail); Apex that calls the async-queries
         endpoint (not among the APIs the guide lists for big objects).

Exit codes: 0 clean or WARN only; 1 on ERROR, missing directory, or WARN with
--strict. An empty directory prints a WARN and exits 0. Stdlib only.

Usage:
    python3 check_data_archival_strategies.py --manifest-dir force-app/main/default [--strict]
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{http://soap.sforce.com/2006/04/metadata}"
INDEX_TEXT_LIMIT = 100
FIXED_TEXT_LENGTH = {"Email": 80, "Phone": 40}
BANNED_INDEX_TYPES = {"LongTextArea", "Url", "URL"}
HISTORY_FIELD_LIMIT = 20
BARE_INSERT_RE = re.compile(r"^\s*Database\.insertImmediate\s*\(", re.IGNORECASE | re.MULTILINE)
ASYNC_QUERY_RE = re.compile(r"/async-queries", re.IGNORECASE)


def find(elem: ET.Element, tag: str) -> ET.Element | None:
    node = elem.find(NS + tag)
    if node is None:
        node = elem.find(tag)
    return node


def findall(elem: ET.Element, tag: str) -> list[ET.Element]:
    return elem.findall(NS + tag) + elem.findall(tag)


def text(elem: ET.Element, tag: str) -> str:
    node = find(elem, tag)
    return node.text.strip() if node is not None and node.text is not None else ""


def parse(path: Path) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as exc:
        print(f"WARN: {path}: cannot parse ({exc})")
        return None


def object_name(path: Path) -> str:
    name = path.name
    for suffix in (".object-meta.xml", ".object"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name


def collect(path: Path) -> tuple[list[ET.Element], list[ET.Element]]:
    """Fields and indexes for one object: inline elements plus source-format children."""
    root = parse(path)
    if root is None:
        return [], []
    fields = findall(root, "fields")
    indexes = findall(root, "indexes")
    folder = path.parent
    if path.name.endswith(".object-meta.xml"):
        for sub, bucket in (("fields", fields), ("indexes", indexes)):
            for child in sorted((folder / sub).glob("*.xml")) if (folder / sub).is_dir() else []:
                node = parse(child)
                if node is not None:
                    bucket.append(node)
    return fields, indexes


def check_big_object(path: Path, fields: list[ET.Element], indexes: list[ET.Element]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    by_name = {text(f, "fullName"): f for f in fields}
    if not indexes:
        out.append(("ERROR", f"{path}: big object has no index; a custom big object needs one and it can't be added or changed after deployment"))
        return out
    for idx in indexes:
        total_text = 0
        for ifield in findall(idx, "fields"):
            name = text(ifield, "name")
            field = by_name.get(name)
            if field is None:
                out.append(("ERROR", f"{path}: index field {name or '(blank)'} does not match any field fullName"))
                continue
            ftype = text(field, "type")
            if text(field, "required").lower() != "true":
                out.append(("ERROR", f"{path}: index field {name} must be marked required"))
            if ftype in BANNED_INDEX_TYPES:
                out.append(("ERROR", f"{path}: index field {name} is {ftype}; LongTextArea and URL fields can't be in the index"))
            if text(ifield, "sortDirection").upper() not in {"ASC", "DESC"}:
                out.append(("ERROR", f"{path}: index field {name} needs sortDirection ASC or DESC"))
            if ftype in FIXED_TEXT_LENGTH:
                total_text += FIXED_TEXT_LENGTH[ftype]
            elif ftype == "Text":
                length = text(field, "length")
                total_text += int(length) if length.isdigit() else 0
        if total_text > INDEX_TEXT_LIMIT:
            out.append(("ERROR", f"{path}: text fields in index total {total_text} characters; the limit is {INDEX_TEXT_LIMIT} unless Support raises it"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Check big object definitions, field history, and archive Apex (data-archival-strategies skill).")
    ap.add_argument("--manifest-dir", default=".", help="Root of the metadata tree")
    ap.add_argument("--strict", action="store_true", help="Treat WARN as failure")
    args = ap.parse_args()

    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)

    objects = sorted(list(root.rglob("*.object")) + list(root.rglob("*.object-meta.xml")))
    apex = sorted(root.rglob("*.cls"))
    if not objects and not apex:
        print(f"WARN: no object metadata or Apex under {root}; nothing to check")
        return 0

    findings: list[tuple[str, str]] = []
    for path in objects:
        fields, indexes = collect(path)
        if object_name(path).endswith("__b"):
            findings.extend(check_big_object(path, fields, indexes))
        tracked = [text(f, "fullName") for f in fields if text(f, "trackHistory").lower() == "true"]
        if len(tracked) > HISTORY_FIELD_LIMIT:
            findings.append(("WARN", f"{path}: {len(tracked)} fields track history; without Field Audit Trail the limit is {HISTORY_FIELD_LIMIT} per object"))
    for path in apex:
        src = path.read_text(encoding="utf-8", errors="replace")
        for m in BARE_INSERT_RE.finditer(src):
            line = src.count("\n", 0, m.start()) + 1
            findings.append(("ERROR", f"{path}:{line}: Database.insertImmediate result is discarded; it returns SaveResults instead of throwing, so failures go unnoticed"))
        m = ASYNC_QUERY_RE.search(src)
        if m is not None:
            line = src.count("\n", 0, m.start()) + 1
            findings.append(("WARN", f"{path}:{line}: calls async-queries; the Big Objects guide lists SOQL, Bulk, Chatter, and SOAP APIs as the supported ones"))

    errors = sum(1 for s, _ in findings if s == "ERROR")
    warns = len(findings) - errors
    for sev, msg in findings:
        print(f"{sev}: {msg}")
    print(f"Scanned {len(objects)} object file(s), {len(apex)} Apex file(s): {errors} ERROR, {warns} WARN")
    if errors or (args.strict and warns):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
