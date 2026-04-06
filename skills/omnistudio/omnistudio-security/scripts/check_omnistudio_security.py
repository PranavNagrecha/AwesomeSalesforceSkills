#!/usr/bin/env python3
"""Audit OmniStudio-related assets for common security smells."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


OMNI_RE = re.compile(r"omnistudio|omniscript|dataraptor|integration procedure|flexcard", re.IGNORECASE)
HTTP_URL_RE = re.compile(r"https?://", re.IGNORECASE)
NAMED_CRED_RE = re.compile(r"namedCredential|Named Credential", re.IGNORECASE)
TOKEN_RE = re.compile(r"bearer\s+[A-Za-z0-9._-]+|api[_-]?key|client[_-]?secret", re.IGNORECASE)
AURA_ENABLED_RE = re.compile(r"@AuraEnabled", re.IGNORECASE)
WITHOUT_SHARING_RE = re.compile(r"\bwithout\s+sharing\b", re.IGNORECASE)
SECURITY_RE = re.compile(r"with\s+sharing|inherited\s+sharing|WITH\s+USER_MODE|WITH\s+SECURITY_ENFORCED|stripInaccessible", re.IGNORECASE)
PUBLIC_GUEST_RE = re.compile(r"guest|public", re.IGNORECASE)
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check OmniStudio-adjacent assets for security and exposure issues.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory to scan for OmniStudio, Apex, and LWC assets.")
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
    allowed = {".json", ".txt", ".xml", ".js", ".cls", ".yaml", ".yml"}
    return sorted(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in allowed)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def audit_file(path: Path) -> list[str]:
    findings: list[str] = []
    text = read_text(path)

    if HTTP_URL_RE.search(text) and not NAMED_CRED_RE.search(text):
        findings.append(f"HIGH {path}: hardcoded HTTP URL found without an obvious Named Credential reference; review outbound security design")
    if TOKEN_RE.search(text):
        findings.append(f"CRITICAL {path}: possible hardcoded credential or token material found")
    if path.suffix.lower() == ".cls" and AURA_ENABLED_RE.search(text):
        if WITHOUT_SHARING_RE.search(text):
            findings.append(f"HIGH {path}: @AuraEnabled Apex uses without sharing; verify OmniStudio exposure is intentionally elevated")
        if not SECURITY_RE.search(text):
            findings.append(f"REVIEW {path}: @AuraEnabled Apex found without obvious sharing or CRUD/FLS enforcement markers")
    if PUBLIC_GUEST_RE.search(text) and re.search(r"\b(create|update|delete|upsert)\b", text, re.IGNORECASE):
        findings.append(f"REVIEW {path}: guest/public markers appear near write-oriented behavior; confirm the external contract is intentionally narrow")

    return findings


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        return emit_result([f"HIGH {root}: manifest directory not found"], "Scanned 0 files; manifest directory was missing.")

    files = iter_files(root)
    findings: list[str] = []
    omni_hits = 0
    for path in files:
        text = read_text(path)
        if OMNI_RE.search(path.name) or OMNI_RE.search(text):
            omni_hits += 1
            findings.extend(audit_file(path))

    if omni_hits == 0:
        return emit_result([f"HIGH {root}: no OmniStudio-related assets found"], "Scanned 0 OmniStudio-related files.")

    summary = f"Observed {omni_hits} OmniStudio-related file(s); {len(findings)} security finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
