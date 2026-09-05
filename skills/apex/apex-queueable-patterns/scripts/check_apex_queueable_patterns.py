#!/usr/bin/env python3
"""check_apex_queueable_patterns.py — static audit of Queueable Apex source.

Scans a source tree of .cls / .trigger files and reports the Queueable-specific
mistakes that compile cleanly and fail (or silently misbehave) at runtime.

Rules
-----
QP001  ERROR     `System.enqueueJob` inside a `for` / `while` loop.
                 50 enqueues per synchronous transaction, 1 per asynchronous one
                 (Apex Developer Guide v67.0, Queueable Apex Limits).
QP002  WARN      A Queueable `execute(QueueableContext)` body calls
                 `System.enqueueJob` more than once with no guard between them.
                 Only one child job may exist per parent.
QP003  WARN      A Queueable chains with neither an `AsyncOptions` depth cap nor a
                 `Test.isRunningTest()` guard — no depth limit is enforced outside
                 Developer and Trial editions.
QP004  ERROR     Callout after DML in the same Queueable `execute()` body
                 (heuristic: class implements `Database.AllowsCallouts`, and an
                 `insert` / `update` / `upsert` / `delete` statement precedes an
                 `HttpRequest` / `Http().send` / `WebServiceCallout.invoke`).
                 Callouts are not allowed once the transaction has pending work.
QP005  ADVISORY  A Queueable holds a `List<SObject>` / `List<Account>`-style member
                 populated from a SOQL query in the constructor — serialized state
                 size, and a snapshot that can already be stale when the job runs.
QP006  ERROR     A test method calls `System.enqueueJob` outside a
                 `Test.startTest()` / `Test.stopTest()` block, so the job never runs
                 and the assertions pass vacuously.
QP007  ERROR     An `@future` method declares a non-primitive parameter. Future
                 parameters must be primitives, arrays of primitives, or
                 collections of primitives; sObjects and objects are rejected.

Exit codes
----------
0   no ERROR findings (WARN and ADVISORY may be present), or an empty directory
1   at least one ERROR finding, or --manifest-dir does not exist
    with --strict, WARN findings are promoted to ERROR and also exit 1

Usage
-----
    python3 check_apex_queueable_patterns.py --manifest-dir force-app/main/default/classes
    python3 check_apex_queueable_patterns.py --manifest-dir src/classes --strict
    python3 check_apex_queueable_patterns.py --manifest-dir src/classes --format text

Stdlib only. This script never compiles Apex; every rule is a textual heuristic
and every finding is a prompt to read the code, not a verdict on it.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

APEX_SUFFIXES = {".cls", ".trigger"}

ERROR = "ERROR"
WARN = "WARN"
ADVISORY = "ADVISORY"

# --------------------------------------------------------------------------
# Patterns
# --------------------------------------------------------------------------

QUEUEABLE_RE = re.compile(r"\bimplements\b[^{;]*\bQueueable\b", re.I)
ALLOWS_CALLOUTS_RE = re.compile(r"\bDatabase\.AllowsCallouts\b", re.I)
EXECUTE_QUEUEABLE_RE = re.compile(r"\bvoid\s+execute\s*\(\s*(?:System\.)?QueueableContext\b", re.I)
ENQUEUE_RE = re.compile(r"\bSystem\.enqueueJob\s*\(", re.I)
ASYNC_OPTIONS_RE = re.compile(r"\bAsyncOptions\b|\bMaximumQueueableStackDepth\b", re.I)
IS_RUNNING_TEST_RE = re.compile(r"\b(?:System\.)?Test\.isRunningTest\s*\(", re.I)
LOOP_OPEN_RE = re.compile(r"\b(?:for|while)\s*\(")
DML_RE = re.compile(r"(?:^|[;{}\s])(insert|update|upsert|delete|undelete)\s+(?:as\s+(?:user|system)\s+)?[A-Za-z_\[]", re.I)
DATABASE_DML_RE = re.compile(r"\bDatabase\.(insert|update|upsert|delete|undelete)\s*\(", re.I)
CALLOUT_RE = re.compile(r"\bHttpRequest\b|\bnew\s+Http\s*\(\s*\)|\bWebServiceCallout\.invoke\b|\.send\s*\(", re.I)
SOQL_IN_CTOR_RE = re.compile(r"=\s*\[\s*SELECT\b", re.I)
SOBJECT_LIST_FIELD_RE = re.compile(
    r"^\s*(?:private|public|protected|global)?\s*(?:final\s+)?(?:transient\s+)?"
    r"List\s*<\s*([A-Za-z_][A-Za-z0-9_]*(?:__c)?)\s*>\s+([A-Za-z_][A-Za-z0-9_]*)\s*[;=]",
    re.I,
)
NON_SOBJECT_LIST_TYPES = {
    "id", "string", "integer", "long", "decimal", "double", "boolean", "date",
    "datetime", "time", "blob", "object",
}
FUTURE_RE = re.compile(r"@\s*future\b", re.I)
METHOD_SIG_RE = re.compile(
    r"\b(?:public|private|global|protected)\s+(?:static\s+)?(?:void|[A-Za-z_][\w<>, .]*)\s+"
    r"([A-Za-z_]\w*)\s*\(([^)]*)\)",
)
PRIMITIVE_PARAM_TYPES = {
    "id", "string", "integer", "long", "decimal", "double", "boolean", "date",
    "datetime", "time", "blob",
}
TEST_METHOD_RE = re.compile(r"@\s*IsTest\b|\btestMethod\b", re.I)
START_TEST_RE = re.compile(r"\bTest\.startTest\s*\(", re.I)
STOP_TEST_RE = re.compile(r"\bTest\.stopTest\s*\(", re.I)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def strip_noise(text: str) -> str:
    """Blank out string literals and comments so keywords inside them do not match.

    Single left-to-right pass, so a quote inside a comment cannot open a string
    and a `/*` inside a string cannot open a comment. Newlines are preserved so
    line numbers stay correct.
    """
    out: list[str] = []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch == "'":
            j = i + 1
            while j < n and text[j] != "'":
                j += 2 if text[j] == "\\" else 1
            out.append(" " * (min(j, n - 1) - i + 1))
            i = j + 1
            continue
        if text.startswith("//", i):
            j = text.find("\n", i)
            j = n if j < 0 else j
            out.append(" " * (j - i))
            i = j
            continue
        if text.startswith("/*", i):
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append("".join(c if c == "\n" else " " for c in text[i:j]))
            i = j
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def block_after(lines: list[str], start: int) -> tuple[int, int]:
    """Return (first_line, last_line) of the brace block opening at or after `start`."""
    depth = 0
    started = False
    for i in range(start, len(lines)):
        depth += lines[i].count("{") - lines[i].count("}")
        if not started and "{" in lines[i]:
            started = True
            first = i
        if started and depth <= 0:
            return first, i
    return (start, len(lines) - 1)


def find_execute_blocks(lines: list[str]) -> list[tuple[int, int]]:
    blocks = []
    for idx, line in enumerate(lines):
        if EXECUTE_QUEUEABLE_RE.search(line):
            blocks.append(block_after(lines, idx))
    return blocks


def loop_line_numbers(lines: list[str]) -> set[int]:
    """Line indices that sit inside a for/while body."""
    inside: set[int] = set()
    idx = 0
    while idx < len(lines):
        if LOOP_OPEN_RE.search(lines[idx]):
            first, last = block_after(lines, idx)
            if last > first:
                inside.update(range(first, last + 1))
                idx = last + 1
                continue
        idx += 1
    return inside


def split_params(raw: str) -> list[str]:
    params, depth, buf = [], 0, ""
    for ch in raw:
        if ch == "<":
            depth += 1
        elif ch == ">":
            depth -= 1
        if ch == "," and depth == 0:
            params.append(buf.strip())
            buf = ""
        else:
            buf += ch
    if buf.strip():
        params.append(buf.strip())
    return params


def param_is_primitive(param: str) -> bool:
    param = param.strip()
    if not param:
        return True
    tokens = param.split()
    if len(tokens) < 2:
        return True  # cannot parse; do not accuse
    ptype = " ".join(tokens[:-1]).strip()
    base = ptype.replace(" ", "")
    if base.endswith("[]"):
        base = base[:-2]
    m = re.match(r"^(List|Set)<([^<>]+)>$", base, re.I)
    if m:
        base = m.group(2)
    m = re.match(r"^Map<([^<>,]+),([^<>]+)>$", base, re.I)
    if m:
        return m.group(1).lower() in PRIMITIVE_PARAM_TYPES and m.group(2).lower() in PRIMITIVE_PARAM_TYPES
    return base.lower() in PRIMITIVE_PARAM_TYPES


# --------------------------------------------------------------------------
# Rules
# --------------------------------------------------------------------------

def audit_file(path: Path, rel: str) -> list[dict]:
    findings: list[dict] = []
    try:
        raw = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [{"rule": "QP000", "severity": ERROR, "location": rel,
                 "message": f"could not read file: {exc}"}]

    code = strip_noise(raw)
    lines = code.splitlines()
    is_queueable = bool(QUEUEABLE_RE.search(code))
    is_test = bool(TEST_METHOD_RE.search(code))

    def add(rule: str, severity: str, line_no: int, message: str) -> None:
        findings.append({
            "rule": rule,
            "severity": severity,
            "location": f"{rel}:{line_no}" if line_no else rel,
            "message": message,
        })

    # QP001 — enqueueJob inside a loop
    in_loop = loop_line_numbers(lines)
    for i, line in enumerate(lines):
        if i in in_loop and ENQUEUE_RE.search(line):
            add("QP001", ERROR, i + 1,
                "System.enqueueJob inside a for/while loop. The synchronous ceiling is 50 jobs "
                "per transaction and the asynchronous ceiling is 1, so this fails on real data "
                "volume, not in a small test. Collect the Ids and enqueue one job.")

    execute_blocks = find_execute_blocks(lines) if is_queueable else []

    for first, last in execute_blocks:
        body = lines[first:last + 1]
        body_text = "\n".join(body)
        enqueue_lines = [first + n + 1 for n, ln in enumerate(body) if ENQUEUE_RE.search(ln)]

        # QP002 — more than one enqueue in one execute body, ungated
        if len(enqueue_lines) > 1:
            guarded = bool(IS_RUNNING_TEST_RE.search(body_text)) or "else" in body_text
            if not guarded:
                add("QP002", WARN, enqueue_lines[1],
                    f"{len(enqueue_lines)} System.enqueueJob calls in one execute(QueueableContext) "
                    "body with no branch between them. Only one child job may exist per parent "
                    "queueable job. If these are mutually exclusive branches, make that explicit.")

        # QP003 — chaining with no depth cap and no test guard
        if enqueue_lines and not ASYNC_OPTIONS_RE.search(body_text) \
                and not IS_RUNNING_TEST_RE.search(body_text):
            add("QP003", WARN, enqueue_lines[0],
                "This queueable chains without an AsyncOptions depth cap and without a "
                "Test.isRunningTest() guard. No depth limit is enforced outside Developer and "
                "Trial editions, so a termination bug runs forever in production. Set "
                "AsyncOptions.MaximumQueueableStackDepth, or carry a depth counter in the "
                "constructor.")

        # QP004 — callout after DML inside the same execute body
        if ALLOWS_CALLOUTS_RE.search(code):
            dml_line = None
            for n, ln in enumerate(body):
                if dml_line is None and (DML_RE.search(ln) or DATABASE_DML_RE.search(ln)):
                    dml_line = first + n + 1
                elif dml_line is not None and CALLOUT_RE.search(ln):
                    add("QP004", ERROR, first + n + 1,
                        f"Callout appears after a DML statement on line {dml_line} in the same "
                        "execute(QueueableContext) body. A callout is not allowed once the "
                        "transaction has pending uncommitted work; Database.AllowsCallouts grants "
                        "permission, not ordering. Move every callout before the first DML, or "
                        "split them across two jobs.")
                    break

    # QP005 — SObject list member populated from a query in the constructor
    if is_queueable:
        class_name = path.stem
        sobject_fields: dict[str, int] = {}
        for i, line in enumerate(lines):
            m = SOBJECT_LIST_FIELD_RE.match(line)
            if m and m.group(1).lower() not in NON_SOBJECT_LIST_TYPES:
                sobject_fields[m.group(2)] = i + 1
        if sobject_fields:
            ctor_re = re.compile(r"\b(?:public|private|global|protected)\s+" + re.escape(class_name) + r"\s*\(")
            for i, line in enumerate(lines):
                if not ctor_re.search(line):
                    continue
                first, last = block_after(lines, i)
                for n in range(first, last + 1):
                    if not SOQL_IN_CTOR_RE.search(lines[n]):
                        continue
                    for field, decl_line in sobject_fields.items():
                        if re.search(r"\b" + re.escape(field) + r"\b", lines[n]):
                            add("QP005", ADVISORY, n + 1,
                                f"Member '{field}' (declared line {decl_line}) is an SObject "
                                "collection populated by a query in the constructor. Every field "
                                "is serialized between transactions on each link of the chain, and "
                                "the values are a snapshot that can be stale when the job runs. "
                                "Carry a Set<Id> and re-query inside execute().")

    # QP006 — enqueueJob in a test outside startTest/stopTest
    if is_test:
        starts = [i for i, ln in enumerate(lines) if START_TEST_RE.search(ln)]
        stops = [i for i, ln in enumerate(lines) if STOP_TEST_RE.search(ln)]
        spans = list(zip(starts, stops))
        for i, line in enumerate(lines):
            if not ENQUEUE_RE.search(line):
                continue
            if any(a < i < b for a, b in spans):
                continue
            add("QP006", ERROR, i + 1,
                "System.enqueueJob in a test outside a Test.startTest()/Test.stopTest() block. "
                "Asynchronous work started in a test runs synchronously only after "
                "Test.stopTest(), so the job never executes and the assertions below it pass "
                "vacuously.")

    # QP007 — @future with a non-primitive parameter
    for i, line in enumerate(lines):
        if not FUTURE_RE.search(line):
            continue
        for j in range(i, min(i + 6, len(lines))):
            m = METHOD_SIG_RE.search(lines[j])
            if not m:
                continue
            bad = [p for p in split_params(m.group(2)) if not param_is_primitive(p)]
            if bad:
                add("QP007", ERROR, j + 1,
                    f"@future method '{m.group(1)}' declares non-primitive parameter(s): "
                    f"{'; '.join(bad)}. Future parameters must be primitives, arrays of "
                    "primitives, or collections of primitives — sObjects and objects are "
                    "rejected at compile time. Pass Ids and re-query, or use Queueable, which "
                    "does support non-primitive member state.")
            break

    return findings


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------

def iter_apex_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in APEX_SUFFIXES)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Static audit of Queueable Apex source for the anti-patterns documented in "
                    "skills/apex/apex-queueable-patterns.",
    )
    ap.add_argument("--manifest-dir", required=True,
                    help="Root directory of the Apex source tree to scan (.cls and .trigger).")
    ap.add_argument("--strict", action="store_true",
                    help="Promote WARN findings to ERROR, so they also fail the run.")
    ap.add_argument("--format", choices=("json", "text"), default="json",
                    help="Output format (default: json).")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.manifest_dir)

    if not root.is_dir():
        print(f"ERROR: --manifest-dir not found: {root}", file=sys.stderr)
        return 1

    files = iter_apex_files(root)
    if not files:
        print(f"WARN: no .cls or .trigger files under {root} — nothing to check.", file=sys.stderr)
        if args.format == "json":
            print(json.dumps({"scanned": 0, "findings": [], "counts": {},
                              "summary": f"No Apex files under {root}."}, indent=2))
        return 0

    findings: list[dict] = []
    queueable_files = 0
    for path in files:
        try:
            rel = str(path.relative_to(root))
        except ValueError:
            rel = str(path)
        file_findings = audit_file(path, rel)
        findings.extend(file_findings)
        if QUEUEABLE_RE.search(path.read_text(encoding="utf-8", errors="ignore")):
            queueable_files += 1

    if args.strict:
        for f in findings:
            if f["severity"] == WARN:
                f["severity"] = ERROR
                f["promoted_by_strict"] = True

    counts = {ERROR: 0, WARN: 0, ADVISORY: 0}
    for f in findings:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1

    summary = (f"Scanned {len(files)} Apex file(s), {queueable_files} implementing Queueable; "
               f"{counts.get(ERROR, 0)} ERROR, {counts.get(WARN, 0)} WARN, "
               f"{counts.get(ADVISORY, 0)} ADVISORY.")

    if args.format == "text":
        for f in findings:
            print(f"{f['severity']:<8} {f['rule']} {f['location']}: {f['message']}")
        print(summary)
    else:
        print(json.dumps({"scanned": len(files), "queueable_classes": queueable_files,
                          "counts": counts, "findings": findings, "summary": summary}, indent=2))

    return 1 if counts.get(ERROR, 0) else 0


if __name__ == "__main__":
    sys.exit(main())
