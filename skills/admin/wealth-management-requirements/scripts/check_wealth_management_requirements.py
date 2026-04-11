#!/usr/bin/env python3
"""Checker script for Wealth Management Requirements skill.

Validates FSC wealth management requirements artifacts for common structural issues:
- Namespace consistency (FinServ__ vs. no-namespace mixing)
- Missing architecture determination documentation
- Missing volume data in requirements documents
- Use of AccountFinancialSummary without PSL integration user note

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_wealth_management_requirements.py [--help]
    python3 check_wealth_management_requirements.py --manifest-dir path/to/metadata
    python3 check_wealth_management_requirements.py --requirements-doc path/to/requirements.md
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Managed-package FSC object names (FinServ__ namespace)
_FINSERV_PATTERN = re.compile(r"FinServ__\w+", re.IGNORECASE)

# FSC Core object names (no namespace)
_FSC_CORE_OBJECTS = re.compile(
    r"\b(FinancialAccount|FinancialGoal|FinancialPlan|FinancialAccountParty"
    r"|FinancialAccountRole|FinancialHolding|AccountFinancialSummary"
    r"|ActionPlan|ActionPlanTemplate)\b",
    re.IGNORECASE,
)

# AccountFinancialSummary without PSL integration user mention
_ACCOUNT_FINANCIAL_SUMMARY = re.compile(r"AccountFinancialSummary", re.IGNORECASE)
_PSL_MENTION = re.compile(r"PSL|Platform Service Layer|integration user", re.IGNORECASE)

# Architecture determination indicators
_ARCH_DETERMINATION = re.compile(
    r"managed.package|FSC.Core|FinServ__.namespace|namespace.confirm|architecture.determin",
    re.IGNORECASE,
)

# Volume data indicators
_VOLUME_DATA = re.compile(
    r"\d+.*(household|advisor|account|client|record|ActionPlan|holding)",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check FSC wealth management requirements artifacts for common structural issues."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Root directory of Salesforce metadata to scan (optional).",
    )
    parser.add_argument(
        "--requirements-doc",
        default=None,
        help="Path to a requirements document (.md or .txt) to validate.",
    )
    return parser.parse_args()


def check_metadata_namespace_mixing(manifest_dir: Path) -> list[str]:
    """Detect files that mix managed-package and FSC Core object names."""
    issues: list[str] = []
    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Scan .xml, .cls, .trigger, .flow files
    extensions = (".xml", ".cls", ".trigger", ".flow", ".json")
    for ext in extensions:
        for fpath in manifest_dir.rglob(f"*{ext}"):
            try:
                content = fpath.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

            has_finserv = bool(_FINSERV_PATTERN.search(content))
            has_core = bool(_FSC_CORE_OBJECTS.search(content))

            if has_finserv and has_core:
                issues.append(
                    f"[NAMESPACE_MIX] {fpath}: contains both FinServ__ (managed package) "
                    f"and no-namespace FSC Core object references. "
                    f"Confirm org architecture and use one naming convention consistently."
                )

    return issues


def check_requirements_document(doc_path: Path) -> list[str]:
    """Validate a requirements document for FSC wealth management completeness."""
    issues: list[str] = []

    if not doc_path.exists():
        issues.append(f"Requirements document not found: {doc_path}")
        return issues

    try:
        content = doc_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        issues.append(f"Could not read requirements document: {exc}")
        return issues

    # Check 1: Architecture determination section present
    if not _ARCH_DETERMINATION.search(content):
        issues.append(
            "[MISSING_ARCH_DETERMINATION] Requirements document does not appear to contain "
            "an architecture determination section. Confirm whether the org uses the "
            "managed package (FinServ__ namespace) or FSC Core (no namespace) before "
            "referencing any FSC object names."
        )

    # Check 2: Mixed namespace references
    has_finserv = bool(_FINSERV_PATTERN.search(content))
    has_core_objects = bool(_FSC_CORE_OBJECTS.search(content))
    if has_finserv and has_core_objects:
        issues.append(
            "[NAMESPACE_MIX] Requirements document references both FinServ__ (managed package) "
            "and no-namespace (FSC Core) object names. Pick one architecture and use it "
            "consistently throughout all requirements documentation."
        )

    # Check 3: AccountFinancialSummary without PSL integration user note
    if _ACCOUNT_FINANCIAL_SUMMARY.search(content) and not _PSL_MENTION.search(content):
        issues.append(
            "[MISSING_PSL_NOTE] Requirements document references AccountFinancialSummary "
            "but does not mention the FSC PSL integration user requirement. "
            "AccountFinancialSummary is only populated via the FSC Platform Service Layer "
            "batch process running under a dedicated integration user. Add this as a "
            "prerequisite requirement."
        )

    # Check 4: Volume data present (warning, not error)
    if not _VOLUME_DATA.search(content):
        issues.append(
            "[MISSING_VOLUME_DATA] Requirements document does not appear to contain "
            "volume data (number of households, advisors, accounts, or records). "
            "Capture volume metrics during requirements discovery to inform architecture "
            "and performance decisions."
        )

    return issues


def main() -> int:
    args = parse_args()
    all_issues: list[str] = []

    if args.manifest_dir:
        manifest_dir = Path(args.manifest_dir)
        all_issues.extend(check_metadata_namespace_mixing(manifest_dir))

    if args.requirements_doc:
        doc_path = Path(args.requirements_doc)
        all_issues.extend(check_requirements_document(doc_path))

    if not args.manifest_dir and not args.requirements_doc:
        # Default: scan current directory as manifest
        all_issues.extend(check_metadata_namespace_mixing(Path(".")))

    if not all_issues:
        print("No issues found.")
        return 0

    for issue in all_issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
