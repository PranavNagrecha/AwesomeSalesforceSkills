#!/usr/bin/env python3
"""Static checks for Apex callout retry / resilience anti-patterns.

Scans .cls files passed on the command line (or recursively under a directory)
and flags:

    P0  Http().send( inside a for/while loop with no retry-count guard
    P0  try/catch around HttpRequest with an empty catch block
    P1  HttpResponse with a 4xx status code triggering enqueueJob
        (retry of a non-retryable response)

Exit codes:
    0   no findings
    1   one or more P0 / P1 findings
    2   usage error

Stdlib only. No pip dependencies.
"""

from __future__ import annotations

import os
import re
import sys
from typing import Iterable, List, Optional, Tuple


HTTP_SEND_RE = re.compile(r"new\s+Http\s*\(\s*\)\s*\.\s*send\s*\(", re.IGNORECASE)
LOOP_OPEN_RE = re.compile(r"\b(for|while)\s*\(", re.IGNORECASE)
ATTEMPT_GUARD_RE = re.compile(
    r"\b(attempt|retries?|retry|maxAttempts?|tries|i|n|count)\b\s*[<>]=?",
    re.IGNORECASE,
)
ENQUEUE_RE = re.compile(r"System\.enqueueJob\s*\(", re.IGNORECASE)
STATUS_4XX_RE = re.compile(
    r"getStatusCode\s*\(\s*\)\s*(==|>=|>)\s*(4\d\d)", re.IGNORECASE
)
STATUS_4XX_RANGE_RE = re.compile(
    r"getStatusCode\s*\(\s*\)\s*>=\s*400\s*&&\s*getStatusCode\s*\(\s*\)\s*<\s*500",
    re.IGNORECASE,
)
TRY_RE = re.compile(r"\btry\s*\{", re.IGNORECASE)
CATCH_OPEN_RE = re.compile(r"\bcatch\s*\(([^)]*)\)\s*\{", re.IGNORECASE)


def _strip_comments(src: str) -> str:
    """Remove // and /* */ comments so they don't fool regex matches."""
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.DOTALL)
    src = re.sub(r"//[^\n]*", "", src)
    return src


def _line_no(src: str, idx: int) -> int:
    return src.count("\n", 0, idx) + 1


def _find_enclosing_loop(src: str, send_idx: int) -> Optional[Tuple[int, int, int]]:
    """Find the nearest preceding for/while header whose `{` block contains send_idx.

    Returns (header_start_idx, brace_open_idx, brace_close_idx) or None.
    """
    best: Optional[Tuple[int, int, int]] = None
    for m in LOOP_OPEN_RE.finditer(src, 0, send_idx):
        i = m.end()
        depth = 1
        while i < len(src) and depth > 0:
            ch = src[i]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            i += 1
        while i < len(src) and src[i] not in "{;":
            i += 1
        if i >= len(src) or src[i] != "{":
            continue
        brace_open = i
        depth = 1
        j = brace_open + 1
        while j < len(src) and depth > 0:
            if src[j] == "{":
                depth += 1
            elif src[j] == "}":
                depth -= 1
            j += 1
        brace_close = j
        if brace_open < send_idx < brace_close:
            best = (m.start(), brace_open, brace_close)
    return best


def _block_text(src: str, brace_open: int) -> str:
    depth = 1
    j = brace_open + 1
    while j < len(src) and depth > 0:
        if src[j] == "{":
            depth += 1
        elif src[j] == "}":
            depth -= 1
        j += 1
    return src[brace_open:j]


def check_file(path: str) -> List[Tuple[str, int, str, str]]:
    """Return list of (severity, line, rule, message) findings for the file."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            raw = fh.read()
    except OSError as exc:
        return [("ERROR", 0, "io", f"could not read {path}: {exc}")]

    if not raw.strip():
        return []

    src = _strip_comments(raw)
    findings: List[Tuple[str, int, str, str]] = []

    # Rule 1 (P0): Http().send( inside a loop with no attempt-guard variable.
    for m in HTTP_SEND_RE.finditer(src):
        encl = _find_enclosing_loop(src, m.start())
        if encl is None:
            continue
        header_start, brace_open, _ = encl
        header_text = src[header_start:brace_open]
        block_text = _block_text(src, brace_open)
        if ATTEMPT_GUARD_RE.search(header_text) or ATTEMPT_GUARD_RE.search(block_text):
            continue
        findings.append(
            (
                "P0",
                _line_no(src, m.start()),
                "unbounded-retry-loop",
                "Http().send() inside loop with no attempt-counter guard "
                "(unbounded retry risk).",
            )
        )

    # Rule 2 (P1): 4xx response triggers enqueueJob (retry of non-retryable).
    for m in ENQUEUE_RE.finditer(src):
        window_start = max(0, m.start() - 600)
        window = src[window_start:m.start()]
        if STATUS_4XX_RE.search(window) or STATUS_4XX_RANGE_RE.search(window):
            findings.append(
                (
                    "P1",
                    _line_no(src, m.start()),
                    "retrying-4xx",
                    "enqueueJob appears to be triggered for a 4xx response — "
                    "4xx (except 408/429) is NOT retryable.",
                )
            )

    # Rule 3 (P0): try around HttpRequest with empty catch block.
    for tm in TRY_RE.finditer(src):
        i = tm.end()
        depth = 1
        while i < len(src) and depth > 0:
            if src[i] == "{":
                depth += 1
            elif src[i] == "}":
                depth -= 1
            i += 1
        try_body = src[tm.end():max(tm.end(), i - 1)]
        has_callout = (
            "HttpRequest" in try_body
            or HTTP_SEND_RE.search(try_body) is not None
        )
        if not has_callout:
            continue
        cm = CATCH_OPEN_RE.search(src, i)
        if cm is None or cm.start() - i > 40:
            continue
        cstart = cm.end()
        depth = 1
        j = cstart
        while j < len(src) and depth > 0:
            if src[j] == "{":
                depth += 1
            elif src[j] == "}":
                depth -= 1
            j += 1
        catch_body = src[cstart:max(cstart, j - 1)].strip()
        if catch_body == "":
            findings.append(
                (
                    "P0",
                    _line_no(src, cm.start()),
                    "empty-catch-on-callout",
                    "Empty catch block around HttpRequest — failure swallowed; "
                    "use dead-letter or rethrow.",
                )
            )

    return findings


def iter_cls_files(targets: Iterable[str]) -> Iterable[str]:
    for t in targets:
        if os.path.isdir(t):
            for root, _, files in os.walk(t):
                for fn in files:
                    if fn.endswith(".cls"):
                        yield os.path.join(root, fn)
        elif os.path.isfile(t) and t.endswith(".cls"):
            yield t


def main(argv: List[str]) -> int:
    if len(argv) < 2:
        print(
            "usage: check_apex_callout_retry_and_resilience.py <file-or-dir> [...]",
            file=sys.stderr,
        )
        return 2
    targets = list(iter_cls_files(argv[1:]))
    if not targets:
        print("no .cls files found in given paths", file=sys.stderr)
        return 0
    worst = 0
    for path in targets:
        findings = check_file(path)
        for severity, line, rule, msg in findings:
            print(f"{path}:{line}: [{severity}] {rule}: {msg}")
            if severity in ("P0", "P1"):
                worst = 1
    return worst


if __name__ == "__main__":
    rc = main(sys.argv)
    if rc == 1:
        # Findings reported above; exit non-zero so CI fails the build.
        sys.exit(1)
    sys.exit(rc)
