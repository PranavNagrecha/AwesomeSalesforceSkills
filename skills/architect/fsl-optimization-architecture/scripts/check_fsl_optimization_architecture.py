#!/usr/bin/env python3
"""Checker script for FSL Optimization Architecture skill.

Reviews documentation or design artifacts for FSL optimization architecture issues.
Since this is an architect skill, checks are heuristic-based on text/markdown files.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_fsl_optimization_architecture.py [--help]
    python3 check_fsl_optimization_architecture.py --manifest-dir path/to/design-docs
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_LARGE_TERRITORY_RE = re.compile(r'\b([6-9]\d|[1-9]\d{2,})\s*resources?\b', re.IGNORECASE)
_ESO_ALL_AT_ONCE_RE = re.compile(r'enable\s+ESO\s+for\s+all\s+territories', re.IGNORECASE)
_CONCURRENT_OPT_RE = re.compile(r'concurrent\s+(global\s+)?optim', re.IGNORECASE)
_NO_MONITOR_RE_TRIGGER = re.compile(r'global\s+optim', re.IGNORECASE)
_MONITOR_RE = re.compile(r'monit|alert|job\s+status|optim.*job', re.IGNORECASE)


def check_fsl_optimization_architecture(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in design documents."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    md_files = list(manifest_dir.rglob("*.md")) + list(manifest_dir.rglob("*.txt"))
    if not md_files:
        return issues

    for doc_file in md_files:
        try:
            content = doc_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        rel = doc_file.relative_to(manifest_dir)

        # Check 1: Territory resource counts over 50 in design docs
        if _LARGE_TERRITORY_RE.search(content):
            issues.append(
                f"{rel}: Document mentions territory with potentially large resource count. "
                "FSL Global optimization is recommended to stay under 50 resources and 1,000 SA/day per territory. "
                "Verify territory sizes are within limits."
            )

        # Check 2: All-at-once ESO adoption
        if _ESO_ALL_AT_ONCE_RE.search(content):
            issues.append(
                f"{rel}: Document recommends enabling ESO for all territories at once. "
                "ESO has no automatic fallback to legacy engine. "
                "Recommend phased territory-by-territory adoption."
            )

        # Check 3: Concurrent optimization mentioned without serialization note
        if _CONCURRENT_OPT_RE.search(content):
            issues.append(
                f"{rel}: Concurrent optimization mentioned. "
                "Territories sharing resources via Secondary ServiceTerritoryMember must serialize optimization. "
                "Verify this document accounts for shared-resource conflicts."
            )

        # Check 4: Global optimization mentioned without monitoring
        if _NO_MONITOR_RE_TRIGGER.search(content) and not _MONITOR_RE.search(content):
            issues.append(
                f"{rel}: Global optimization mentioned but no monitoring/alerting discussed. "
                "Global optimization timeouts are silent (no exception). "
                "Add monitoring for optimization job completion status."
            )

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check FSL Optimization Architecture design documents for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory containing design documents (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_fsl_optimization_architecture(manifest_dir)

    if not issues:
        print("No FSL Optimization Architecture issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
