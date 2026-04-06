#!/usr/bin/env python3
"""Validate sandbox strategy plans for required sections and common omissions."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


REQUIRED_SECTIONS = [
    "Environment Inventory",
    "Refresh Cadence",
    "Masking and Data Policy",
    "Post-Refresh Tasks",
    "Release Path",
]
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


def audit_plan(path: Path) -> list[str]:
    findings: list[str] = []
    if not path.is_file():
        return [f"HIGH {path}: file not found"]

    text = path.read_text(encoding="utf-8", errors="ignore")
    for section in REQUIRED_SECTIONS:
        pattern = rf"^##+\s+{re.escape(section)}\b"
        if not re.search(pattern, text, re.MULTILINE):
            findings.append(f"HIGH {path}: missing required section `{section}`")

    if "TODO" in text:
        findings.append(f"LOW {path}: unresolved TODO markers remain")

    lower = text.lower()
    if any(token in lower for token in ("partial copy", "full sandbox", "full copy")) and "mask" not in lower:
        findings.append(f"HIGH {path}: production-like sandbox mentioned without masking policy")

    if "refresh" in lower and "post-refresh" not in lower:
        findings.append(f"MEDIUM {path}: refresh cadence described without post-refresh task section")

    if "developer sandbox" in lower and "source" not in lower and "devops center" not in lower:
        findings.append(f"LOW {path}: developer sandbox strategy does not mention source discipline")

    return findings


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


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check sandbox strategy markdown plans for required sections and masking/refresh omissions."
    )
    parser.add_argument("plans", nargs="+", help="Markdown strategy files to review")
    args = parser.parse_args()

    findings: list[str] = []
    for value in args.plans:
        findings.extend(audit_plan(Path(value)))

    summary = f"Scanned {len(args.plans)} sandbox strategy plan input(s); {len(findings)} finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
