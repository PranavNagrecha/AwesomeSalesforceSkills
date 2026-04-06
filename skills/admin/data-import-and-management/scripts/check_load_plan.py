#!/usr/bin/env python3
"""Validate CSV load files for required columns and External ID issues."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}


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


def audit_csv(path: Path, required: list[str], external_id: str | None) -> list[str]:
    findings: list[str] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        missing_columns = [column for column in required if column not in fieldnames]
        for column in missing_columns:
            findings.append(f"HIGH {path}: missing required column `{column}`")

        seen_external_ids: set[str] = set()
        for index, row in enumerate(reader, start=2):
            for column in required:
                if column in row and not (row.get(column) or "").strip():
                    findings.append(f"MEDIUM {path}:{index}: blank value in required column `{column}`")

            if external_id:
                value = (row.get(external_id) or "").strip()
                if not value:
                    findings.append(f"HIGH {path}:{index}: blank External ID in `{external_id}`")
                elif value in seen_external_ids:
                    findings.append(f"HIGH {path}:{index}: duplicate External ID `{value}`")
                else:
                    seen_external_ids.add(value)

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check CSV load files for required columns, blanks, and duplicate External IDs."
    )
    parser.add_argument("files", nargs="+", help="CSV files to audit")
    parser.add_argument("--required", nargs="*", default=[], help="Required column names")
    parser.add_argument("--external-id", help="Column used as External ID / upsert key")
    args = parser.parse_args()

    findings: list[str] = []
    scanned = 0
    for value in args.files:
        path = Path(value)
        if not path.is_file():
            findings.append(f"HIGH {path}: file not found")
            continue
        scanned += 1
        findings.extend(audit_csv(path, args.required, args.external_id))

    summary = f"Scanned {scanned} CSV load file(s); {len(findings)} finding(s) detected."
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
