#!/usr/bin/env python3
"""Audit Apex event publication and subscriber patterns."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


TEXT_SUFFIXES = {".cls", ".trigger"}
LOOP_RE = re.compile(r"\b(for|while)\b")
PUBLISH_RE = re.compile(r"\bEventBus\.publish\s*\(", re.IGNORECASE)
SAVE_RESULT_RE = re.compile(r"SaveResult|isSuccess\s*\(|getErrors\s*\(", re.IGNORECASE)
EVENT_TRIGGER_RE = re.compile(r"trigger\s+\w+\s+on\s+\w+__e\s*\(", re.IGNORECASE)
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Apex event publication and trigger-subscriber anti-patterns.")
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
    return sorted(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES)


def audit_file(path: Path) -> list[str]:
    findings: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    loop_depth = 0

    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if LOOP_RE.search(line) and "for each" not in line.lower():
            loop_depth += line.count("{") or 1

        if loop_depth > 0 and PUBLISH_RE.search(line):
            findings.append(f"HIGH {path}:{line_number}: `EventBus.publish()` appears inside a loop")

        if "}" in line and loop_depth > 0:
            loop_depth = max(0, loop_depth - line.count("}"))

    if PUBLISH_RE.search(text) and not SAVE_RESULT_RE.search(text):
        findings.append(f"REVIEW {path}: event publication found without obvious publish-result inspection")

    if path.suffix.lower() == ".trigger" and EVENT_TRIGGER_RE.search(text):
        if "before insert" in text.lower():
            findings.append(f"CRITICAL {path}: platform event trigger appears to declare `before insert` instead of subscriber `after insert`")
        if text.count("System.enqueueJob(") == 0 and len(lines) > 25:
            findings.append(f"REVIEW {path}: platform event trigger is fairly heavy; confirm logic should not be delegated to a worker class")

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

    summary = f"Scanned {len(files)} Apex file(s); {len(findings)} platform-event finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
