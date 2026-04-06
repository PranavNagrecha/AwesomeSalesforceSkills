#!/usr/bin/env python3
"""Audit Salesforce profiles and permission sets for risky access grants."""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


DANGEROUS_PERMISSIONS = {
    "ViewAllData",
    "ModifyAllData",
    "ManageUsers",
    "AuthorApex",
    "CustomizeApplication",
    "ManageAuthProviders",
    "SingleSignOn",
    "ApiEnabled",
}

METADATA_SUFFIXES = (
    ".profile-meta.xml",
    ".permissionset-meta.xml",
    ".permissionsetgroup-meta.xml",
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


def audit_file(path: Path) -> list[str]:
    findings: list[str] = []
    root = ET.parse(path).getroot()
    root_type = local_name(root.tag)

    if root_type == "PermissionSetGroup":
        return findings

    for block in root.iter():
        if local_name(block.tag) == "userPermissions":
            name = child_text(block, "name")
            enabled = child_text(block, "enabled").lower() == "true"
            if enabled and name in DANGEROUS_PERMISSIONS:
                findings.append(
                    f"HIGH {path}: {root_type} grants dangerous system permission `{name}`"
                )

        if local_name(block.tag) == "objectPermissions":
            object_name = child_text(block, "object") or "<unknown object>"
            if child_text(block, "viewAllRecords").lower() == "true":
                findings.append(
                    f"HIGH {path}: {object_name} has `viewAllRecords=true`"
                )
            if child_text(block, "modifyAllRecords").lower() == "true":
                findings.append(
                    f"HIGH {path}: {object_name} has `modifyAllRecords=true`"
                )

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Salesforce profile and permission set metadata for "
            "dangerous system permissions and sharing bypass grants."
        )
    )
    parser.add_argument("paths", nargs="+", help="Files or directories to scan")
    args = parser.parse_args()

    files = iter_metadata_files([Path(value) for value in args.paths])
    if not files:
        return emit_result(
            ["HIGH no profile, permission set, or permission set group metadata files found"],
            "Scanned 0 access-model metadata file(s); no files matched the provided paths.",
        )

    findings: list[str] = []
    for path in files:
        findings.extend(audit_file(path))

    summary = f"Scanned {len(files)} access-model metadata file(s); {len(findings)} finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
