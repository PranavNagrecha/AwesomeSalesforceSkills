#!/usr/bin/env python3
"""Scan metadata for risky sharing defaults and sharing bypass permissions."""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


SUFFIXES = (".object-meta.xml", ".profile-meta.xml", ".permissionset-meta.xml")
SYSTEM_BYPASSES = {"ViewAllData", "ModifyAllData"}
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
            for candidate in path.rglob("*"):
                if candidate.is_file() and candidate.name.endswith(SUFFIXES):
                    files.append(candidate)
        elif path.is_file() and path.name.endswith(SUFFIXES):
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
    root_type = local_name(root.tag)

    if root_type == "CustomObject":
        sharing_model = child_text(root, "sharingModel")
        external_model = child_text(root, "externalSharingModel")
        if sharing_model in {"ReadWrite", "ReadWriteTransfer", "PublicReadWriteTransfer"}:
            findings.append(f"REVIEW {path}: internal sharing model is `{sharing_model}`")
        if external_model in {"ReadWrite", "ReadOnly"}:
            findings.append(f"REVIEW {path}: external sharing model is `{external_model}`")

    for block in root.iter():
        tag_name = local_name(block.tag)
        if tag_name == "userPermissions":
            name = child_text(block, "name")
            enabled = child_text(block, "enabled").lower() == "true"
            if enabled and name in SYSTEM_BYPASSES:
                findings.append(f"HIGH {path}: system bypass permission `{name}` enabled")
        if tag_name == "objectPermissions":
            object_name = child_text(block, "object") or "<unknown object>"
            if child_text(block, "viewAllRecords").lower() == "true":
                findings.append(f"HIGH {path}: `{object_name}` has viewAllRecords=true")
            if child_text(block, "modifyAllRecords").lower() == "true":
                findings.append(f"HIGH {path}: `{object_name}` has modifyAllRecords=true")

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check Salesforce metadata for risky sharing defaults and bypass grants."
    )
    parser.add_argument("paths", nargs="+", help="Files or directories to scan")
    args = parser.parse_args()

    findings: list[str] = []
    files = iter_files([Path(value) for value in args.paths])
    if not files:
        return emit_result(
            ["HIGH no object, profile, or permission set metadata files found"],
            "Scanned 0 sharing-model metadata file(s); no files matched the provided paths.",
        )

    for path in files:
        findings.extend(audit_file(path))

    summary = f"Scanned {len(files)} sharing-model metadata file(s); {len(findings)} finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
