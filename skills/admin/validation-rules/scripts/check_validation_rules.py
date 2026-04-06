#!/usr/bin/env python3
"""Lint validation rule metadata for common admin mistakes."""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


METADATA_SUFFIXES = (".object-meta.xml", ".validationRule-meta.xml")
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def local_name(tag: str) -> str:
    return tag.split("}", 1)[-1]


def child_text(element: ET.Element, child_name: str) -> str:
    for child in element:
        if local_name(child.tag) == child_name:
            return (child.text or "").strip()
    return ""


def iter_metadata_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            for candidate in path.rglob("*"):
                if candidate.is_file() and candidate.name.endswith(METADATA_SUFFIXES):
                    files.append(candidate)
        elif path.is_file() and path.name.endswith(METADATA_SUFFIXES):
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


def collect_rules(path: Path) -> list[tuple[str, bool, str, str]]:
    root = ET.parse(path).getroot()
    root_type = local_name(root.tag)
    rules: list[tuple[str, bool, str, str]] = []

    if root_type == "ValidationRule":
        full_name = child_text(root, "fullName") or path.stem
        active = child_text(root, "active").lower() == "true"
        formula = child_text(root, "errorConditionFormula")
        error_message = child_text(root, "errorMessage")
        rules.append((full_name, active, formula, error_message))
        return rules

    if root_type != "CustomObject":
        return rules

    for child in root:
        if local_name(child.tag) != "validationRules":
            continue
        full_name = child_text(child, "fullName") or "<unnamed rule>"
        active = child_text(child, "active").lower() == "true"
        formula = child_text(child, "errorConditionFormula")
        error_message = child_text(child, "errorMessage")
        rules.append((full_name, active, formula, error_message))
    return rules


def audit_rule(path: Path, name: str, active: bool, formula: str, error_message: str) -> list[str]:
    findings: list[str] = []
    upper_formula = formula.upper()
    normalized_error = error_message.strip().lower()

    if "PRIORVALUE(" in upper_formula and "ISNEW()" not in upper_formula:
        findings.append(
            f"HIGH {path}::{name}: PRIORVALUE is used without an ISNEW guard"
        )

    if "RECORDTYPE.NAME" in upper_formula:
        findings.append(
            f"MEDIUM {path}::{name}: uses RecordType.Name; prefer RecordType.DeveloperName"
        )

    if "ISPICKVAL(RECORDTYPE.DEVELOPERNAME" in upper_formula:
        findings.append(
            f"MEDIUM {path}::{name}: RecordType.DeveloperName is text, not a picklist"
        )

    if "ISPICKVAL(" in upper_formula and "ISBLANK(" not in upper_formula:
        findings.append(
            f"REVIEW {path}::{name}: picklist logic has no explicit blank guard"
        )

    if active and "$PERMISSION." not in upper_formula:
        findings.append(
            f"REVIEW {path}::{name}: no custom-permission bypass detected; confirm data-load and integration strategy"
        )

    if not error_message or len(error_message.strip()) < 20 or "validation error" in normalized_error:
        findings.append(
            f"MEDIUM {path}::{name}: error message is missing or too generic"
        )

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scan validation rule metadata for formula and error-message issues."
    )
    parser.add_argument("paths", nargs="+", help="Files or directories to scan")
    args = parser.parse_args()

    files = iter_metadata_files([Path(value) for value in args.paths])
    if not files:
        return emit_result(
            ["HIGH no validation rule metadata files found"],
            "Scanned 0 validation rule metadata file(s); no files matched the provided paths.",
        )

    findings: list[str] = []
    rule_count = 0
    for path in files:
        for rule in collect_rules(path):
            rule_count += 1
            findings.extend(audit_rule(path, *rule))

    summary = f"Scanned {rule_count} validation rule(s) across {len(files)} file(s); {len(findings)} finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
