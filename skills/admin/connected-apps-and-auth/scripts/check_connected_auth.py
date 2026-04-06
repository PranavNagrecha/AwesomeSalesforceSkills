#!/usr/bin/env python3
"""Audit connected-app and auth-related files for common security anti-patterns."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


TEXT_SUFFIXES = {".xml", ".json", ".cls", ".trigger", ".js", ".ts", ".md", ".txt"}
DIRECT_ENDPOINT_PATTERN = re.compile(r"setEndpoint\(\s*['\"]https?://", re.IGNORECASE)
SECRET_PATTERN = re.compile(
    r"authorization:\s*bearer\s+[A-Za-z0-9._-]+|client[_-]?secret|consumersecret|password\s*=",
    re.IGNORECASE,
)
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def iter_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(candidate for candidate in path.rglob("*") if candidate.is_file())
        else:
            files.append(path)
    return files


def normalize_finding(finding: str) -> dict[str, str]:
    severity, _, remainder = finding.partition(" ")
    location = ""
    message = remainder
    if ": " in remainder:
        location, message = remainder.split(": ", 1)
    return {"severity": severity or "INFO", "location": location, "message": message}


def emit_result(findings: list[str], summary: str) -> int:
    normalized = [normalize_finding(finding) for finding in findings]
    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(item["severity"], 0) for item in normalized))
    print(json.dumps({"score": score, "findings": normalized, "summary": summary}, indent=2))
    if normalized:
        print(f"WARN: {len(normalized)} finding(s) detected", file=sys.stderr)
    return 1 if normalized else 0


def audit_file(path: Path) -> tuple[list[str], bool]:
    findings: list[str] = []
    found_named_credential = False

    if not path.exists():
        return [f"HIGH {path}: file not found"], found_named_credential
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return findings, found_named_credential

    text = path.read_text(encoding="utf-8", errors="ignore")
    lower_path = str(path).lower()

    if "namedcredential" in lower_path or "externalcredential" in lower_path or path.name.endswith(".namedCredential-meta.xml"):
        found_named_credential = True

    if SECRET_PATTERN.search(text):
        findings.append(f"HIGH {path}: possible hardcoded secret, bearer token, or password material found")

    if DIRECT_ENDPOINT_PATTERN.search(text):
        findings.append(f"MEDIUM {path}: direct HTTPS endpoint in code; prefer Named Credentials and `callout:` references")

    if re.search(r"username[- ]password|password flow", text, re.IGNORECASE):
        findings.append(f"HIGH {path}: username-password flow reference found; review for stronger OAuth alternative")

    if re.search(r"<scope>\s*full\s*</scope>|[\s,]full[\s,]", text, re.IGNORECASE):
        findings.append(f"MEDIUM {path}: broad `full` OAuth scope detected; confirm least-privilege need")

    return findings, found_named_credential


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check connected-app, Named Credential, and integration auth files for risky patterns."
    )
    parser.add_argument("paths", nargs="+", help="Files or directories to inspect")
    args = parser.parse_args()

    findings: list[str] = []
    named_credential_found = False
    files = iter_files(args.paths)
    for path in files:
        file_findings, file_has_named_credential = audit_file(path)
        findings.extend(file_findings)
        named_credential_found = named_credential_found or file_has_named_credential

    if findings and not named_credential_found:
        findings.append("LOW no Named Credential or External Credential metadata detected in scanned paths")

    if not files:
        findings.append("HIGH no connected-app or auth-related files matched the provided paths")

    summary = (
        f"Scanned {len(files)} connected-app or auth-related file(s); "
        f"{len(findings)} finding(s) detected."
    )
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
