#!/usr/bin/env python3
"""Checker script for limits-and-scalability-planning skill.

Scans a limits planning document (or every *.md / *.txt file in a directory)
for evidence of governor limit awareness:
- Batch scope size recommendations
- SOQL count documentation (expected query count per transaction)
- CPU time estimates or budget notes
- DML statement count documentation
- Heap size considerations
- Async offload decisions (future, queueable, batch)
- Platform event throughput notes
- Data volume projections
- SOQL selectivity

It also flags stale heap figures: a 6 MB / 12 MB figure in a sentence or table
row that mentions "heap" is the pre-Winter '27 limit (Apex Developer Guide 264
L19780 gives 10 MB sync / 25 MB async) unless that sentence labels it as
Summer '26 / release 262 / API 67.0. MB figures in sentences without "heap"
(file sizes, callout sizes, Apex code size) are ignored.

Exit codes:
    0  pass, advisory gaps, stale-heap WARNs, or no planning files found
    1  ERROR (missing path, unreadable file); with --strict also any WARN,
       any required check missing, or no planning files found

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_limits_plan.py --help
    python3 check_limits_plan.py --file path/to/planning-doc.md
    python3 check_limits_plan.py --manifest-dir path/to/plans/ --strict
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

PLAN_SUFFIXES = {".md", ".txt"}

# ---------------------------------------------------------------------------
# Check definitions
# ---------------------------------------------------------------------------


@dataclass
class Check:
    name: str
    description: str
    patterns: list[re.Pattern]
    required_in_strict: bool = True


def _p(pattern: str) -> re.Pattern:
    return re.compile(pattern, re.IGNORECASE)


CHECKS: list[Check] = [
    Check(
        name="batch_scope_size",
        description="Batch Apex scope size documented (default 200; QueryLocator max 2,000)",
        patterns=[
            _p(r'\bscope\s*(?:size)?\s*[:=]\s*\d+'),
            _p(r'\bexecutebatch\s*\(.*,\s*\d+\s*\)'),
            _p(r'\brecords?\s+per\s+(?:batch|chunk|execute)\b'),
            _p(r'\bbatch\s+(?:size|scope)\b'),
        ],
    ),
    Check(
        name="soql_count",
        description=(
            "SOQL query count documented per transaction "
            "(limit: 100 sync / 200 async; non-certified package code shares it)"
        ),
        patterns=[
            _p(r'\bsoql\s+(?:count|queries|query\s+count)\b'),
            _p(r'\b\d+\s+(?:soql|queries)\b'),
            _p(r'\bgetqueries\b'),
            _p(r'\btoo\s+many\s+soql\b'),
            _p(r'\bsoql\s+budget\b'),
            _p(r'\b100\s+(?:soql|queries|query)\s+limit\b'),
        ],
    ),
    Check(
        name="cpu_time_estimate",
        description="CPU time budget or estimate noted (limit: 10,000ms sync / 60,000ms async)",
        patterns=[
            _p(r'\bcpu\s+(?:time|budget|limit|estimate)\b'),
            _p(r'\b10[,.]?000\s*ms\b'),
            _p(r'\b60[,.]?000\s*ms\b'),
            _p(r'\bgetcputime\b'),
        ],
    ),
    Check(
        name="dml_statement_count",
        description="DML statement count documented per transaction (limit: 150 statements, 10,000 rows)",
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
            "(limit: 10MB sync / 25MB async from Winter '27; 6MB / 12MB through Summer '26)"
        ),
        # MB figures are deliberately absent here: a bare "25 MB" is usually a
        # file size. Heap figures count through _heap_segments() below.
        patterns=[
            _p(r'\bheap\b'),
            _p(r'\bgetheapsize\b'),
            _p(r'\bselect\s+only\s+(?:needed|required|specific)\s+fields?\b'),
            _p(r'\bfield\s+list\s+(?:reduction|selective|minimal)\b'),
        ],
        required_in_strict=False,
    ),
    Check(
        name="async_offload_decision",
        description="Async offload strategy documented (future method, Queueable, Batch, or scheduled Apex)",
        patterns=[
            _p(r'\b@future\b'),
            _p(r'\bqueueable\b'),
            _p(r'\bbatch\s+apex\b'),
            _p(r'\bscheduled\s+apex\b'),
            _p(r'\basync\s+(?:offload|processing|pattern)\b'),
            _p(r'\boff(?:load|loading)\s+to\s+(?:async|future|batch|queueable)\b'),
        ],
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
            "Platform event throughput noted (publishing 250,000/hour EE/UE; "
            "external delivery 25,000 EE / 50,000 UE per 24 h)"
        ),
        patterns=[
            _p(r'\bplatform\s+event\s+(?:limit|throughput|delivery|volume|allocation)\b'),
            _p(r'\b250[,.]?000\s+(?:event|delivery|publish)'),
            _p(r'\bevent\s+deliveries?\s+per\s+(?:hour|24|day)\b'),
            _p(r'\b__e\b'),
        ],
        required_in_strict=False,
    ),
    Check(
        name="soql_selectivity",
        description="SOQL selectivity or indexed field usage documented (non-selective queries scan the table)",
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

HEAP_WORD = _p(r'\bheap\b')
STALE_HEAP_MB = _p(r'\b(?:6|12)\s*MB\b')
SUMMER26_LABEL = _p(r"summer\s*['’]?\s*26|\b262\b|\bapi\s*(?:version\s*)?67(?:\.0)?\b")
SENTENCE_SPLIT = re.compile(r'(?<=[.!?])\s+(?=[A-Z(`*_\-])')

# ---------------------------------------------------------------------------
# Core analysis logic
# ---------------------------------------------------------------------------


def _segments(text: str) -> list[tuple[int, str]]:
    """Split text into (line_no, segment): one per table row, one per prose sentence."""
    segs: list[tuple[int, str]] = []
    para: list[str] = []
    para_start = 0

    def flush() -> None:
        if para:
            for sentence in SENTENCE_SPLIT.split(" ".join(para)):
                segs.append((para_start, sentence))
            para.clear()

    for no, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            flush()
            if line:
                segs.append((no, line))
            continue
        if line.startswith("|"):
            flush()
            segs.append((no, line))
            continue
        if not para:
            para_start = no
        para.append(line)
    flush()
    return segs


def analyze_text(text: str) -> tuple[set[str], list[str]]:
    """Return (names of checks found, stale-heap warnings)."""
    segs = _segments(text)
    found = {
        c.name for c in CHECKS
        if any(p.search(seg) for _, seg in segs for p in c.patterns)
    }
    stale: list[str] = []
    for no, seg in segs:
        if HEAP_WORD.search(seg) and STALE_HEAP_MB.search(seg) and not SUMMER26_LABEL.search(seg):
            snippet = seg if len(seg) <= 100 else seg[:97] + "..."
            stale.append(
                f"L{no}: stale heap figure (6 MB / 12 MB is the Summer '26 limit; "
                f"Winter '27 is 10 MB sync / 25 MB async, Apex Developer Guide 264 L19780) "
                f"— label it Summer '26 or update it: {snippet}"
            )
    return found, stale


def report(path: Path, found: set[str], stale: list[str], strict: bool) -> int:
    """Print results for one file and return its exit code."""
    missing = [c for c in CHECKS if c.name not in found]
    strict_missing = [c for c in missing if c.required_in_strict]

    print(f"\nLimits and Scalability Plan Check: {path}")
    print("=" * 60)
    print(f"Checks passed: {len(CHECKS) - len(missing)}/{len(CHECKS)}")
    for c in CHECKS:
        state = "FOUND  " if c.name in found else "MISSING"
        print(f"  {state}  [{c.name}]: {c.description}")
    for w in stale:
        print(f"WARN: {w}")

    if strict and (strict_missing or stale):
        parts = []
        if strict_missing:
            parts.append("required missing: " + ", ".join(c.name for c in strict_missing))
        if stale:
            parts.append(f"{len(stale)} stale heap WARN(s)")
        print("FAIL (--strict): " + "; ".join(parts))
        return 1
    if not missing and not stale:
        print("PASS: All limit planning checks are documented.")
    else:
        print(f"ADVISORY: {len(missing)} check(s) not documented, {len(stale)} WARN(s). Use --strict to fail on them.")
    return 0


def collect_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in PLAN_SUFFIXES)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a Salesforce limits planning document, or every *.md / *.txt file in a "
            "directory, for governor limit awareness (batch scope, SOQL counts, CPU, DML, heap, "
            "async offload, data volume, platform events, selectivity) and for stale "
            "6 MB / 12 MB heap figures.\n\n"
            "Exit 0 = pass, advisory gaps, WARNs, or no planning files found; "
            "exit 1 = ERROR (missing path or unreadable file), or with --strict any WARN, "
            "required check missing, or no planning files found."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument('--file', help='Planning document, or a directory of them, to analyze.')
    target.add_argument('--manifest-dir', help='Directory of planning documents (*.md, *.txt) to analyze.')
    parser.add_argument(
        '--strict',
        action='store_true',
        help=(
            'Exit 1 on any WARN (stale heap figure, no planning files) or any missing required check: '
            'batch_scope_size, soql_count, cpu_time_estimate, async_offload_decision.'
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    path = Path(args.file or args.manifest_dir)

    if not path.exists():
        print(f"ERROR: path not found: {path}")
        sys.exit(1)

    files = collect_files(path)
    if not files:
        print(f"WARN: no planning files (*.md, *.txt) found in {path}")
        return 1 if args.strict else 0

    worst = 0
    for f in files:
        try:
            text = f.read_text(encoding='utf-8', errors='replace')
        except OSError as exc:
            print(f"ERROR: cannot read {f}: {exc}")
            worst = 1
            continue
        found, stale = analyze_text(text)
        worst = max(worst, report(f, found, stale, args.strict))
    return worst


if __name__ == '__main__':
    sys.exit(main())
