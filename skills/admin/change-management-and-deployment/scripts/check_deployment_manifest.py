#!/usr/bin/env python3
"""Audit deployment manifests and metadata folders for common release risks."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


RISKY_TYPES = {"SharingRules", "ConnectedApp", "ExternalCredential", "NamedCredential"}
TEXT_SUFFIXES = {".xml", ".cls", ".trigger", ".js", ".json", ".yaml", ".yml"}
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


def audit_package_xml(path: Path, text: str) -> list[str]:
    findings: list[str] = []
    if "<version>" not in text:
        findings.append(f"HIGH {path}: package.xml is missing an API version")

    if re.search(r"<name>\s*Profile\s*</name>", text):
        findings.append(f"MEDIUM {path}: manifest includes Profile metadata; review for accidental broad access changes")

    for metadata_type in RISKY_TYPES:
        if re.search(rf"<name>\s*{metadata_type}\s*</name>", text):
            findings.append(f"HIGH {path}: manifest includes {metadata_type}; require explicit review and smoke tests")

    wildcard_pattern = re.compile(
        r"<members>\s*\*\s*</members>\s*<name>\s*(Flow|Profile|PermissionSet|CustomObject)\s*</name>",
        re.MULTILINE,
    )
    for match in wildcard_pattern.finditer(text):
        findings.append(f"MEDIUM {path}: wildcard deployment for `{match.group(1)}` reduces review precision")

    return findings


def audit_file(path: Path) -> list[str]:
    findings: list[str] = []
    if not path.exists():
        return [f"HIGH {path}: file not found"]
    if path.suffix.lower() not in TEXT_SUFFIXES and path.name != "package.xml":
        return findings

    text = path.read_text(encoding="utf-8", errors="ignore")
    lower_path = str(path).lower()

    if path.name == "package.xml":
        findings.extend(audit_package_xml(path, text))

    if "/profiles/" in lower_path or path.name.endswith(".profile-meta.xml"):
        findings.append(f"MEDIUM {path}: profile deployment detected; prefer permission-set-focused releases where possible")

    if "/flows/" in lower_path and "<status>Active</status>" in text:
        findings.append(f"LOW {path}: active Flow metadata present; confirm activation timing and smoke tests")

    if any(token in lower_path for token in ("connectedapp", "namedcredential", "externalcredential")):
        findings.append(f"HIGH {path}: integration metadata present; verify environment-specific config and rollback")

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check deployment manifests and metadata folders for release-risk indicators."
    )
    parser.add_argument("paths", nargs="+", help="Manifest files or metadata directories to inspect")
    args = parser.parse_args()

    files = iter_files(args.paths)
    findings: list[str] = []
    for path in files:
        findings.extend(audit_file(path))

    if not files:
        findings.append("HIGH no manifest or metadata files matched the provided paths")

    summary = (
        f"Scanned {len(files)} manifest or metadata file(s); "
        f"{len(findings)} finding(s) detected."
    )
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
