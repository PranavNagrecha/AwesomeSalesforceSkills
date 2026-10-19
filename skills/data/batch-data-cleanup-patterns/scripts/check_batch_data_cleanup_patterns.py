#!/usr/bin/env python3
"""Checker for the batch-data-cleanup-patterns skill.

Scans Apex (.cls, .trigger) with comments stripped.

Severity:
  ERROR  `delete [SELECT ...]` or Database.delete inside a .trigger file (bulk
         deletion in the caller's transaction); bare `delete <var>;` in a class
         that implements Database.Batchable (all-or-none: one failure rolls back
         the chunk).
  WARN   Database.emptyRecycleBin inside finish() (the method accepts at most
         10,000 records per call; purge per chunk instead); `< LAST_N_YEARS:`
         (calendar-aligned, not "older than n years"); Database.executeBatch in a
         .trigger file (five queued/active batch jobs at a time); a Batchable
         that calls Database.delete but never checks isSuccess(); a test class
         with SeeAllData=true that runs a batch.

Exit codes: 0 clean or WARN only; 1 on ERROR, missing directory, or WARN with
--strict. An empty directory prints a WARN and exits 0. Stdlib only.

Usage:
    python3 check_batch_data_cleanup_patterns.py --manifest-dir force-app/main/default [--strict]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

BATCHABLE_RE = re.compile(r"\bimplements\b[^{]*\bDatabase\.Batchable\b", re.IGNORECASE)
TRIGGER_DELETE_RE = re.compile(r"\bdelete\s*\[\s*SELECT\b|\bDatabase\.delete\s*\(", re.IGNORECASE)
BARE_DELETE_RE = re.compile(r"^\s*delete\s+\w+\s*;", re.IGNORECASE | re.MULTILINE)
DB_DELETE_RE = re.compile(r"\bDatabase\.delete\s*\(", re.IGNORECASE)
IS_SUCCESS_RE = re.compile(r"\.isSuccess\s*\(", re.IGNORECASE)
FINISH_RE = re.compile(r"\bvoid\s+finish\s*\(", re.IGNORECASE)
EMPTY_BIN_RE = re.compile(r"\bDatabase\.emptyRecycleBin\s*\(", re.IGNORECASE)
LAST_N_YEARS_RE = re.compile(r"<\s*LAST_N_YEARS\s*:", re.IGNORECASE)
EXECUTE_BATCH_RE = re.compile(r"\bDatabase\.executeBatch\s*\(", re.IGNORECASE)
SEE_ALL_DATA_RE = re.compile(r"@isTest\s*\(\s*SeeAllData\s*=\s*true", re.IGNORECASE)


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


def method_body(src: str, start: int) -> tuple[int, int]:
    """Return (open, close) offsets of the brace block that follows start."""
    open_i = src.find("{", start)
    if open_i == -1:
        return start, start
    depth = 0
    for j in range(open_i, len(src)):
        if src[j] == "{":
            depth += 1
        elif src[j] == "}":
            depth -= 1
            if depth == 0:
                return open_i, j
    return open_i, len(src)


def line_at(src: str, offset: int) -> int:
    return src.count("\n", 0, offset) + 1


def scan(path: Path) -> list[tuple[str, str]]:
    src = strip_comments(path.read_text(encoding="utf-8", errors="replace"))
    out: list[tuple[str, str]] = []
    if path.suffix == ".trigger":
        for m in TRIGGER_DELETE_RE.finditer(src):
            out.append(("ERROR", f"{path}:{line_at(src, m.start())}: bulk delete inside a trigger runs in the caller's transaction; move it to a scheduled batch"))
        for m in EXECUTE_BATCH_RE.finditer(src):
            out.append(("WARN", f"{path}:{line_at(src, m.start())}: executeBatch from a trigger; bulk saves can exceed the five queued/active batch jobs"))
        return out
    batchable = BATCHABLE_RE.search(src) is not None
    if batchable:
        for m in BARE_DELETE_RE.finditer(src):
            out.append(("ERROR", f"{path}:{line_at(src, m.start())}: bare delete in a Batchable is all-or-none; use Database.delete(scope, false) and log failures"))
        if DB_DELETE_RE.search(src) is not None and IS_SUCCESS_RE.search(src) is None:
            m = DB_DELETE_RE.search(src)
            out.append(("WARN", f"{path}:{line_at(src, m.start())}: Database.delete results are never checked with isSuccess(); failures go unrecorded"))
        fm = FINISH_RE.search(src)
        if fm is not None:
            a, b = method_body(src, fm.end())
            em = EMPTY_BIN_RE.search(src, a, b)
            if em is not None:
                out.append(("WARN", f"{path}:{line_at(src, em.start())}: emptyRecycleBin in finish(); it accepts at most 10,000 records per call, so purge per chunk in execute()"))
    for m in LAST_N_YEARS_RE.finditer(src):
        out.append(("WARN", f"{path}:{line_at(src, m.start())}: '< LAST_N_YEARS' is calendar-aligned (ends Dec 31 of last year); bind a computed Date for rolling retention"))
    if SEE_ALL_DATA_RE.search(src) is not None and EXECUTE_BATCH_RE.search(src) is not None:
        m = SEE_ALL_DATA_RE.search(src)
        out.append(("WARN", f"{path}:{line_at(src, m.start())}: SeeAllData=true in a batch test; insert records on both sides of the cutoff instead"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Flag batch cleanup anti-patterns (batch-data-cleanup-patterns skill).")
    ap.add_argument("--manifest-dir", default=".", help="Root to scan for .cls and .trigger files")
    ap.add_argument("--strict", action="store_true", help="Treat WARN as failure")
    args = ap.parse_args()

    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)

    files = sorted(list(root.rglob("*.cls")) + list(root.rglob("*.trigger")))
    if not files:
        print(f"WARN: no .cls or .trigger files under {root}; nothing to check")
        return 0

    findings: list[tuple[str, str]] = []
    for f in files:
        findings.extend(scan(f))
    errors = sum(1 for s, _ in findings if s == "ERROR")
    warns = len(findings) - errors
    for sev, msg in findings:
        print(f"{sev}: {msg}")
    print(f"Scanned {len(files)} file(s): {errors} ERROR, {warns} WARN")
    if errors or (args.strict and warns):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
