#!/usr/bin/env python3
"""Audit metadata for legacy automation and overlapping tool-boundary smells."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path


FLOW_OBJECT_RE = re.compile(r"<object>\s*([A-Za-z0-9_]+)\s*</object>", re.IGNORECASE)
PROCESS_TYPE_RE = re.compile(r"<processType>\s*([A-Za-z0-9_]+)\s*</processType>", re.IGNORECASE)
TRIGGER_RE = re.compile(r"trigger\s+\w+\s+on\s+([A-Za-z0-9_]+)", re.IGNORECASE)
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Salesforce metadata for weak automation tool selection and legacy overlap.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory to scan for metadata and Apex.")
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


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        return emit_result([f"HIGH {root}: manifest directory not found"], "Scanned 0 files; manifest directory was missing.")

    findings: list[str] = []
    object_flows: dict[str, int] = defaultdict(int)
    object_triggers: dict[str, int] = defaultdict(int)

    workflow_files = sorted(root.rglob("*.workflow-meta.xml"))
    if workflow_files:
        findings.append(f"REVIEW {root}: {len(workflow_files)} Workflow Rule metadata file(s) found; treat them as migration inventory, not ongoing design")

    for path in sorted(root.rglob("*.flow-meta.xml")):
        text = read_text(path)
        object_match = FLOW_OBJECT_RE.search(text)
        if object_match:
            object_flows[object_match.group(1)] += 1
        process_type = PROCESS_TYPE_RE.search(text)
        if process_type and process_type.group(1).lower() == "workflow":
            findings.append(f"REVIEW {path}: legacy workflow-style Flow metadata found; verify this is migration scope and not an active architecture choice")

    for path in sorted(root.rglob("*.trigger")):
        text = read_text(path)
        object_match = TRIGGER_RE.search(text)
        if object_match:
            object_triggers[object_match.group(1)] += 1

    for object_name in sorted(set(object_flows) | set(object_triggers)):
        flow_count = object_flows.get(object_name, 0)
        trigger_count = object_triggers.get(object_name, 0)
        if flow_count >= 3:
            findings.append(f"REVIEW {root}: {flow_count} Flow metadata files found for object {object_name}; confirm automation ownership is still clear")
        if flow_count > 0 and trigger_count > 0:
            findings.append(f"REVIEW {root}: object {object_name} has both Flow and Apex trigger automation; verify the tool boundary is intentional and documented")

    scanned = len(workflow_files) + len(list(root.rglob('*.flow-meta.xml'))) + len(list(root.rglob('*.trigger')))
    if scanned == 0:
        return emit_result([f"HIGH {root}: no Flow, Workflow Rule, or trigger metadata found"], "Scanned 0 automation files.")

    summary = f"Scanned {scanned} automation file(s); {len(findings)} selection-boundary finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
