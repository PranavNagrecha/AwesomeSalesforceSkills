#!/usr/bin/env python3
"""Checker script for FSL Offline Architecture skill.

Reviews design documents for FSL offline architecture issues:
- Reliance on validation rules for offline data quality
- Missing page reference calculation
- Missing ghost record cleanup mention

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_fsl_offline_architecture.py [--help]
    python3 check_fsl_offline_architecture.py --manifest-dir path/to/design-docs
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_VR_OFFLINE_RE = re.compile(r'validation\s*rule.*offline|offline.*validation\s*rule', re.IGNORECASE)
_PAGE_REF_RE = re.compile(r'page\s*reference|1[,.]?000\s*page|priming\s*limit', re.IGNORECASE)
_PRIMING_RE = re.compile(r'prim(e|ing)', re.IGNORECASE)
_GHOST_RE = re.compile(r'ghost\s*record|cleanResyncGhosts', re.IGNORECASE)
_OFFLINE_RE = re.compile(r'offline', re.IGNORECASE)


def check_fsl_offline_architecture(manifest_dir: Path) -> list[str]:
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

        # Skip small files that likely aren't design documents
        if len(content) < 200:
            continue

        # Check 1: Validation rules mentioned as offline quality mechanism
        if _VR_OFFLINE_RE.search(content):
            issues.append(
                f"{rel}: Validation rules mentioned in offline context. "
                "VRs fire at sync time, not during offline work. "
                "Add app-layer (LWC/OmniScript) checks for offline quality enforcement."
            )

        # Check 2: Priming mentioned but no page reference limit calculation
        if _PRIMING_RE.search(content) and not _PAGE_REF_RE.search(content):
            issues.append(
                f"{rel}: FSL priming mentioned but no page reference limit calculation found. "
                "Calculate: WOs per tech × WOLIs per WO × child objects. "
                "Must stay under 1,000 page references to avoid silent priming failure."
            )

        # Check 3: Offline mentioned but no ghost record cleanup
        if _OFFLINE_RE.search(content) and not _GHOST_RE.search(content):
            issues.append(
                f"{rel}: FSL offline architecture mentioned but no ghost record cleanup strategy found. "
                "Ghost records (server-deleted while offline) persist until cleanResyncGhosts() is called. "
                "Add automated ghost record cleanup to the post-sync workflow."
            )

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check FSL Offline Architecture design documents for common issues.",
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
    issues = check_fsl_offline_architecture(manifest_dir)

    if not issues:
        print("No FSL Offline Architecture issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
