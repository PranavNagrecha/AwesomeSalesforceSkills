#!/usr/bin/env python3
"""Check Bulk API 2.0 job specs, load files, and loader scripts for an ETL pipeline.

Stdlib only. Scans a folder for:
  * Bulk API 2.0 job request bodies (*.json with "operation" plus "object" or "query")
  * CSV load files (*.csv)
  * loader scripts (*.sh, *.py, *.js, *.ts, *.groovy, *.dwl)

Every rule cites the Summer '26 (262) source it encodes:
  BULK2  = Bulk API 2.0 and Bulk API Developer Guide
  LIMITS = Salesforce Developer Limits and Allocations Quick Reference
  REST   = REST API Developer Guide

Rules
  ETL-JOB-01  ERROR  contentType other than CSV on an ingest or query job. BULK2: "Only CSV is supported."
  ETL-JOB-02  ERROR  upsert without externalIdFieldName. BULK2: "Required for upsert operations."
  ETL-JOB-03  ERROR  Unknown operation. BULK2 ingest: insert, delete, hardDelete, update, upsert;
                     query jobs: query, queryAll.
  ETL-JOB-04  ERROR  Unknown columnDelimiter or lineEnding. BULK2: BACKQUOTE, CARET, COMMA, PIPE,
                     SEMICOLON, TAB; LF or CRLF.
  ETL-JOB-05  WARN   hardDelete. BULK2: deleted records skip the Recycle Bin; the "Bulk API Hard
                     Delete" permission is off by default.
  ETL-CSV-01  ERROR  CSV larger than 150 MB. LIMITS: Bulk API 2.0 maximum file size is 150 MB per job.
  ETL-CSV-02  WARN   CSV larger than 100 MB. LIMITS: base64 adds about 50%; upload no more than 100 MB.
  ETL-REST-01 WARN   A loop in a script that posts to a single-record /sobjects/<Object> URL. BULK2 intro:
                     more than 2,000 records suits Bulk API 2.0; fewer should use bulkified calls
                     such as Composite. REST: sObject Collections carry up to 200 records per call.

Usage
  python3 check_etl_vs_api_data_patterns.py --manifest-dir path/to/folder
  python3 check_etl_vs_api_data_patterns.py --manifest-dir path --strict   # WARN fails too
  python3 check_etl_vs_api_data_patterns.py --self-test

Exit codes: 0 clean (or WARN only without --strict); 1 any ERROR, a missing folder,
or WARN under --strict.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

INGEST_OPS = {"insert", "delete", "hardDelete", "update", "upsert"}
QUERY_OPS = {"query", "queryAll"}
DELIMITERS = {"BACKQUOTE", "CARET", "COMMA", "PIPE", "SEMICOLON", "TAB"}
LINE_ENDINGS = {"LF", "CRLF"}
SCRIPT_SUFFIXES = (".sh", ".py", ".js", ".ts", ".groovy", ".dwl")
MB = 1024 * 1024
SINGLE_SOBJECT_RE = re.compile(r"/sobjects/[A-Za-z0-9_]+/?[\"'\s]")
LOOP_RE = re.compile(r"^\s*(for|while)\b|\.forEach\(|\bmap\(", re.MULTILINE)
Finding = tuple[str, str, str]


def check_job(path: Path, job: dict) -> list[Finding]:
    findings: list[Finding] = []
    op = job.get("operation")
    is_query = "query" in job and "object" not in job
    valid_ops = QUERY_OPS if is_query else INGEST_OPS
    if op not in valid_ops:
        findings.append(("ERROR", "ETL-JOB-03", f"{path}: operation {op!r} is not one of {sorted(valid_ops)}."))
    content_type = job.get("contentType")
    if content_type is not None and content_type != "CSV":
        findings.append(("ERROR", "ETL-JOB-01", f"{path}: contentType {content_type!r}; Bulk API 2.0 supports only CSV."))
    if op == "upsert" and not job.get("externalIdFieldName"):
        findings.append(("ERROR", "ETL-JOB-02", f"{path}: upsert job has no externalIdFieldName."))
    delimiter = job.get("columnDelimiter")
    if delimiter is not None and delimiter not in DELIMITERS:
        findings.append(("ERROR", "ETL-JOB-04", f"{path}: columnDelimiter {delimiter!r} is not valid."))
    line_ending = job.get("lineEnding")
    if line_ending is not None and line_ending not in LINE_ENDINGS:
        findings.append(("ERROR", "ETL-JOB-04", f"{path}: lineEnding {line_ending!r} is not LF or CRLF."))
    if op == "hardDelete":
        findings.append(("WARN", "ETL-JOB-05", f"{path}: hardDelete skips the Recycle Bin and needs the Bulk API Hard Delete permission."))
    return findings


def check_csv(path: Path) -> list[Finding]:
    size = path.stat().st_size
    if size > 150 * MB:
        return [("ERROR", "ETL-CSV-01", f"{path}: {size // MB} MB exceeds the 150 MB Bulk API 2.0 job limit.")]
    if size > 100 * MB:
        return [("WARN", "ETL-CSV-02", f"{path}: {size // MB} MB; keep uploads at or under 100 MB before base64.")]
    return []


def check_script(path: Path, text: str) -> list[Finding]:
    if LOOP_RE.search(text) is None:
        return []
    findings: list[Finding] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if "composite/sobjects" in line:
            continue
        if SINGLE_SOBJECT_RE.search(line) is not None and re.search(r"\b(POST|PATCH|post|patch)\b", line) is not None:
            findings.append(("WARN", "ETL-REST-01",
                             f"{path}:{line_no}: single-record /sobjects/ write in a looping script; "
                             "use sObject Collections under 2,000 records or Bulk API 2.0 above."))
    return findings


def scan(folder: Path) -> tuple[list[Finding], int]:
    findings: list[Finding] = []
    seen = 0
    for path in sorted(p for p in folder.rglob("*") if p.is_file()):
        name = path.name
        if name.endswith(".csv"):
            seen += 1
            findings.extend(check_csv(path))
            continue
        if not (name.endswith(".json") or name.endswith(SCRIPT_SUFFIXES)):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        seen += 1
        if name.endswith(".json"):
            try:
                doc = json.loads(text)
            except ValueError:
                continue
            if isinstance(doc, dict) and "operation" in doc and ("object" in doc or "query" in doc):
                findings.extend(check_job(path, doc))
        else:
            findings.extend(check_script(path, text))
    return findings, seen


def report(findings: list[Finding], strict: bool) -> int:
    for level, rule, message in findings:
        print(f"{level}: [{rule}] {message}")
    errors = sum(1 for f in findings if f[0] == "ERROR")
    warns = sum(1 for f in findings if f[0] == "WARN")
    print(f"{errors} error(s), {warns} warning(s)")
    if errors or (strict and warns):
        return 1
    return 0


def self_test() -> int:
    base = Path(__file__).resolve().parent / "fixtures"
    good, bad = base / "good", base / "bad"
    if not good.is_dir() or not bad.is_dir():
        print("ERROR: fixtures/good or fixtures/bad is missing")
        return 1
    failures = 0
    good_findings, _ = scan(good)
    if good_findings:
        failures += 1
        print("ERROR: self-test: fixtures/good produced findings:")
        for finding in good_findings:
            print(f"  {finding}")
    bad_findings, _ = scan(bad)
    for path in sorted(p for p in bad.iterdir() if p.is_file()):
        if not any(f[2].startswith(str(path)) for f in bad_findings):
            failures += 1
            print(f"ERROR: self-test: {path.name} produced no finding")
    if failures:
        return 1
    print("self-test passed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Bulk API 2.0 job specs, CSV files, and loader scripts.")
    parser.add_argument("--manifest-dir", help="folder to scan")
    parser.add_argument("--strict", action="store_true", help="treat WARN as failure")
    parser.add_argument("--self-test", action="store_true", help="run against scripts/fixtures")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if not args.manifest_dir:
        parser.print_help()
        return 1
    folder = Path(args.manifest_dir)
    if not folder.is_dir():
        print(f"ERROR: {folder} is not a folder")
        sys.exit(1)
    findings, seen = scan(folder)
    if seen == 0:
        print(f"WARN: no job JSON, CSV, or loader scripts under {folder}")
        return 1 if args.strict else 0
    return report(findings, args.strict)


if __name__ == "__main__":
    sys.exit(main())
