#!/usr/bin/env python3
"""Checker for the soql-query-optimization skill.

Scans Apex source (.cls, .trigger) for SOQL shapes that the Large Data Volumes
guide and the Apex Developer Guide say keep the optimizer from using an index.
Comments are stripped before scanning, so commented-out SOQL is ignored.

Severity:
  ERROR  in a .trigger file, a query whose WHERE clause has no positive filter
         (every predicate is negative or compares with an empty value), or a
         query with neither WHERE nor LIMIT. The Apex guide says queries must be
         selective "particularly for queries inside triggers".
  WARN   anywhere: leading-wildcard LIKE; null comparison on a custom field
         (index tables exclude nulls by default); OR in a WHERE clause (every OR
         field must be indexed); negative operators (!=, NOT IN, NOT LIKE);
         FIELDS(ALL) or FIELDS(CUSTOM).

Exit codes: 0 clean or WARN only; 1 on any ERROR, on a missing directory, or on
WARN when --strict is set. An empty directory prints a WARN and exits 0.

Stdlib only.

Usage:
    python3 check_soql_query_optimization.py --manifest-dir force-app/main/default
    python3 check_soql_query_optimization.py --manifest-dir force-app --strict
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

INLINE_SOQL_RE = re.compile(r"\[\s*(SELECT\b.*?)\]", re.IGNORECASE | re.DOTALL)
STRING_SOQL_RE = re.compile(r"'(\s*SELECT\b(?:[^'\\]|\\.)*)'", re.IGNORECASE | re.DOTALL)
WHERE_RE = re.compile(
    r"\bWHERE\b(.*?)(?=\bORDER\s+BY\b|\bGROUP\s+BY\b|\bLIMIT\b|\bOFFSET\b|\bFOR\s+(?:UPDATE|VIEW|REFERENCE)\b|\bALL\s+ROWS\b|\bWITH\b|$)",
    re.IGNORECASE | re.DOTALL,
)
LIMIT_RE = re.compile(r"\bLIMIT\b", re.IGNORECASE)
SPLIT_RE = re.compile(r"\s+(?:AND|OR)\s+", re.IGNORECASE)
OR_RE = re.compile(r"\s+OR\s+", re.IGNORECASE)
NEGATIVE_RE = re.compile(r"!=|<>|\bNOT\s+IN\b|\bNOT\s+LIKE\b|^\s*\(?\s*NOT\b", re.IGNORECASE)
EMPTY_RE = re.compile(r"(?:!=|=)\s*''")
LEADING_WILDCARD_RE = re.compile(r"\bLIKE\s+'%", re.IGNORECASE)
NULL_CUSTOM_RE = re.compile(r"\b\w+__c\s*(?:!=|=)\s*null\b", re.IGNORECASE)
FIELDS_RE = re.compile(r"\bFIELDS\s*\(\s*(?:ALL|CUSTOM)\s*\)", re.IGNORECASE)


def strip_comments(src: str) -> str:
    """Blank out // and /* */ comments, keeping string literals and line numbers."""
    out: list[str] = []
    i, n = 0, len(src)
    in_str = False
    while i < n:
        c = src[i]
        if in_str:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(src[i + 1])
                i += 2
                continue
            if c == "'":
                in_str = False
            i += 1
            continue
        if c == "'":
            in_str = True
            out.append(c)
            i += 1
            continue
        if src.startswith("//", i):
            j = src.find("\n", i)
            j = n if j == -1 else j
            i = j
            continue
        if src.startswith("/*", i):
            j = src.find("*/", i + 2)
            j = n if j == -1 else j + 2
            out.append("".join("\n" if ch == "\n" else " " for ch in src[i:j]))
            i = j
            continue
        out.append(c)
        i += 1
    return "".join(out)


def queries(src: str):
    """Yield (offset, soql) for inline [SELECT ...] blocks and 'SELECT ...' strings."""
    for m in INLINE_SOQL_RE.finditer(src):
        yield m.start(), m.group(1)
    for m in STRING_SOQL_RE.finditer(src):
        yield m.start(), m.group(1)


def check_query(soql: str, in_trigger: bool) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    where_m = WHERE_RE.search(soql)
    where = where_m.group(1) if where_m is not None else ""
    if in_trigger and where_m is None and LIMIT_RE.search(soql) is None:
        findings.append(("ERROR", "query in trigger context has no WHERE and no LIMIT; it reads the whole object"))
    if where:
        preds = [p for p in SPLIT_RE.split(where) if p.strip()]
        weak = [p for p in preds if NEGATIVE_RE.search(p) is not None or EMPTY_RE.search(p) is not None]
        if in_trigger and preds and len(weak) == len(preds):
            findings.append(("ERROR", "query in trigger context has no positive filter (only negative or empty-value comparisons), so no index can drive it"))
        elif weak:
            findings.append(("WARN", "negative operator or empty-value comparison; a custom index is typically not used for these"))
        if OR_RE.search(where) is not None:
            findings.append(("WARN", "OR in WHERE; every field in the OR must be indexed and each branch under its threshold"))
        if NULL_CUSTOM_RE.search(where) is not None:
            findings.append(("WARN", "null comparison on a custom field; index tables exclude null rows unless Support built a null-inclusive index"))
    if LEADING_WILDCARD_RE.search(soql) is not None:
        findings.append(("WARN", "leading-wildcard LIKE; capture the plan (?explain=) or use SOSL for keyword search"))
    if FIELDS_RE.search(soql) is not None:
        findings.append(("WARN", "FIELDS(ALL)/FIELDS(CUSTOM); select only the fields the transaction reads"))
    return findings


def scan_file(path: Path) -> list[tuple[str, str]]:
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [("ERROR", f"{path}: cannot read file ({exc})")]
    src = strip_comments(raw)
    in_trigger = path.suffix == ".trigger"
    results: list[tuple[str, str]] = []
    for offset, soql in queries(src):
        line = src.count("\n", 0, offset) + 1
        for sev, msg in check_query(soql, in_trigger):
            results.append((sev, f"{path}:{line}: {msg}"))
    return results


def main() -> int:
    ap = argparse.ArgumentParser(description="Flag SOQL that cannot use an index (soql-query-optimization skill).")
    ap.add_argument("--manifest-dir", default=".", help="Root to scan for .cls and .trigger files")
    ap.add_argument("--strict", action="store_true", help="Treat WARN as failure")
    args = ap.parse_args()

    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)

    files = sorted(list(root.rglob("*.cls")) + list(root.rglob("*.trigger")))
    if not files:
        print(f"WARN: no .cls or .trigger files under {root}; nothing to check")
        return 0

    errors = warns = 0
    for f in files:
        for sev, msg in scan_file(f):
            print(f"{sev}: {msg}")
            if sev == "ERROR":
                errors += 1
            else:
                warns += 1

    print(f"Scanned {len(files)} file(s): {errors} ERROR, {warns} WARN")
    if errors or (args.strict and warns):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
