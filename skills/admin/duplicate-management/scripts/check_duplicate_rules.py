#!/usr/bin/env python3
"""Audit Salesforce matching-rule and duplicate-rule metadata for common gaps."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def iter_rule_files(paths: list[str]) -> tuple[list[Path], list[Path]]:
    duplicate_rules: list[Path] = []
    matching_rules: list[Path] = []
    for raw in paths:
        path = Path(raw)
        candidates = [path] if path.is_file() else list(path.rglob("*")) if path.is_dir() else [path]
        for candidate in candidates:
            if not candidate.is_file():
                continue
            name = candidate.name
            if name.endswith(".duplicateRule-meta.xml"):
                duplicate_rules.append(candidate)
            elif name.endswith(".matchingRule-meta.xml"):
                matching_rules.append(candidate)
    return duplicate_rules, matching_rules


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


def audit_duplicate_rule(path: Path) -> list[str]:
    findings: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore")

    if "<isActive>true</isActive>" not in text:
        findings.append(f"MEDIUM {path}: duplicate rule is not active")

    if "actionOnInsert" not in text and "actionOnEdit" not in text:
        findings.append(f"HIGH {path}: duplicate rule has no insert/edit action configuration")

    if re.search(r"<actionOnInsert>\s*Allow\s*</actionOnInsert>", text, re.IGNORECASE):
        findings.append(f"MEDIUM {path}: insert behavior allows save; confirm steward process for alerts")

    if re.search(r"<actionOnEdit>\s*Allow\s*</actionOnEdit>", text, re.IGNORECASE):
        findings.append(f"LOW {path}: edit behavior allows save; verify whether this is intentional")

    if "alertText" not in text:
        findings.append(f"LOW {path}: duplicate rule has no alert text for end users")

    return findings


def audit_matching_rule(path: Path) -> list[str]:
    findings: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore")
    field_count = len(re.findall(r"<field(?:Name)?>", text))

    if field_count == 0:
        findings.append(f"HIGH {path}: matching rule appears to have no fields configured")
    elif field_count == 1:
        findings.append(f"MEDIUM {path}: matching rule uses a single field; confirm it is strong enough")

    if "fuzzy" not in text.lower() and "exact" not in text.lower():
        findings.append(f"LOW {path}: matching method is not obvious from metadata text; review manually")

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check duplicate-rule and matching-rule metadata for activation, actions, and weak matching design."
    )
    parser.add_argument("paths", nargs="+", help="Metadata files or directories to inspect")
    args = parser.parse_args()

    duplicate_rules, matching_rules = iter_rule_files(args.paths)
    findings: list[str] = []

    if not duplicate_rules:
        findings.append("HIGH no duplicate rule metadata files found")
    if not matching_rules:
        findings.append("HIGH no matching rule metadata files found")

    for path in duplicate_rules:
        findings.extend(audit_duplicate_rule(path))
    for path in matching_rules:
        findings.extend(audit_matching_rule(path))

    total_files = len(duplicate_rules) + len(matching_rules)
    summary = (
        f"Scanned {total_files} duplicate-management metadata file(s); "
        f"{len(findings)} finding(s) detected."
    )
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
