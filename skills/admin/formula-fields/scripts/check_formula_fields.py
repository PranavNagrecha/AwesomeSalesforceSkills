#!/usr/bin/env python3
"""Review formula field metadata for common complexity and performance smells."""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


SUFFIX = ".field-meta.xml"
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def local_name(tag: str) -> str:
    return tag.split("}", 1)[-1]


def child_text(element: ET.Element, child_name: str) -> str:
    for child in element:
        if local_name(child.tag) == child_name:
            return (child.text or "").strip()
    return ""


def iter_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            files.extend(candidate for candidate in path.rglob(f"*{SUFFIX}") if candidate.is_file())
        elif path.is_file() and path.name.endswith(SUFFIX):
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


def audit_field(path: Path) -> list[str]:
    findings: list[str] = []
    root = ET.parse(path).getroot()
    if local_name(root.tag) != "CustomField":
        return findings

    formula = child_text(root, "formula")
    if not formula:
        return findings

    upper_formula = formula.upper()
    if len(formula) > 3500:
        findings.append(f"REVIEW {path}: formula text is {len(formula)} characters")
    if upper_formula.count("IF(") >= 5:
        findings.append(f"MEDIUM {path}: nested IF usage suggests readability debt")
    if "__R." in upper_formula or re.search(r"\b(Account|Owner|Parent)\.", formula):
        findings.append(f"REVIEW {path}: cross-object reference detected")
    if "HYPERLINK(" in upper_formula or "IMAGE(" in upper_formula:
        findings.append(f"REVIEW {path}: decorative formula function in use")

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check Salesforce formula field metadata for complexity and performance smells."
    )
    parser.add_argument("paths", nargs="+", help="Field metadata files or directories")
    args = parser.parse_args()

    findings: list[str] = []
    files = iter_files([Path(value) for value in args.paths])
    if not files:
        return emit_result(
            ["HIGH no custom field metadata files found"],
            "Scanned 0 custom field metadata file(s); no files matched the provided paths.",
        )

    for path in files:
        findings.extend(audit_field(path))

    summary = f"Scanned {len(files)} custom field metadata file(s); {len(findings)} finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
