#!/usr/bin/env python3
"""Audit Apex structure for layering and responsibility anti-patterns."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


TRIGGER_RE = re.compile(r"trigger\s+\w+\s+on\s+\w+\s*\(", re.IGNORECASE)
SOQL_RE = re.compile(r"\[\s*SELECT\b", re.IGNORECASE)
DML_RE = re.compile(r"\b(insert|update|upsert|delete|undelete|merge)\b", re.IGNORECASE)
HTTP_RE = re.compile(r"\bHttp(Request|Response)?\b")
TEST_RUNNING_RE = re.compile(r"Test\.isRunningTest\s*\(", re.IGNORECASE)
UTIL_CLASS_RE = re.compile(r"\bclass\s+\w*Util\w*\b")
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Apex files for fat triggers, god classes, and missing test seams.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory to scan for Apex classes and triggers.")
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
    return sorted(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in {".cls", ".trigger"})


def audit_file(path: Path) -> list[str]:
    findings: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()

    if path.suffix.lower() == ".trigger" and TRIGGER_RE.search(text):
        if SOQL_RE.search(text) or DML_RE.search(text):
            findings.append(f"HIGH {path}: trigger body contains direct SOQL or DML; verify it delegates to a handler/service")

    if path.suffix.lower() == ".cls":
        score = sum(bool(pattern.search(text)) for pattern in (SOQL_RE, DML_RE, HTTP_RE))
        if score >= 3 and len(lines) > 80:
            findings.append(f"REVIEW {path}: class mixes query, DML, and HTTP concerns; possible god-class")
        if TEST_RUNNING_RE.search(text):
            findings.append(f"MEDIUM {path}: `Test.isRunningTest()` found; consider interface-based dependency injection instead")
        if UTIL_CLASS_RE.search(text) and (SOQL_RE.search(text) or DML_RE.search(text)):
            findings.append(f"REVIEW {path}: utility-style class contains data access or DML; verify responsibility is clear")

    return findings


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        return emit_result([f"HIGH {root}: manifest directory not found"], "Scanned 0 Apex files; manifest directory was missing.")
    files = iter_files(root)
    if not files:
        return emit_result([f"HIGH {root}: no Apex files found"], "Scanned 0 Apex files; no .cls or .trigger files were found.")

    findings: list[str] = []
    for path in files:
        findings.extend(audit_file(path))
    summary = f"Scanned {len(files)} Apex file(s); {len(findings)} design-pattern finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
