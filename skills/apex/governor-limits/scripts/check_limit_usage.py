#!/usr/bin/env python3
"""Scan Apex files for common governor-limit anti-patterns."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


TEXT_SUFFIXES = {".cls", ".trigger"}
SOQL_RE = re.compile(r"\[\s*SELECT\b", re.IGNORECASE)
DML_RE = re.compile(r"\b(insert|update|upsert|delete|undelete|merge)\b", re.IGNORECASE)
LOOP_START_RE = re.compile(r"\b(for|while)\b")
QUEUEABLE_RE = re.compile(r"\bSystem\.enqueueJob\s*\(", re.IGNORECASE)
FUTURE_RE = re.compile(r"@future", re.IGNORECASE)
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

    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    loop_depth = 0
    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if LOOP_START_RE.search(line) and "for each" not in line.lower():
            loop_depth += line.count("{") or 1

        if loop_depth > 0 and SOQL_RE.search(line):
            findings.append(f"CRITICAL {path}:{line_number}: SOQL detected inside a loop")

        if loop_depth > 0 and DML_RE.search(line) and not line.lower().startswith("//"):
            findings.append(f"CRITICAL {path}:{line_number}: DML detected inside a loop")

        if QUEUEABLE_RE.search(line) and "for " in line:
            findings.append(f"HIGH {path}:{line_number}: Queueable jobs appear to be enqueued inside a loop")

        if "{" in line and LOOP_START_RE.search(line):
            continue
        if "}" in line and loop_depth > 0:
            loop_depth = max(0, loop_depth - line.count("}"))

    text = "\n".join(lines)
    if FUTURE_RE.search(text) and not QUEUEABLE_RE.search(text):
        findings.append(f"REVIEW {path}: @future usage found; confirm Queueable is not the better modern choice")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check Apex files for governor-limit anti-patterns such as SOQL or DML inside loops."
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
