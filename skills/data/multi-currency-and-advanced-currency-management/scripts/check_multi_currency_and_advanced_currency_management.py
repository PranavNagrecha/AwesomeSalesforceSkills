#!/usr/bin/env python3
"""Audit Apex for risky multi-currency assumptions.

Stdlib only. Scans *.cls and *.trigger files under --manifest-dir and prints a JSON
report (score, findings, summary). Exit 1 when any finding is reported.

Rules and the Summer '26 (262) source each one encodes:
  HIGH    convertCurrency() in WHERE or ORDER BY, or wrapping an aggregate.
          SOQL and SOSL Reference, "convertCurrency()": not allowed in WHERE (returns an
          error) or ORDER BY; aggregate results cannot be converted.
  HIGH    DML on CurrencyType or DatedConversionRate.
          Apex Developer Guide, "sObjects That Don't Support DML Operations."
  MEDIUM  Static SOQL naming CurrencyIsoCode or CurrencyType with no
          UserInfo.isMultiCurrencyOrganization() guard in the file.
          Object Reference: CurrencyIsoCode exists only in multicurrency orgs;
          CurrencyType is not available in single-currency orgs.
  REVIEW  SOQL selects Amount without CurrencyIsoCode or convertCurrency().
  REVIEW  Hardcoded currency code literal.

Usage
  python3 check_multi_currency_and_advanced_currency_management.py --manifest-dir force-app
  python3 check_multi_currency_and_advanced_currency_management.py --self-test
"""

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
CONVERT_IN_WHERE_RE = re.compile(r"\bWHERE\b[^\];]*?convertCurrency\s*\(", re.IGNORECASE)
CONVERT_IN_ORDER_RE = re.compile(r"\bORDER\s+BY\b[^\];]*?convertCurrency\s*\(", re.IGNORECASE)
CONVERT_AGG_RE = re.compile(r"convertCurrency\s*\(\s*(SUM|MAX|MIN|AVG|COUNT)\s*\(", re.IGNORECASE)
NEW_RATE_RE = re.compile(r"\bnew\s+(CurrencyType|DatedConversionRate)\s*\(", re.IGNORECASE)
RATE_VAR_RE = re.compile(r"\b(?:List\s*<\s*)?(CurrencyType|DatedConversionRate)\s*>?\s+(\w+)\s*[=;:)]", re.IGNORECASE)
STATIC_CURRENCY_SOQL_RE = re.compile(r"\[\s*SELECT\b[^\]]*\b(CurrencyIsoCode|FROM\s+CurrencyType)\b", re.IGNORECASE)
GUARD_RE = re.compile(r"isMultiCurrencyOrganization\s*\(", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Apex files for weak multi-currency handling patterns.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory to scan for Apex classes.")
    parser.add_argument("--self-test", action="store_true", help="Run against scripts/fixtures/good and bad.")
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
    return sorted(path for path in root.rglob("*") if path.is_file() and path.suffix in (".cls", ".trigger"))


def strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.DOTALL)
    return re.sub(r"//[^\n]*", "", text)


def audit_file(path: Path) -> list[str]:
    findings: list[str] = []
    text = strip_comments(path.read_text(encoding="utf-8", errors="ignore"))
    if CONVERT_IN_WHERE_RE.search(text) or CONVERT_IN_ORDER_RE.search(text):
        findings.append(f"HIGH {path}: convertCurrency() in WHERE or ORDER BY is not allowed; filter with an ISO-prefixed literal such as Amount > USD5000")
    if CONVERT_AGG_RE.search(text):
        findings.append(f"HIGH {path}: convertCurrency() cannot convert an aggregate; aggregates return the org default currency")
    rate_vars = {m.group(2) for m in RATE_VAR_RE.finditer(text)}
    dml_on_var = any(
        re.search(rf"\b(insert|update|upsert|delete)\s+{re.escape(v)}\b|Database\.(insert|update|upsert|delete)\s*\(\s*{re.escape(v)}\b", text, re.IGNORECASE)
        for v in rate_vars
    )
    if NEW_RATE_RE.search(text) or dml_on_var:
        findings.append(f"HIGH {path}: CurrencyType and DatedConversionRate do not support DML in Apex; load rates through the API")
    if STATIC_CURRENCY_SOQL_RE.search(text) and not GUARD_RE.search(text):
        findings.append(f"MEDIUM {path}: static SOQL names CurrencyIsoCode or CurrencyType without a UserInfo.isMultiCurrencyOrganization() guard; it fails in single-currency orgs")
    if AMOUNT_QUERY_RE.search(text) and not (CURRENCY_ISO_RE.search(text) or CONVERT_RE.search(text)):
        findings.append(f"REVIEW {path}: SOQL selects `Amount` without obvious `CurrencyIsoCode` or `convertCurrency()` usage; verify currency context is not being lost")
    if HARDCODED_CODE_RE.search(text):
        findings.append(f"REVIEW {path}: hardcoded currency code literal found; verify currency assumptions are not fixed to one market")
    return findings


def self_test() -> int:
    base = Path(__file__).resolve().parent / "fixtures"
    good, bad = base / "good", base / "bad"
    if not good.is_dir() or not bad.is_dir():
        print("ERROR: fixtures/good or fixtures/bad is missing")
        return 1
    failures = 0
    for path in iter_files(good):
        found = audit_file(path)
        if found:
            failures += 1
            print(f"ERROR: self-test: good fixture {path.name} produced {found}")
    for path in iter_files(bad):
        if not audit_file(path):
            failures += 1
            print(f"ERROR: self-test: bad fixture {path.name} produced no finding")
    if failures:
        return 1
    print("self-test passed")
    return 0


def main() -> int:
    args = parse_args()
    if args.self_test:
        return self_test()
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
