#!/usr/bin/env python3
"""Audit LWC JavaScript files for lifecycle and platform anti-patterns."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


TEXT_SUFFIXES = {".js", ".ts"}
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def iter_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(candidate for candidate in path.rglob("*") if candidate.is_file())
    return sorted(set(files))


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


def audit_file(path: Path) -> list[str]:
    findings: list[str] = []
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return findings

    text = path.read_text(encoding="utf-8", errors="ignore")
    if "addEventListener(" in text and "removeEventListener(" not in text:
        findings.append(f"CRITICAL {path}: addEventListener found without matching removeEventListener")
    if "renderedCallback()" in text and "_initialized" not in text and "_rendered" not in text:
        findings.append(f"HIGH {path}: renderedCallback found without an obvious one-time guard")
    if "window.location" in text:
        findings.append(f"HIGH {path}: window.location usage found; prefer NavigationMixin")
    if "document.querySelector" in text:
        findings.append(f"HIGH {path}: document.querySelector found; prefer this.template.querySelector")
    if re.search(r"\balert\s*\(", text):
        findings.append(f"MEDIUM {path}: alert() usage found; prefer ShowToastEvent or inline UI")
    if "@wire" in text and "error" not in text:
        findings.append(f"REVIEW {path}: wire usage found without obvious error handling branch")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check Lightning Web Component source files for lifecycle anti-patterns."
    )
    parser.add_argument("paths", nargs="+", help="Files or directories to inspect")
    args = parser.parse_args()

    files = iter_files(args.paths)
    if not files:
        return emit_result(
            ["HIGH no LWC files matched the provided paths"],
            "Scanned 0 LWC files; no matching .js or .ts files were found.",
        )

    findings: list[str] = []
    scanned = 0
    for path in files:
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        scanned += 1
        findings.extend(audit_file(path))

    if scanned == 0:
        findings.append("HIGH no LWC files matched the provided paths")
    summary = f"Scanned {scanned} LWC file(s); {len(findings)} finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
