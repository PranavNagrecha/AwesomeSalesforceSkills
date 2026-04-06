#!/usr/bin/env python3
"""Audit SOSL usage for injection and query-shape issues."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


DYNAMIC_SOSL_RE = re.compile(r"Search\.query\s*\(", re.IGNORECASE)
CONCAT_RE = re.compile(r"\+\s*\w+|\w+\s*\+")
SEARCH_METHOD_RE = re.compile(r"\b(search|find)\b", re.IGNORECASE)
LIKE_SEARCH_RE = re.compile(r"LIKE\s+'%|LIKE\s+:")
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Apex files for weak SOSL and search-query patterns.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory to scan for Apex classes.")
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
    text = path.read_text(encoding="utf-8", errors="ignore")
    if DYNAMIC_SOSL_RE.search(text) and CONCAT_RE.search(text):
        findings.append(f"HIGH {path}: dynamic `Search.query()` appears to concatenate input; review for SOSL injection risk")
    if SEARCH_METHOD_RE.search(text) and LIKE_SEARCH_RE.search(text):
        findings.append(f"REVIEW {path}: search-oriented Apex appears to use SOQL `LIKE`; confirm SOSL is not the better fit")
    return findings


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        return emit_result([f"HIGH {root}: manifest directory not found"], "Scanned 0 Apex files; manifest directory was missing.")
    files = iter_files(root)
    if not files:
        return emit_result([f"HIGH {root}: no Apex files found"], "Scanned 0 Apex files; no .cls files were found.")
    findings: list[str] = []
    for path in files:
        findings.extend(audit_file(path))
    summary = f"Scanned {len(files)} Apex file(s); {len(findings)} SOSL finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
