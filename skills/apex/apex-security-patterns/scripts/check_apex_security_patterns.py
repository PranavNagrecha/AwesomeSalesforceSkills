#!/usr/bin/env python3
"""Audit Apex files for sharing-model and CRUD/FLS enforcement risks."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


TEXT_SUFFIXES = {".cls", ".trigger"}
CLASS_RE = re.compile(r"\b(public|global)\s+(virtual\s+|abstract\s+)?(with|without|inherited)?\s*sharing?\s*class\b", re.IGNORECASE)
PUBLIC_CLASS_RE = re.compile(r"\b(public|global)\s+(virtual\s+|abstract\s+)?class\b", re.IGNORECASE)
WITHOUT_SHARING_RE = re.compile(r"\bwithout\s+sharing\b", re.IGNORECASE)
WITH_OR_INHERITED_RE = re.compile(r"\b(with|inherited)\s+sharing\b", re.IGNORECASE)
ENTRY_POINT_RE = re.compile(r"@AuraEnabled|@InvocableMethod|@RestResource", re.IGNORECASE)
READ_ENFORCEMENT_RE = re.compile(r"WITH\s+USER_MODE|WITH\s+SECURITY_ENFORCED|isAccessible\s*\(", re.IGNORECASE)
WRITE_ENFORCEMENT_RE = re.compile(r"stripInaccessible\s*\(|isCreateable\s*\(|isUpdateable\s*\(", re.IGNORECASE)
DML_RE = re.compile(r"\b(insert|update|upsert|delete|undelete|merge)\b", re.IGNORECASE)
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex files for ambiguous sharing declarations and missing CRUD/FLS protections."
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

    if path.suffix.lower() == ".cls" and PUBLIC_CLASS_RE.search(text) and not (
        WITH_OR_INHERITED_RE.search(text) or WITHOUT_SHARING_RE.search(text)
    ):
        findings.append(f"HIGH {path}: public/global Apex class has no explicit sharing declaration")

    if WITHOUT_SHARING_RE.search(text):
        findings.append(f"HIGH {path}: `without sharing` found; verify and document intentional privilege elevation")

    if ENTRY_POINT_RE.search(text) and not (WITH_OR_INHERITED_RE.search(text) or WITHOUT_SHARING_RE.search(text)):
        findings.append(f"HIGH {path}: user-facing entry point has no explicit sharing declaration")

    if ENTRY_POINT_RE.search(text) and not READ_ENFORCEMENT_RE.search(text):
        findings.append(f"HIGH {path}: user-facing entry point lacks obvious read-access enforcement (`WITH USER_MODE`, `WITH SECURITY_ENFORCED`, or describe checks)")

    if ENTRY_POINT_RE.search(text) and DML_RE.search(text) and not WRITE_ENFORCEMENT_RE.search(text):
        findings.append(f"HIGH {path}: user-facing entry point performs DML without obvious write-access enforcement")

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
    for path in files:
        findings.extend(audit_file(path))

    summary = f"Scanned {len(files)} Apex file(s); {len(findings)} security-pattern finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
