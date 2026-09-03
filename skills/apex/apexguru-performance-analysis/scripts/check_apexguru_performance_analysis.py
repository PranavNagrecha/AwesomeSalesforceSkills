#!/usr/bin/env python3
"""Validate and normalize Salesforce Code Analyzer ApexGuru JSON output."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate ApexGuru Code Analyzer JSON output.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", help="Optional normalized ApexGuru JSON output")
    parser.add_argument("--allow-other-engines", action="store_true")
    return parser.parse_args()


def as_int(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def check_report(report: Any, allow_other: bool) -> tuple[list[str], list[dict[str, Any]], str]:
    issues: list[str] = []
    normalized: list[dict[str, Any]] = []
    if not isinstance(report, dict):
        return ["JSON root must be an object"], [], "Source analysis"

    for key in ("runDir", "violationCounts", "versions", "violations"):
        if key not in report:
            issues.append(f"missing root property: {key}")
    violations = report.get("violations")
    if not isinstance(violations, list):
        issues.append("violations must be an array")
        violations = []

    explicit_mode = report.get("analysisMode")
    if explicit_mode == "static":
        evidence_mode = "Static only"
    elif explicit_mode == "full":
        evidence_mode = "Production insights"
    elif isinstance(explicit_mode, str) and explicit_mode.strip():
        evidence_mode = explicit_mode.strip()
    else:
        evidence_mode = "Source analysis"

    for index, violation in enumerate(violations):
        prefix = f"violations[{index}]"
        if not isinstance(violation, dict):
            issues.append(f"{prefix} must be an object")
            continue
        engine = str(violation.get("engine", ""))
        is_apexguru = engine.lower() == "apexguru"
        if not is_apexguru:
            if not allow_other:
                issues.append(f"{prefix}.engine is {engine!r}, expected 'apexguru'")
            continue

        rule = violation.get("rule")
        message = violation.get("message")
        severity = as_int(violation.get("severity"))
        locations = violation.get("locations")
        primary = as_int(violation.get("primaryLocationIndex"))
        if not isinstance(rule, str) or not rule.strip():
            issues.append(f"{prefix}.rule must be a non-empty string")
        if not isinstance(message, str) or not message.strip():
            issues.append(f"{prefix}.message must be a non-empty string")
        if severity not in {1, 2, 3, 4, 5}:
            issues.append(f"{prefix}.severity must be an integer from 1 to 5")
        if not isinstance(locations, list) or not locations:
            issues.append(f"{prefix}.locations must be a non-empty array")
            locations = []
        if primary is None or primary < 0 or primary >= len(locations):
            issues.append(f"{prefix}.primaryLocationIndex is out of range")

        normalized_locations: list[dict[str, Any]] = []
        for loc_index, location in enumerate(locations):
            loc_prefix = f"{prefix}.locations[{loc_index}]"
            if not isinstance(location, dict):
                issues.append(f"{loc_prefix} must be an object")
                continue
            file_name = location.get("file")
            start_line = as_int(location.get("startLine"))
            if not isinstance(file_name, str) or not file_name.lower().endswith((".cls", ".trigger")):
                issues.append(f"{loc_prefix}.file must reference .cls or .trigger")
            if start_line is None or start_line < 1:
                issues.append(f"{loc_prefix}.startLine must be a positive integer")
            normalized_locations.append({
                "file": file_name,
                "startLine": start_line,
                "startColumn": location.get("startColumn"),
                "endLine": location.get("endLine"),
                "endColumn": location.get("endColumn"),
                "comment": location.get("comment"),
            })

        normalized.append({
            "finding_id": f"AG-{len(normalized) + 1:03d}",
            "rule": rule,
            "engine": engine,
            "severity": severity,
            "message": message,
            "tags": violation.get("tags", []),
            "primaryLocationIndex": primary,
            "locations": normalized_locations,
            "resources": violation.get("resources", []),
            "evidence_mode": evidence_mode,
        })
    return issues, normalized, evidence_mode


def main() -> int:
    args = parse_args()
    path = Path(args.input)
    if not path.is_file():
        print(f"ERROR: not found: {path}")
        return 2
    raw = path.read_bytes()
    try:
        report = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid JSON: {exc}")
        return 2

    issues, findings, evidence_mode = check_report(report, args.allow_other_engines)
    for issue in issues:
        print(f"ISSUE: {issue}")
    print(f"REPORT sha256={hashlib.sha256(raw).hexdigest()} evidence_mode={evidence_mode!r} apexguru_findings={len(findings)}")

    if args.output:
        output = {
            "source": str(path),
            "source_sha256": hashlib.sha256(raw).hexdigest(),
            "evidence_mode": evidence_mode,
            "finding_count": len(findings),
            "findings": findings,
        }
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"WROTE: {out_path}")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
