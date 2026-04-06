#!/usr/bin/env python3
"""Audit OmniStudio DataRaptor assets for type-fit and maintainability smells."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


JSON_SUFFIXES = {".json", ".txt", ".xml"}
DATARAPTOR_RE = re.compile(r"DataRaptor|DR[A-Za-z]", re.IGNORECASE)
TURBO_RE = re.compile(r"Turbo", re.IGNORECASE)
FORMULA_RE = re.compile(r"formula", re.IGNORECASE)
MAPPING_RE = re.compile(r"map|mapping|field", re.IGNORECASE)
ID_RE = re.compile(r"\b[0-9A-Za-z]{15,18}\b")
PLACEHOLDER_RE = re.compile(r"DataRaptor\d+|DR\d+", re.IGNORECASE)
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check DataRaptor-like assets for weak type choices and brittle mappings.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory to scan for OmniStudio assets.")
    return parser.parse_args()


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


def iter_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in JSON_SUFFIXES)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def audit_file(path: Path) -> list[str]:
    findings: list[str] = []
    text = read_text(path)

    if not (DATARAPTOR_RE.search(path.name) or DATARAPTOR_RE.search(text)):
        return findings

    if PLACEHOLDER_RE.search(path.name) or PLACEHOLDER_RE.search(text):
        findings.append(f"REVIEW {path}: placeholder-style DataRaptor naming found; use business-meaningful asset names")

    if TURBO_RE.search(path.name) or TURBO_RE.search(text):
        if FORMULA_RE.search(text):
            findings.append(f"HIGH {path}: Turbo-style DataRaptor contains formula markers; verify a standard Extract is the correct asset instead")

    mapping_count = len(MAPPING_RE.findall(text))
    if mapping_count >= 120:
        findings.append(f"REVIEW {path}: DataRaptor contains heavy mapping density; confirm the asset should not be split into clearer read/transform boundaries")

    if "Load" in path.name or re.search(r"DataRaptor\s+Load", text, re.IGNORECASE):
        for match in ID_RE.findall(text):
            if len(match) in {15, 18}:
                findings.append(f"REVIEW {path}: possible hardcoded ID found in a DataRaptor Load asset; verify write behavior is environment-safe")
                break

    return findings


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        return emit_result([f"HIGH {root}: manifest directory not found"], "Scanned 0 files; manifest directory was missing.")

    files = iter_files(root)
    findings: list[str] = []
    dataraptor_hits = 0
    for path in files:
        text = read_text(path)
        if DATARAPTOR_RE.search(path.name) or DATARAPTOR_RE.search(text):
            dataraptor_hits += 1
            findings.extend(audit_file(path))

    if dataraptor_hits == 0:
        return emit_result([f"HIGH {root}: no DataRaptor-like assets found"], "Scanned 0 DataRaptor-related files.")

    summary = f"Observed {dataraptor_hits} DataRaptor-related file(s); {len(findings)} DataRaptor finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
