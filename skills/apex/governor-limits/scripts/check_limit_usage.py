#!/usr/bin/env python3
"""Scan Apex files for common governor-limit anti-patterns.

Stdlib only. Pass files or folders; prints a JSON report. Exit 1 when findings exist.

Rules and the Apex Developer Guide (262) limit each one protects (see references/limits-table.md):
  CRITICAL  SOQL inside a loop: 100 synchronous / 200 asynchronous queries (L19544).
  CRITICAL  DML inside a loop: 150 DML statements (L19554).
  HIGH      System.enqueueJob in a loop: 50 synchronous / 1 asynchronous (L19573).
  REVIEW    Database.getQueryLocator outside a Database.Batchable class: 10,000 rows (L19548);
            50 million applies only to a Batch QueryLocator (L19856).
  REVIEW    @future with no Queueable in the file: Salesforce recommends Queueable.

Usage
  python3 check_limit_usage.py force-app/main/default
  python3 check_limit_usage.py --self-test
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


TEXT_SUFFIXES = {".cls", ".trigger"}
SOQL_RE = re.compile(r"\[\s*SELECT\b", re.IGNORECASE)
DML_RE = re.compile(r"\b(insert|update|upsert|delete|undelete|merge)\b", re.IGNORECASE)
LOOP_START_RE = re.compile(r"\b(for|while)\b")
QUEUEABLE_RE = re.compile(r"\bSystem\.enqueueJob\s*\(", re.IGNORECASE)
FUTURE_RE = re.compile(r"@future", re.IGNORECASE)
QUERY_LOCATOR_RE = re.compile(r"Database\.getQueryLocator\s*\(", re.IGNORECASE)
BATCHABLE_RE = re.compile(r"\bimplements\b[^{;]*\bDatabase\.Batchable\b", re.IGNORECASE)
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def iter_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(candidate for candidate in path.rglob("*") if candidate.is_file())
    return sorted(set(files))


def normalize_finding(finding: str) -> dict[str, str]:
    severity, _, remainder = finding.partition(" ")
    location = ""
    message = remainder
    if ": " in remainder:
        location, message = remainder.split(": ", 1)
    return {"severity": severity or "INFO", "location": location, "message": message}


def emit_result(findings: list[str], summary: str) -> int:
    normalized = [normalize_finding(item) for item in findings]
    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(item["severity"], 0) for item in normalized))
    print(json.dumps({"score": score, "findings": normalized, "summary": summary}, indent=2))
    if normalized:
        print(f"WARN: {len(normalized)} finding(s) detected", file=sys.stderr)
    return 1 if normalized else 0


def audit_file(path: Path) -> list[str]:
    findings: list[str] = []
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return findings

    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    loop_depth = 0
    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if LOOP_START_RE.search(line) and "for each" not in line.lower():
            loop_depth += line.count("{") or 1

        if loop_depth > 0 and SOQL_RE.search(line):
            findings.append(f"CRITICAL {path}:{line_number}: SOQL detected inside a loop")

        if loop_depth > 0 and DML_RE.search(line) and not line.lower().startswith("//"):
            findings.append(f"CRITICAL {path}:{line_number}: DML detected inside a loop")

        if QUEUEABLE_RE.search(line) and "for " in line:
            findings.append(f"HIGH {path}:{line_number}: Queueable jobs appear to be enqueued inside a loop")

        if "{" in line and LOOP_START_RE.search(line):
            continue
        if "}" in line and loop_depth > 0:
            loop_depth = max(0, loop_depth - line.count("}"))

    text = "\n".join(lines)
    if QUERY_LOCATOR_RE.search(text) and not BATCHABLE_RE.search(text):
        findings.append(f"REVIEW {path}: Database.getQueryLocator outside a Batchable class is capped at 10,000 rows; 50 million applies only to a Batch start method")
    if FUTURE_RE.search(text) and not QUEUEABLE_RE.search(text):
        findings.append(f"REVIEW {path}: @future usage found; confirm Queueable is not the better modern choice")
    return findings


def self_test() -> int:
    base = Path(__file__).resolve().parent / "fixtures"
    good, bad = base / "good", base / "bad"
    if not good.is_dir() or not bad.is_dir():
        print("ERROR: fixtures/good or fixtures/bad is missing")
        return 1
    failures = 0
    for path in iter_files([str(good)]):
        found = audit_file(path)
        if found:
            failures += 1
            print(f"ERROR: self-test: good fixture {path.name} produced {found}")
    for path in iter_files([str(bad)]):
        if not audit_file(path):
            failures += 1
            print(f"ERROR: self-test: bad fixture {path.name} produced no finding")
    if failures:
        return 1
    print("self-test passed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check Apex files for governor-limit anti-patterns such as SOQL or DML inside loops."
    )
    parser.add_argument("paths", nargs="*", help="Files or directories to inspect")
    parser.add_argument("--self-test", action="store_true", help="Run against scripts/fixtures/good and bad.")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if not args.paths:
        parser.print_help()
        return 1

    files = iter_files(args.paths)
    if not files:
        return emit_result(
            ["HIGH no Apex files matched the provided paths"],
            "Scanned 0 Apex files; no matching .cls or .trigger files were found.",
        )

    findings: list[str] = []
    scanned = 0
    for path in files:
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        scanned += 1
        findings.extend(audit_file(path))

    if scanned == 0:
        findings.append("HIGH no Apex files matched the provided paths")
    summary = f"Scanned {scanned} Apex file(s); {len(findings)} finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
