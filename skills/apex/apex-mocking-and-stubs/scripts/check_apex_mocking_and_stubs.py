#!/usr/bin/env python3
"""Audit Apex tests and seams for mocking anti-patterns."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


TEST_CLASS_RE = re.compile(r"@isTest|\btestMethod\b", re.IGNORECASE)
HTTP_RE = re.compile(r"\bHttp(Request|Response)?\b")
SETMOCK_RE = re.compile(r"Test\.setMock\s*\(", re.IGNORECASE)
CREATE_STUB_RE = re.compile(r"Test\.createStub\s*\(", re.IGNORECASE)
STUB_PROVIDER_RE = re.compile(r"implements\s+StubProvider", re.IGNORECASE)
TEST_RUNNING_RE = re.compile(r"Test\.isRunningTest\s*\(", re.IGNORECASE)
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Apex files for weak mocking seams and transport-mock mistakes.")
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
    if TEST_CLASS_RE.search(text):
        if HTTP_RE.search(text) and not SETMOCK_RE.search(text):
            findings.append(f"HIGH {path}: test class references HTTP types without obvious `Test.setMock(...)` usage")
        if CREATE_STUB_RE.search(text) and not STUB_PROVIDER_RE.search(text):
            findings.append(f"REVIEW {path}: `Test.createStub()` found without a local `StubProvider`; verify the stub seam is defined elsewhere intentionally")
    else:
        if TEST_RUNNING_RE.search(text):
            findings.append(f"MEDIUM {path}: `Test.isRunningTest()` found in production code; verify a mock seam is missing")

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
    summary = f"Scanned {len(files)} Apex class file(s); {len(findings)} mocking/stub finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
