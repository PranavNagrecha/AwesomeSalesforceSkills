#!/usr/bin/env python3
"""check_apex_limits_monitoring.py — audit an Apex source tree for limits-monitoring defects.

Stdlib only. Scans .cls / .trigger files and *.object-meta.xml under --manifest-dir and
applies the seven rules this skill's gotchas are about:

  R1  Limits.getX() compared against a hardcoded number instead of the
      matching Limits.getLimitX()                                        WARN
  R2  Limits.getCpuTime() evaluated on every iteration of a loop with no
      sampling gate (the guard consumes the resource it guards)          ADVISORY
  R3  catch (System.LimitException ...) anywhere                          ERROR
      (uncatchable — apexdev L39720-39728; catch AND finally are skipped)
  R4  a class that reads OrgLimits but implements no Schedulable /
      Queueable / Batchable dispatch (a poller nobody runs)              ADVISORY
  R5  a *_Snapshot__c-style limit object with no DateTime field
      (a current value, not a time series)                                ERROR
  R6  the same threshold literal duplicated across >= 2 classes
      (belongs in Custom Metadata)                                       WARN
  R7  a test method asserting on a limit guard with no measurable
      consumption between Test.startTest() and the assertion             ADVISORY

Exit codes: 0 clean or advisories/warnings only, 1 on any ERROR or a hard failure
(missing --manifest-dir). --strict promotes WARN to failure as well. An empty tree is a
WARN with exit 0 — nothing to judge is not a failure.

Usage:
    python3 check_apex_limits_monitoring.py --manifest-dir force-app/main/default
    python3 check_apex_limits_monitoring.py --manifest-dir . --format text --strict
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

MDAPI_NS = "{http://soap.sforce.com/2006/04/metadata}"

SEVERITY_ORDER = {"ERROR": 0, "WARN": 1, "ADVISORY": 2}
SEVERITY_WEIGHTS = {"ERROR": 20, "WARN": 8, "ADVISORY": 2}

# Limits.getX() where X is one of the meters people guard, followed by a comparison
# operator and a bare number. `Limits.getLimitQueries() - Limits.getQueries() < 10` is
# fine; `Limits.getQueries() > 90` is the defect.
GUARDED_METERS = (
    "Queries|DMLStatements|DmlStatements|DMLRows|DmlRows|CpuTime|HeapSize|QueryRows"
    "|Callouts|SoslQueries|FutureCalls|QueueableJobs|AggregateQueries"
)
HARDCODED_CMP_RE = re.compile(
    r"\bLimits\s*\.\s*get(?!Limit)(?:" + GUARDED_METERS + r")\s*\(\s*\)"
    r"\s*(?:<=|>=|<|>|==|!=)\s*(\d[\d_]*)",
    re.IGNORECASE,
)
HARDCODED_CMP_REVERSED_RE = re.compile(
    r"(\d[\d_]*)\s*(?:<=|>=|<|>|==|!=)\s*"
    r"\bLimits\s*\.\s*get(?!Limit)(?:" + GUARDED_METERS + r")\s*\(\s*\)",
    re.IGNORECASE,
)

CPU_TIME_RE = re.compile(r"\bLimits\s*\.\s*getCpuTime\s*\(\s*\)", re.IGNORECASE)
LOOP_HEAD_RE = re.compile(r"\b(for|while|do)\b\s*[({]")
# A sampling gate: modulo, a counter comparison, or an explicit "check every N" variable.
SAMPLING_GATE_RE = re.compile(
    r"\bMath\s*\.\s*mod\s*\(|%\s*\w*(?:checkEvery|sampleEvery|interval|batchSize)\w*"
    r"|\bcheckEvery\b|\bsampleEvery\b|\bnextCheckAt\b|\bcheckCounter\b",
    re.IGNORECASE,
)
CATCH_LIMIT_EXCEPTION_RE = re.compile(
    r"\bcatch\s*\(\s*(?:System\s*\.\s*)?LimitException\b", re.IGNORECASE
)
ORG_LIMITS_RE = re.compile(r"\bOrgLimits\s*\.\s*(?:getAll|getMap)\s*\(", re.IGNORECASE)
DISPATCH_RE = re.compile(
    r"\bimplements\b[^{;]*\b(Schedulable|Queueable|Database\s*\.\s*Batchable|Database\s*\.\s*AllowsCallouts)\b"
    r"|\bSystem\s*\.\s*schedule\s*\(|\bSystem\s*\.\s*enqueueJob\s*\(|\bDatabase\s*\.\s*executeBatch\s*\(",
    re.IGNORECASE,
)
# `private static final Integer WARN_PCT = 80;` style threshold constants.
THRESHOLD_CONST_RE = re.compile(
    r"\b(?:static\s+)?(?:final\s+)?(?:Integer|Decimal|Double|Long)\s+"
    r"(\w*(?:THRESHOLD|PCT|PERCENT|WARN|CRITICAL|LIMIT|SAFETY|BUFFER)\w*)\s*=\s*(\d+)\s*;",
    re.IGNORECASE,
)
TEST_CLASS_RE = re.compile(r"@is\s*test\b|\btestMethod\b", re.IGNORECASE)
TEST_METHOD_SPLIT_RE = re.compile(r"@is\s*test\b", re.IGNORECASE)
START_TEST_RE = re.compile(r"\bTest\s*\.\s*startTest\s*\(", re.IGNORECASE)
GUARD_CALL_RE = re.compile(
    r"\bLimitGuard\s*\.\s*(?:near\w+|hasRoomFor|worst|pctUsedByMeter)\s*\("
    r"|\bLimits\s*\.\s*getLimit\w+\s*\(\s*\)\s*-\s*\bLimits\s*\.\s*get\w+\s*\(",
    re.IGNORECASE,
)
ASSERT_RE = re.compile(r"\b(?:System\s*\.\s*assert\w*|Assert\s*\.\s*\w+)\s*\(", re.IGNORECASE)
# A test proving an exception path, not a threshold: no consumption is expected.
EXCEPTION_TEST_RE = re.compile(r"\bcatch\s*\(|\bAssert\s*\.\s*fail\s*\(", re.IGNORECASE)
# Anything that actually moves a meter.
CONSUMPTION_RE = re.compile(
    r"\[\s*SELECT\b|\b(?:insert|update|upsert|delete|undelete)\s+"
    r"|\bDatabase\s*\.\s*(?:insert|update|upsert|delete|query|countQuery)\s*\("
    r"|\.\s*repeat\s*\(|\bHttp\s*\(\s*\)\s*\.\s*send\s*\(",
    re.IGNORECASE,
)
LIMIT_OBJECT_NAME_RE = re.compile(
    r"(limit|governor|usage|quota|allocation).*(snapshot|reading|sample|metric|usage|history)"
    r"|(snapshot|reading|sample|metric).*(limit|governor|usage|quota)",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--manifest-dir", required=True, help="Root of the source tree to scan.")
    parser.add_argument("--format", choices=("json", "text"), default="json", help="Output format.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Promote WARN findings to failures (exit 1). ERROR always fails.",
    )
    return parser.parse_args()


def child(parent, tag):
    """Return the first child element with `tag`, or None.

    Never use `a.find(x) or a.find(y)`: an Element with no children is falsy, so a real
    leaf element would be discarded in favour of the fallback.
    """
    found = parent.find(MDAPI_NS + tag)
    if found is None:
        found = parent.find(tag)
    return found


def children(parent, tag):
    found = parent.findall(MDAPI_NS + tag)
    if not found:
        found = parent.findall(tag)
    return found


def strip_apex(src: str) -> str:
    """Blank string literals and comments so regexes never match inside them.
    Newlines are preserved so reported line numbers stay accurate."""
    out = []
    i, n = 0, len(src)
    while i < n:
        ch = src[i]
        if ch == "'":
            j = i + 1
            while j < n and src[j] != "'":
                j += 2 if src[j] == "\\" else 1
            out.append(" " * (min(j, n - 1) + 1 - i))
            i = j + 1
            continue
        if src.startswith("//", i):
            j = src.find("\n", i)
            j = n if j < 0 else j
            out.append(" " * (j - i))
            i = j
            continue
        if src.startswith("/*", i):
            j = src.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append("".join(c if c == "\n" else " " for c in src[i:j]))
            i = j
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def block_end(text: str, open_brace: int) -> int:
    """Index just past the matching '}' for the '{' at open_brace, or len(text)."""
    depth = 0
    for i in range(open_brace, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i + 1
    return len(text)


def loop_bodies(code: str):
    """Yield (start, end) index pairs for every loop body in `code`."""
    for m in LOOP_HEAD_RE.finditer(code):
        brace = code.find("{", m.start())
        if brace == -1:
            continue
        # Only treat it as a body if the brace is close enough to be this loop's.
        if code.count("\n", m.start(), brace) > 4:
            continue
        yield brace, block_end(code, brace)


def audit_apex(path: Path, findings: list[str], thresholds: dict[str, set[str]]) -> None:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    code = strip_apex(raw)
    rel = path.as_posix()
    is_test = bool(TEST_CLASS_RE.search(code))

    # R3 — catch (System.LimitException ...) is always wrong.
    for m in CATCH_LIMIT_EXCEPTION_RE.finditer(code):
        findings.append(
            f"ERROR {rel}:{line_of(code, m.start())}: `catch (System.LimitException)` is "
            "unreachable — the exception is uncatchable and the finally block is skipped too "
            "(apexdev L39720-39728). Guard before the operation instead."
        )

    # R1 — a meter compared against a bare number.
    for regex in (HARDCODED_CMP_RE, HARDCODED_CMP_REVERSED_RE):
        for m in regex.finditer(code):
            findings.append(
                f"WARN {rel}:{line_of(code, m.start())}: Limits meter compared against the "
                f"literal {m.group(1)} instead of the matching Limits.getLimitX(). The ceiling "
                "differs by context (100 vs 200 SOQL, 10,000 vs 60,000 ms CPU) and scheduled "
                "Apex runs under the synchronous column."
            )

    # R2 — getCpuTime() inside a loop with no sampling gate.
    for start, end in loop_bodies(code):
        body = code[start:end]
        if not CPU_TIME_RE.search(body):
            continue
        if SAMPLING_GATE_RE.search(body):
            continue
        m = CPU_TIME_RE.search(body)
        findings.append(
            f"ADVISORY {rel}:{line_of(code, start + m.start())}: Limits.getCpuTime() is "
            "evaluated on every iteration of this loop. The check is itself Apex execution "
            "and is charged to the CPU meter it guards; sample every N iterations instead."
        )

    # R4 — a class that reads OrgLimits but has no async dispatch.
    if ORG_LIMITS_RE.search(code) and not is_test and not DISPATCH_RE.search(code):
        m = ORG_LIMITS_RE.search(code)
        findings.append(
            f"ADVISORY {rel}:{line_of(code, m.start())}: reads OrgLimits but declares no "
            "Schedulable/Queueable/Batchable dispatch and never schedules or enqueues one. "
            "An org-limits reading is a trend sample; taken once by hand it is not a monitor."
        )

    # R6 — collect threshold literals for the cross-file pass.
    if not is_test:
        for m in THRESHOLD_CONST_RE.finditer(code):
            name, value = m.group(1), m.group(2)
            thresholds[f"{name.upper()}={value}"].add(rel)

    # R7 — a test that asserts on a guard without consuming anything first.
    if is_test:
        audit_guard_test(rel, code, findings)


def audit_guard_test(rel: str, code: str, findings: list[str]) -> None:
    """Split the class on @IsTest and check each method body in isolation."""
    marks = [m.start() for m in TEST_METHOD_SPLIT_RE.finditer(code)]
    for idx, start in enumerate(marks):
        end = marks[idx + 1] if idx + 1 < len(marks) else len(code)
        body = code[start:end]
        guard = GUARD_CALL_RE.search(body)
        if guard is None:
            continue
        assertion = ASSERT_RE.search(body)
        if assertion is None:
            continue
        # An exception-path test (Assert.fail + catch) legitimately consumes nothing.
        if EXCEPTION_TEST_RE.search(body):
            continue
        st = START_TEST_RE.search(body)
        window_start = st.end() if st else 0
        # Look across the whole method after startTest, not just up to the first
        # assertion: the correct pattern asserts the "before" state, consumes budget,
        # then asserts the transition, so the setup follows the first assertion.
        if CONSUMPTION_RE.search(body[window_start:]):
            continue
        findings.append(
            f"ADVISORY {rel}:{line_of(code, start + guard.start())}: asserts on a limit guard "
            "with no SOQL, DML or allocation before the assertion. On an untouched transaction "
            "every meter reads zero, so the assertion proves only that zero is below the "
            "threshold. Consume measurable budget, then assert the transition."
        )


def audit_object(path: Path, findings: list[str]) -> None:
    """R5 — a limit-snapshot-shaped object with no DateTime field is not a time series."""
    name = path.name.replace(".object-meta.xml", "")
    if not LIMIT_OBJECT_NAME_RE.search(name.replace("_", " ")):
        return
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        findings.append(f"ERROR {path.as_posix()}:1: object metadata does not parse — {exc}")
        return

    field_types: list[str] = []
    # Fields may be inline in the object file or in a sibling fields/ directory.
    for field in children(root, "fields"):
        ftype = child(field, "type")
        if ftype is not None and ftype.text:
            field_types.append(ftype.text.strip())
    fields_dir = path.parent / "fields"
    if fields_dir.is_dir():
        for fpath in sorted(fields_dir.glob("*.field-meta.xml")):
            try:
                froot = ET.parse(fpath).getroot()
            except ET.ParseError as exc:
                findings.append(f"ERROR {fpath.as_posix()}:1: field metadata does not parse — {exc}")
                continue
            ftype = child(froot, "type")
            if ftype is not None and ftype.text:
                field_types.append(ftype.text.strip())

    if not any(t.lower() in ("datetime", "date") for t in field_types):
        findings.append(
            f"ERROR {path.as_posix()}:1: `{name}` looks like a limit-snapshot object but has "
            "no DateTime (or Date) field across its inline fields and fields/ directory. "
            "Without a capture timestamp it holds a current value, which OrgLimits already "
            "returns for free — there is no trend to alert on."
        )


def audit_thresholds(thresholds: dict[str, set[str]], findings: list[str]) -> None:
    """R6 — the same threshold literal in two or more classes belongs in Custom Metadata."""
    for key, files in sorted(thresholds.items()):
        if len(files) < 2:
            continue
        name, _, value = key.partition("=")
        where = ", ".join(sorted(files))
        findings.append(
            f"WARN {where.split(', ')[0]}:1: threshold literal {name} = {value} is duplicated "
            f"across {len(files)} classes ({where}). Move it to a Custom Metadata Type such as "
            "Limit_Threshold__mdt so tuning it is a reviewed deploy, not an edit in N places. "
            "Custom metadata reads also do not consume the SOQL ceiling (apexdev L19617-19618)."
        )


def normalize(finding: str) -> dict:
    severity, _, remainder = finding.partition(" ")
    location, _, message = remainder.partition(": ")
    return {"severity": severity or "ADVISORY", "location": location, "message": message or remainder}


def emit(findings: list[str], summary: str, fmt: str, exit_code: int) -> int:
    rows = [normalize(f) for f in findings]
    rows.sort(key=lambda r: (SEVERITY_ORDER.get(r["severity"], 9), r["location"]))
    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(r["severity"], 0) for r in rows))
    if fmt == "text":
        for r in rows:
            print(f"{r['severity']:9} {r['location']}  {r['message']}")
        print(summary)
    else:
        print(json.dumps({"score": score, "findings": rows, "summary": summary}, indent=2))
    for r in rows:
        if r["severity"] == "ERROR":
            print(f"ERROR: {r['location']} {r['message']}", file=sys.stderr)
    if rows:
        print(f"WARN: {len(rows)} finding(s) detected", file=sys.stderr)
    return exit_code


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}", file=sys.stderr)
        sys.exit(1)

    apex_files = sorted(p for p in root.rglob("*") if p.suffix in (".cls", ".trigger") and p.is_file())
    object_files = sorted(root.rglob("*.object-meta.xml"))
    if not apex_files and not object_files:
        print(f"WARN: no .cls, .trigger or .object-meta.xml files under {root}", file=sys.stderr)
        return emit([], f"Scanned 0 files under {root}; nothing to check.", args.format, 0)

    findings: list[str] = []
    thresholds: dict[str, set[str]] = defaultdict(set)
    for path in apex_files:
        audit_apex(path, findings, thresholds)
    for path in object_files:
        audit_object(path, findings)
    audit_thresholds(thresholds, findings)

    counts = {"ERROR": 0, "WARN": 0, "ADVISORY": 0}
    for f in findings:
        counts[f.split(" ", 1)[0]] = counts.get(f.split(" ", 1)[0], 0) + 1

    summary = (
        f"Scanned {len(apex_files)} Apex file(s) and {len(object_files)} object file(s); "
        f"{counts['ERROR']} error(s), {counts['WARN']} warning(s), "
        f"{counts['ADVISORY']} advisory/advisories."
    )
    failing = counts["ERROR"] > 0 or (args.strict and counts["WARN"] > 0)
    return emit(findings, summary, args.format, 1 if failing else 0)


if __name__ == "__main__":
    sys.exit(main())
