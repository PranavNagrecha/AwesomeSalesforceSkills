#!/usr/bin/env python3
"""Checker for the bulk-api-patterns skill.

Scans integration source (.cls, .trigger, .py, .js, .ts, .java, .sh) for Bulk API
2.0 call-sequence mistakes described in the Bulk API 2.0 Developer Guide.

Severity:
  ERROR  a file that uploads ingest data (jobs/ingest .../batches, no
         multipart) but never sets the state to UploadComplete (the job stays
         Open); a file that reads Sforce-Locator but never compares it with the
         string "null" (the loop cannot detect the last set).
  WARN   ingest code that never reads failedResults or unprocessedrecords;
         the camelCase path `unprocessedRecords` (the documented URI is
         lowercase); `Sforce-Enable-PKChunking` sent to a v2 jobs/query
         endpoint (v2 chunks automatically); `concurrencyMode` set to Serial in
         a v2 job body (parallel only); the v1 `X-SFDC-Session` header in a file
         that calls v2 endpoints.

Exit codes: 0 clean or WARN only; 1 on ERROR, missing directory, or WARN with
--strict. An empty directory prints a WARN and exits 0. Stdlib only.

Usage:
    python3 check_bulk_api_patterns.py --manifest-dir path/to/integration [--strict]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

EXTENSIONS = {".cls", ".trigger", ".py", ".js", ".ts", ".java", ".sh"}
INGEST_RE = re.compile(r"jobs/ingest", re.IGNORECASE)
QUERY_RE = re.compile(r"jobs/query", re.IGNORECASE)
MULTIPART_RE = re.compile(r"multipart/form-data", re.IGNORECASE)
UPLOAD_COMPLETE_RE = re.compile(r"UploadComplete")
FAILED_RE = re.compile(r"failedResults", re.IGNORECASE)
UNPROCESSED_ANY_RE = re.compile(r"unprocessedrecords", re.IGNORECASE)
UNPROCESSED_CAMEL_RE = re.compile(r"unprocessedRecords")
LOCATOR_RE = re.compile(r"Sforce-Locator", re.IGNORECASE)
NULL_STRING_RE = re.compile(r"""[!=]==?\s*["']null["']|["']null["']\s*[!=]==?|["']null["']\.equals\(""", re.IGNORECASE)
UPLOAD_RE = re.compile(r"/batches", re.IGNORECASE)
PK_HEADER_RE = re.compile(r"Sforce-Enable-PKChunking", re.IGNORECASE)
SERIAL_RE = re.compile(r"concurrencyMode[\"']?\s*[:=]\s*[\"']Serial", re.IGNORECASE)
V1_SESSION_RE = re.compile(r"X-SFDC-Session", re.IGNORECASE)
V2_PATH_RE = re.compile(r"/services/data/v\d+\.\d+/jobs/", re.IGNORECASE)


def first_line(src: str, rx: re.Pattern) -> int:
    m = rx.search(src)
    return src.count("\n", 0, m.start()) + 1 if m is not None else 1


def scan(path: Path) -> list[tuple[str, str]]:
    src = path.read_text(encoding="utf-8", errors="replace")
    out: list[tuple[str, str]] = []
    ingest = INGEST_RE.search(src) is not None
    uploads = ingest and UPLOAD_RE.search(src) is not None
    if uploads and MULTIPART_RE.search(src) is None and UPLOAD_COMPLETE_RE.search(src) is None:
        out.append(("ERROR", f"{path}:{first_line(src, UPLOAD_RE)}: uploads ingest data but never sets state UploadComplete; a standard job stays Open"))
    if LOCATOR_RE.search(src) is not None and NULL_STRING_RE.search(src) is None:
        out.append(("ERROR", f"{path}:{first_line(src, LOCATOR_RE)}: reads Sforce-Locator but never compares it with the string \"null\"; the pagination loop cannot detect the last set"))
    if ingest and (FAILED_RE.search(src) is None or UNPROCESSED_ANY_RE.search(src) is None):
        out.append(("WARN", f"{path}:{first_line(src, INGEST_RE)}: ingest code does not read both failedResults and unprocessedrecords; reconciliation is incomplete"))
    if UNPROCESSED_CAMEL_RE.search(src) is not None:
        out.append(("WARN", f"{path}:{first_line(src, UNPROCESSED_CAMEL_RE)}: path uses 'unprocessedRecords'; the documented URI is .../unprocessedrecords/"))
    if QUERY_RE.search(src) is not None and PK_HEADER_RE.search(src) is not None and V2_PATH_RE.search(src) is not None:
        out.append(("WARN", f"{path}:{first_line(src, PK_HEADER_RE)}: Sforce-Enable-PKChunking is a Bulk API v1 header; v2 query jobs chunk automatically"))
    if SERIAL_RE.search(src) is not None and V2_PATH_RE.search(src) is not None:
        out.append(("WARN", f"{path}:{first_line(src, SERIAL_RE)}: concurrencyMode Serial in a v2 job; Bulk API 2.0 supports parallel mode only"))
    if V1_SESSION_RE.search(src) is not None and V2_PATH_RE.search(src) is not None:
        out.append(("WARN", f"{path}:{first_line(src, V1_SESSION_RE)}: X-SFDC-Session is v1 authentication; v2 uses an OAuth bearer token"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Flag Bulk API 2.0 call-sequence mistakes (bulk-api-patterns skill).")
    ap.add_argument("--manifest-dir", default=".", help="Root of the integration source to scan")
    ap.add_argument("--strict", action="store_true", help="Treat WARN as failure")
    args = ap.parse_args()

    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)

    files = sorted(p for p in root.rglob("*") if p.is_file() and p.suffix in EXTENSIONS)
    if not files:
        print(f"WARN: no source files ({', '.join(sorted(EXTENSIONS))}) under {root}; nothing to check")
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
