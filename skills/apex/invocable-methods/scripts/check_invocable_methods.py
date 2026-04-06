#!/usr/bin/env python3
"""Audit Apex invocable method contracts for common Flow-boundary mistakes."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


INVOKABLE_RE = re.compile(r"@InvocableMethod", re.IGNORECASE)
PUBLIC_STATIC_RE = re.compile(r"public\s+static", re.IGNORECASE)
LIST_SIGNATURE_RE = re.compile(r"\(\s*List<", re.IGNORECASE)
INVOKABLE_VAR_RE = re.compile(r"@InvocableVariable", re.IGNORECASE)
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check invocable Apex classes for weak signatures and missing wrapper metadata.")
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
    if not INVOKABLE_RE.search(text):
        return findings

    if not PUBLIC_STATIC_RE.search(text):
        findings.append(f"HIGH {path}: invocable annotation found without obvious `public static` method declaration")
    if not LIST_SIGNATURE_RE.search(text):
        findings.append(f"HIGH {path}: invocable method does not appear to accept a `List<...>` input")
    if text.count("@InvocableMethod") > 1:
        findings.append(f"REVIEW {path}: multiple `@InvocableMethod` annotations found; verify the class is intentionally structured")
    if "class Request" in text or "class Result" in text:
        if not INVOKABLE_VAR_RE.search(text):
            findings.append(f"MEDIUM {path}: request/response wrapper classes found without `@InvocableVariable` metadata")

    return findings


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        return emit_result([f"HIGH {root}: manifest directory not found"], "Scanned 0 Apex classes; manifest directory was missing.")
    files = iter_files(root)
    if not files:
        return emit_result([f"HIGH {root}: no Apex classes found"], "Scanned 0 Apex classes; no .cls files were found.")
    findings: list[str] = []
    for path in files:
        findings.extend(audit_file(path))
    summary = f"Scanned {len(files)} Apex class file(s); {len(findings)} invocable-method finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
