#!/usr/bin/env python3
"""Checker script for limits-and-scalability-planning skill.

Scans a manifest or planning text file for evidence of governor limit awareness:
- Batch scope size recommendations (documented in comments or planning notes)
- SOQL count documentation (expected query count per transaction)
- CPU time estimates or budget notes
- DML statement count documentation
- Heap size considerations
- Async offload decisions (future, queueable, batch)
- Platform event throughput notes
- Data volume projections

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_limits_plan.py --help
    python3 check_limits_plan.py --file path/to/planning-doc.md
    python3 check_limits_plan.py --file path/to/manifest.txt --strict
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Check definitions
# ---------------------------------------------------------------------------

@dataclass
class Check:
    name: str
    description: str
    patterns: list[re.Pattern]
    required_in_strict: bool = True
    found: bool = False


def _p(pattern: str) -> re.Pattern:
    return re.compile(pattern, re.IGNORECASE)


CHECKS: list[Check] = [
    Check(
        name="batch_scope_size",
        description="Batch Apex scope size documented (recommended: 200 records; range 1–2000)",
        patterns=[
            _p(r'\bscope\s*(?:size)?\s*[:=]\s*\d+'),
            _p(r'\bexecutebatch\s*\(.*,\s*\d+\s*\)'),
            _p(r'\brecords?\s+per\s+(?:batch|chunk|execute)\b'),
            _p(r'\bbatch\s+(?:size|scope)\b'),
        ],
        required_in_strict=True,
    ),
    Check(
        name="soql_count",
        description=(
            "SOQL query count documented per transaction "
            "(limit: 100 sync and async; shared with managed packages)"
        ),
        patterns=[
            _p(r'\bsoql\s+(?:count|queries|query\s+count)\b'),
            _p(r'\b\d+\s+(?:soql|queries)\b'),
            _p(r'\bgetqueries\b'),
            _p(r'\btoo\s+many\s+soql\b'),
            _p(r'\bsoql\s+budget\b'),
            _p(r'\b100\s+(?:soql|queries|query)\s+limit\b'),
        ],
        required_in_strict=True,
    ),
    Check(
        name="cpu_time_estimate",
        description=(
            "CPU time budget or estimate noted "
            "(limit: 10,000ms sync / 60,000ms async)"
        ),
        patterns=[
            _p(r'\bcpu\s+(?:time|budget|limit|estimate)\b'),
            _p(r'\b10[,.]?000\s*ms\b'),
            _p(r'\b60[,.]?000\s*ms\b'),
            _p(r'\bcpu\s+limit\b'),
            _p(r'\bgetcputime\b'),
        ],
        required_in_strict=True,
    ),
    Check(
        name="dml_statement_count",
        description=(
            "DML statement count documented per transaction "
            "(limit: 150 statements, 10,000 rows)"
        ),
        patterns=[
            _p(r'\bdml\s+(?:count|statements?|limit)\b'),
            _p(r'\b150\s+dml\b'),
            _p(r'\bgetdmlstatements\b'),
            _p(r'\bdml\s+(?:rows?|row\s+count)\b'),
            _p(r'\b10[,.]?000\s+(?:dml\s+)?rows?\b'),
        ],
        required_in_strict=False,
    ),
    Check(
        name="heap_size_consideration",
        description=(
            "Heap size noted or SELECT field list reduction mentioned "
            "(limit: 6MB sync / 12MB async)"
        ),
        patterns=[
            _p(r'\bheap\s+(?:size|limit|usage)\b'),
            _p(r'\b6\s*mb\b'),
            _p(r'\b12\s*mb\b'),
            _p(r'\bgetheapsize\b'),
            _p(r'\bselect\s+only\s+(?:needed|required|specific)\s+fields?\b'),
            _p(r'\bfield\s+list\s+(?:reduction|selective|minimal)\b'),
        ],
        required_in_strict=False,
    ),
    Check(
        name="async_offload_decision",
        description=(
            "Async offload strategy documented "
            "(future method, Queueable, Batch, or scheduled Apex)"
        ),
        patterns=[
            _p(r'\b@future\b'),
            _p(r'\bqueueable\b'),
            _p(r'\bbatch\s+apex\b'),
            _p(r'\bscheduled\s+apex\b'),
            _p(r'\basync\s+(?:offload|processing|pattern)\b'),
            _p(r'\boff(?:load|loading)\s+to\s+(?:async|future|batch|queueable)\b'),
        ],
        required_in_strict=True,
    ),
    Check(
        name="data_volume_projection",
        description="Data volume projections included (record counts or growth estimates per object)",
        patterns=[
            _p(r'\b\d+[,.]?\d*\s*(?:million|M|k|thousand)\s+records?\b'),
            _p(r'\brecord\s+(?:count|volume|growth)\b'),
            _p(r'\bdata\s+volume\b'),
            _p(r'\brows?\s+per\s+(?:object|year|month)\b'),
            _p(r'\bldv\b'),
            _p(r'\blarge\s+data\s+volume\b'),
        ],
        required_in_strict=False,
    ),
    Check(
        name="platform_event_throughput",
        description=(
            "Platform event throughput or delivery limit noted "
            "(250,000 deliveries/24hrs for standard orgs)"
        ),
        patterns=[
            _p(r'\bplatform\s+event\s+(?:limit|throughput|delivery|volume)\b'),
            _p(r'\b250[,.]?000\s+(?:event|delivery)\b'),
            _p(r'\bevent\s+deliveries?\s+per\s+(?:hour|24|day)\b'),
            _p(r'\b__e\b'),
        ],
        required_in_strict=False,
    ),
    Check(
        name="soql_selectivity",
        description=(
            "SOQL selectivity or indexed field usage documented "
            "(non-selective queries cause full table scans on large objects)"
        ),
        patterns=[
            _p(r'\bselectiv(?:e|ity)\b'),
            _p(r'\bindexed\s+field\b'),
            _p(r'\bfull\s+table\s+scan\b'),
            _p(r'\bskinny\s+table\b'),
            _p(r'\bsoql\s+optimization\b'),
            _p(r'\bquery\s+plan\b'),
        ],
        required_in_strict=False,
    ),
]


# ---------------------------------------------------------------------------
# Core analysis logic
# ---------------------------------------------------------------------------

def analyze_file(path: Path) -> tuple[list[str], list[str]]:
    """Read the file and run all checks. Return (findings, warnings)."""
    try:
        content = path.read_text(encoding='utf-8', errors='replace')
    except OSError as exc:
        return [], [f"Cannot read file {path}: {exc}"]

    lines = content.splitlines()

    # Run each check: scan all lines for any matching pattern
    for check in CHECKS:
        for line in lines:
            if any(p.search(line) for p in check.patterns):
                check.found = True
                break

    findings: list[str] = []
    warnings: list[str] = []

    for check in CHECKS:
        if check.found:
            findings.append(f"  FOUND    [{check.name}]: {check.description}")
        else:
            warnings.append(f"  MISSING  [{check.name}]: {check.description}")

    return findings, warnings


def build_summary(path: Path, findings: list[str], warnings: list[str], strict: bool) -> int:
    """Print results and return exit code."""
    total = len(CHECKS)
    found_count = sum(1 for c in CHECKS if c.found)
    missing_count = total - found_count
    strict_missing = [c for c in CHECKS if not c.found and c.required_in_strict]

    print(f"\nLimits and Scalability Plan Check: {path}")
    print(f"{'=' * 60}")
    print(f"Checks passed: {found_count}/{total}")
    print()

    if findings:
        print("Documented (good):")
        for f in findings:
            print(f)
        print()

    if warnings:
        print("Not documented (gaps):")
        for w in warnings:
            print(w)
        print()

    # Guidance for missing items
    if missing_count > 0:
        print("Guidance for gaps:")
        for check in CHECKS:
            if not check.found:
                print(f"  - [{check.name}] Add a section to the planning document that addresses: {check.description}")
        print()

    # Exit code decision
    if strict and strict_missing:
        print(
            f"FAIL: {len(strict_missing)} required item(s) missing in strict mode: "
            + ", ".join(c.name for c in strict_missing)
        )
        return 1

    if missing_count == 0:
        print("PASS: All limit planning checks are documented.")
        return 0

    print(
        f"ADVISORY: {missing_count} optional item(s) not documented. "
        "Add them to improve completeness. Use --strict to fail on required items only."
    )
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a Salesforce limits planning document or manifest for "
            "evidence of governor limit awareness: batch scope, SOQL counts, "
            "CPU estimates, DML documentation, heap considerations, async offload "
            "decisions, data volume projections, and platform event throughput notes.\n\n"
            "Exit code 0 = pass or advisory; Exit code 1 = missing required items (--strict mode)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        '--file',
        required=True,
        help='Path to the planning document or manifest file to analyze.',
    )
    parser.add_argument(
        '--strict',
        action='store_true',
        default=False,
        help=(
            'Fail (exit 1) if any required check is missing. '
            'Required checks: batch_scope_size, soql_count, cpu_time_estimate, async_offload_decision.'
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    path = Path(args.file)

    if not path.exists():
        print(f"ERROR: File not found: {path}")
        return 1

    if not path.is_file():
        print(f"ERROR: Path is not a file: {path}")
        return 1

    findings, warnings = analyze_file(path)
    return build_summary(path, findings, warnings, strict=args.strict)


if __name__ == '__main__':
    sys.exit(main())
