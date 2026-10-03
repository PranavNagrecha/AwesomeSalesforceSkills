#!/usr/bin/env python3
"""Audit Apex files for common Async Apex selection and implementation risks.

Stdlib only. Scans *.cls and *.trigger under --manifest-dir and prints a JSON report.
Exit 1 when any finding is reported.

Rules and the Apex Developer Guide (262) statement each one encodes:
  CRITICAL  System.enqueueJob inside a loop. 50 enqueues per synchronous transaction, 1 per
            asynchronous transaction (Per-Transaction Apex Limits).
  CRITICAL  HTTP callout code in a trigger. Move outbound work to async Apex.
  HIGH      Queueable making callouts without Database.AllowsCallouts ("Queueable Apex" note).
  HIGH      More than one enqueue in a Queueable file. Only one child job per parent.
  HIGH      @future call inside a Database.Batchable class. 0 future calls in batch and
            future contexts (Per-Transaction Apex Limits).
  HIGH      HTTP callout inside a Schedulable class with no Queueable or Batch dispatch.
            "Synchronous Web service callouts aren't supported from scheduled Apex."
  REVIEW    Legacy @future usage. Salesforce recommends Queueable instead.
  REVIEW    Batch scope above 200; above 2,000 a QueryLocator is re-chunked to 2,000.

Usage
  python3 check_async_apex.py --manifest-dir force-app/main/default
  python3 check_async_apex.py --self-test
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


TEXT_SUFFIXES = {".cls", ".trigger"}
LOOP_START_RE = re.compile(r"\b(for|while)\b")
ENQUEUE_RE = re.compile(r"\bSystem\.enqueueJob\s*\(", re.IGNORECASE)
FUTURE_RE = re.compile(r"@future", re.IGNORECASE)
QUEUEABLE_CLASS_RE = re.compile(r"\bimplements\b[^{;]*\bQueueable\b", re.IGNORECASE)
ALLOWS_CALLOUTS_RE = re.compile(r"\bDatabase\.AllowsCallouts\b", re.IGNORECASE)
HTTP_RE = re.compile(r"\b(HttpRequest|Http\b|WebServiceCallout)\b")
BATCHABLE_RE = re.compile(r"\bimplements\b[^{;]*\bDatabase\.Batchable\b", re.IGNORECASE)
SCHEDULABLE_RE = re.compile(r"\bimplements\b[^{;]*\bSchedulable\b", re.IGNORECASE)
FUTURE_CALL_TARGETS_RE = re.compile(r"@future[^\n]*\n\s*(?:public|global|private)?\s*static\s+void\s+(\w+)", re.IGNORECASE)
DISPATCH_RE = re.compile(r"System\.enqueueJob|Database\.executeBatch", re.IGNORECASE)
EXECUTE_BATCH_RE = re.compile(r"Database\.executeBatch\s*\([^,]+,\s*(\d+)\s*\)", re.IGNORECASE)
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex files for Async Apex anti-patterns such as looped enqueues or weak callout setup."
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory to scan for Apex classes and triggers.",
    )
    parser.add_argument("--self-test", action="store_true", help="Run against scripts/fixtures/good and bad.")
    return parser.parse_args()


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


def iter_apex_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES
    )


FUTURE_METHOD_NAMES: set[str] = set()


def collect_future_methods(files: list[Path]) -> None:
    FUTURE_METHOD_NAMES.clear()
    for path in files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        FUTURE_METHOD_NAMES.update(m.group(1) for m in FUTURE_CALL_TARGETS_RE.finditer(text))


def audit_file(path: Path) -> list[str]:
    findings: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()

    loop_depth = 0
    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if LOOP_START_RE.search(line) and "for each" not in line.lower():
            loop_depth += line.count("{") or 1

        if loop_depth > 0 and ENQUEUE_RE.search(line):
            findings.append(f"CRITICAL {path}:{line_number}: `System.enqueueJob()` appears inside a loop")

        if "}" in line and loop_depth > 0:
            loop_depth = max(0, loop_depth - line.count("}"))

    if FUTURE_RE.search(text):
        findings.append(f"REVIEW {path}: legacy `@future` usage found; confirm Queueable is not the better fit")

    if QUEUEABLE_CLASS_RE.search(text) and HTTP_RE.search(text) and not ALLOWS_CALLOUTS_RE.search(text):
        findings.append(f"HIGH {path}: Queueable appears to make callouts without `Database.AllowsCallouts`")

    if path.suffix.lower() == ".trigger" and HTTP_RE.search(text):
        findings.append(f"CRITICAL {path}: trigger contains HTTP callout code; move outbound work to async Apex")

    if "void execute(QueueableContext" in text and text.count("System.enqueueJob(") > 1:
        findings.append(f"HIGH {path}: Queueable file contains multiple enqueue calls; verify single-child chaining rule")

    if BATCHABLE_RE.search(text) and FUTURE_METHOD_NAMES:
        for name in sorted(FUTURE_METHOD_NAMES):
            if re.search(rf"\.\s*{re.escape(name)}\s*\(", text) or (re.search(rf"\b{re.escape(name)}\s*\(", text) and "@future" not in text.lower()):
                findings.append(f"HIGH {path}: Batchable class calls @future method {name}; batch and future contexts allow 0 future calls")
                break

    if SCHEDULABLE_RE.search(text) and HTTP_RE.search(text) and not DISPATCH_RE.search(text):
        findings.append(f"HIGH {path}: Schedulable makes HTTP calls; synchronous callouts aren't supported from scheduled Apex, so enqueue a Queueable with Database.AllowsCallouts")

    for match in EXECUTE_BATCH_RE.finditer(text):
        scope = int(match.group(1))
        if scope > 2000:
            findings.append(f"REVIEW {path}: batch scope {scope}; a QueryLocator start method is re-chunked to at most 2,000 records")
        elif scope > 200:
            findings.append(f"REVIEW {path}: batch scope {scope} detected; verify throughput, callout, and heap assumptions")

    return findings


def self_test() -> int:
    base = Path(__file__).resolve().parent / "fixtures"
    good, bad = base / "good", base / "bad"
    if not good.is_dir() or not bad.is_dir():
        print("ERROR: fixtures/good or fixtures/bad is missing")
        return 1
    failures = 0
    for folder, expect_findings in ((good, False), (bad, True)):
        files = iter_apex_files(folder)
        collect_future_methods(files)
        for path in files:
            all_found = audit_file(path)
            found = [f for f in all_found if not f.startswith("REVIEW")]
            if expect_findings and not all_found:
                failures += 1
                print(f"ERROR: self-test: bad fixture {path.name} produced no finding")
            if not expect_findings and found:
                failures += 1
                print(f"ERROR: self-test: good fixture {path.name} produced {found}")
    if failures:
        return 1
    print("self-test passed")
    return 0


def main() -> int:
    args = parse_args()
    if args.self_test:
        return self_test()
    root = Path(args.manifest_dir)
    if not root.exists():
        return emit_result([f"HIGH {root}: manifest directory not found"], "Scanned 0 Apex files; manifest directory was missing.")

    files = iter_apex_files(root)
    if not files:
        return emit_result([f"HIGH {root}: no Apex files found"], "Scanned 0 Apex files; no .cls or .trigger files were found.")

    collect_future_methods(files)
    findings: list[str] = []
    for path in files:
        findings.extend(audit_file(path))

    summary = f"Scanned {len(files)} Apex file(s); {len(findings)} async-Apex finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
