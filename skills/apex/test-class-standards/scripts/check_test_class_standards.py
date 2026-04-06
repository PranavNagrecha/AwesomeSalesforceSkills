#!/usr/bin/env python3
"""Audit Apex test classes for common isolation and assertion issues."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


TEST_CLASS_RE = re.compile(r"@isTest|\btestMethod\b", re.IGNORECASE)
ASSERT_RE = re.compile(r"\b(System\.)?assert[A-Za-z]*\s*\(|\bAssert\.", re.IGNORECASE)
SEE_ALL_DATA_RE = re.compile(r"SeeAllData\s*=\s*true", re.IGNORECASE)
ASYNC_CALL_RE = re.compile(r"System\.enqueueJob|Database\.executeBatch|System\.schedule", re.IGNORECASE)
START_TEST_RE = re.compile(r"Test\.startTest\s*\(", re.IGNORECASE)
STOP_TEST_RE = re.compile(r"Test\.stopTest\s*\(", re.IGNORECASE)
HARD_CODED_ID_RE = re.compile(r"['\"][a-zA-Z0-9]{15,18}['\"]")
TEST_SETUP_RE = re.compile(r"@testSetup", re.IGNORECASE)
INSERT_RE = re.compile(r"\binsert\b", re.IGNORECASE)
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex test classes for weak assertions, org-data dependence, and async test mistakes."
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory to scan for Apex classes.",
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
    return sorted(path for path in root.rglob("*.cls") if path.is_file())


def audit_test_class(path: Path) -> list[str]:
    findings: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore")
    if not TEST_CLASS_RE.search(text):
        return findings

    if SEE_ALL_DATA_RE.search(text):
        findings.append(f"HIGH {path}: test class uses `SeeAllData=true`; verify org-data dependency is truly required")

    if not ASSERT_RE.search(text):
        findings.append(f"CRITICAL {path}: test class has no obvious assertions")

    if ASYNC_CALL_RE.search(text) and not (START_TEST_RE.search(text) and STOP_TEST_RE.search(text)):
        findings.append(f"HIGH {path}: async behavior detected without a complete `Test.startTest()` / `Test.stopTest()` boundary")

    if HARD_CODED_ID_RE.search(text):
        findings.append(f"MEDIUM {path}: hard-coded Salesforce-style ID literal found in test class")

    if text.lower().count("@istest") + text.lower().count(" testmethod ") >= 3 and not TEST_SETUP_RE.search(text):
        if len(INSERT_RE.findall(text)) >= 4:
            findings.append(f"REVIEW {path}: multiple test methods with repeated inserts but no `@testSetup`; consider shared setup")

    if "System.assert(true" in text.replace(" ", "") or "System.assertEquals(true" in text.replace(" ", ""):
        findings.append(f"MEDIUM {path}: assertion pattern suggests coverage-only verification")

    return findings


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        return emit_result([f"HIGH {root}: manifest directory not found"], "Scanned 0 Apex classes; manifest directory was missing.")

    files = iter_apex_files(root)
    if not files:
        return emit_result([f"HIGH {root}: no Apex classes found"], "Scanned 0 Apex classes; no .cls files were found.")

    findings: list[str] = []
    tested = 0
    for path in files:
        file_findings = audit_test_class(path)
        if TEST_CLASS_RE.search(path.read_text(encoding="utf-8", errors="ignore")):
            tested += 1
        findings.extend(file_findings)

    if tested == 0:
        findings.append(f"REVIEW {root}: no Apex test classes detected in the scanned tree")
    summary = f"Scanned {len(files)} Apex class file(s); evaluated {tested} test class(es); {len(findings)} finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
