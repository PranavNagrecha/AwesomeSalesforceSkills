#!/usr/bin/env python3
"""Audit Apex triggers and handlers for broad recursion-guard anti-patterns."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


STATIC_BOOLEAN_RE = re.compile(r"static\s+Boolean\s+\w*(recurs|execut|run|guard)\w*", re.IGNORECASE)
SET_GUARD_RE = re.compile(r"static\s+Set<Id>\s+\w*", re.IGNORECASE)
TRIGGER_RE = re.compile(r"trigger\s+\w+\s+on\s+(\w+)", re.IGNORECASE)
DML_RE = re.compile(r"\b(update|insert|upsert|delete)\b", re.IGNORECASE)
OLDMAP_RE = re.compile(r"Trigger\.oldMap|oldMap", re.IGNORECASE)
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Apex files for blunt recursion guards and missing delta logic.")
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
    text = path.read_text(encoding="utf-8", errors="ignore")

    if STATIC_BOOLEAN_RE.search(text):
        findings.append(f"HIGH {path}: static Boolean recursion guard found; verify it does not suppress valid multi-record processing")

    if path.suffix.lower() == ".trigger" and TRIGGER_RE.search(text):
        if DML_RE.search(text) and not (SET_GUARD_RE.search(text) or OLDMAP_RE.search(text)):
            findings.append(f"REVIEW {path}: trigger contains DML without obvious set-based guard or delta-check logic")

    if "after update" in text.lower() and DML_RE.search(text) and not OLDMAP_RE.search(text):
        findings.append(f"REVIEW {path}: after-update logic with DML found without obvious old/new delta comparison")

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
    summary = f"Scanned {len(files)} Apex file(s); {len(findings)} recursion-prevention finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
