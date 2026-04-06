#!/usr/bin/env python3
"""Audit GraphQL usage patterns in Salesforce codebases."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


GRAPHQL_RE = re.compile(r"/graphql\b|lightning/(ui)?graphql", re.IGNORECASE)
RAW_FETCH_RE = re.compile(r"fetch\s*\([^)]*/services/data/v\d+\.\d+/graphql", re.IGNORECASE)
INTERPOLATED_QUERY_RE = re.compile(r"gql`[^`]*\$\{|query\s*[:=]\s*`[^`]*\$\{|query\s*[:=][^;\n]*\+[^;\n]*", re.IGNORECASE | re.DOTALL)
VARIABLES_RE = re.compile(r"\bvariables\b")
UI_GRAPHQL_RE = re.compile(r"lightning/uiGraphQLApi", re.IGNORECASE)
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check GraphQL files for unsafe query construction and weak adapter choices.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory to scan for code and metadata.")
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
    allowed = {".js", ".ts", ".cls", ".json", ".gql", ".graphql", ".yml", ".yaml"}
    return sorted(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in allowed)


def audit_file(path: Path) -> list[str]:
    findings: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore")
    if not GRAPHQL_RE.search(text):
        return findings

    if INTERPOLATED_QUERY_RE.search(text):
        findings.append(f"HIGH {path}: GraphQL query appears to be built with interpolation or concatenation; prefer static documents plus variables")
    if RAW_FETCH_RE.search(text):
        findings.append(f"REVIEW {path}: raw HTTP call to Salesforce GraphQL endpoint found; verify a platform adapter or shared transport abstraction is not the better fit")
    if "$" in text and "query" in text.lower() and not VARIABLES_RE.search(text):
        findings.append(f"REVIEW {path}: GraphQL parameter marker found without obvious `variables` usage; verify runtime values are not being inlined")
    if UI_GRAPHQL_RE.search(text):
        findings.append(f"REVIEW {path}: `lightning/uiGraphQLApi` import found; confirm Mobile Offline support is the actual reason for this adapter choice")

    return findings


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        return emit_result([f"HIGH {root}: manifest directory not found"], "Scanned 0 files; manifest directory was missing.")
    files = iter_files(root)
    if not files:
        return emit_result([f"HIGH {root}: no relevant files found"], "Scanned 0 files; no GraphQL-relevant source files were found.")
    findings: list[str] = []
    for path in files:
        findings.extend(audit_file(path))
    summary = f"Scanned {len(files)} file(s); {len(findings)} GraphQL finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
