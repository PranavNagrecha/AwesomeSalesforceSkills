#!/usr/bin/env python3
"""Check retention-matrix documents for completeness.

Reads a retention matrix markdown file and flags:
- Events without retention tiers filled in.
- Absent regulatory mapping.
- Absent cost model.
- Absent query runbook.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED_SECTIONS = (
    "regulatory mapping",
    "routing architecture",
    "query runbook",
)

REQUIRED_EVENTS = (
    "Login",
    "RestApi",
    "ReportExport",
    "ApexExecution",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect a retention matrix markdown document.",
    )
    parser.add_argument("--doc", required=True, help="Path to retention-matrix.md.")
    return parser.parse_args()


def check_doc(path: Path) -> list[str]:
    issues: list[str] = []
    if not path.exists():
        return [f"Doc not found: {path}"]

    text = path.read_text(encoding="utf-8", errors="ignore")
    lower = text.lower()

    for section in REQUIRED_SECTIONS:
        if section not in lower:
            issues.append(f"{path}: missing section `{section}`")

    for event in REQUIRED_EVENTS:
        if event in text:
            line = next((ln for ln in text.splitlines() if event in ln), "")
            filled_cells = [c.strip() for c in line.split("|") if c.strip() and c.strip() != event]
            if len(filled_cells) < 4:
                issues.append(f"{path}: event `{event}` row is not fully filled in")
        else:
            issues.append(f"{path}: expected event `{event}` not represented")

    if "cost" not in lower:
        issues.append(f"{path}: no cost model mentioned — retention decisions usually hinge on ingest cost")

    return issues


def main() -> int:
    args = parse_args()
    issues = check_doc(Path(args.doc))

    if not issues:
        print("Retention matrix looks complete.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
