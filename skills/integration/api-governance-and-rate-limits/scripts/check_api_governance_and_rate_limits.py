#!/usr/bin/env python3
"""Checker for the api-governance-and-rate-limits skill.

Scans integration client code (.js .ts .mjs .py .java .cls .cs .go .rb) that calls the
Salesforce APIs for limit-handling mistakes.

ERROR  a file that handles REQUEST_LIMIT_EXCEEDED inside an unbounded loop
       (while (true) / while True / for (;;)) — a retry storm against an allocation
WARN   retry logic keyed on HTTP 429 in a file that calls Salesforce (the daily and
       concurrency limits return REQUEST_LIMIT_EXCEEDED; the daily one is HTTP 403)
WARN   REQUEST_LIMIT_EXCEEDED handled without reading /limits or DailyApiRequests,
       so daily exhaustion can't be told apart from concurrency
WARN   use of composite/batch (each subrequest counts against limits; /composite
       counts once)
WARN   setInterval / schedule polling /limits more often than once a minute

A file "calls Salesforce" if it mentions /services/data/ or a known SF client.
Comments are not stripped (keep examples of what not to do out of scanned code).
Exit 1 on ERROR (or WARN with --strict) and when --manifest-dir is missing. Stdlib only.

Usage:
    python3 check_api_governance_and_rate_limits.py --manifest-dir path/to/integration
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SUFFIXES = {".js", ".ts", ".mjs", ".cjs", ".py", ".java", ".cls", ".cs", ".go", ".rb"}
SF_RE = re.compile(r"/services/data/|jsforce|simple_salesforce|Sforce-Limit-Info|REQUEST_LIMIT_EXCEEDED", re.I)
RLE_RE = re.compile(r"REQUEST_LIMIT_EXCEEDED")
UNBOUNDED_RE = re.compile(r"while\s*\(\s*true\s*\)|while\s+True\s*:|for\s*\(\s*;\s*;\s*\)")
RETRY_429_RE = re.compile(r"(status(Code)?|\.status)\s*(===?|==)\s*429|\b429\b[^\n]{0,60}retr|retr[^\n]{0,60}\b429\b", re.I)
LIMITS_RE = re.compile(r"/limits\b|DailyApiRequests", re.I)
BATCH_RE = re.compile(r"composite/batch", re.I)
INTERVAL_RE = re.compile(r"setInterval\s*\([^,]+,\s*(\d+)\s*\)")


def scan(path: Path, out: list[tuple[str, str]]) -> bool:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if not SF_RE.search(text):
        return False
    if RLE_RE.search(text) and UNBOUNDED_RE.search(text):
        out.append(("ERROR", f"{path}: REQUEST_LIMIT_EXCEEDED handled in a file with an unbounded loop; bound attempts and open a circuit breaker on daily exhaustion"))
    m = RETRY_429_RE.search(text)
    if m:
        out.append(("WARN", f"{path}:{text.count(chr(10), 0, m.start()) + 1}: retry keyed on HTTP 429; Salesforce API limits return REQUEST_LIMIT_EXCEEDED (daily limit: HTTP 403)"))
    if RLE_RE.search(text) and not LIMITS_RE.search(text):
        out.append(("WARN", f"{path}: handles REQUEST_LIMIT_EXCEEDED without reading /limits (DailyApiRequests.Remaining) to tell daily exhaustion from concurrency"))
    m = BATCH_RE.search(text)
    if m:
        out.append(("WARN", f"{path}:{text.count(chr(10), 0, m.start()) + 1}: composite/batch counts each subrequest; use /composite when the goal is fewer counted calls"))
    if LIMITS_RE.search(text):
        for im in INTERVAL_RE.finditer(text):
            if int(im.group(1)) < 60000:
                out.append(("WARN", f"{path}:{text.count(chr(10), 0, im.start()) + 1}: polls more often than once a minute; /limits is accurate within five minutes"))
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check integration code for Salesforce API limit handling.")
    parser.add_argument("--manifest-dir", required=True, type=Path, help="Integration source directory to scan.")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on WARN as well as ERROR.")
    args = parser.parse_args(argv)
    root = args.manifest_dir
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)
    out: list[tuple[str, str]] = []
    files = [p for p in sorted(root.rglob("*")) if p.is_file() and p.suffix in SUFFIXES and "node_modules" not in p.parts]
    scanned = sum(1 for p in files if scan(p, out))
    if not scanned:
        print(f"WARN: no source files calling Salesforce APIs under {root}; nothing to check")
        return 0
    for level, msg in out:
        print(f"{level}: {msg}")
    errors = sum(1 for lvl, _ in out if lvl == "ERROR")
    warns = len(out) - errors
    print(f"Scanned {scanned} file(s): {errors} error(s), {warns} warning(s).")
    return 1 if errors or (args.strict and warns) else 0


if __name__ == "__main__":
    sys.exit(main())
