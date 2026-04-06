#!/usr/bin/env python3
"""Review local email template files for hardcoded addresses and missing merge context."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


TEXT_SUFFIXES = (".html", ".htm", ".txt", ".email", ".md")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def iter_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            for candidate in path.rglob("*"):
                if candidate.is_file() and candidate.suffix.lower() in TEXT_SUFFIXES:
                    files.append(candidate)
        elif path.is_file():
            files.append(path)
    return sorted(set(files))


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


def audit_file(path: Path) -> list[str]:
    findings: list[str] = []
    content = path.read_text(encoding="utf-8", errors="ignore")

    addresses = sorted(set(EMAIL_RE.findall(content)))
    for address in addresses:
        if "example." not in address.lower():
            findings.append(f"REVIEW {path}: hardcoded email address `{address}` found in template content")

    if "{!" not in content and "{{" not in content:
        findings.append(f"REVIEW {path}: no obvious merge fields found")

    if "subject" not in content.lower() and path.suffix.lower() in {".md", ".txt"}:
        findings.append(f"REVIEW {path}: subject line is not documented")

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check email template files for hardcoded addresses and missing merge context."
    )
    parser.add_argument("paths", nargs="+", help="Files or directories to scan")
    args = parser.parse_args()

    files = iter_files([Path(value) for value in args.paths])
    if not files:
        return emit_result(
            ["HIGH no email template files found"],
            "Scanned 0 email template file(s); no files matched the provided paths.",
        )

    findings: list[str] = []
    for path in files:
        findings.extend(audit_file(path))

    summary = f"Scanned {len(files)} email template file(s); {len(findings)} finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
