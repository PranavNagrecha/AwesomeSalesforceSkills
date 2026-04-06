#!/usr/bin/env python3
"""Audit Apex files for common Async Apex selection and implementation risks."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


TEXT_SUFFIXES = {".cls", ".trigger"}
LOOP_START_RE = re.compile(r"\b(for|while)\b")
ENQUEUE_RE = re.compile(r"\bSystem\.enqueueJob\s*\(", re.IGNORECASE)
FUTURE_RE = re.compile(r"@future", re.IGNORECASE)
QUEUEABLE_CLASS_RE = re.compile(r"\bimplements\b[^{;]*\bQueueable\b", re.IGNORECASE)
ALLOWS_CALLOUTS_RE = re.compile(r"\bDatabase\.AllowsCallouts\b", re.IGNORECASE)
HTTP_RE = re.compile(r"\b(HttpRequest|Http\b|WebServiceCallout)\b")
EXECUTE_BATCH_RE = re.compile(r"Database\.executeBatch\s*\([^,]+,\s*(\d+)\s*\)", re.IGNORECASE)
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex files for Async Apex anti-patterns such as looped enqueues or weak callout setup."
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
    lines = text.splitlines()

    loop_depth = 0
    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if LOOP_START_RE.search(line) and "for each" not in line.lower():
            loop_depth += line.count("{") or 1

        if loop_depth > 0 and ENQUEUE_RE.search(line):
            findings.append(f"CRITICAL {path}:{line_number}: `System.enqueueJob()` appears inside a loop")

        if "}" in line and loop_depth > 0:
            loop_depth = max(0, loop_depth - line.count("}"))

    if FUTURE_RE.search(text):
        findings.append(f"REVIEW {path}: legacy `@future` usage found; confirm Queueable is not the better fit")

    if QUEUEABLE_CLASS_RE.search(text) and HTTP_RE.search(text) and not ALLOWS_CALLOUTS_RE.search(text):
        findings.append(f"HIGH {path}: Queueable appears to make callouts without `Database.AllowsCallouts`")

    if path.suffix.lower() == ".trigger" and HTTP_RE.search(text):
        findings.append(f"CRITICAL {path}: trigger contains HTTP callout code; move outbound work to async Apex")

    if "void execute(QueueableContext" in text and text.count("System.enqueueJob(") > 1:
        findings.append(f"HIGH {path}: Queueable file contains multiple enqueue calls; verify single-child chaining rule")

    for match in EXECUTE_BATCH_RE.finditer(text):
        scope = int(match.group(1))
        if scope > 200:
            findings.append(f"REVIEW {path}: batch scope {scope} detected; verify throughput, callout, and heap assumptions")

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

    summary = f"Scanned {len(files)} Apex file(s); {len(findings)} async-Apex finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
