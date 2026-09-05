#!/usr/bin/env python3
"""Checker for the apex-batch-chaining skill.

Static analysis of Apex source (*.cls, *.trigger) for the chaining defects that
the compiler cannot see and that `references/gotchas.md` documents. Stdlib only,
no network, no org connection.

This script NEVER compiles Apex and never claims to. Every finding is a
lexical/regex signal over the source text, so every rule can produce a false
positive on unusual formatting; the message names the gotcha so a human can
adjudicate.

Rules (each maps to a gotcha or anti-pattern in this package):

  C001  ERROR    `Database.executeBatch` inside the `execute()` of a
                 Database.Batchable class. Chain from `finish()`, not from
                 `execute()` — chaining is defined as calling executeBatch or
                 scheduleBatch "from the finish method of the current batch
                 class" (apexdev L17817-17818), and an execute()-level call runs
                 once per scope chunk, multiplying jobs by the chunk count.
  C002  WARN     More than one `System.enqueueJob` in a Queueable `execute()` or
                 in a batch `finish()`, with no guard. "In asynchronous
                 transactions (for example, from a batch Apex job), you can add
                 only one job to the queue with System.enqueueJob"
                 (apexdev L16175-16177); "Only one child job can exist for each
                 parent queueable job" (apexdev L16187-16189).
  C003  ADVISORY Database.Stateful class whose instance collection field is
                 `.add(`-ed inside execute(). Stateful members are serialized
                 between every execute() transaction (apexdev L17519-17521), so a
                 per-scope-growing collection grows the payload for the rest of
                 the job. Heuristic: List</Map</Set< instance field + .add( in
                 execute.
  C004  WARN     `Database.executeBatch` or `System.scheduleBatch` inside a
                 trigger. "Use extreme caution if you're planning to invoke a
                 batch job from a trigger. You must be able to guarantee that the
                 trigger doesn't add more batch jobs than the limit"
                 (apexdev L17727-17730).
  C005  ADVISORY A class that chains (calls executeBatch/enqueueJob from finish()
                 or from a Queueable execute()) with no kill-switch read.
                 Name-based heuristic: no `__mdt`, `__c.getInstance`,
                 `getOrgDefaults`, `getInstance(` or `Enabled` token anywhere in
                 the file.
  C006  ERROR    A test class that calls `System.enqueueJob` or
                 `Database.executeBatch` outside a `Test.startTest()` block.
                 "Use the Test methods startTest and stopTest around the
                 executeBatch method to ensure that it finishes before continuing
                 your test" (apexdev L17740-17743).
  C007  WARN     A Queueable that chains (enqueueJob inside its own execute())
                 with neither a `Test.isRunningTest()` guard nor an
                 `AsyncOptions`/`MaximumQueueableStackDepth` bound. No limit is
                 enforced on chain depth outside Developer/Trial orgs
                 (apexdev L16182-16186).
  C008  WARN     `System.FlexQueue.getJobIds` — a method that does not exist. The
                 FlexQueue class has exactly moveAfterJob, moveBeforeJob,
                 moveJobToEnd, moveJobToFront (apexrefguide L215739-215762).
  C009  WARN     `AsyncApexJob` query with no `JobType` predicate that is not
                 pinned to a specific Id. Internal BatchApexWorker rows inflate
                 the result (apexdev L17755-17758).
  C010  ERROR    `Database.executeBatch(x, scope)` with a literal scope > 2000 or
                 <= 0. Max is 2,000 for a QueryLocator start(); the value "must
                 be greater than 0" (apexrefguide L207052-207058).

Exit codes:
    0  no ERROR findings (WARN/ADVISORY may be present, or --strict not set)
    1  a missing --manifest-dir, or at least one ERROR
       (with --strict, WARN is promoted to ERROR)

Usage:
    python3 check_apex_batch_chaining.py --manifest-dir force-app
    python3 check_apex_batch_chaining.py --manifest-dir force-app --strict
    python3 check_apex_batch_chaining.py --manifest-dir force-app --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ERROR = "ERROR"
WARN = "WARN"
ADVISORY = "ADVISORY"

BATCHABLE = re.compile(r"implements[^{;]*\bDatabase\s*\.\s*Batchable\b", re.I)
STATEFUL = re.compile(r"\bDatabase\s*\.\s*Stateful\b", re.I)
QUEUEABLE = re.compile(r"implements[^{;]*\bQueueable\b", re.I)
IS_TEST = re.compile(r"@\s*IsTest\b", re.I)

EXECUTE_BATCH = re.compile(r"\bDatabase\s*\.\s*executeBatch\s*\(", re.I)
SCHEDULE_BATCH = re.compile(r"\bSystem\s*\.\s*scheduleBatch\s*\(|(?<![.\w])scheduleBatch\s*\(", re.I)
ENQUEUE_JOB = re.compile(r"\b(?:System\s*\.\s*)?enqueueJob\s*\(", re.I)
START_TEST = re.compile(r"\bTest\s*\.\s*startTest\s*\(", re.I)
IS_RUNNING_TEST = re.compile(r"\bTest\s*\.\s*isRunningTest\s*\(", re.I)
STACK_DEPTH = re.compile(r"\bMaximumQueueableStackDepth\b|\bAsyncOptions\b", re.I)
GET_JOB_IDS = re.compile(r"\bFlexQueue\s*\.\s*getJobIds\s*\(", re.I)
KILL_SWITCH = re.compile(r"__mdt\b|getInstance\s*\(|getOrgDefaults\s*\(|\bEnabled\w*\b", re.I)

# `Database.executeBatch(new Foo(), 5000)` -> capture the trailing literal
SCOPE_LITERAL = re.compile(
    r"\bDatabase\s*\.\s*executeBatch\s*\([^();]*(?:\([^()]*\))?[^();]*,\s*(-?\d+)\s*\)", re.I
)

COLLECTION_FIELD = re.compile(
    r"^\s*(?:@\w+\s+)*(?:private|public|protected|global)?\s*(?:static\s+)?(?:final\s+)?"
    r"(List|Map|Set)\s*<[^>]*>\s+(\w+)\s*(?:=|;)",
    re.M,
)

AGG_ASYNC_QUERY = re.compile(r"\bFROM\s+AsyncApexJob\b", re.I)


def strip_noise(src: str) -> str:
    """Blank out string literals and comments in one left-to-right pass so a
    brace or keyword inside either is never read as code."""
    out = []
    i, n = 0, len(src)
    while i < n:
        ch = src[i]
        if ch == "'":
            j = i + 1
            while j < n and src[j] != "'":
                j += 2 if src[j] == "\\" else 1
            out.append(" " * (min(j, n) - i + 1))
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
            out.append(" " * (j - i))
            i = j
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def line_of(src: str, index: int) -> int:
    return src.count("\n", 0, index) + 1


def method_body(src: str, header_re: re.Pattern) -> tuple[str, int] | None:
    """Return (body, absolute_start_offset) of the first method whose signature
    matches header_re, by brace matching from the signature's opening brace.
    Returns None when the method is absent or unbalanced."""
    m = header_re.search(src)
    if not m:
        return None
    open_idx = src.find("{", m.end() - 1)
    if open_idx == -1:
        return None
    depth, i, n = 0, open_idx, len(src)
    while i < n:
        if src[i] == "{":
            depth += 1
        elif src[i] == "}":
            depth -= 1
            if depth == 0:
                return src[open_idx : i + 1], open_idx
        i += 1
    return None


EXEC_HDR = re.compile(
    r"\b(?:public|global|protected|private)\b[^;{}]*\bexecute\s*\(\s*(?:Database\s*\.\s*)?BatchableContext\b[^)]*\)",
    re.I,
)
FINISH_HDR = re.compile(
    r"\b(?:public|global|protected|private)\b[^;{}]*\bfinish\s*\(\s*(?:Database\s*\.\s*)?BatchableContext\b[^)]*\)",
    re.I,
)
Q_EXEC_HDR = re.compile(
    r"\b(?:public|global|protected|private)\b[^;{}]*\bexecute\s*\(\s*(?:System\s*\.\s*)?QueueableContext\b[^)]*\)",
    re.I,
)


def finding(code: str, severity: str, path: Path, line: int, message: str, fix: str) -> dict:
    return {
        "code": code,
        "severity": severity,
        "file": str(path),
        "line": line,
        "message": message,
        "fix": fix,
    }


def check_source(path: Path, raw: str) -> list[dict]:
    src = strip_noise(raw)
    out: list[dict] = []
    is_trigger = path.suffix == ".trigger"
    is_batchable = bool(BATCHABLE.search(src))
    is_queueable = bool(QUEUEABLE.search(src))
    is_test = bool(IS_TEST.search(raw))

    # ---- C001 executeBatch inside a Batchable execute() -------------------
    if is_batchable:
        found = method_body(src, EXEC_HDR)
        if found:
            body, off = found
            for m in EXECUTE_BATCH.finditer(body):
                out.append(finding(
                    "C001", ERROR, path, line_of(src, off + m.start()),
                    "Database.executeBatch called inside execute() of a "
                    "Database.Batchable class — this runs once per scope chunk.",
                    "Move the hand-off to finish(). Chaining is defined as calling "
                    "executeBatch or scheduleBatch from the finish method "
                    "(apexdev L17817-17818).",
                ))

    # ---- C002 more than one enqueueJob in one async transaction -----------
    for hdr, ctx in ((Q_EXEC_HDR, "Queueable execute()"), (FINISH_HDR, "batch finish()")):
        if hdr is Q_EXEC_HDR and not is_queueable:
            continue
        if hdr is FINISH_HDR and not is_batchable:
            continue
        found = method_body(src, hdr)
        if not found:
            continue
        body, off = found
        calls = list(ENQUEUE_JOB.finditer(body))
        if len(calls) > 1 and "if" not in body:
            out.append(finding(
                "C002", WARN, path, line_of(src, off + calls[1].start()),
                f"{len(calls)} System.enqueueJob calls in {ctx} with no branching "
                "guard — an async transaction may enqueue only one job.",
                "Keep exactly one enqueue on any path, or branch so only one runs "
                "(apexdev L16175-16177, L16187-16189).",
            ))

    # ---- C003 Stateful collection grown per scope ------------------------
    if is_batchable and STATEFUL.search(src):
        found = method_body(src, EXEC_HDR)
        exec_body = found[0] if found else ""
        # instance (non-static) collection fields declared at class level
        class_level = EXEC_HDR.split(src)[0] if EXEC_HDR.search(src) else src
        for m in COLLECTION_FIELD.finditer(class_level):
            if "static" in m.group(0).lower():
                continue
            name = m.group(2)
            if re.search(rf"\b{re.escape(name)}\s*\.\s*(?:add|addAll|put)\s*\(", exec_body):
                out.append(finding(
                    "C003", ADVISORY, path, line_of(src, m.start()),
                    f"Database.Stateful instance {m.group(1)} field '{name}' grows "
                    "inside execute() — it is re-serialized before every remaining chunk.",
                    "Keep Stateful members to counters/scalars; write per-record detail "
                    "to a staging sObject (apexdev L17519-17521).",
                ))

    # ---- C004 batch started from a trigger --------------------------------
    if is_trigger:
        for rx in (EXECUTE_BATCH, SCHEDULE_BATCH):
            for m in rx.finditer(src):
                out.append(finding(
                    "C004", WARN, path, line_of(src, m.start()),
                    "Batch job started from a trigger — one bulk update can submit "
                    "more jobs than the org's concurrency and flex-queue limits allow.",
                    "Gate on a static recursion flag and a record-count threshold, or "
                    "move the start to a scheduled job (apexdev L17727-17730).",
                ))

    # ---- C005 chaining class with no kill-switch read ---------------------
    chains = False
    for hdr in (FINISH_HDR, Q_EXEC_HDR):
        found = method_body(src, hdr)
        if found and (EXECUTE_BATCH.search(found[0]) or ENQUEUE_JOB.search(found[0])
                      or SCHEDULE_BATCH.search(found[0])):
            chains = True
    if chains and not is_test and not KILL_SWITCH.search(src):
        out.append(finding(
            "C005", ADVISORY, path, 1,
            "This class starts a downstream job but reads no kill-switch "
            "(no __mdt / getInstance / Enabled token anywhere in the file).",
            "Read a Custom Metadata flag before every hand-off so a human can stop "
            "the chain without a deployment. CMDT reads do not count against SOQL "
            "limits (apexdev L19614-19615).",
        ))

    # ---- C006 async started in a test outside startTest/stopTest ----------
    if is_test:
        starts = [m.start() for m in START_TEST.finditer(src)]
        for rx in (ENQUEUE_JOB, EXECUTE_BATCH):
            for m in rx.finditer(src):
                if not any(s < m.start() for s in starts):
                    out.append(finding(
                        "C006", ERROR, path, line_of(src, m.start()),
                        "Async job submitted in a test class with no preceding "
                        "Test.startTest() — the job will not have run when the "
                        "assertions execute.",
                        "Wrap the submission in Test.startTest()/Test.stopTest() "
                        "(apexdev L17740-17743).",
                    ))

    # ---- C007 unbounded Queueable self-chain ------------------------------
    if is_queueable and not is_test:
        found = method_body(src, Q_EXEC_HDR)
        if found and ENQUEUE_JOB.search(found[0]):
            if not IS_RUNNING_TEST.search(src) and not STACK_DEPTH.search(src):
                out.append(finding(
                    "C007", WARN, path, line_of(src, found[1]),
                    "Queueable chains to another job with neither a "
                    "Test.isRunningTest() guard nor an AsyncOptions stack-depth bound.",
                    "Set AsyncOptions.MaximumQueueableStackDepth (and read it back via "
                    "AsyncInfo) — outside Developer/Trial orgs no depth limit is "
                    "enforced (apexdev L16182-16186, L16044-16062).",
                ))

    # ---- C008 FlexQueue.getJobIds does not exist --------------------------
    for m in GET_JOB_IDS.finditer(src):
        out.append(finding(
            "C008", WARN, path, line_of(src, m.start()),
            "System.FlexQueue.getJobIds() is not a real method.",
            "FlexQueue exposes only moveAfterJob, moveBeforeJob, moveJobToEnd and "
            "moveJobToFront (apexrefguide L215739-215762). Read queue depth with SOQL "
            "on AsyncApexJob instead.",
        ))

    # ---- C009 AsyncApexJob query with no JobType filter -------------------
    for m in AGG_ASYNC_QUERY.finditer(src):
        window = src[m.start(): m.start() + 400]
        end = window.find("]")
        window = window[: end if end != -1 else len(window)]
        # A query pinned to specific Ids cannot pick up stray BatchApexWorker rows.
        if re.search(r"\bId\s*(?:=|IN)\s*:", window, re.I):
            continue
        if not re.search(r"\bJobType\b", window, re.I):
            out.append(finding(
                "C009", WARN, path, line_of(src, m.start()),
                "AsyncApexJob query with no JobType predicate — internal "
                "BatchApexWorker rows are included.",
                "Add JobType = 'BatchApex' or JobType != 'BatchApexWorker' "
                "(apexdev L17755-17758).",
            ))

    # ---- C010 illegal literal scope --------------------------------------
    for m in SCOPE_LITERAL.finditer(src):
        try:
            scope = int(m.group(1))
        except ValueError:
            continue
        if scope > 2000:
            out.append(finding(
                "C010", ERROR, path, line_of(src, m.start()),
                f"executeBatch scope literal {scope} exceeds the 2,000 maximum for a "
                "QueryLocator start().",
                "Use a value <= 2000, ideally a factor of 2000 (apexrefguide "
                "L207052-207058). If start() returns an Iterable there is no cap — "
                "say so in a comment.",
            ))
        elif scope <= 0:
            out.append(finding(
                "C010", ERROR, path, line_of(src, m.start()),
                f"executeBatch scope literal {scope} is not greater than zero.",
                "The scope value must be greater than 0 (apexrefguide L207052).",
            ))

    return out


def collect(root: Path) -> list[Path]:
    files: list[Path] = []
    for pattern in ("*.cls", "*.trigger"):
        files.extend(p for p in root.rglob(pattern) if p.is_file())
    return sorted(files)


def run(manifest_dir: Path) -> tuple[list[dict], int, str | None]:
    if not manifest_dir.exists() or not manifest_dir.is_dir():
        return [], 0, f"Manifest directory not found: {manifest_dir}"
    files = collect(manifest_dir)
    findings: list[dict] = []
    for path in files:
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            findings.append(finding("C000", WARN, path, 1, f"Unreadable: {exc}",
                                    "Check file permissions."))
            continue
        findings.extend(check_source(path, raw))
    return findings, len(files), None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Static checks for Apex batch/Queueable chaining implementations.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce source tree to scan (default: current directory).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Promote WARN findings to ERROR for the exit code (ADVISORY stays informational).",
    )
    parser.add_argument("--json", action="store_true", help="Emit findings as JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    findings, scanned, fatal = run(Path(args.manifest_dir))

    if fatal:
        if args.json:
            print(json.dumps({"error": fatal, "scanned_files": 0, "findings": []}, indent=2))
        else:
            print(f"ERROR: {fatal}", file=sys.stderr)
        return 1

    blocking = {ERROR, WARN} if args.strict else {ERROR}
    failed = [f for f in findings if f["severity"] in blocking]

    if args.json:
        print(json.dumps(
            {"scanned_files": scanned, "strict": args.strict,
             "blocking": len(failed), "findings": findings},
            indent=2,
        ))
        return 1 if failed else 0

    if scanned == 0:
        print(f"WARN: no .cls or .trigger files found under {args.manifest_dir}",
              file=sys.stderr)
        return 0

    if not findings:
        print(f"No issues found ({scanned} file(s) scanned).")
        return 0

    for f in findings:
        print(f"{f['severity']:8} {f['code']} {f['file']}:{f['line']}: {f['message']}",
              file=sys.stderr)
        print(f"         fix: {f['fix']}", file=sys.stderr)

    counts = {sev: sum(1 for f in findings if f["severity"] == sev)
              for sev in (ERROR, WARN, ADVISORY)}
    print(
        f"\n{counts[ERROR]} ERROR, {counts[WARN]} WARN, {counts[ADVISORY]} ADVISORY "
        f"across {scanned} file(s)."
        + ("  [--strict: WARN counts as failure]" if args.strict else ""),
        file=sys.stderr,
    )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
