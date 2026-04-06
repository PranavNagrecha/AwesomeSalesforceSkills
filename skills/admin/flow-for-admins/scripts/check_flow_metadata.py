#!/usr/bin/env python3
"""Review Flow metadata for missing fault paths and complexity signals."""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


FLOW_SUFFIX = ".flow-meta.xml"
DATA_ACTION_ELEMENTS = {
    "recordCreates",
    "recordDeletes",
    "recordLookups",
    "recordUpdates",
    "actionCalls",
}
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def local_name(tag: str) -> str:
    return tag.split("}", 1)[-1]


def child_text(element: ET.Element, child_name: str) -> str:
    for child in element:
        if local_name(child.tag) == child_name:
            return (child.text or "").strip()
    return ""


def iter_flow_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            files.extend(candidate for candidate in path.rglob(f"*{FLOW_SUFFIX}") if candidate.is_file())
        elif path.is_file() and path.name.endswith(FLOW_SUFFIX):
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


def has_child(element: ET.Element, child_name: str) -> bool:
    return any(local_name(child.tag) == child_name for child in element)


def audit_flow(path: Path) -> list[str]:
    findings: list[str] = []
    root = ET.parse(path).getroot()

    counts = {"decisions": 0, "loops": 0}
    data_action_count = 0

    for child in root:
        tag_name = local_name(child.tag)
        if tag_name == "decisions":
            counts["decisions"] += 1
        if tag_name == "loops":
            counts["loops"] += 1
        if tag_name in DATA_ACTION_ELEMENTS:
            data_action_count += 1
            label = child_text(child, "label") or child_text(child, "name") or "<unnamed element>"
            if not has_child(child, "faultConnector"):
                findings.append(
                    f"HIGH {path}: `{label}` ({tag_name}) has no fault connector"
                )

    if counts["decisions"] > 10:
        findings.append(
            f"MEDIUM {path}: flow has {counts['decisions']} decision elements; consider subflows"
        )

    if counts["loops"] and data_action_count:
        findings.append(
            f"REVIEW {path}: flow contains loops plus data/action elements; confirm no queries or DML happen inside loops"
        )

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scan Flow metadata for missing fault connectors and complexity risks."
    )
    parser.add_argument("paths", nargs="+", help="Files or directories to scan")
    args = parser.parse_args()

    files = iter_flow_files([Path(value) for value in args.paths])
    if not files:
        return emit_result(
            ["HIGH no Flow metadata files found"],
            "Scanned 0 Flow metadata file(s); no files matched the provided paths.",
        )

    findings: list[str] = []
    for path in files:
        findings.extend(audit_flow(path))

    summary = f"Scanned {len(files)} Flow metadata file(s); {len(findings)} finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
