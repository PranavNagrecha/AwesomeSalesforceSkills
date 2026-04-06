#!/usr/bin/env python3
"""Audit Apex logging usage and debug noise."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


TEST_CLASS_RE = re.compile(r"@isTest|\btestMethod\b", re.IGNORECASE)
SYSTEM_DEBUG_RE = re.compile(r"System\.debug\s*\(", re.IGNORECASE)
LOG_LEVEL_RE = re.compile(r"System\.debug\s*\(\s*LoggingLevel\.", re.IGNORECASE)
SENSITIVE_RE = re.compile(r"password|token|secret|authorization|bearer", re.IGNORECASE)
ASYNC_RE = re.compile(r"implements\s+Queueable|implements\s+Database\.Batchable|System\.enqueueJob|Database\.executeBatch", re.IGNORECASE)
ASYNC_JOB_RE = re.compile(r"AsyncApexJob|getJobId\s*\(", re.IGNORECASE)
LOGGER_RE = re.compile(r"Log__c|Logger|logError|logInfo|EventBus\.publish", re.IGNORECASE)
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Apex files for excessive debug usage and weak logging patterns.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory to scan for Apex files.")
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
        return findings

    debug_count = len(SYSTEM_DEBUG_RE.findall(text))
    if debug_count >= 5:
        findings.append(f"REVIEW {path}: {debug_count} `System.debug` statements found; verify debug noise is intentional")
    if debug_count > 0 and not LOG_LEVEL_RE.search(text):
        findings.append(f"MEDIUM {path}: `System.debug` usage found without explicit `LoggingLevel`")
    if debug_count > 0 and SENSITIVE_RE.search(text):
        findings.append(f"HIGH {path}: debug logging appears near sensitive terms such as token or password")
    if ASYNC_RE.search(text) and not (ASYNC_JOB_RE.search(text) or LOGGER_RE.search(text)):
        findings.append(f"REVIEW {path}: async code found without obvious job-correlation or structured logging")

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
    summary = f"Scanned {len(files)} Apex class file(s); {len(findings)} debug/logging finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
