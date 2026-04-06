#!/usr/bin/env python3
"""Audit Apex HTTP callout code for common security and reliability issues."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


TEXT_SUFFIXES = {".cls", ".trigger"}
HTTP_RE = re.compile(r"\b(HttpRequest|Http\b|HttpResponse)\b")
ENDPOINT_RE = re.compile(r"setEndpoint\s*\(\s*(['\"])(.+?)\1\s*\)", re.IGNORECASE)
TIMEOUT_RE = re.compile(r"setTimeout\s*\(", re.IGNORECASE)
QUEUEABLE_RE = re.compile(r"\bimplements\b[^{;]*\bQueueable\b", re.IGNORECASE)
ALLOWS_CALLOUTS_RE = re.compile(r"\bDatabase\.AllowsCallouts\b", re.IGNORECASE)
SETMOCK_RE = re.compile(r"Test\.setMock\s*\(\s*HttpCalloutMock\.class", re.IGNORECASE)
TEST_CLASS_RE = re.compile(r"@isTest|\btestMethod\b", re.IGNORECASE)
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex callout code for hardcoded endpoints, missing timeouts, and weak testability."
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory to scan for Apex classes and triggers.",
    )
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


def audit_file(path: Path) -> list[str]:
    findings: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore")
    if not HTTP_RE.search(text):
        return findings

    if path.suffix.lower() == ".trigger":
        findings.append(f"CRITICAL {path}: trigger contains HTTP callout code; move outbound work out of trigger context")

    if QUEUEABLE_RE.search(text) and not ALLOWS_CALLOUTS_RE.search(text):
        findings.append(f"HIGH {path}: Queueable appears to perform callouts without `Database.AllowsCallouts`")

    if not TIMEOUT_RE.search(text):
        findings.append(f"MEDIUM {path}: callout code has no explicit `setTimeout()`")

    for match in ENDPOINT_RE.finditer(text):
        endpoint = match.group(2)
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            findings.append(f"HIGH {path}: hardcoded absolute endpoint `{endpoint}` found; prefer Named Credential `callout:` syntax")
        elif not endpoint.startswith("callout:"):
            findings.append(f"REVIEW {path}: endpoint `{endpoint}` does not use Named Credential syntax")

    if TEST_CLASS_RE.search(text) and HTTP_RE.search(text) and not SETMOCK_RE.search(text):
        findings.append(f"HIGH {path}: test class references HTTP objects without obvious `Test.setMock(HttpCalloutMock.class, ...)` usage")

    return findings


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        return emit_result([f"HIGH {root}: manifest directory not found"], "Scanned 0 Apex files; manifest directory was missing.")

    files = iter_apex_files(root)
    if not files:
        return emit_result([f"HIGH {root}: no Apex files found"], "Scanned 0 Apex files; no .cls or .trigger files were found.")

    findings: list[str] = []
    scanned = 0
    for path in files:
        scanned += 1
        findings.extend(audit_file(path))

    summary = f"Scanned {scanned} Apex file(s); {len(findings)} callout/integration finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
