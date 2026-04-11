#!/usr/bin/env python3
"""Checker script for FSC Financial Calculations skill.

Inspects Apex class metadata under a Salesforce project directory for common
FSC financial calculation anti-patterns:

  1. Trigger-based portfolio calculations on FinancialHolding that include
     inner SOQL queries (row-lock / limit risk).
  2. Database.Batchable classes using Database.Stateful with large accumulator
     collections (Map/List fields growing across execute chunks).
  3. Bulk-load scripts that reference FinancialHolding inserts/upserts without
     any reference to WealthAppConfig or RollupRecalculationBatchable.
  4. DML or SOQL inside execute() loops in batch classes.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_fsc_financial_calculations.py [--help]
    python3 check_fsc_financial_calculations.py --manifest-dir path/to/force-app
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Detect a trigger on FinancialHolding (namespace-agnostic)
_TRIGGER_ON_HOLDING = re.compile(
    r"\btrigger\b.+\bon\b.+FinancialHolding",
    re.IGNORECASE,
)

# SOQL inside a trigger body (simplified: SELECT inside a trigger file)
_INNER_SOQL = re.compile(r"\bSELECT\b", re.IGNORECASE)

# Database.Batchable implementation
_BATCHABLE = re.compile(r"\bDatabase\.Batchable\b", re.IGNORECASE)

# Database.Stateful
_STATEFUL = re.compile(r"\bDatabase\.Stateful\b", re.IGNORECASE)

# Instance-level Map or List field declarations (state accumulator risk)
# Matches lines like:  global Map<Id, List<Decimal>> results = ...
_STATEFUL_COLLECTION = re.compile(
    r"^\s*(global|public|private)\s+(Map|List)\s*<",
    re.IGNORECASE | re.MULTILINE,
)

# References to WealthAppConfig (trigger suppression pattern)
_WEALTH_APP_CONFIG = re.compile(r"WealthAppConfig", re.IGNORECASE)

# References to RollupRecalculationBatchable
_RECALC_BATCH = re.compile(r"RollupRecalculationBatchable", re.IGNORECASE)

# FinancialHolding insert/upsert in a non-trigger Apex file
_HOLDING_DML = re.compile(
    r"\b(insert|upsert)\b.+FinancialHolding",
    re.IGNORECASE,
)

# DML inside a for loop (rough heuristic: for(...) or for ... : followed by insert/update)
_FOR_LOOP_DML = re.compile(
    r"for\s*[\(\:].*\n(?:.*\n)*?.*\b(insert|update|upsert|delete)\b",
    re.IGNORECASE | re.MULTILINE,
)

# SOQL inside a for loop
_FOR_LOOP_SOQL = re.compile(
    r"for\s*[\(\:].*\n(?:.*\n)*?.*\bSELECT\b",
    re.IGNORECASE | re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_apex_files(manifest_dir: Path) -> list[tuple[Path, str]]:
    """Return list of (path, content) for all .cls and .trigger files."""
    results = []
    for ext in ("*.cls", "*.trigger"):
        for f in manifest_dir.rglob(ext):
            try:
                content = f.read_text(encoding="utf-8", errors="replace")
                results.append((f, content))
            except OSError:
                pass
    return results


def _is_trigger_file(path: Path, content: str) -> bool:
    return path.suffix == ".trigger" or bool(_TRIGGER_ON_HOLDING.search(content))


def _is_batch_file(content: str) -> bool:
    return bool(_BATCHABLE.search(content))


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def check_trigger_with_soql_on_holding(
    path: Path, content: str, issues: list[str]
) -> None:
    """Warn when a trigger on FinancialHolding contains a SOQL query."""
    if _is_trigger_file(path, content) and _TRIGGER_ON_HOLDING.search(content):
        if _INNER_SOQL.search(content):
            issues.append(
                f"{path}: Trigger on FinancialHolding__c contains SOQL — "
                "at bulk scale this causes row-lock contention on parent FinancialAccount__c. "
                "Move aggregate queries and calculations to a Database.Batchable class instead."
            )


def check_stateful_batch_with_accumulator(
    path: Path, content: str, issues: list[str]
) -> None:
    """Warn when a Stateful batch class declares instance-level Map/List fields."""
    if _is_batch_file(content) and _STATEFUL.search(content):
        collections = _STATEFUL_COLLECTION.findall(content)
        if collections:
            issues.append(
                f"{path}: Database.Stateful batch class declares {len(collections)} "
                "instance-level Map/List field(s). Accumulating large collections across "
                "execute() chunks causes heap exhaustion. Write results to the DB at the end "
                "of each execute() chunk; reserve Database.Stateful for lightweight counters only."
            )


def check_bulk_holding_dml_without_safety_pattern(
    path: Path, content: str, issues: list[str]
) -> None:
    """Warn when an Apex file inserts/upserts FinancialHolding without the safety pattern."""
    if _HOLDING_DML.search(content):
        has_config_reference = bool(_WEALTH_APP_CONFIG.search(content))
        has_recalc_reference = bool(_RECALC_BATCH.search(content))
        if not has_config_reference and not has_recalc_reference:
            issues.append(
                f"{path}: File performs DML on FinancialHolding__c but does not reference "
                "WealthAppConfig__c or FinServ.RollupRecalculationBatchable. "
                "Bulk loads must disable FSC rollup triggers before loading and run "
                "RollupRecalculationBatchable after. Missing this causes UNABLE_TO_LOCK_ROW errors."
            )


def check_dml_in_for_loop(path: Path, content: str, issues: list[str]) -> None:
    """Warn when DML or SOQL appears to be inside a for loop."""
    if _FOR_LOOP_DML.search(content):
        issues.append(
            f"{path}: Possible DML inside a for loop detected. "
            "In batch execute() context this will hit governor limits at bulk scale. "
            "Collect results in a List and perform a single DML call after the loop."
        )
    if _FOR_LOOP_SOQL.search(content):
        issues.append(
            f"{path}: Possible SOQL inside a for loop detected. "
            "Refactor to query outside the loop and use a Map for lookups."
        )


# ---------------------------------------------------------------------------
# Main checker
# ---------------------------------------------------------------------------


def check_fsc_financial_calculations(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found under manifest_dir."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    apex_files = _read_apex_files(manifest_dir)

    if not apex_files:
        # Not necessarily an error — the directory may be intentionally empty
        return issues

    for path, content in apex_files:
        check_trigger_with_soql_on_holding(path, content, issues)
        check_stateful_batch_with_accumulator(path, content, issues)
        check_bulk_holding_dml_without_safety_pattern(path, content, issues)
        check_dml_in_for_loop(path, content, issues)

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce Apex files for FSC financial calculation anti-patterns. "
            "Covers: trigger-based portfolio queries, unsafe bulk loads missing the "
            "WealthAppConfig safety protocol, Database.Stateful accumulator misuse, "
            "and DML/SOQL inside for loops."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    args = parser.parse_args()
    manifest_dir = Path(args.manifest_dir)

    issues = check_fsc_financial_calculations(manifest_dir)

    if not issues:
        print("No FSC financial calculation issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
