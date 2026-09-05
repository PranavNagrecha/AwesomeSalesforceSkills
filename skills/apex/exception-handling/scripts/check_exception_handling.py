#!/usr/bin/env python3
"""check_exception_handling.py — audit an Apex source tree for exception-handling defects.

Stdlib only. Scans .cls and .trigger files under --manifest-dir and applies the rules
this skill's gotchas are about:

  R1  empty catch block                                              (CRITICAL, swallow)
  R2  catch block whose only executable statement is System.debug    (HIGH, swallow)
  R3  custom exception class naming / inheritance:
        - `extends Exception` but the class name does not end in "Exception"
        - name ends in "Exception" but the class does not extend an exception type
      (apexdev L40143-40145: extend Exception AND end the name in Exception)
  R4  `new AuraHandledException(<something>.getMessage())` inside a class that
      declares @AuraEnabled, with no durable logger call in the same catch block
      (MEDIUM, advisory - the raw DML/Query message carries field API names)
  R5  Database.setSavepoint() followed in the same method by a callout with no
      Database.releaseSavepoint() in between
      (HIGH - apexdev L8742-8750, "All active Savepoints must be released...")
  R6  Database.insert/update/upsert/delete(x, false) whose result is never inspected
      (HIGH - apexdev L9060-9063, partial-success failures never throw)
  R7  a test method that calls something inside try{} and asserts in catch(), with no
      Assert.fail() / System.assert(false, ...) before the catch
      (HIGH - the test passes when the method stops throwing)

Never claims to compile Apex. Every rule is a regex/brace heuristic over source text.

Exit codes: 0 clean, 1 findings, 1 on a missing --manifest-dir.
An empty directory is a WARN with exit 0 - nothing to judge is not a failure.

Usage:
    python3 check_exception_handling.py --manifest-dir force-app/main/default
    python3 check_exception_handling.py --manifest-dir . --format text
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}

CATCH_RE = re.compile(r"\bcatch\s*\(\s*([A-Za-z0-9_.]+)\s+([A-Za-z0-9_]+)\s*\)")
CLASS_DECL_RE = re.compile(
    r"^\s*(?:global|public|private|protected)?\s*(?:abstract\s+|virtual\s+|with\s+sharing\s+|"
    r"without\s+sharing\s+|inherited\s+sharing\s+)*class\s+([A-Za-z0-9_]+)"
    r"(?:\s+extends\s+([A-Za-z0-9_.]+))?",
    re.IGNORECASE,
)
# At least one modifier keyword, then a return type, then the method name. Keeps
# `if (...) {` / `for (...) {` / `catch (...) {` out of the match.
METHOD_DECL_RE = re.compile(
    r"^\s*(?:@\w+\s+)*"
    r"(?:(?:global|public|private|protected|static|override|virtual|testMethod)\s+)+"
    r"[A-Za-z0-9_.]+(?:\s*<[^>()]*>)?(?:\s*\[\s*\])?\s+"
    r"([A-Za-z0-9_]+)\s*\([^;{}]*\)\s*\{?\s*$",
)
SYSTEM_DEBUG_RE = re.compile(r"\bSystem\s*\.\s*debug\s*\(", re.IGNORECASE)
LOGGER_RE = re.compile(
    r"\b(ApplicationLogger|LogService|Logger|Nebula|EventBus\s*\.\s*publish|"
    r"logAndRethrow|logAndSwallow)\b",
    re.IGNORECASE,
)
DURABLE_SINK_RE = re.compile(r"\b(insert|upsert)\s+\w*(log|error|audit)\w*\b", re.IGNORECASE)
AURA_RAW_RE = re.compile(
    r"new\s+AuraHandledException\s*\(\s*[^)]*\b([A-Za-z0-9_]+)\s*\.\s*getMessage\s*\(\s*\)",
)
AURA_ENABLED_RE = re.compile(r"@\s*AuraEnabled", re.IGNORECASE)
SAVEPOINT_RE = re.compile(r"\bDatabase\s*\.\s*setSavepoint\s*\(", re.IGNORECASE)
RELEASE_RE = re.compile(r"\bDatabase\s*\.\s*releaseSavepoint\s*\(", re.IGNORECASE)
CALLOUT_RE = re.compile(
    r"\bnew\s+Http\s*\(\s*\)\s*\.\s*send\s*\(|\bhttp\s*\.\s*send\s*\(|"
    r"\bWebServiceCallout\s*\.\s*invoke\s*\(|setEndpoint\s*\(\s*'callout:",
    re.IGNORECASE,
)
PARTIAL_DML_RE = re.compile(
    r"\bDatabase\s*\.\s*(insert|update|upsert|delete|undelete)\s*\(",
    re.IGNORECASE,
)
RESULT_INSPECT_RE = re.compile(
    r"\b(isSuccess\s*\(|getErrors\s*\(|SaveResult|UpsertResult|DeleteResult|UndeleteResult)\b",
    re.IGNORECASE,
)
IS_TEST_RE = re.compile(r"@\s*is\s*test\b|\btestMethod\b", re.IGNORECASE)
TEST_METHOD_RE = re.compile(r"@\s*is\s*test\b", re.IGNORECASE)
ASSERT_RE = re.compile(r"\b(Assert\s*\.\s*\w+|System\s*\.\s*assert\w*)\s*\(", re.IGNORECASE)
FAIL_RE = re.compile(
    r"\bAssert\s*\.\s*fail\s*\(|\bSystem\s*\.\s*assert\s*\(\s*false\b", re.IGNORECASE
)
EXCEPTION_BASE_RE = re.compile(r"Exception$", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--manifest-dir", required=True, help="Root of the source tree to scan.")
    parser.add_argument(
        "--format", choices=("json", "text"), default="json", help="Output format."
    )
    return parser.parse_args()


def strip_noise(src: str) -> str:
    """Blank string literals and comments in one left-to-right pass, preserving line count."""
    out: list[str] = []
    i, n = 0, len(src)
    while i < n:
        ch = src[i]
        if ch == "'":
            j = i + 1
            while j < n and src[j] != "'":
                j += 2 if src[j] == "\\" else 1
            out.append(" " * (min(j, n - 1) - i + 1))
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


def block_bounds(lines: list[str], header_index: int) -> tuple[int, int]:
    """Return (first_body_line, last_body_line) for the { } block opened at or after header_index."""
    depth = 0
    seen_open = False
    open_line = header_index
    for idx in range(header_index, len(lines)):
        for ch in lines[idx]:
            if ch == "{":
                if not seen_open:
                    seen_open = True
                    open_line = idx
                depth += 1
            elif ch == "}":
                if not seen_open:
                    # a closing brace belonging to the block this header terminates,
                    # e.g. the `}` of `try` in `} catch (DmlException e) {`
                    continue
                depth -= 1
                if depth == 0:
                    return open_line + 1, idx - 1
    return open_line + 1, len(lines) - 1


def executable(body: list[str]) -> list[str]:
    return [ln.strip() for ln in body if ln.strip() and ln.strip() not in {"}", "};", "{"}]


def audit_catches(path: Path, lines: list[str], is_test: bool, has_aura: bool, out: list[str]) -> None:
    for idx, line in enumerate(lines):
        m = CATCH_RE.search(line)
        if not m:
            continue
        exc_type, var = m.group(1), m.group(2)
        start, end = block_bounds(lines, idx)
        body = lines[start : end + 1]
        stmts = executable(body)
        text = "\n".join(body)
        loc = f"{path}:{idx + 1}"

        # R1 empty catch
        if not stmts:
            out.append(f"CRITICAL {loc}: empty catch block for `{exc_type}` swallows the failure")
            continue

        # R2 debug-only catch
        non_debug = [s for s in stmts if not SYSTEM_DEBUG_RE.search(s)]
        if SYSTEM_DEBUG_RE.search(text) and not non_debug:
            out.append(
                f"HIGH {loc}: catch (`{exc_type}`) only calls System.debug - no durable log, "
                f"no rethrow, invisible in production"
            )

        # R4 raw getMessage() into AuraHandledException (advisory)
        raw = AURA_RAW_RE.search(text)
        if raw and has_aura:
            logged = LOGGER_RE.search(text) or DURABLE_SINK_RE.search(text)
            if not logged:
                out.append(
                    f"MEDIUM {loc}: `new AuraHandledException({raw.group(1)}.getMessage())` sends the "
                    f"raw platform message to the client and nothing durable is written in this block"
                )


def audit_classes(path: Path, lines: list[str], out: list[str]) -> None:
    """R3 - custom exception naming and inheritance."""
    for idx, line in enumerate(lines):
        m = CLASS_DECL_RE.match(line)
        if not m:
            continue
        name, parent = m.group(1), (m.group(2) or "")
        loc = f"{path}:{idx + 1}"
        parent_is_exception = bool(parent) and EXCEPTION_BASE_RE.search(parent.split(".")[-1])
        name_is_exception = bool(EXCEPTION_BASE_RE.search(name))
        if parent_is_exception and not name_is_exception:
            out.append(
                f"CRITICAL {loc}: class `{name}` extends `{parent}` but its name does not end in "
                f"'Exception' - it will not compile (apexdev L40143-40145)"
            )
        elif name_is_exception and parent and not parent_is_exception:
            out.append(
                f"HIGH {loc}: class `{name}` is named like an exception but extends `{parent}`, "
                f"not Exception"
            )
        elif name_is_exception and not parent:
            out.append(
                f"HIGH {loc}: class `{name}` is named like an exception but declares no "
                f"`extends Exception`"
            )


def audit_methods(path: Path, lines: list[str], is_test: bool, out: list[str]) -> None:
    """R5 savepoint-then-callout, R6 uninspected partial DML, R7 negative test without Assert.fail."""
    for idx, line in enumerate(lines):
        if not METHOD_DECL_RE.match(line):
            continue
        start, end = block_bounds(lines, idx)
        body = lines[start : end + 1]
        loc = f"{path}:{idx + 1}"

        # R5 savepoint -> callout with no release in between
        sp_line = next((i for i, ln in enumerate(body) if SAVEPOINT_RE.search(ln)), None)
        if sp_line is not None:
            rel_line = next(
                (i for i, ln in enumerate(body) if i > sp_line and RELEASE_RE.search(ln)), None
            )
            call_line = next(
                (i for i, ln in enumerate(body) if i > sp_line and CALLOUT_RE.search(ln)), None
            )
            if call_line is not None and (rel_line is None or rel_line > call_line):
                out.append(
                    f"HIGH {path}:{start + call_line + 1}: callout reached with an active savepoint "
                    f"from line {start + sp_line + 1} - Database.releaseSavepoint() must run first "
                    f"(apexdev L8742-8750)"
                )

        # R6 partial-success DML whose result is never inspected
        for i, ln in enumerate(body):
            dm = PARTIAL_DML_RE.search(ln)
            if not dm:
                continue
            call = ln[dm.start() :]
            if not re.search(r",\s*false\s*\)", call):
                continue
            window = "\n".join(body[i : min(len(body), i + 40)])
            assigned = "=" in ln.split(dm.group(0))[0]
            if not RESULT_INSPECT_RE.search(window) or not assigned:
                out.append(
                    f"HIGH {path}:{start + i + 1}: `Database.{dm.group(1)}(..., false)` allows partial "
                    f"success but no SaveResult inspection follows - row failures are lost silently "
                    f"(apexdev L9060-9063)"
                )

        # R7 negative test with no Assert.fail before the catch
        if not is_test:
            continue
        for i, ln in enumerate(body):
            if not re.match(r"^\s*try\s*\{?\s*$", ln) and "try {" not in ln:
                continue
            t_start, t_end = block_bounds(body, i)
            try_body = executable(body[t_start : t_end + 1])
            if not try_body:
                continue
            catch_idx = next(
                (j for j in range(t_end, min(len(body), t_end + 4)) if CATCH_RE.search(body[j])),
                None,
            )
            if catch_idx is None:
                continue
            c_start, c_end = block_bounds(body, catch_idx)
            catch_body = "\n".join(body[c_start : c_end + 1])
            if not ASSERT_RE.search(catch_body):
                continue
            if not FAIL_RE.search("\n".join(body[t_start : t_end + 1])):
                out.append(
                    f"HIGH {path}:{start + i + 1}: negative test asserts inside `catch` but the try "
                    f"block has no Assert.fail() - it passes when the method stops throwing "
                    f"(apexrefguide L200594-200595)"
                )


def audit_file(path: Path, out: list[str]) -> None:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    src = strip_noise(raw)
    lines = src.splitlines()
    is_test = bool(IS_TEST_RE.search(src))
    has_aura = bool(AURA_ENABLED_RE.search(src))
    audit_classes(path, lines, out)
    audit_catches(path, lines, is_test, has_aura, out)
    audit_methods(path, lines, is_test, out)


def emit(findings: list[str], summary: str, fmt: str, exit_code: int) -> int:
    rows = []
    for item in findings:
        severity, _, remainder = item.partition(" ")
        location, _, message = remainder.partition(": ")
        rows.append({"severity": severity, "location": location, "message": message})
    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(r["severity"], 0) for r in rows))
    if fmt == "text":
        for r in rows:
            print(f"{r['severity']:<9} {r['location']}: {r['message']}")
        print(summary)
    else:
        print(json.dumps({"score": score, "findings": rows, "summary": summary}, indent=2))
    if rows:
        print(f"WARN: {len(rows)} finding(s) detected", file=sys.stderr)
    return exit_code


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.is_dir():
        return emit(
            [f"CRITICAL {root}:0: manifest directory not found"],
            f"Manifest directory {root} does not exist.",
            args.format,
            1,
        )

    files = sorted(p for p in root.rglob("*") if p.is_file() and p.suffix in (".cls", ".trigger"))
    if not files:
        print(f"WARN: no .cls or .trigger files under {root}", file=sys.stderr)
        return emit([], f"Scanned 0 files under {root}; nothing to check.", args.format, 0)

    findings: list[str] = []
    for path in files:
        audit_file(path, findings)

    summary = (
        f"Scanned {len(files)} Apex file(s); {len(findings)} exception-handling finding(s)."
    )
    return emit(findings, summary, args.format, 1 if findings else 0)


if __name__ == "__main__":
    sys.exit(main())
