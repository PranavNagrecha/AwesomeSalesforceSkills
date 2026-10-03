#!/usr/bin/env python3
"""Check Apex and metadata that use Salesforce Connect external objects (__x).

Stdlib only. Rules are grounded on the SOQL and SOSL Reference v67.0 (SOQL Object
Limits and Limitations: External objects), the Apex Developer Guide v67.0 (Salesforce
Connect chapter), and the Metadata API Developer Guide v67.0 (ExternalDataSource).

Correction (2026-10-03): the previous version reported any COUNT( on an external object
as an unsupported aggregate and flagged ALL ROWS as a review item. COUNT() is supported
(OData adapters need Request Row Counts), and no fetched guide documents ALL ROWS for
external objects, so that rule was dropped. The documented unsupported clauses are now
reported precisely.

Rules
  SC-TRIG-01     ERROR  Apex trigger on an __x object (triggers are not available; use the
                        OData 4.0 change event object instead).
  SC-SOQL-01     ERROR  SOQL on an __x object uses an unsupported function or clause: AVG, SUM,
                        MIN, MAX, COUNT(field), GROUP BY, HAVING, LIKE, INCLUDES, EXCLUDES,
                        toLabel, TYPEOF, FOR VIEW, FOR REFERENCE, or WITH.
  SC-SOQL-02     WARN   COUNT() on an __x object; OData adapters need Request Row Counts.
  SC-DML-01      ERROR  Plain insert/update/upsert/delete on an __x record; Apex must use
                        Database.insertAsync/updateAsync/deleteAsync or the Immediate variants.
  SC-TEST-01     WARN   Static SOQL on an __x object in a test class; custom adapter tests fail
                        with static SOQL; use dynamic SOQL or Test.createSoqlStub.
  SC-LOOP-01     WARN   SOQL on an __x object inside a loop; every query is a round trip.
  SC-ADAPTER-01  ERROR  DML inside a DataSource.Connection class; not allowed in custom adapters.
  SC-DS-01       WARN   OData data source with Request Row Counts (inlineCountEnabled) off.

Usage
  python3 check_salesforce_connect_external_objects.py --manifest-dir force-app/main/default [--strict]
  python3 check_salesforce_connect_external_objects.py --self-test

Exit codes: 0 clean (WARN allowed unless --strict); 1 on ERROR, a missing folder, or WARN with --strict.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

TRIGGER_RE = re.compile(r"\btrigger\s+\w+\s+on\s+\w+__x\b", re.IGNORECASE)
FROM_X_RE = re.compile(r"\bFROM\s+(\w+__x)\b", re.IGNORECASE)
UNSUPPORTED = [
    (re.compile(r"\b(AVG|SUM|MIN|MAX)\s*\(", re.I), "aggregate function"),
    (re.compile(r"\bCOUNT\s*\(\s*\w+", re.I), "COUNT(field)"),
    (re.compile(r"\bGROUP\s+BY\b", re.I), "GROUP BY"),
    (re.compile(r"\bHAVING\b", re.I), "HAVING"),
    (re.compile(r"\bLIKE\b", re.I), "LIKE"),
    (re.compile(r"\b(INCLUDES|EXCLUDES)\s*\(", re.I), "INCLUDES/EXCLUDES"),
    (re.compile(r"\btoLabel\s*\(", re.I), "toLabel()"),
    (re.compile(r"\bTYPEOF\b", re.I), "TYPEOF"),
    (re.compile(r"\bFOR\s+(VIEW|REFERENCE)\b", re.I), "FOR VIEW/REFERENCE"),
    (re.compile(r"\bWITH\s+\w+", re.I), "WITH clause"),
]
COUNT_EMPTY_RE = re.compile(r"\bCOUNT\s*\(\s*\)", re.I)
LOOP_RE = re.compile(r"\b(for|while)\s*\(")


def strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def soql_statements(text: str) -> list[tuple[int, str]]:
    """Return (line, soql text) for bracketed SOQL and SELECT string literals."""
    found: list[tuple[int, str]] = []
    for m in re.finditer(r"\[\s*(SELECT\b.*?)\]", text, re.S | re.I):
        found.append((text.count("\n", 0, m.start()) + 1, m.group(1)))
    for stmt_match in re.finditer(r"Database\.\w+\s*\((.*?)\)\s*;", text, re.S):
        literals = re.findall(r"'((?:\\'|[^'])*)'", stmt_match.group(1))
        joined = " ".join(literals)
        if re.search(r"\bSELECT\b", joined, re.I):
            found.append((text.count("\n", 0, stmt_match.start()) + 1, joined))
    return found


def x_variables(text: str) -> set[str]:
    names = set(re.findall(r"\b\w+__x\s+(\w+)\s*[=;]", text))
    names |= set(re.findall(r"List\s*<\s*\w+__x\s*>\s+(\w+)\s*[=;]", text))
    return names


def audit_apex(path: Path, raw: str) -> list[str]:
    findings: list[str] = []
    text = strip_comments(raw)
    if TRIGGER_RE.search(text):
        findings.append(f"ERROR SC-TRIG-01 {path}: trigger on an external object; triggers are not available for __x "
                        f"(use the OData 4.0 change event object)")
    is_test = re.search(r"@IsTest", text, re.I) is not None
    for line, soql in soql_statements(text):
        main_from = FROM_X_RE.search(re.sub(r"\(\s*SELECT\b.*?\)", " ", soql, flags=re.S | re.I))
        if not main_from:
            continue
        for rx, label in UNSUPPORTED:
            if rx.search(soql):
                findings.append(f"ERROR SC-SOQL-01 {path}:{line}: {label} on {main_from.group(1)} is not supported for external objects")
                break
        if COUNT_EMPTY_RE.search(soql):
            findings.append(f"WARN SC-SOQL-02 {path}:{line}: COUNT() on {main_from.group(1)}; OData adapters need Request Row Counts enabled")
    if is_test and re.search(r"\[\s*SELECT\b[^\]]*\bFROM\s+\w+__x\b", text, re.I):
        findings.append(f"WARN SC-TEST-01 {path}: static SOQL on an external object in a test; use dynamic SOQL or Test.createSoqlStub")
    xvars = x_variables(text)
    dml_new = re.search(r"\b(insert|update|upsert|delete)\s+new\s+\w+__x\s*\(", text, re.I)
    dml_var = any(re.search(rf"\b(insert|update|upsert|delete)\s+{re.escape(v)}\s*;", text, re.I) for v in xvars)
    if dml_new or dml_var:
        findings.append(f"ERROR SC-DML-01 {path}: plain DML on an external object; use Database.insertAsync/updateAsync/"
                        f"deleteAsync or the Immediate variants")
    depth = 0
    in_loop_depth = []
    for number, line in enumerate(text.splitlines(), start=1):
        if LOOP_RE.search(line):
            in_loop_depth.append(depth)
        depth += line.count("{") - line.count("}")
        while in_loop_depth and depth <= in_loop_depth[-1] and "}" in line:
            in_loop_depth.pop()
        if in_loop_depth and re.search(r"\bFROM\s+\w+__x\b", line, re.I):
            findings.append(f"WARN SC-LOOP-01 {path}:{number}: external object query inside a loop; each query is a round trip")
            break
    if re.search(r"extends\s+DataSource\.Connection\b", text) and re.search(r"\b(insert|update|upsert|delete)\s+\w", text):
        findings.append(f"ERROR SC-ADAPTER-01 {path}: DML inside a DataSource.Connection class; DML is not allowed in custom adapter code")
    return findings


def audit_datasource(path: Path, raw: str) -> list[str]:
    if not re.search(r"<type>\s*OData4?\s*</type>", raw):
        return []
    if re.search(r'"inlineCountEnabled"\s*:\s*"false"', raw) or '"inlineCountEnabled"' not in raw:
        return [f"WARN SC-DS-01 {path}: OData data source without Request Row Counts; COUNT() and batch Apex query locators need it"]
    return []


def scan(root: Path) -> tuple[int, list[str]]:
    if not root.exists():
        return 0, [f"ERROR SC-DIR-01 {root}: folder not found"]
    findings: list[str] = []
    count = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        name = path.name
        if name.endswith((".cls", ".trigger")):
            count += 1
            findings.extend(audit_apex(path, path.read_text(encoding="utf-8", errors="ignore")))
        elif name.endswith(".dataSource-meta.xml") or name.endswith(".dataSource"):
            count += 1
            findings.extend(audit_datasource(path, path.read_text(encoding="utf-8", errors="ignore")))
    return count, findings


def self_test() -> int:
    here = Path(__file__).resolve().parent / "fixtures"
    _, good = scan(here / "good")
    _, bad = scan(here / "bad")
    expected = {"SC-TRIG-01", "SC-SOQL-01", "SC-SOQL-02", "SC-DML-01", "SC-TEST-01", "SC-LOOP-01", "SC-ADAPTER-01", "SC-DS-01"}
    seen = {f.split()[1] for f in bad}
    print(f"good fixtures: {len(good)} finding(s) (expected 0)")
    for f in good:
        print(f"  unexpected: {f}")
    print(f"bad fixtures: rules seen {sorted(seen)}; missing {sorted(expected - seen)}")
    return 0 if not good and expected <= seen else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Check Apex and metadata that use Salesforce Connect external objects.")
    ap.add_argument("--manifest-dir", default=".", help="Project folder to scan (default: current directory).")
    ap.add_argument("--strict", action="store_true", help="Exit 1 on WARN as well as ERROR.")
    ap.add_argument("--self-test", action="store_true", help="Run the bundled fixtures and exit.")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    count, findings = scan(Path(args.manifest_dir))
    for f in findings:
        print(f)
    errors = [f for f in findings if f.startswith("ERROR")]
    warns = [f for f in findings if f.startswith("WARN")]
    print(f"Scanned {count} file(s): {len(errors)} error(s), {len(warns)} warning(s).")
    return 1 if errors or (args.strict and warns) else 0


if __name__ == "__main__":
    sys.exit(main())
