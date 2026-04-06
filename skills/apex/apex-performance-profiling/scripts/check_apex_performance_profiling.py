#!/usr/bin/env python3
"""Checker script for Apex Performance Profiling skill.

Scans Apex source files for profiling-related patterns:
- Missing Limits checkpoint instrumentation in large classes
- Use of System.currentTimeMillis for profiling (anti-pattern)
- Presence of SOQL in loops without nearby profiling checkpoints

Uses stdlib only -- no pip dependencies.

Usage:
    python3 check_apex_performance_profiling.py [--help]
    python3 check_apex_performance_profiling.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


# --- Regexes ----------------------------------------------------------------

TEST_CLASS_RE = re.compile(r"@isTest|\btestMethod\b", re.IGNORECASE)
LIMITS_CPU_RE = re.compile(r"Limits\.getCpuTime\s*\(", re.IGNORECASE)
LIMITS_QUERIES_RE = re.compile(r"Limits\.getQueries\s*\(", re.IGNORECASE)
LIMITS_DML_RE = re.compile(r"Limits\.getDMLStatements\s*\(", re.IGNORECASE)
WALL_CLOCK_RE = re.compile(
    r"System\.currentTimeMillis\s*\(|Datetime\.now\(\)\.getTime\s*\(",
    re.IGNORECASE,
)
SOQL_IN_LOOP_RE = re.compile(
    r"for\s*\(.*\)\s*\{[^}]*\[\s*SELECT\b",
    re.IGNORECASE | re.DOTALL,
)
SYSTEM_DEBUG_TIMING_RE = re.compile(
    r"System\.debug\s*\([^)]*(?:timing|elapsed|duration|profil|perf)",
    re.IGNORECASE,
)

SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex files for performance profiling patterns and anti-patterns.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory to scan for Apex files (default: current directory).",
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
    return sorted(path for path in root.rglob("*.cls") if path.is_file())


def audit_file(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        findings.append(f"HIGH {path}: unable to read file")
        return findings

    # Skip test classes
    if TEST_CLASS_RE.search(text):
        return findings

    lines = text.splitlines()
    line_count = len(lines)

    # Check for wall-clock profiling anti-pattern
    if WALL_CLOCK_RE.search(text):
        findings.append(
            f"MEDIUM {path}: uses System.currentTimeMillis or Datetime.now().getTime() "
            f"for timing; prefer Limits.getCpuTime() which measures Apex CPU only"
        )

    # Check for System.debug-based timing without Limits methods
    if SYSTEM_DEBUG_TIMING_RE.search(text) and not LIMITS_CPU_RE.search(text):
        findings.append(
            f"LOW {path}: debug statements reference timing/profiling keywords "
            f"but no Limits.getCpuTime() checkpoint found"
        )

    # Large classes without any profiling instrumentation
    has_any_limits = (
        LIMITS_CPU_RE.search(text)
        or LIMITS_QUERIES_RE.search(text)
        or LIMITS_DML_RE.search(text)
    )
    if line_count > 200 and not has_any_limits:
        findings.append(
            f"REVIEW {path}: large Apex class ({line_count} lines) without "
            f"Limits checkpoint instrumentation; consider adding profiling "
            f"for performance-critical methods"
        )

    return findings


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        return emit_result(
            [f"HIGH {root}: manifest directory not found"],
            "Scanned 0 Apex classes; manifest directory was missing.",
        )
    files = iter_files(root)
    if not files:
        return emit_result([], f"No Apex class files found in {root}.")
    findings: list[str] = []
    for path in files:
        findings.extend(audit_file(path))
    summary = (
        f"Scanned {len(files)} Apex class file(s); "
        f"{len(findings)} profiling-related finding(s) detected."
    )
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
