#!/usr/bin/env python3
"""Audit Apex files for CPU- and heap-heavy patterns."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


SOQL_RE = re.compile(r"\[\s*SELECT\b", re.IGNORECASE)
LOOP_RE = re.compile(r"\b(for|while)\b")
JSON_RE = re.compile(r"JSON\.(deserialize|serialize)", re.IGNORECASE)
PATTERN_RE = re.compile(r"Pattern\.compile|string\.matches\s*\(", re.IGNORECASE)
STRING_CONCAT_RE = re.compile(r"\+\s*\w+|\w+\s*\+")
LIMITS_CPU_RE = re.compile(r"Limits\.getCpuTime\s*\(", re.IGNORECASE)
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Apex files for CPU and heap anti-patterns such as nested loops and payload work in loops.")
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
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    loop_depth = 0
    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if LOOP_RE.search(line) and "for each" not in line.lower():
            loop_depth += line.count("{") or 1
            if loop_depth > 1:
                findings.append(f"REVIEW {path}:{line_number}: nested loop detected; inspect CPU cost")

        if loop_depth > 0 and JSON_RE.search(line):
            findings.append(f"HIGH {path}:{line_number}: JSON serialize/deserialize detected inside a loop")
        if loop_depth > 0 and PATTERN_RE.search(line):
            findings.append(f"MEDIUM {path}:{line_number}: regex-style work detected inside a loop")
        if loop_depth > 0 and STRING_CONCAT_RE.search(line) and '"' in line:
            findings.append(f"MEDIUM {path}:{line_number}: string concatenation detected inside a loop")

        if "}" in line and loop_depth > 0:
            loop_depth = max(0, loop_depth - line.count("}"))

    text = "\n".join(lines)
    if SOQL_RE.search(text) and not LIMITS_CPU_RE.search(text) and len(lines) > 120:
        findings.append(f"REVIEW {path}: larger Apex file found without obvious CPU checkpoints; verify profiling approach during optimization")
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
    summary = f"Scanned {len(files)} Apex file(s); {len(findings)} CPU/heap finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
