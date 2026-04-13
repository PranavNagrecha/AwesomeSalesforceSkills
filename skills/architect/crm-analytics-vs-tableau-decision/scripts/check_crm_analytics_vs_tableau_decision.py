#!/usr/bin/env python3
"""Checker script for CRM Analytics vs Tableau Decision skill.

Scans a project directory for analytics decision documentation and flags
common omissions: missing freshness documentation, missing connector
constraint acknowledgment, missing license comparison, and use of the
deprecated "Tableau CRM" product name without disambiguation.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_crm_analytics_vs_tableau_decision.py [--help]
    python3 check_crm_analytics_vs_tableau_decision.py --manifest-dir path/to/project
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Patterns that indicate a decision document exists and covers key concerns
# ---------------------------------------------------------------------------

# Deprecated product name used without a disambiguation note
DEPRECATED_NAME_PATTERN = re.compile(
    r"\bTableau CRM\b",
    re.IGNORECASE,
)

# Connector constraint: extract-only acknowledgment
EXTRACT_ONLY_PATTERN = re.compile(
    r"extract[-\s]only|not\s+live|no\s+live\s+query|scheduled\s+refresh|refresh\s+cadence",
    re.IGNORECASE,
)

# 30-day lookback cap acknowledgment
THIRTY_DAY_PATTERN = re.compile(
    r"30[-\s]day|thirty[-\s]day|lookback\s+cap|incremental.*cap|cap.*incremental",
    re.IGNORECASE,
)

# No Custom SQL acknowledgment
NO_CUSTOM_SQL_PATTERN = re.compile(
    r"no\s+custom\s+sql|custom\s+sql\s+not\s+supported|does\s+not\s+support.*custom\s+sql",
    re.IGNORECASE,
)

# License model documentation
LICENSE_PATTERN = re.compile(
    r"permission\s+set\s+licen|PSL|creator.*explorer.*viewer|viewer.*creator|tableau\+|Tableau\s+Next",
    re.IGNORECASE,
)

# Row-level security consideration
RLS_PATTERN = re.compile(
    r"row[-\s]level\s+security|RLS|sharing\s+model|dataset\s+predicate|OWD",
    re.IGNORECASE,
)

# Markdown files that may contain decision documentation
DECISION_FILE_GLOB_PATTERNS = [
    "*.md",
    "docs/*.md",
    "decisions/*.md",
    "architecture/*.md",
    "analytics/*.md",
]


def find_markdown_files(root: Path) -> list[Path]:
    """Return all Markdown files under root."""
    return list(root.rglob("*.md"))


def scan_files_for_pattern(files: list[Path], pattern: re.Pattern) -> bool:
    """Return True if any file contains a match for pattern."""
    for f in files:
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            if pattern.search(content):
                return True
        except OSError:
            continue
    return False


def find_deprecated_name_files(files: list[Path]) -> list[str]:
    """Return paths of files that use the deprecated 'Tableau CRM' name."""
    hits: list[str] = []
    disambig = re.compile(
        r"deprecated|old\s+name|formerly|previously\s+known|renamed|CRM\s+Analytics",
        re.IGNORECASE,
    )
    for f in files:
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            if DEPRECATED_NAME_PATTERN.search(content):
                # Check if there is a nearby disambiguation
                if not disambig.search(content):
                    hits.append(str(f))
        except OSError:
            continue
    return hits


def check_crm_analytics_vs_tableau_decision(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    md_files = find_markdown_files(manifest_dir)

    if not md_files:
        issues.append(
            "No Markdown files found under the manifest directory. "
            "Expected at least one analytics decision or architecture document."
        )
        return issues

    # Check 1: Deprecated name usage without disambiguation
    deprecated_hits = find_deprecated_name_files(md_files)
    for path in deprecated_hits:
        issues.append(
            f"'Tableau CRM' used without disambiguation in: {path}. "
            "'Tableau CRM' is the deprecated name for CRM Analytics (formerly Einstein Analytics). "
            "Add a note clarifying it is not the same as Tableau Desktop/Server/Cloud."
        )

    # Check 2: Extract-only constraint documented
    if not scan_files_for_pattern(md_files, EXTRACT_ONLY_PATTERN):
        issues.append(
            "No documentation found acknowledging that the Tableau Salesforce connector is "
            "extract-only (not live/direct query). Decision documents should explicitly state "
            "this constraint when Tableau is evaluated for Salesforce-centric use cases."
        )

    # Check 3: 30-day lookback cap documented
    if not scan_files_for_pattern(md_files, THIRTY_DAY_PATTERN):
        issues.append(
            "No documentation found acknowledging the 30-day incremental refresh lookback cap "
            "on the Tableau Salesforce connector. This constraint affects historical data "
            "accuracy and should be documented in the analytics decision record."
        )

    # Check 4: No Custom SQL constraint documented
    if not scan_files_for_pattern(md_files, NO_CUSTOM_SQL_PATTERN):
        issues.append(
            "No documentation found acknowledging that the Tableau Salesforce connector does "
            "not support Custom SQL. Decision documents should note this limitation when "
            "complex data shaping is required from Salesforce."
        )

    # Check 5: License model documented
    if not scan_files_for_pattern(md_files, LICENSE_PATTERN):
        issues.append(
            "No documentation found comparing CRM Analytics Permission Set License (PSL) model "
            "with Tableau's Creator/Explorer/Viewer or Tableau+ license model. Analytics platform "
            "decisions should include a licensing cost and model comparison."
        )

    # Check 6: Row-level security addressed
    if not scan_files_for_pattern(md_files, RLS_PATTERN):
        issues.append(
            "No documentation found addressing row-level security or the Salesforce sharing model. "
            "CRM Analytics vs Tableau decisions must assess whether Salesforce record-level "
            "security needs to be enforced in the analytics layer."
        )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_crm_analytics_vs_tableau_decision(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check analytics decision documentation for CRM Analytics vs Tableau "
            "decision completeness. Flags missing constraint acknowledgments, "
            "deprecated naming, and omitted license comparisons."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory to scan for analytics decision documents (default: current directory).",
    )
    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(main())
