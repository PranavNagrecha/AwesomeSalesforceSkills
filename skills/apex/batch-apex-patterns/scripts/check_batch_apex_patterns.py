#!/usr/bin/env python3
"""Audit Batch Apex implementations for common lifecycle and scale issues."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


BATCH_RE = re.compile(r"implements\s+[^{;]*Database\.Batchable", re.IGNORECASE)
STATEFUL_RE = re.compile(r"Database\.Stateful", re.IGNORECASE)
ALLOWS_CALLOUTS_RE = re.compile(r"Database\.AllowsCallouts", re.IGNORECASE)
HTTP_RE = re.compile(r"\bHttp(Request|Response)?\b")
QUERY_LOCATOR_RE = re.compile(r"Database\.getQueryLocator\s*\(", re.IGNORECASE)
EXECUTE_BATCH_SCOPE_RE = re.compile(r"Database\.executeBatch\s*\([^,]+,\s*(\d+)\s*\)", re.IGNORECASE)
ASYNC_JOB_RE = re.compile(r"AsyncApexJob|getJobId\s*\(", re.IGNORECASE)
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Batch Apex classes for scope, callout, and monitoring anti-patterns.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory to scan for Apex classes.")
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


def iter_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.cls") if path.is_file())


def audit_file(path: Path) -> list[str]:
    findings: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore")

    if BATCH_RE.search(text):
        if HTTP_RE.search(text) and not ALLOWS_CALLOUTS_RE.search(text):
            findings.append(f"HIGH {path}: Batch class appears to make callouts without `Database.AllowsCallouts`")
        if "start(" in text and not QUERY_LOCATOR_RE.search(text):
            findings.append(f"REVIEW {path}: Batch class does not use `Database.getQueryLocator()`; verify Iterable/list input is intentional")
        if "finish(" in text and not ASYNC_JOB_RE.search(text):
            findings.append(f"REVIEW {path}: `finish()` found without obvious `AsyncApexJob` or job-ID visibility logic")
        if STATEFUL_RE.search(text) and len(text.splitlines()) > 120:
            findings.append(f"REVIEW {path}: large `Database.Stateful` batch found; verify state payload is lightweight")

    for match in EXECUTE_BATCH_SCOPE_RE.finditer(text):
        scope = int(match.group(1))
        if scope > 200:
            findings.append(f"REVIEW {path}: batch scope {scope} detected; confirm it is safe for payload size and limits")

    return findings


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        return emit_result([f"HIGH {root}: manifest directory not found"], "Scanned 0 Apex classes; manifest directory was missing.")
    files = iter_files(root)
    if not files:
        return emit_result([f"HIGH {root}: no Apex classes found"], "Scanned 0 Apex classes; no .cls files were found.")
    findings: list[str] = []
    for path in files:
        findings.extend(audit_file(path))
    summary = f"Scanned {len(files)} Apex class file(s); {len(findings)} batch-pattern finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
