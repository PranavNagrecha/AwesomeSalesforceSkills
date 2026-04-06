#!/usr/bin/env python3
"""Review approval-process metadata for missing actions and step definitions."""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


SUFFIX = ".approvalProcess-meta.xml"
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def local_name(tag: str) -> str:
    return tag.split("}", 1)[-1]


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


def audit_file(path: Path) -> list[str]:
    findings: list[str] = []
    root = ET.parse(path).getroot()
    child_tags = [local_name(child.tag) for child in root]

    if "approvalStep" not in child_tags:
        findings.append(f"HIGH {path}: no approval steps defined")
    if "initialSubmissionActions" not in child_tags:
        findings.append(f"REVIEW {path}: no initial submission actions configured")
    if "finalApprovalActions" not in child_tags:
        findings.append(f"REVIEW {path}: no final approval actions configured")
    if "finalRejectionActions" not in child_tags:
        findings.append(f"REVIEW {path}: no final rejection actions configured")

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scan Salesforce approval-process metadata for missing steps or action blocks."
    )
    parser.add_argument("paths", nargs="+", help="Approval-process files or directories")
    args = parser.parse_args()

    files = iter_files([Path(value) for value in args.paths])
    if not files:
        return emit_result(
            ["HIGH no approval-process metadata files found"],
            "Scanned 0 approval-process metadata files; no files matched the provided paths.",
        )

    findings: list[str] = []
    for path in files:
        findings.extend(audit_file(path))

    summary = (
        f"Scanned {len(files)} approval-process metadata file(s); "
        f"{len(findings)} finding(s) detected."
    )
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
