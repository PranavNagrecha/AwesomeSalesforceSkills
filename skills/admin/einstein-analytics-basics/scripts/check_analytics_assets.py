#!/usr/bin/env python3
"""Audit CRM Analytics dashboard and planning files for common anti-patterns."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


TEXT_SUFFIXES = {".json", ".wdash", ".xmd", ".md", ".txt"}
HOSTNAME_PATTERN = re.compile(
    r"https?://[A-Za-z0-9.-]*(salesforce|force)\.com|my\.salesforce\.com|lightning\.force\.com",
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


def count_widgets(payload: object) -> int:
    total = 0
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key == "widgets":
                if isinstance(value, dict):
                    total += len(value)
                elif isinstance(value, list):
                    total += len(value)
            total += count_widgets(value)
    elif isinstance(payload, list):
        for item in payload:
            total += count_widgets(item)
    return total


def has_filters(payload: object) -> bool:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in {"filters", "filterpanel", "filterPanel"} and value:
                return True
            if has_filters(value):
                return True
    elif isinstance(payload, list):
        return any(has_filters(item) for item in payload)
    return False


def audit_file(path: Path, max_widgets: int) -> list[str]:
    findings: list[str] = []
    if not path.exists():
        return [f"HIGH {path}: file not found"]
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return findings

    text = path.read_text(encoding="utf-8", errors="ignore")
    if HOSTNAME_PATTERN.search(text):
        findings.append(f"MEDIUM {path}: hardcoded Salesforce hostname found; use environment-safe references")
    if "TODO" in text:
        findings.append(f"LOW {path}: unresolved TODO markers remain")

    if path.suffix.lower() in {".json", ".wdash", ".xmd"}:
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            findings.append(f"MEDIUM {path}: invalid JSON ({exc.msg})")
            return findings

        widgets = count_widgets(payload)
        if widgets > max_widgets:
            findings.append(
                f"MEDIUM {path}: dashboard appears to contain {widgets} widgets; trim to decision-focused views"
            )
        if widgets and not has_filters(payload):
            findings.append(f"LOW {path}: dashboard has widgets but no obvious filter configuration")

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check CRM Analytics files for hardcoded hostnames, oversized dashboards, and unfinished planning docs."
    )
    parser.add_argument("paths", nargs="+", help="Files or directories to inspect")
    parser.add_argument("--max-widgets", type=int, default=12, help="Warn if a dashboard exceeds this widget count")
    args = parser.parse_args()

    findings: list[str] = []
    files = iter_files(args.paths)
    for path in files:
        findings.extend(audit_file(path, args.max_widgets))

    if not files:
        findings.append("HIGH no analytics asset files matched the provided paths")

    summary = f"Scanned {len(files)} analytics asset file(s); {len(findings)} finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
