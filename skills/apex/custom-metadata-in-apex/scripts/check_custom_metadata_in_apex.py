#!/usr/bin/env python3
"""Audit Apex usage of Custom Metadata Types for common design mistakes."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


TEST_SEEALLDATA_RE = re.compile(r"SeeAllData\s*=\s*true", re.IGNORECASE)
CMT_RE = re.compile(r"__mdt\b")
DML_ON_CMT_RE = re.compile(r"\b(insert|update|upsert|delete)\s+[A-Za-z0-9_<>.,\s]*__mdt\b", re.IGNORECASE)
LOOP_RE = re.compile(r"\b(for|while)\b")
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex files for weak Custom Metadata usage patterns.",
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


def iter_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in {".cls", ".trigger"})


def audit_file(path: Path) -> list[str]:
    findings: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore")

    if DML_ON_CMT_RE.search(text):
        findings.append(f"HIGH {path}: apparent DML statement on `__mdt` detected; verify the design is not treating custom metadata like ordinary data")
    if TEST_SEEALLDATA_RE.search(text) and CMT_RE.search(text):
        findings.append(f"REVIEW {path}: `SeeAllData=true` used in a file that references custom metadata; verify tests do not rely on unnecessary org-data exposure")

    loop_depth = 0
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if LOOP_RE.search(line) and "for each" not in line.lower():
            loop_depth += line.count("{") or 1
        if loop_depth > 0 and CMT_RE.search(line) and "SELECT" in line.upper():
            findings.append(f"MEDIUM {path}:{line_number}: custom metadata query found inside a loop; cache or prefetch configuration outside iteration")
        if "}" in line and loop_depth > 0:
            loop_depth = max(0, loop_depth - line.count("}"))

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
    summary = f"Scanned {len(files)} Apex file(s); {len(findings)} custom-metadata finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
