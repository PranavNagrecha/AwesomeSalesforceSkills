#!/usr/bin/env python3
"""Audit Apex Platform Cache usage for scope and safety issues."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ORG_CACHE_RE = re.compile(r"Cache\.Org", re.IGNORECASE)
SESSION_CACHE_RE = re.compile(r"Cache\.Session", re.IGNORECASE)
PUT_RE = re.compile(r"\.put\s*\(", re.IGNORECASE)
SENSITIVE_RE = re.compile(r"token|password|secret|authorization|ssn", re.IGNORECASE)
ASYNC_RE = re.compile(r"implements\s+Queueable|implements\s+Database\.Batchable|System\.enqueueJob|Database\.executeBatch", re.IGNORECASE)
USER_ID_RE = re.compile(r"UserInfo\.getUserId\s*\(", re.IGNORECASE)
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Apex Platform Cache usage for unsafe scope and invalidation smells.")
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

    if ORG_CACHE_RE.search(text):
        if USER_ID_RE.search(text):
            findings.append(f"HIGH {path}: org cache appears tied to `UserInfo.getUserId()`; verify user-specific data is not stored in shared cache")
        if SENSITIVE_RE.search(text) and PUT_RE.search(text):
            findings.append(f"HIGH {path}: cache put found near sensitive terms; verify secrets are not cached")

    if SESSION_CACHE_RE.search(text) and ASYNC_RE.search(text):
        findings.append(f"REVIEW {path}: session cache used in code that also appears async-related; verify session scope is actually available")

    if (ORG_CACHE_RE.search(text) or SESSION_CACHE_RE.search(text)) and "get(" in text and "put(" not in text:
        findings.append(f"REVIEW {path}: cache read found without obvious cache-aside repopulation path")

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
    summary = f"Scanned {len(files)} Apex class file(s); {len(findings)} platform-cache finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
