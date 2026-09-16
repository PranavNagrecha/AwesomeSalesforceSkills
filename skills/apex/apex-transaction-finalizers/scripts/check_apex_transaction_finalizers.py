#!/usr/bin/env python3
"""Checker for the apex-transaction-finalizers skill.

Static analysis of Apex source (*.cls) for the defect shapes that the compiler
cannot see and that `references/gotchas.md` documents. Stdlib only, no network,
no org connection. This script NEVER compiles Apex and never claims to — every
finding is a lexical/regex signal over the source text.

Checks (each maps to a gotcha or anti-pattern in this skill package):

  F001  Class implements Finalizer but has no `execute(FinalizerContext ...)`
        -> apexrefguide L215587: `public void execute(System.FinalizerContext)`.
  F002  `System.attachFinalizer(...)` called outside a Queueable `execute`
        -> apexdev L16543-16567 "System.attachFinalizer(Finalizer) is not
           allowed in this context".
  F003  More than one `attachFinalizer` call in one Queueable `execute`
        -> apexdev L16543-16567 "More than one Finalizer cannot be attached to
           same Async Apex Job".
  F004  Finalizer re-enqueues with no bounded attempt counter, or with a
        ceiling >= 5 -> apexdev L16293-16295 (five consecutive re-enqueues).
  F005  More than one async-job start (`enqueueJob` / `executeBatch` / a
        `@future` call) inside a Finalizer `execute`
        -> apexdev L16355-16356 (a single asynchronous Apex job).
  F006  `getJobId()` used on a FinalizerContext parameter
        -> apexdev L16317: the four methods are getAsyncApexJobId,
           getRequestId, getResult, getException.
  F007  `transient` field on a Finalizer implementation
        -> apexdev L16360-16362 (transient vars don't persist in the finalizer).
  F008  Unguarded DML inside a Finalizer `execute` (no try/catch and not the
        partial-success `Database.<op>(x, false)` form)
        -> apexdev L16578-16587 (finalizer runtime errors are log-only).
  F009  `System.attachFinalizer` inside a Finalizer's own execute
        -> same context error as F002.
  F010  No @IsTest class anywhere in the tree names the Finalizer class.
  F011  Finalizer class has no explicit sharing declaration
        -> apexdev L4870-4874 (recommended on any class doing DML/SOQL).

Usage:
    python3 check_apex_transaction_finalizers.py --manifest-dir force-app
    python3 check_apex_transaction_finalizers.py --manifest-dir force-app --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# Lexical helpers
# --------------------------------------------------------------------------

CLASS_DECL = re.compile(
    r"^[ \t]*(?:@\w+(?:\([^)]*\))?[ \t]*)*"
    r"(?P<mods>(?:(?:global|public|private|protected|virtual|abstract|with\s+sharing"
    r"|without\s+sharing|inherited\s+sharing|static)\s+)*)"
    r"class\s+(?P<name>\w+)(?P<rest>[^{]*)\{",
    re.M,
)
IMPLEMENTS = re.compile(r"\bimplements\s+([^{]+)", re.S)
FINALIZER_EXECUTE = re.compile(
    r"\bvoid\s+execute\s*\(\s*(?:System\s*\.\s*)?FinalizerContext\s+(\w+)\s*\)", re.M
)
QUEUEABLE_EXECUTE = re.compile(
    r"\bvoid\s+execute\s*\(\s*(?:System\s*\.\s*)?QueueableContext\s+(\w+)\s*\)", re.M
)
ATTACH = re.compile(r"\bSystem\s*\.\s*attachFinalizer\s*\(")
ENQUEUE = re.compile(r"\bSystem\s*\.\s*enqueueJob\s*\(")
EXECUTE_BATCH = re.compile(r"\bDatabase\s*\.\s*executeBatch\s*\(")
DML_STMT = re.compile(r"\b(?:insert|update|upsert|delete|undelete|merge)\s+(?:as\s+\w+\s+)?[A-Za-z_]\w*")
DML_DATABASE = re.compile(r"\bDatabase\s*\.\s*(insert|update|upsert|delete|undelete|merge)\s*\(([^;]*)")
TRANSIENT_FIELD = re.compile(r"^[^/\n]*\btransient\b[^;{}\n]*;", re.M)
MAX_CONST = re.compile(
    r"\b(?:Integer|Long)\s+(?P<name>\w*(?:MAX|LIMIT|CEILING|ATTEMPT|RETRY)\w*)\s*=\s*(?P<value>\d+)",
    re.I,
)
SHARING_KEYWORDS = ("with sharing", "without sharing", "inherited sharing")
PLATFORM_RETRY_CAP = 5


def strip_noise(src: str) -> str:
    """Blank `//` line comments, `/* … */` block comments, and `'…'` literals to spaces.

    Comments first so a possessive apostrophe inside a comment never opens a string.
    Same length as `src`; newlines in block comments stay newlines so line numbers stay aligned.
    """
    out: list[str] = []
    i, n = 0, len(src)
    while i < n:
        ch = src[i]
        if ch == "/" and i + 1 < n and src[i + 1] == "/":
            j = i
            while j < n and src[j] != "\n":
                out.append(" ")
                j += 1
            i = j
            continue
        if ch == "/" and i + 1 < n and src[i + 1] == "*":
            out.append(" ")
            out.append(" ")
            j = i + 2
            while j + 1 < n and not (src[j] == "*" and src[j + 1] == "/"):
                out.append("\n" if src[j] == "\n" else " ")
                j += 1
            if j + 1 < n:
                out.append(" ")
                out.append(" ")
                j += 2
            elif j < n:
                out.append("\n" if src[j] == "\n" else " ")
                j += 1
            i = j
            continue
        if ch == "'":
            out.append(" ")
            i += 1
            while i < n:
                if src[i] == "\n":
                    out.append("\n")
                    i += 1
                    break
                if src[i] == "\\" and i + 1 < n:
                    out.append(" ")
                    out.append(" ")
                    i += 2
                    continue
                if src[i] == "'":
                    if i + 1 < n and src[i + 1] == "'":
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


def matching_brace(src: str, open_idx: int) -> int:
    """Index just past the '}' that closes the '{' at open_idx, or len(src)."""
    depth = 0
    for i in range(open_idx, len(src)):
        ch = src[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i + 1
    return len(src)


def method_body(src: str, decl_end: int) -> str:
    """Body of the method whose signature ends at decl_end."""
    brace = src.find("{", decl_end)
    if brace == -1:
        return ""
    return src[brace: matching_brace(src, brace)]


def line_of(src: str, idx: int) -> int:
    return src.count("\n", 0, idx) + 1


# --------------------------------------------------------------------------
# Per-file analysis
# --------------------------------------------------------------------------


class ApexFile:
    def __init__(self, path: Path, raw: str) -> None:
        self.path = path
        self.raw = raw
        self.src = strip_noise(raw)
        self.is_test = "@istest" in self.src.lower()

        self.class_name = ""
        self.class_mods = ""
        self.implements: list[str] = []
        m = CLASS_DECL.search(self.src)
        if m:
            self.class_name = m.group("name")
            self.class_mods = m.group("mods") or ""
            impl = IMPLEMENTS.search(m.group("rest") or "")
            if impl:
                self.implements = [
                    part.strip().split(".")[-1]
                    for part in impl.group(1).replace("\n", " ").split(",")
                    if part.strip()
                ]

        self.fin_match = FINALIZER_EXECUTE.search(self.src)
        self.que_match = QUEUEABLE_EXECUTE.search(self.src)
        self.fin_body = method_body(self.src, self.fin_match.end()) if self.fin_match else ""
        self.que_body = method_body(self.src, self.que_match.end()) if self.que_match else ""
        self.fin_ctx_var = self.fin_match.group(1) if self.fin_match else ""

    @property
    def declares_finalizer(self) -> bool:
        return any(i == "Finalizer" for i in self.implements)

    @property
    def declares_queueable(self) -> bool:
        return any(i == "Queueable" for i in self.implements)


def issue(code: str, path: Path, line: int, message: str, fix: str) -> dict:
    return {"code": code, "file": str(path), "line": line, "message": message, "fix": fix}


def check_file(f: ApexFile, all_files: list[ApexFile]) -> list[dict]:
    out: list[dict] = []
    src = f.src

    # ---- F001 -----------------------------------------------------------
    if f.declares_finalizer and f.fin_match is None:
        out.append(issue(
            "F001", f.path, line_of(src, src.find("class")),
            f"{f.class_name} implements Finalizer but declares no "
            f"execute(FinalizerContext ...) method.",
            "Add `public void execute(FinalizerContext ctx)` — the interface "
            "signature is `public void execute(System.FinalizerContext)` "
            "(apexrefguide L215587).",
        ))

    # ---- F002 / F003 / F009 --------------------------------------------
    attach_positions = [m.start() for m in ATTACH.finditer(src)]
    if attach_positions:
        que_start = src.find(f.que_body) if f.que_body else -1
        que_end = que_start + len(f.que_body) if que_start != -1 else -1
        fin_start = src.find(f.fin_body) if f.fin_body else -1
        fin_end = fin_start + len(f.fin_body) if fin_start != -1 else -1

        in_queueable = [p for p in attach_positions if que_start <= p < que_end]
        in_finalizer = [p for p in attach_positions if fin_start <= p < fin_end and fin_start != -1]
        elsewhere = [
            p for p in attach_positions
            if p not in in_queueable and p not in in_finalizer
        ]

        for p in in_finalizer:
            out.append(issue(
                "F009", f.path, line_of(src, p),
                "System.attachFinalizer() called inside a Finalizer's own "
                "execute() — a Finalizer transaction is not a Queueable context.",
                "Spend the single enqueue slot on a new Queueable that attaches "
                "its own Finalizer instead (apexdev L16543-16567).",
            ))
        for p in elsewhere:
            out.append(issue(
                "F002", f.path, line_of(src, p),
                "System.attachFinalizer() is not inside an "
                "execute(QueueableContext ...) method.",
                "Move the call into the Queueable's execute(); outside one the "
                "platform logs `System.attachFinalizer(Finalizer) is not allowed "
                "in this context` (apexdev L16543-16567).",
            ))
        if len(in_queueable) > 1:
            out.append(issue(
                "F003", f.path, line_of(src, in_queueable[1]),
                f"{len(in_queueable)} attachFinalizer() calls in one "
                "execute(QueueableContext ...).",
                "Attach exactly once, as the first statement — a second call logs "
                "`More than one Finalizer cannot be attached to same Async Apex "
                "Job` (apexdev L16543-16567, L16354).",
            ))

    if not f.fin_body:
        return out

    # Scope for the Finalizer-side checks: the whole class, minus the Queueable
    # half when one class implements both interfaces. Blanking the Queueable
    # body (rather than slicing it out) keeps every index aligned with `src`,
    # so reported line numbers stay accurate.
    fin = src
    if f.que_body:
        q_start = src.find(f.que_body)
        if q_start != -1:
            blanked = re.sub(r"[^\n]", " ", f.que_body)
            fin = src[:q_start] + blanked + src[q_start + len(f.que_body):]
    fin_offset = 0

    # Extents of every try{...} block in scope, for the DML guard check.
    try_spans: list[tuple[int, int]] = []
    for m in re.finditer(r"\btry\s*\{", fin):
        brace = fin.index("{", m.start())
        try_spans.append((brace, matching_brace(fin, brace)))

    def inside_try(pos: int) -> bool:
        return any(start <= pos < end for start, end in try_spans)

    # ---- F004 / F005 ----------------------------------------------------
    async_starts = (
        [("System.enqueueJob", m.start()) for m in ENQUEUE.finditer(fin)]
        + [("Database.executeBatch", m.start()) for m in EXECUTE_BATCH.finditer(fin)]
    )
    if len(async_starts) > 1:
        out.append(issue(
            "F005", f.path, line_of(src, fin_offset + async_starts[1][1]),
            f"{len(async_starts)} async-job starts inside the Finalizer "
            f"({', '.join(name for name, _ in async_starts)}).",
            "A finalizer may enqueue a single asynchronous Apex job — Queueable, "
            "Future or Batch (apexdev L16355-16356). Do the logging with DML in "
            "this transaction and keep the slot for the retry.",
        ))

    if async_starts:
        ceilings = [(m.group("name"), int(m.group("value"))) for m in MAX_CONST.finditer(src)]
        guarded = bool(
            ceilings
            and re.search(r"\b(?:" + "|".join(re.escape(n) for n, _ in ceilings) + r")\b", fin)
        )
        if not guarded:
            out.append(issue(
                "F004", f.path, line_of(src, fin_offset + async_starts[0][1]),
                "Finalizer re-enqueues with no attempt ceiling in scope.",
                "Carry an attempt counter on the Finalizer and compare it against "
                "a MAX_ATTEMPTS constant. Unbounded retry is not an infinite loop "
                "— the platform fails the enqueue on the fifth consecutive "
                "failure and your dead-letter branch never runs "
                "(apexdev L16293-16295, L16523).",
            ))
        else:
            for name, value in ceilings:
                if re.search(r"\b" + re.escape(name) + r"\b", fin) and value >= PLATFORM_RETRY_CAP:
                    out.append(issue(
                        "F004", f.path, line_of(src, src.find(name)),
                        f"Retry ceiling {name} = {value} is at or above the "
                        f"platform cap of {PLATFORM_RETRY_CAP} consecutive "
                        "re-enqueues.",
                        "Lower it to 3 or 4 so your own dead-letter DML runs "
                        "before the platform fails the enqueue "
                        "(apexdev L16293-16295).",
                    ))

    # ---- F006 -----------------------------------------------------------
    bad = None
    if f.fin_ctx_var:
        bad = re.search(
            r"\b" + re.escape(f.fin_ctx_var) + r"\s*\.\s*getJobId\s*\(", f.fin_body
        )
        if bad:
            bad_pos = src.find(f.fin_body) + bad.start()
    if bad is None and not f.declares_queueable:
        # Pure Finalizer class: getJobId() cannot legitimately appear anywhere.
        bad = re.search(r"\.\s*getJobId\s*\(", src)
        if bad:
            bad_pos = bad.start()
    if bad:
        out.append(issue(
            "F006", f.path, line_of(src, bad_pos),
            "getJobId() called on a FinalizerContext.",
            "FinalizerContext has four methods: getAsyncApexJobId, "
            "getRequestId, getResult, getException (apexdev L16317). "
            "getJobId() belongs to QueueableContext.",
        ))

    # ---- F007 -----------------------------------------------------------
    for m in TRANSIENT_FIELD.finditer(src):
        out.append(issue(
            "F007", f.path, line_of(src, m.start()),
            f"transient field on Finalizer implementation {f.class_name}: "
            f"{m.group(0).strip()[:80]}",
            "Remove `transient`. Transient variables are ignored by "
            "serialization and don't persist in the Transaction Finalizer "
            "(apexdev L16360-16362) — the field is silently empty at run time.",
        ))

    # ---- F008 -----------------------------------------------------------
    offenders: list[tuple[int, str]] = []
    for m in DML_STMT.finditer(fin):
        if not inside_try(m.start()):
            offenders.append((m.start(), m.group(0).strip()))
    for m in DML_DATABASE.finditer(fin):
        # Database.insert(x, false) degrades to partial success; that counts as guarded.
        if re.search(r",\s*false\s*\)", m.group(2)):
            continue
        if not inside_try(m.start()):
            offenders.append((m.start(), f"Database.{m.group(1)}(...)"))
    if offenders:
        for pos, text in sorted(offenders)[:1]:
            out.append(issue(
                "F008", f.path, line_of(src, fin_offset + pos),
                f"Unguarded DML in the Finalizer: `{text}`.",
                "Wrap it in try/catch, or use Database.<op>(records, false). A "
                "Finalizer that throws has no second Finalizer to catch it — the "
                "failure appears only as `Error processing finalizer for "
                "queueable job id:` in the log (apexdev L16578-16587).",
            ))

    # ---- F010 -----------------------------------------------------------
    if f.class_name:
        referenced = any(
            other is not f
            and other.is_test
            and re.search(r"\b" + re.escape(f.class_name) + r"\b", other.src)
            for other in all_files
        )
        if not referenced and not f.is_test:
            out.append(issue(
                "F010", f.path, line_of(src, src.find("class")),
                f"No @IsTest class in the tree references {f.class_name}.",
                "Add a test that drives both ParentJobResult.SUCCESS and "
                "ParentJobResult.UNHANDLED_EXCEPTION — see "
                "references/code-examples.md section 6.",
            ))

    # ---- F011 -----------------------------------------------------------
    mods = f.class_mods.lower().replace("\t", " ")
    mods = re.sub(r"\s+", " ", mods)
    if not any(k in mods for k in SHARING_KEYWORDS) and not f.is_test:
        out.append(issue(
            "F011", f.path, line_of(src, src.find("class")),
            f"{f.class_name} has no explicit sharing declaration.",
            "Declare `with sharing` / `inherited sharing`. The guide recommends "
            "an explicit declaration on any class that does DML or SOQL "
            "(apexdev L4870-4874), even though v67.0+ defaults to with sharing "
            "(apexdev L4961).",
        ))

    return out


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------


def collect(manifest_dir: Path) -> list[ApexFile]:
    files: list[ApexFile] = []
    for path in sorted(manifest_dir.rglob("*.cls")):
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        files.append(ApexFile(path, raw))
    return files


def run(manifest_dir: Path) -> tuple[list[dict], int]:
    if not manifest_dir.exists():
        return [issue("F000", manifest_dir, 0,
                      f"Manifest directory not found: {manifest_dir}",
                      "Pass --manifest-dir pointing at the source tree "
                      "(e.g. force-app).")], 0

    files = collect(manifest_dir)
    if not files:
        return [issue("F000", manifest_dir, 0,
                      f"No .cls files found under {manifest_dir}",
                      "Point --manifest-dir at a directory containing Apex "
                      "classes.")], 0

    relevant = [
        f for f in files
        if f.declares_finalizer or f.fin_match is not None or ATTACH.search(f.src)
    ]
    findings: list[dict] = []
    for f in relevant:
        findings.extend(check_file(f, files))
    return findings, len(relevant)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Static checks for Apex Transaction Finalizer implementations.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce source tree to scan (default: current directory).",
    )
    parser.add_argument("--json", action="store_true", help="Emit findings as JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    findings, scanned = run(Path(args.manifest_dir))

    if args.json:
        print(json.dumps({"scanned_classes": scanned, "findings": findings}, indent=2))
        return 1 if findings else 0

    if not findings:
        print(f"No issues found ({scanned} Finalizer-related class(es) scanned).")
        return 0

    for f in findings:
        print(f"{f['code']} {f['file']}:{f['line']}: {f['message']}", file=sys.stderr)
        print(f"      fix: {f['fix']}", file=sys.stderr)
    print(
        f"\n{len(findings)} issue(s) across {scanned} Finalizer-related class(es).",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
