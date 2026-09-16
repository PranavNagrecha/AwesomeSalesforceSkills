#!/usr/bin/env python3
"""Static checks for Scheduled Apex (Schedulable) source.

Canonical checker for skills/apex/apex-scheduled-jobs. Stdlib only.

Scans every ``*.cls`` under ``--manifest-dir`` and applies six rules. Each rule is
grounded in the Apex Developer Guide (apexdev) / Apex Reference Guide (apexrefguide) /
Object Reference; the grounding is quoted in the finding message so a reviewer can check
it without leaving the terminal.

Rules
-----
R1  ADVISORY  Schedulable ``execute`` does more than dispatch: > 1 DML statement or
              > 2 SOQL queries in the method body. Scheduled Apex runs under SYNCHRONOUS
              governor limits (apexdev: "Although scheduled Apex is an asynchronous
              feature, synchronous limits apply to scheduled Apex jobs"), so heavy work
              in execute() has less headroom than the Batch it should dispatch to.
              Reported as WARN.
R2  ERROR     Schedulable class makes an HTTP callout directly. apexdev: "Synchronous Web
              service callouts aren't supported from scheduled Apex."
R3  ERROR     Malformed CRON string literal: not 6 or 7 whitespace-separated fields, or
              neither day field is '?'. apexdev gives the syntax as
              "Seconds Minutes Hours Day_of_month Month Day_of_week Optional_year" and
              defines '?' as available "only ... for Day_of_month and Day_of_week".
R4  WARN      ``System.schedule`` in a non-test class with a hardcoded job name and no
              abort of a prior job in the same file. apexdev: a duplicate name throws
              'System.AsyncException: The Apex job named "jobName" is already scheduled
              for execution'.
R5  ERROR     A test class calls ``System.schedule`` outside a
              ``Test.startTest()`` / ``Test.stopTest()`` bracket. apexdev: asynchronous
              work collected after startTest "run[s] synchronously" at stopTest; outside
              the bracket the job runs only at the end of the test method.
R6  ADVISORY  A Schedulable calls ``Database.executeBatch`` with no in-flight guard and no
              ``Test.isRunningTest()`` fence. CronTrigger 'BLOCKED' guards re-entry of the
              scheduler, not the worker it dispatched (Object Reference, CronTrigger.State).
              Reported as ADVISORY; never fails the run.

Exit codes
----------
0  no ERROR findings (WARN / ADVISORY may be present), or the directory held no .cls files
1  at least one ERROR, or --manifest-dir does not exist, or --strict and at least one WARN

Usage
-----
    python3 check_apex_scheduled_jobs.py --manifest-dir force-app/main/default/classes
    python3 check_apex_scheduled_jobs.py --manifest-dir src --strict
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ERROR = "ERROR"
WARN = "WARN"
ADVISORY = "ADVISORY"

# --------------------------------------------------------------------------------------
# Lexing helpers
# --------------------------------------------------------------------------------------


def strip_comments(source: str) -> str:
    """Blank `//` and `/* … */` comments to spaces; leave string literal contents intact.

    R3 reads CRON string literals. Comments first so a possessive apostrophe inside a
    comment never opens a string. Same length as `source`; newlines preserved.
    """
    out: list[str] = []
    i, n = 0, len(source)
    while i < n:
        ch = source[i]
        if ch == "/" and i + 1 < n and source[i + 1] == "/":
            j = i
            while j < n and source[j] != "\n":
                out.append(" ")
                j += 1
            i = j
            continue
        if ch == "/" and i + 1 < n and source[i + 1] == "*":
            out.append(" ")
            out.append(" ")
            j = i + 2
            while j + 1 < n and not (source[j] == "*" and source[j + 1] == "/"):
                out.append("\n" if source[j] == "\n" else " ")
                j += 1
            if j + 1 < n:
                out.append(" ")
                out.append(" ")
                j += 2
            elif j < n:
                out.append("\n" if source[j] == "\n" else " ")
                j += 1
            i = j
            continue
        if ch == "'":
            out.append("'")
            i += 1
            while i < n:
                if source[i] == "\n":
                    out.append("\n")
                    i += 1
                    break
                if source[i] == "\\" and i + 1 < n:
                    out.append(source[i])
                    out.append(source[i + 1])
                    i += 2
                    continue
                if source[i] == "'":
                    if i + 1 < n and source[i + 1] == "'":
                        out.append("'")
                        out.append("'")
                        i += 2
                        continue
                    out.append("'")
                    i += 1
                    break
                out.append(source[i])
                i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def blank_strings(source: str) -> str:
    """Blank out single-quoted Apex string literals, preserving length and newlines.

    Assumes comments are already blanked (so apostrophes inside comments are gone).
    Handles Apex doubled quotes `''` and backslash escapes.
    """
    out: list[str] = []
    i, n = 0, len(source)
    while i < n:
        ch = source[i]
        if ch == "'":
            out.append(" ")
            i += 1
            while i < n:
                if source[i] == "\n":
                    out.append("\n")
                    i += 1
                    break
                if source[i] == "\\" and i + 1 < n:
                    out.append(" ")
                    out.append(" ")
                    i += 2
                    continue
                if source[i] == "'":
                    if i + 1 < n and source[i + 1] == "'":
                        out.append(" ")
                        out.append(" ")
                        i += 2
                        continue
                    out.append(" ")
                    i += 1
                    break
                out.append(" ")
                i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def line_of(source: str, index: int) -> int:
    return source.count("\n", 0, index) + 1


def extract_method_body(source: str, start_index: int) -> str:
    """Return the brace-balanced body that follows start_index, or '' if unbalanced."""
    open_at = source.find("{", start_index)
    if open_at == -1:
        return ""
    depth = 0
    for i in range(open_at, len(source)):
        if source[i] == "{":
            depth += 1
        elif source[i] == "}":
            depth -= 1
            if depth == 0:
                return source[open_at + 1:i]
    return ""


# --------------------------------------------------------------------------------------
# Patterns
# --------------------------------------------------------------------------------------

SCHEDULABLE_RE = re.compile(r"\bimplements\b[^{;]{0,200}?\bSchedulable\b", re.I)
IS_TEST_RE = re.compile(r"@\s*IsTest\b", re.I)
EXECUTE_RE = re.compile(r"\bvoid\s+execute\s*\(\s*SchedulableContext\b", re.I)

SOQL_RE = re.compile(r"\[\s*(SELECT|FIND)\b", re.I)
DML_STMT_RE = re.compile(
    r"(?<![\w.])(insert|update|upsert|delete|undelete|merge)\s+(?:as\s+(?:user|system)\s+)?[\w(\[]",
    re.I,
)
DML_DATABASE_RE = re.compile(
    r"\bDatabase\s*\.\s*(insert|update|upsert|delete|undelete|merge)\s*\(", re.I
)

CALLOUT_RE = re.compile(
    r"\bnew\s+Http\s*\(|\bnew\s+HttpRequest\s*\(|\bHttp\s*\(\s*\)\s*\.\s*send\s*\(|"
    r"\bWebServiceCallout\s*\.\s*invoke\s*\(",
    re.I,
)

SYSTEM_SCHEDULE_RE = re.compile(r"\bSystem\s*\.\s*schedule\s*\(", re.I)
ABORT_JOB_RE = re.compile(r"\bSystem\s*\.\s*abortJob\s*\(", re.I)
START_TEST_RE = re.compile(r"\bTest\s*\.\s*startTest\s*\(\s*\)", re.I)
STOP_TEST_RE = re.compile(r"\bTest\s*\.\s*stopTest\s*\(\s*\)", re.I)
EXECUTE_BATCH_RE = re.compile(r"\bDatabase\s*\.\s*executeBatch\s*\(", re.I)
IS_RUNNING_TEST_RE = re.compile(r"\bTest\s*\.\s*isRunningTest\s*\(\s*\)", re.I)
ASYNC_APEX_JOB_RE = re.compile(r"\bAsyncApexJob\b", re.I)

STRING_LITERAL_RE = re.compile(r"'([^'\\\n]*(?:\\.[^'\\\n]*)*)'")

# A token that could plausibly belong to a CRON field.
CRON_TOKEN = re.compile(r"^[0-9A-Za-z?*,/#\-]+$")
MONTHS = {"JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"}
DAYS = {"SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"}


def looks_like_cron(literal: str) -> bool:
    """Heuristic: does this string literal look like someone meant it as a CRON expression?

    Deliberately conservative — a false positive here becomes an ERROR, so only accept
    literals that are entirely CRON-shaped tokens and that contain a CRON-ish signal.
    """
    parts = literal.strip().split()
    if not 4 <= len(parts) <= 9:
        return False
    if not all(CRON_TOKEN.match(part) for part in parts):
        return False
    upper = {p.upper() for p in parts}
    has_wildcard = any(c in literal for c in "*?")
    has_named = bool(upper & MONTHS) or any(
        any(d in p.upper() for d in DAYS) for p in parts
    )
    if not (has_wildcard or has_named):
        return False
    # At least half the fields must be a bare integer, '*', '?', or a named constant —
    # this keeps ordinary sentences and SOQL fragments out.
    plain = 0
    for part in parts:
        token = part.upper()
        if token in {"*", "?"} or token.isdigit() or token in MONTHS or token in DAYS:
            plain += 1
    return plain >= max(2, len(parts) // 2)


def cron_problem(literal: str) -> str | None:
    """Return a human-readable problem with this CRON literal, or None if it is fine."""
    parts = literal.strip().split()
    n = len(parts)
    if n not in (6, 7):
        return (
            f"has {n} field(s); the documented syntax is "
            "'Seconds Minutes Hours Day_of_month Month Day_of_week Optional_year' "
            "(6 required fields, year optional). A 5-field Unix cron is never valid here"
        )
    day_of_month, day_of_week = parts[3], parts[5]
    if day_of_month != "?" and day_of_week != "?":
        return (
            f"sets both day fields (Day_of_month='{day_of_month}', "
            f"Day_of_week='{day_of_week}'); '?' is available only for these two fields "
            "and is used when specifying a value for one and not the other"
        )
    if day_of_month == "?" and day_of_week == "?":
        return "sets '?' in both day fields, so no day is ever selected"
    return None


# --------------------------------------------------------------------------------------
# Rules
# --------------------------------------------------------------------------------------

class Finding:
    def __init__(self, severity: str, path: Path, line: int, rule: str, message: str):
        self.severity = severity
        self.path = path
        self.line = line
        self.rule = rule
        self.message = message

    def render(self) -> str:
        return f"{self.severity}: {self.path}:{self.line} [{self.rule}] {self.message}"


def check_file(path: Path, raw: str) -> list[Finding]:
    findings: list[Finding] = []
    code = strip_comments(raw)
    code_nostr = blank_strings(code)

    is_schedulable = bool(SCHEDULABLE_RE.search(code_nostr))
    is_test = bool(IS_TEST_RE.search(code))

    # ---- R3: CRON literals (any class — post-deploy scripts live in classes too) ----
    for m in STRING_LITERAL_RE.finditer(code):
        literal = m.group(1)
        if not looks_like_cron(literal):
            continue
        problem = cron_problem(literal)
        if problem:
            findings.append(Finding(
                ERROR, path, line_of(code, m.start()), "R3-cron",
                f"CRON literal '{literal}' {problem}.",
            ))

    if is_schedulable:
        # ---- R2: direct callout anywhere in a Schedulable class ----
        for m in CALLOUT_RE.finditer(code_nostr):
            findings.append(Finding(
                ERROR, path, line_of(code_nostr, m.start()), "R2-callout",
                "HTTP callout constructed inside a Schedulable class. The Apex Developer "
                "Guide states \"Synchronous Web service callouts aren't supported from "
                "scheduled Apex\"; move the callout to a Queueable or Batch class "
                "carrying Database.AllowsCallouts.",
            ))

        # ---- R1 / R6: inspect each execute(SchedulableContext) body ----
        for m in EXECUTE_RE.finditer(code_nostr):
            body_nostr = extract_method_body(code_nostr, m.end())
            if not body_nostr:
                continue
            line = line_of(code_nostr, m.start())

            soql = len(SOQL_RE.findall(body_nostr))
            dml = len(DML_STMT_RE.findall(body_nostr)) + len(DML_DATABASE_RE.findall(body_nostr))

            if dml > 1 or soql > 2:
                findings.append(Finding(
                    WARN, path, line, "R1-thin-execute",
                    f"execute(SchedulableContext) contains {soql} SOQL and {dml} DML "
                    "operation(s), which is more than a dispatch. Scheduled Apex runs "
                    "under SYNCHRONOUS governor limits (100 SOQL / 6 MB heap / 10,000 ms "
                    "CPU); the guide recommends \"all processing must take place in a "
                    "separate class\". Delegate to Batch or Queueable.",
                ))

            if EXECUTE_BATCH_RE.search(body_nostr) and not (
                ASYNC_APEX_JOB_RE.search(code_nostr) or IS_RUNNING_TEST_RE.search(body_nostr)
            ):
                findings.append(Finding(
                    ADVISORY, path, line, "R6-overlap-guard",
                    "execute() dispatches a batch with no in-flight guard and no "
                    "Test.isRunningTest() fence. CronTrigger 'BLOCKED' guards re-entry of "
                    "the scheduler, not the worker it dispatched — query AsyncApexJob for "
                    "in-flight jobs of the batch class before calling executeBatch if the "
                    "batch can outlive its schedule interval.",
                ))

    # ---- R4 / R5: System.schedule call sites ----
    for m in SYSTEM_SCHEDULE_RE.finditer(code_nostr):
        idx = m.start()
        line = line_of(code_nostr, idx)

        if is_test:
            before = code_nostr[:idx]
            after = code_nostr[idx:]
            starts = len(START_TEST_RE.findall(before))
            stops = len(STOP_TEST_RE.findall(before))
            bracketed = starts > stops and bool(STOP_TEST_RE.search(after))
            if not bracketed:
                findings.append(Finding(
                    ERROR, path, line, "R5-test-bracket",
                    "System.schedule() in a test class is not bracketed by "
                    "Test.startTest() / Test.stopTest(). Asynchronous work collected "
                    "after startTest runs synchronously at stopTest; outside the bracket "
                    "the job runs only at the end of the test method (API 25.0+), too "
                    "late for any assertion in it.",
                ))
            continue

        # Non-test class: hardcoded job name and no abort in the same file.
        call_tail = code[idx:idx + 400]
        arg_literal = STRING_LITERAL_RE.search(call_tail)
        hardcoded_name = bool(arg_literal) and call_tail.find(arg_literal.group(0)) < call_tail.find(",") + 2
        if hardcoded_name and not ABORT_JOB_RE.search(code_nostr):
            findings.append(Finding(
                WARN, path, line, "R4-abort-before-schedule",
                f"System.schedule() with the hardcoded job name {arg_literal.group(0)} and "
                "no System.abortJob() anywhere in this file. A second run throws "
                "'System.AsyncException: The Apex job named \"jobName\" is already "
                "scheduled for execution', so the script is not re-runnable after a failed "
                "release. Abort any live CronTrigger of that name first.",
            ))

    return findings


# --------------------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------------------

def scan(manifest_dir: Path) -> tuple[list[Finding], int]:
    findings: list[Finding] = []
    files = sorted(manifest_dir.rglob("*.cls"))
    for path in files:
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            findings.append(Finding(WARN, path, 0, "R0-io", f"cannot read file — {exc}"))
            continue
        findings.extend(check_file(path, raw))
    return findings, len(files)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Static checks for Scheduled Apex source: thin execute(), no direct callouts, "
            "well-formed CRON literals, abort-before-schedule, and test bracketing."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        required=True,
        help="Root of the Salesforce source tree to scan (searched recursively for *.cls).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Promote WARN findings to failures. ADVISORY never fails the run.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest_dir = Path(args.manifest_dir)

    if not manifest_dir.is_dir():
        print(f"ERROR: --manifest-dir not found or not a directory: {manifest_dir}")
        return 1

    findings, file_count = scan(manifest_dir)

    if file_count == 0:
        print(f"WARN: no .cls files found under {manifest_dir} — nothing to check.")
        return 0

    order = {ERROR: 0, WARN: 1, ADVISORY: 2}
    for finding in sorted(findings, key=lambda f: (order[f.severity], str(f.path), f.line)):
        print(finding.render())

    errors = sum(1 for f in findings if f.severity == ERROR)
    warns = sum(1 for f in findings if f.severity == WARN)
    advisories = sum(1 for f in findings if f.severity == ADVISORY)

    print(
        f"\nScanned {file_count} .cls file(s) under {manifest_dir}: "
        f"{errors} ERROR, {warns} WARN, {advisories} ADVISORY."
    )

    if errors:
        return 1
    if args.strict and warns:
        print("--strict: WARN findings promoted to failure.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
