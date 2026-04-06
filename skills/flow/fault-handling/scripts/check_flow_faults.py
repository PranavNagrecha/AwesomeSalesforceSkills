#!/usr/bin/env python3
"""Review Flow metadata for missing fault connectors and weak error handling."""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


FLOW_SUFFIX = ".flow-meta.xml"
RISKY_ELEMENTS = {"recordCreates", "recordDeletes", "recordLookups", "recordUpdates", "actionCalls", "subflows"}
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def local_name(tag: str) -> str:
    return tag.split("}", 1)[-1]


def child_text(element: ET.Element, child_name: str) -> str:
    for child in element:
        if local_name(child.tag) == child_name:
            return (child.text or "").strip()
    return ""


def has_child(element: ET.Element, child_name: str) -> bool:
    return any(local_name(child.tag) == child_name for child in element)


def iter_flow_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        path = Path(raw)
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
    normalized = [normalize_finding(item) for item in findings]
    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(item["severity"], 0) for item in normalized))
    print(json.dumps({"score": score, "findings": normalized, "summary": summary}, indent=2))
    if normalized:
        print(f"WARN: {len(normalized)} finding(s) detected", file=sys.stderr)
    return 1 if normalized else 0


def audit_flow(path: Path) -> list[str]:
    findings: list[str] = []
    root = ET.parse(path).getroot()
    for child in root:
        tag_name = local_name(child.tag)
        if tag_name not in RISKY_ELEMENTS:
            continue
        label = child_text(child, "label") or child_text(child, "name") or "<unnamed element>"
        if not has_child(child, "faultConnector"):
            findings.append(f"HIGH {path}: `{label}` ({tag_name}) has no fault connector")

    fault_message_mentions = 0
    for text_node in root.iter():
        if text_node.text and "$Flow.FaultMessage" in text_node.text:
            fault_message_mentions += 1
    if fault_message_mentions == 0:
        findings.append(f"REVIEW {path}: no $Flow.FaultMessage usage found; confirm diagnostic detail is captured elsewhere")

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check Flow metadata for missing fault connectors and weak diagnostic handling."
    )
    parser.add_argument("paths", nargs="+", help="Flow metadata files or directories")
    args = parser.parse_args()

    files = iter_flow_files(args.paths)
    if not files:
        return emit_result(
            ["HIGH no Flow metadata files found"],
            "Scanned 0 Flow metadata file(s); no matching .flow-meta.xml files were found.",
        )

    findings: list[str] = []
    for path in files:
        findings.extend(audit_flow(path))

    summary = f"Scanned {len(files)} Flow metadata file(s); {len(findings)} finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
