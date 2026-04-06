#!/usr/bin/env python3
"""Audit OAuth and connected-app usage for weak integration patterns."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


USERNAME_PASSWORD_RE = re.compile(r"grant_type\s*[=:]\s*[\"']password[\"']|grant_type=password|username-password", re.IGNORECASE)
FULL_SCOPE_RE = re.compile(r"scope[^\n]{0,80}\bfull\b", re.IGNORECASE)
HARDCODED_SECRET_RE = re.compile(r"(client_secret|consumersecret|refresh_token|access_token)\s*[=:]\s*[\"'][^\"']+[\"']", re.IGNORECASE)
TOKEN_LITERAL_RE = re.compile(r"Bearer\s+[A-Za-z0-9._-]{16,}", re.IGNORECASE)
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check code and config for weak OAuth flow and secret handling patterns.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory to scan for source and metadata files.")
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
    allowed = {".cls", ".js", ".ts", ".xml", ".json", ".yml", ".yaml", ".properties"}
    return sorted(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in allowed)


def audit_file(path: Path) -> list[str]:
    findings: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore")
    if USERNAME_PASSWORD_RE.search(text):
        findings.append(f"HIGH {path}: username-password OAuth flow pattern detected; review for a stronger OAuth alternative")
    if FULL_SCOPE_RE.search(text):
        findings.append(f"MEDIUM {path}: broad `full` OAuth scope detected; confirm least-privilege need")
    if HARDCODED_SECRET_RE.search(text) or TOKEN_LITERAL_RE.search(text):
        findings.append(f"HIGH {path}: apparent hardcoded OAuth secret or bearer token detected")
    return findings


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        return emit_result([f"HIGH {root}: manifest directory not found"], "Scanned 0 files; manifest directory was missing.")
    files = iter_files(root)
    if not files:
        return emit_result([f"HIGH {root}: no relevant files found"], "Scanned 0 files; no OAuth-relevant source or metadata files were found.")
    findings: list[str] = []
    for path in files:
        findings.extend(audit_file(path))
    summary = f"Scanned {len(files)} file(s); {len(findings)} OAuth finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
