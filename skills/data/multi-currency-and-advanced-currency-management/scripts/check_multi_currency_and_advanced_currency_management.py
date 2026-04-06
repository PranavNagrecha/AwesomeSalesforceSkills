#!/usr/bin/env python3
"""Audit source for risky multi-currency assumptions."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


AMOUNT_QUERY_RE = re.compile(r"SELECT\s+[^;\n]*\bAmount\b", re.IGNORECASE)
CURRENCY_ISO_RE = re.compile(r"CurrencyIsoCode", re.IGNORECASE)
CONVERT_RE = re.compile(r"convertCurrency\s*\(", re.IGNORECASE)
HARDCODED_CODE_RE = re.compile(r"['\"](USD|EUR|GBP|JPY|AUD|CAD)['\"]")
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Apex files for weak multi-currency handling patterns.")
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
    if AMOUNT_QUERY_RE.search(text) and not (CURRENCY_ISO_RE.search(text) or CONVERT_RE.search(text)):
        findings.append(f"REVIEW {path}: SOQL selects `Amount` without obvious `CurrencyIsoCode` or `convertCurrency()` usage; verify currency context is not being lost")
    if HARDCODED_CODE_RE.search(text):
        findings.append(f"REVIEW {path}: hardcoded currency code literal found; verify currency assumptions are not fixed to one market")
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
    summary = f"Scanned {len(files)} Apex file(s); {len(findings)} currency-management finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
