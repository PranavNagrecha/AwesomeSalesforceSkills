#!/usr/bin/env python3
"""Audit OmniStudio Integration Procedure JSON for common operability risks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


JSON_SUFFIXES = {".json", ".txt"}
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
    if path.suffix.lower() not in JSON_SUFFIXES:
        return findings

    text = path.read_text(encoding="utf-8", errors="ignore")
    if "rollbackOnError" not in text:
        findings.append(f"CRITICAL {path}: rollbackOnError setting not found")
    elif '"rollbackOnError": false' in text or "'rollbackOnError': false" in text:
        findings.append(f"CRITICAL {path}: rollbackOnError is set to false")
    if "namedCredential" not in text and '"type": "HTTPAction"' in text:
        findings.append(f"HIGH {path}: HTTP action found without namedCredential reference")
    if "timeout" not in text and '"type": "HTTPAction"' in text:
        findings.append(f"HIGH {path}: HTTP action found without explicit timeout")
    if "Business approved verbiage" in text:
        findings.append(f"HIGH {path}: placeholder failureResponse text found")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check OmniStudio Integration Procedure files for rollback, auth, and timeout issues."
    )
    parser.add_argument("paths", nargs="+", help="Files or directories to inspect")
    args = parser.parse_args()

    files = iter_files(args.paths)
    if not files:
        return emit_result(
            ["HIGH no Integration Procedure files matched the provided paths"],
            "Scanned 0 files; no matching JSON-like files were found.",
        )

    findings: list[str] = []
    scanned = 0
    for path in files:
        if path.suffix.lower() not in JSON_SUFFIXES:
            continue
        scanned += 1
        findings.extend(audit_file(path))

    if scanned == 0:
        findings.append("HIGH no Integration Procedure files matched the provided paths")
    summary = f"Scanned {scanned} Integration Procedure file(s); {len(findings)} finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
