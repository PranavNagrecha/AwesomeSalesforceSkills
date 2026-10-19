#!/usr/bin/env python3
"""Checker for the sosl-search-result-limits skill.

Scans Apex (.cls, .trigger) and custom object metadata (*.object-meta.xml) for the
silent result limits documented in the SOQL and SOSL Reference ("SOSL Limits on
Search Results", "RETURNING FieldSpec", "LIMIT n") and the Metadata API guide
(CustomObject.enableSearch). Comments are stripped before scanning Apex.

Severity:
  ERROR  a RETURNING object clause with WHERE/ORDER BY/LIMIT/OFFSET but no field
         list (the reference calls this improper syntax); OFFSET in a multi-object
         RETURNING (OFFSET is single-object only); a SOSL search that returns a
         custom object whose metadata in the scanned tree has enableSearch=false;
         an object-meta.xml file that does not parse.
  WARN   single-object RETURNING with no WHERE and no ORDER BY (capped at 250;
         a LIMIT alone cannot raise it); nine or more objects (each capped below
         250 by min(2000/n, 250)); a LIMIT above 2,000; Search.query() in a file
         with no length() check on the search term; a custom object with
         enableSearch=false.

Exit codes: 0 clean or WARN only; 1 on ERROR, on a missing directory, or on WARN
with --strict. An empty directory prints a WARN and exits 0. Stdlib only.

Usage:
    python3 check_sosl_search_result_limits.py --manifest-dir force-app/main/default [--strict]
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{http://soap.sforce.com/2006/04/metadata}"
STATIC_SOSL_RE = re.compile(r"\[\s*FIND\b[^\[\]]*\]", re.IGNORECASE | re.DOTALL)
STRING_SOSL_RE = re.compile(r"'\s*FIND\s*\{(?:[^'\\]|\\.)*'", re.IGNORECASE | re.DOTALL)
RETURNING_RE = re.compile(r"\bRETURNING\b", re.IGNORECASE)
RAISER_RE = re.compile(r"\bWHERE\b|\bORDER\s+BY\b", re.IGNORECASE)
KEYWORD_FIRST_RE = re.compile(r"^\s*(WHERE|ORDER\s+BY|LIMIT|OFFSET|USING)\b", re.IGNORECASE)
OFFSET_RE = re.compile(r"\bOFFSET\b", re.IGNORECASE)
LIMIT_N_RE = re.compile(r"\bLIMIT\s+(\d+)", re.IGNORECASE)
DYNAMIC_RE = re.compile(r"\bSearch\.query\s*\(", re.IGNORECASE)
LENGTH_RE = re.compile(r"\.length\s*\(\s*\)")
STOP_WORDS = {"LIMIT", "WITH", "UPDATE", "IN", "FIND"}


def strip_comments(src: str) -> str:
    out: list[str] = []
    i, n, in_str = 0, len(src), False
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
            i = n if j == -1 else j
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


def child_text(elem: ET.Element, tag: str) -> str | None:
    node = elem.find(NS + tag)
    if node is None:
        node = elem.find(tag)
    return node.text.strip() if node is not None and node.text is not None else None


def unsearchable_objects(root: Path, errors: list[tuple[str, str]]) -> dict[str, Path]:
    found: dict[str, Path] = {}
    for f in root.rglob("*.object-meta.xml"):
        name = f.name[: -len(".object-meta.xml")]
        if not name.endswith("__c"):
            continue
        try:
            tree = ET.parse(f)
        except ET.ParseError as exc:
            errors.append(("ERROR", f"{f}: cannot parse ({exc}); enableSearch not checked"))
            continue
        if child_text(tree.getroot(), "enableSearch") == "false":
            found[name.lower()] = f
    return found


def returning_clauses(sosl: str) -> list[tuple[str, str | None]]:
    """Return [(object, inner-or-None)] for the RETURNING clause, balancing parentheses."""
    m = RETURNING_RE.search(sosl)
    if m is None:
        return []
    s = sosl[m.end():]
    i, n = 0, len(s)
    clauses: list[tuple[str, str | None]] = []
    while i < n:
        while i < n and s[i] in " \t\r\n,":
            i += 1
        nm = re.match(r"[A-Za-z_]\w*", s[i:])
        if nm is None or nm.group(0).upper() in STOP_WORDS:
            break
        name = nm.group(0)
        i += len(name)
        while i < n and s[i] in " \t\r\n":
            i += 1
        inner = None
        if i < n and s[i] == "(":
            depth, j, in_str = 0, i, False
            while j < n:
                ch = s[j]
                if in_str:
                    if ch == "\\":
                        j += 2
                        continue
                    if ch == "'":
                        in_str = False
                elif ch == "'":
                    in_str = True
                elif ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            inner = s[i + 1 : j]
            i = j + 1
        clauses.append((name, inner))
        while i < n and s[i] in " \t\r\n":
            i += 1
        if i < n and s[i] != ",":
            break
    return clauses


def check_sosl(sosl: str, where: str, hidden: dict[str, Path]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    clauses = returning_clauses(sosl)
    n = len(clauses)
    for name, inner in clauses:
        if inner is not None and KEYWORD_FIRST_RE.search(inner) is not None:
            out.append(("ERROR", f"{where}: RETURNING {name}(...) has a clause but no field list; the reference calls this improper syntax"))
        if inner is not None and OFFSET_RE.search(inner) is not None and n > 1:
            out.append(("ERROR", f"{where}: OFFSET in a {n}-object RETURNING; OFFSET can be used only when querying a single object"))
        if name.lower() in hidden:
            out.append(("ERROR", f"{where}: searches {name}, whose metadata ({hidden[name.lower()]}) has enableSearch=false, so SOSL cannot find its records"))
    if n == 1:
        name, inner = clauses[0]
        if inner is None or RAISER_RE.search(inner) is None:
            extra = " (a LIMIT alone cannot raise it)" if inner is not None and LIMIT_N_RE.search(inner) is not None else ""
            out.append(("WARN", f"{where}: single-object RETURNING {name} has no WHERE or ORDER BY, so it is capped at 250 records{extra}"))
    elif n >= 9:
        out.append(("WARN", f"{where}: {n} objects in RETURNING; each is capped at min(2000/{n}, 250) = {2000 // n}"))
    for lim in LIMIT_N_RE.findall(sosl):
        if int(lim) > 2000:
            out.append(("WARN", f"{where}: LIMIT {lim} exceeds 2,000; SOSL returns at most 2,000 and LIMIT cannot raise that"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Flag SOSL result-limit risks (sosl-search-result-limits skill).")
    ap.add_argument("--manifest-dir", default=".", help="Root to scan for Apex and object metadata")
    ap.add_argument("--strict", action="store_true", help="Treat WARN as failure")
    args = ap.parse_args()

    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)

    apex = sorted(list(root.rglob("*.cls")) + list(root.rglob("*.trigger")))
    objects = list(root.rglob("*.object-meta.xml"))
    if not apex and not objects:
        print(f"WARN: no Apex or object metadata under {root}; nothing to check")
        return 0

    findings: list[tuple[str, str]] = []
    hidden = unsearchable_objects(root, findings)
    for name, path in sorted(hidden.items()):
        findings.append(("WARN", f"{path}: {name} has enableSearch=false; its records cannot be found by SOSL or search"))
    for f in apex:
        src = strip_comments(f.read_text(encoding="utf-8", errors="replace"))
        for rx in (STATIC_SOSL_RE, STRING_SOSL_RE):
            for m in rx.finditer(src):
                line = src.count("\n", 0, m.start()) + 1
                sosl = m.group(0)
                if rx is STRING_SOSL_RE:
                    sosl = sosl[1:-1].replace("\\'", "'")
                findings.extend(check_sosl(sosl, f"{f}:{line}", hidden))
        dyn = DYNAMIC_RE.search(src)
        if dyn is not None and LENGTH_RE.search(src) is None:
            line = src.count("\n", 0, dyn.start()) + 1
            findings.append(("WARN", f"{f}:{line}: Search.query() with no length() check; terms over 4,000 characters turn AND into OR, over 10,000 return no rows"))

    errors = sum(1 for s, _ in findings if s == "ERROR")
    warns = len(findings) - errors
    for sev, msg in findings:
        print(f"{sev}: {msg}")
    print(f"Scanned {len(apex)} Apex file(s), {len(objects)} object file(s): {errors} ERROR, {warns} WARN")
    if errors or (args.strict and warns):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
