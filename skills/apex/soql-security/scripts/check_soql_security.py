#!/usr/bin/env python3
"""Scan Apex files for SOQL injection and CRUD/FLS risk patterns."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


TEXT_SUFFIXES = {".cls", ".trigger"}
DATABASE_QUERY_RE = re.compile(r"Database\.query\s*\(", re.IGNORECASE)
STRING_CONCAT_RE = re.compile(r"\+\s*\w+|\w+\s*\+")
WITHOUT_SHARING_RE = re.compile(r"\bwithout\s+sharing\b", re.IGNORECASE)
AURA_OR_REST_RE = re.compile(r"@AuraEnabled|@RestResource|global\s+static|public\s+static", re.IGNORECASE)
USER_MODE_RE = re.compile(r"WITH\s+USER_MODE", re.IGNORECASE)
SECURITY_ENFORCED_RE = re.compile(r"WITH\s+SECURITY_ENFORCED", re.IGNORECASE)
STRIP_RE = re.compile(r"stripInaccessible\s*\(", re.IGNORECASE)
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

    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()

    if WITHOUT_SHARING_RE.search(text):
        findings.append(f"HIGH {path}: class uses without sharing; verify and document intentional system context")

    if AURA_OR_REST_RE.search(text) and not (
        USER_MODE_RE.search(text) or SECURITY_ENFORCED_RE.search(text) or STRIP_RE.search(text)
    ):
        findings.append(f"MEDIUM {path}: public or API-facing Apex found without obvious CRUD/FLS enforcement pattern")

    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if DATABASE_QUERY_RE.search(line) and STRING_CONCAT_RE.search(line):
            findings.append(f"CRITICAL {path}:{line_number}: Database.query appears to use string concatenation")
        if "ORDER BY" in line.upper() and STRING_CONCAT_RE.search(line):
            findings.append(f"HIGH {path}:{line_number}: dynamic ORDER BY detected; confirm allowlist protection")

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check Apex files for dynamic SOQL and CRUD/FLS risk patterns."
    )
    parser.add_argument("paths", nargs="+", help="Files or directories to inspect")
    args = parser.parse_args()

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
