#!/usr/bin/env python3
"""Audit record type and page layout metadata for admin complexity issues."""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


METADATA_SUFFIXES = (
    ".object-meta.xml",
    ".profile-meta.xml",
    ".permissionset-meta.xml",
    ".layout-meta.xml",
)
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


def audit_object(path: Path, root: ET.Element) -> list[str]:
    findings: list[str] = []
    record_types = [child for child in root if local_name(child.tag) == "recordTypes"]
    count = len(record_types)
    if count > 13:
        findings.append(f"HIGH {path}: object has {count} record types")
    elif count > 8:
        findings.append(f"MEDIUM {path}: object has {count} record types")
    return findings


def audit_assignment_file(path: Path, root: ET.Element) -> list[str]:
    findings: list[str] = []
    root_type = local_name(root.tag)
    rt_visibilities = [child for child in root if local_name(child.tag) == "recordTypeVisibilities"]
    layout_assignments = [child for child in root if local_name(child.tag) == "layoutAssignments"]

    if layout_assignments and not rt_visibilities:
        findings.append(
            f"REVIEW {path}: {root_type} has layout assignments but no explicit record type visibilities"
        )

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scan object, profile, and permission set metadata for record type/layout risks."
    )
    parser.add_argument("paths", nargs="+", help="Files or directories to scan")
    args = parser.parse_args()

    files = iter_metadata_files([Path(value) for value in args.paths])
    if not files:
        return emit_result(
            ["HIGH no object, profile, permission set, or layout metadata files found"],
            "Scanned 0 record-type/layout metadata file(s); no files matched the provided paths.",
        )

    findings: list[str] = []
    for path in files:
        root = ET.parse(path).getroot()
        root_type = local_name(root.tag)
        if root_type == "CustomObject":
            findings.extend(audit_object(path, root))
        elif root_type in {"Profile", "PermissionSet"}:
            findings.extend(audit_assignment_file(path, root))

    summary = f"Scanned {len(files)} record-type/layout metadata file(s); {len(findings)} finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
