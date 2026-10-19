#!/usr/bin/env python3
"""Pre-review scan of Apex source for the code-review-checklist-salesforce skill.

Walks a source directory (an SFDX package directory such as force-app, or a
Metadata API retrieve) and reports the mechanical findings a reviewer should
not have to hunt for by eye. Comments and string literals are blanked before
any rule runs, so a commented-out query never raises a finding.

ERROR (blocking, exit 1):
  - WITH SECURITY_ENFORCED in a class or trigger whose -meta.xml apiVersion is
    67.0 or later (the clause is not allowed from API 67.0).

WARN (review prompt, exit 0 unless --strict):
  - WITH SECURITY_ENFORCED on a pre-67.0 file (migrate to WITH USER_MODE).
  - WITH SECURITY_ENFORCED inside a string literal (dynamic SOQL), any version.
  - a non-test class with SOQL/DML but no with/without/inherited sharing keyword
    (its default flips at 67.0: with sharing; before that it depends on callers).
  - SOQL or DML inside a for-loop body.
  - SOQL or DML written directly in a trigger body (logic belongs in a handler).
  - @IsTest(SeeAllData=true).
  - a test class with no Assert.* / System.assert* call.
  - a .cls/.trigger with no -meta.xml or no apiVersion.

Stdlib only.

Usage:
    python3 check_code_review_checklist_salesforce.py --manifest-dir force-app
    python3 check_code_review_checklist_salesforce.py --manifest-dir force-app --strict
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{http://soap.sforce.com/2006/04/metadata}"
SOQL_RE = re.compile(r"\[\s*select\b", re.I)
DML_RE = re.compile(r"(?<![\w.])(insert|update|upsert|delete|undelete|merge)\s+(as\s+(user|system)\s+)?(new\b|\[|[a-z_][\w.]*\s*;)", re.I)
DB_RE = re.compile(r"\bDatabase\.(insert|update|upsert|delete|undelete|merge|query)\s*\(", re.I)
SHARING_RE = re.compile(r"\b(with|without|inherited)\s+sharing\b", re.I)
SEC_ENF_RE = re.compile(r"\bWITH\s+SECURITY_ENFORCED\b", re.I)
SEEALL_RE = re.compile(r"seealldata\s*=\s*true", re.I)
ISTEST_RE = re.compile(r"@istest\b", re.I)
ASSERT_RE = re.compile(r"\b(Assert\.\w+|System\.assert\w*)\s*\(", re.I)
FOR_RE = re.compile(r"\bfor\s*\(", re.I)


def _child(elem: ET.Element, tag: str) -> ET.Element | None:
    """Return a namespaced or bare child; never `find(a) or find(b)` (leaf elements are falsy)."""
    found = elem.find(NS + tag)
    if found is not None:
        return found
    return elem.find(tag)


def strip_code(src: str, keep_strings: bool = False) -> str:
    """Blank comments (and string literals unless keep_strings) in one pass, keeping newlines and length."""
    out = []
    i, n = 0, len(src)
    while i < n:
        if src.startswith("//", i):
            j = src.find("\n", i)
            j = n if j < 0 else j
            out.append(" " * (j - i))
            i = j
        elif src.startswith("/*", i):
            j = src.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append("".join(c if c == "\n" else " " for c in src[i:j]))
            i = j
        elif src[i] == "'" and not keep_strings:
            j = i + 1
            while j < n and src[j] != "'":
                j += 2 if src[j] == "\\" else 1
            j = min(j + 1, n)
            out.append("'" + " " * max(j - i - 2, 0) + ("'" if j - i >= 2 else ""))
            i = j
        elif src[i] == "'":
            j = i + 1
            while j < n and src[j] != "'":
                j += 2 if src[j] == "\\" else 1
            j = min(j + 1, n)
            out.append(src[i:j])
            i = j
        else:
            out.append(src[i])
            i += 1
    return "".join(out)


def api_version(source: Path) -> float | None:
    meta = source.with_name(source.name + "-meta.xml")
    if not meta.is_file():
        return None
    try:
        root = ET.parse(meta).getroot()
    except ET.ParseError:
        return None
    node = _child(root, "apiVersion")
    if node is None or not (node.text or "").strip():
        return None
    try:
        return float(node.text.strip())
    except ValueError:
        return None


def _block_end(code: str, start: int) -> int:
    """Index just past the statement or brace block that starts at `start`."""
    i = start
    while i < len(code) and code[i].isspace():
        i += 1
    if i < len(code) and code[i] == "{":
        depth = 0
        for j in range(i, len(code)):
            if code[j] == "{":
                depth += 1
            elif code[j] == "}":
                depth -= 1
                if depth == 0:
                    return j + 1
        return len(code)
    j = code.find(";", i)
    return len(code) if j < 0 else j + 1


def loop_bodies(code: str) -> list[tuple[int, str]]:
    bodies = []
    for m in FOR_RE.finditer(code):
        depth, j = 0, m.end() - 1
        while j < len(code):
            if code[j] == "(":
                depth += 1
            elif code[j] == ")":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        # only the body is scanned: `for (X x : [SELECT ...])` runs its query once
        end = _block_end(code, j + 1)
        bodies.append((code.count("\n", 0, m.start()) + 1, code[j + 1:end]))
    return bodies


def scan_file(path: Path, findings: list[tuple[str, str]]) -> None:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    code = strip_code(raw)
    ver = api_version(path)
    is_trigger = path.suffix == ".trigger"
    is_test = bool(ISTEST_RE.search(code))
    has_db = bool(SOQL_RE.search(code) or DML_RE.search(code) or DB_RE.search(code))

    if ver is None:
        findings.append(("WARN", f"{path}: no -meta.xml apiVersion found; the access-mode default cannot be determined"))
    if SEC_ENF_RE.search(code):
        if ver is not None and ver >= 67.0:
            findings.append(("ERROR", f"{path}: WITH SECURITY_ENFORCED on an API {ver} file; not allowed from 67.0, use WITH USER_MODE"))
        else:
            findings.append(("WARN", f"{path}: WITH SECURITY_ENFORCED (API {ver}); migrate to WITH USER_MODE before the next version bump"))
    elif SEC_ENF_RE.search(strip_code(raw, keep_strings=True)):
        # dynamic SOQL: the clause sits inside a string literal passed to Database.query
        findings.append(("WARN", f"{path}: WITH SECURITY_ENFORCED inside a string literal (dynamic SOQL, API {ver}); the 67.0 removal covers SOQL in Apex, use WITH USER_MODE / AccessLevel.USER_MODE"))
    if not is_trigger and not is_test and has_db and not SHARING_RE.search(code):
        findings.append(("WARN", f"{path}: database operations but no sharing keyword; default is with sharing at 67.0+, caller-dependent before (API {ver})"))
    if is_trigger and has_db:
        findings.append(("WARN", f"{path}: SOQL/DML in the trigger body; move logic to a handler class"))
    for line, body in loop_bodies(code):
        if SOQL_RE.search(body) or DML_RE.search(body) or DB_RE.search(body):
            findings.append(("WARN", f"{path}:{line}: SOQL or DML inside a for-loop body; collect ids and query/DML once"))
    if SEEALL_RE.search(code):
        findings.append(("WARN", f"{path}: @IsTest(SeeAllData=true); prefer created test data or Test.getStandardPricebookId()"))
    if is_test and not ASSERT_RE.search(code):
        findings.append(("WARN", f"{path}: test class without any Assert.* or System.assert* call"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan Apex source for code-review checklist findings.")
    parser.add_argument("--manifest-dir", required=True, type=Path,
                        help="Source directory to scan (e.g. force-app or a retrieve's unpackaged/).")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on WARN as well as ERROR.")
    args = parser.parse_args(argv)

    root = args.manifest_dir
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)
    sources = sorted(p for p in root.rglob("*") if p.is_file() and p.suffix in (".cls", ".trigger"))
    if not sources:
        print(f"WARN: no .cls or .trigger files under {root}; nothing to review")
        return 0

    findings: list[tuple[str, str]] = []
    for src in sources:
        scan_file(src, findings)
    for level, msg in findings:
        print(f"{level}: {msg}")
    errors = sum(1 for lvl, _ in findings if lvl == "ERROR")
    warns = len(findings) - errors
    print(f"Scanned {len(sources)} file(s): {errors} error(s), {warns} warning(s).")
    if errors or (args.strict and warns):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
