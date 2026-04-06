#!/usr/bin/env python3
"""Audit Flow custom property editor LWCs for weak builder contracts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


FLOW_TARGET_RE = re.compile(r"lightning__FlowScreen", re.IGNORECASE)
CONFIG_EDITOR_RE = re.compile(r"configurationEditor\s*=", re.IGNORECASE)
INPUT_VARS_RE = re.compile(r"inputVariables", re.IGNORECASE)
BUILDER_CTX_RE = re.compile(r"builderContext", re.IGNORECASE)
CHANGE_EVENT_RE = re.compile(r"configuration_editor_input_value_changed", re.IGNORECASE)
VALIDATE_RE = re.compile(r"\bvalidate\s*\(", re.IGNORECASE)
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check LWC metadata and JS for custom property editor contract issues.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory to scan for LWC files.")
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
    allowed = {".js", ".xml"}
    return sorted(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in allowed)


def audit_file(path: Path) -> list[str]:
    findings: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore")
    lower_name = path.name.lower()

    if path.suffix.lower() == ".xml" and FLOW_TARGET_RE.search(text) and not CONFIG_EDITOR_RE.search(text):
        findings.append(f"REVIEW {path}: Flow screen target found without obvious `configurationEditor` registration; verify a custom property editor is wired intentionally")
    if (INPUT_VARS_RE.search(text) or BUILDER_CTX_RE.search(text) or "editor" in lower_name) and path.suffix.lower() == ".js":
        if not CHANGE_EVENT_RE.search(text):
            findings.append(f"REVIEW {path}: builder-style editor JS found without the standard configuration-editor change event")
        if BUILDER_CTX_RE.search(text) and not VALIDATE_RE.search(text):
            findings.append(f"REVIEW {path}: builder-context-aware editor found without an obvious `validate()` method; verify builder-side validation is intentionally omitted")
    return findings


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        return emit_result([f"HIGH {root}: manifest directory not found"], "Scanned 0 LWC files; manifest directory was missing.")
    files = iter_files(root)
    if not files:
        return emit_result([f"HIGH {root}: no LWC files found"], "Scanned 0 LWC files; no .js or .xml files were found.")
    findings: list[str] = []
    for path in files:
        findings.extend(audit_file(path))
    summary = f"Scanned {len(files)} LWC file(s); {len(findings)} custom-property-editor finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
