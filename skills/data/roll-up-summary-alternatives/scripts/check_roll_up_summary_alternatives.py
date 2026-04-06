#!/usr/bin/env python3
"""Audit roll-up summary alternatives for scale and metadata-limit risks."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


SUMMARY_FIELD_RE = re.compile(r"<type>\s*Summary\s*</type>|<summarizedField>", re.IGNORECASE)
AGG_SOQL_RE = re.compile(r"\[\s*SELECT\b.*\b(COUNT|SUM|AVG|MIN|MAX)\s*\(", re.IGNORECASE)
LOOP_RE = re.compile(r"\b(for|while)\b")
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check metadata and Apex for weak roll-up summary alternative patterns.")
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


def iter_summary_fields(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*field-meta.xml") if path.is_file())


def iter_apex(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in {".cls", ".trigger"})


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        return emit_result([f"HIGH {root}: manifest directory not found"], "Scanned 0 files; manifest directory was missing.")

    findings: list[str] = []
    summary_fields = [path for path in iter_summary_fields(root) if SUMMARY_FIELD_RE.search(path.read_text(encoding="utf-8", errors="ignore"))]
    if len(summary_fields) >= 35:
        findings.append(f"REVIEW {root}: {len(summary_fields)} roll-up summary field metadata file(s) found; verify the org is not approaching native summary limits")

    for path in iter_apex(root):
        text = path.read_text(encoding="utf-8", errors="ignore")
        loop_depth = 0
        for line_number, raw_line in enumerate(text.splitlines(), start=1):
            line = raw_line.strip()
            if LOOP_RE.search(line) and "for each" not in line.lower():
                loop_depth += line.count("{") or 1
            if loop_depth > 0 and AGG_SOQL_RE.search(line):
                findings.append(f"HIGH {path}:{line_number}: aggregate SOQL found inside a loop; collect parent IDs and aggregate once")
            if "}" in line and loop_depth > 0:
                loop_depth = max(0, loop_depth - line.count("}"))

    scanned = len(summary_fields) + len(iter_apex(root))
    if scanned == 0:
        return emit_result([f"HIGH {root}: no relevant metadata or Apex files found"], "Scanned 0 files; no roll-up-related files were found.")
    summary = f"Scanned {scanned} file(s); {len(findings)} roll-up-alternative finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
