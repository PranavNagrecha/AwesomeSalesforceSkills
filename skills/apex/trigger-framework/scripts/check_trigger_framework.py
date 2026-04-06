#!/usr/bin/env python3
"""Audit Apex trigger files for structural framework issues."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path


TRIGGER_RE = re.compile(r"trigger\s+(\w+)\s+on\s+(\w+)", re.IGNORECASE)
HANDLER_RE = re.compile(r"Handler", re.IGNORECASE)
ACTIVATION_RE = re.compile(r"TriggerSettings__c|Trigger_Setting__mdt|isActive\s*\(", re.IGNORECASE)
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def iter_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(candidate for candidate in path.rglob("*.trigger") if candidate.is_file())
            files.extend(candidate for candidate in path.rglob("*.cls") if candidate.is_file())
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


def audit_trigger(path: Path) -> tuple[list[str], tuple[str, str] | None]:
    findings: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore")
    match = TRIGGER_RE.search(text)
    if not match:
        return findings, None

    trigger_name, object_name = match.groups()
    lines = text.splitlines()
    body_lines = [line.strip() for line in lines if line.strip() and not line.strip().startswith("//")]
    if any("[" in line or " insert " in line.lower() or " update " in line.lower() for line in body_lines[1:]):
        findings.append(f"HIGH {path}: trigger body appears to contain logic instead of pure delegation")
    if not HANDLER_RE.search(text):
        findings.append(f"HIGH {path}: no obvious handler delegation found in trigger body")
    if not ACTIVATION_RE.search(text):
        findings.append(f"MEDIUM {path}: no activation bypass pattern found")
    if "Trigger.isAfter" in text and "update " in text.lower() and "processed" not in text.lower():
        findings.append(f"REVIEW {path}: after-trigger DML detected; confirm recursion guard exists in handler")
    return findings, (trigger_name, object_name)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check Apex trigger files for common framework and operability issues."
    )
    parser.add_argument("paths", nargs="+", help="Files or directories to inspect")
    args = parser.parse_args()

    files = iter_files(args.paths)
    if not files:
        return emit_result(
            ["HIGH no trigger or Apex files matched the provided paths"],
            "Scanned 0 files; no matching trigger or Apex files were found.",
        )

    findings: list[str] = []
    triggers_by_object: defaultdict[str, list[str]] = defaultdict(list)
    scanned_triggers = 0
    for path in files:
        if path.suffix == ".trigger":
            scanned_triggers += 1
            trigger_findings, info = audit_trigger(path)
            findings.extend(trigger_findings)
            if info:
                _, object_name = info
                triggers_by_object[object_name].append(str(path))

    for object_name, trigger_paths in triggers_by_object.items():
        if len(trigger_paths) > 1:
            findings.append(
                f"CRITICAL {object_name}: multiple trigger files detected ({', '.join(trigger_paths)})"
            )

    summary = f"Scanned {scanned_triggers} trigger file(s); {len(findings)} finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
