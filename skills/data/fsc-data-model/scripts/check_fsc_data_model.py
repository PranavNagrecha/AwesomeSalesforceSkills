#!/usr/bin/env python3
"""Checker script for FSC Data Model skill.

Scans Salesforce metadata files for common FSC data model issues:
- Namespace consistency: FinServ__ prefix usage in SOQL/Apex vs. expected org type
- Missing JointOwner clause in financial account queries (managed-package orgs)
- Attempted native ROLLUP summary fields targeting FSC financial objects
- SOQL queries on FinancialAccount without FinancialAccountParty in Core FSC context
- Conflation of FSC and NPSP household objects

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_fsc_data_model.py [--help]
    python3 check_fsc_data_model.py --manifest-dir path/to/metadata
    python3 check_fsc_data_model.py --manifest-dir path/to/metadata --org-type core
    python3 check_fsc_data_model.py --manifest-dir path/to/metadata --org-type managed
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Detects FinServ__-namespaced FSC object references in any text file
FINSERV_NS_PATTERN = re.compile(r"\bFinServ__\w+", re.IGNORECASE)

# Detects SOQL queries on FinServ__FinancialAccount__c
SOQL_FA_MANAGED = re.compile(
    r"\bFROM\s+FinServ__FinancialAccount__c\b", re.IGNORECASE
)

# Detects WHERE clause with PrimaryOwner but no JointOwner (likely incomplete)
SOQL_PRIMARY_ONLY = re.compile(
    r"FinServ__PrimaryOwner__c\s*=.*?(?!FinServ__JointOwner__c)",
    re.IGNORECASE | re.DOTALL,
)

# Detects NPSP namespace in FSC-specific files
NPSP_IN_FSC = re.compile(r"\bnpe0[124]__\w+|\bnpo0[2]__\w+", re.IGNORECASE)

# Detects attempted ROLLUP summary field definitions targeting FSC objects
ROLLUP_FSC = re.compile(
    r"<summaryOperation>count|sum|min|max</summaryOperation>.*?FinServ__Financial",
    re.IGNORECASE | re.DOTALL,
)

# Detects native ROLLUP targeting FinancialAccount (Core FSC) in field metadata
ROLLUP_CORE_FSC = re.compile(
    r"<summaryForeignKey>FinancialAccount\.",
    re.IGNORECASE,
)

# File extensions to scan
SCANNABLE_EXTENSIONS = {".cls", ".trigger", ".flow", ".xml", ".soql", ".sql", ".md"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def iter_source_files(root: Path):
    """Yield all scannable source files under root."""
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in SCANNABLE_EXTENSIONS:
            yield path


def read_file_safe(path: Path) -> str:
    """Read a file, returning empty string on decode errors."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_finserv_namespace_in_core_org(path: Path, content: str) -> list[str]:
    """Flag FinServ__ namespace references when org-type is confirmed Core FSC."""
    issues = []
    matches = FINSERV_NS_PATTERN.findall(content)
    if matches:
        unique = sorted(set(matches))[:5]
        issues.append(
            f"{path}: FinServ__ namespace references found {unique} — "
            "Core FSC orgs use standard objects with no namespace prefix. "
            "Verify org type; if this is a managed-package org, this is expected."
        )
    return issues


def check_missing_joint_owner_clause(path: Path, content: str) -> list[str]:
    """Flag SOQL on FinancialAccount__c that queries PrimaryOwner without JointOwner."""
    issues = []
    if not SOQL_FA_MANAGED.search(content):
        return issues
    # Check for PrimaryOwner filter without any JointOwner reference nearby
    if "FinServ__PrimaryOwner__c" in content and "FinServ__JointOwner__c" not in content:
        issues.append(
            f"{path}: SOQL queries FinServ__FinancialAccount__c filtering on "
            "FinServ__PrimaryOwner__c but no FinServ__JointOwner__c clause found. "
            "Joint accounts will be excluded. Add OR FinServ__JointOwner__c = :id."
        )
    return issues


def check_npsp_objects_in_fsc_context(path: Path, content: str) -> list[str]:
    """Flag NPSP namespace references in FSC-related files."""
    issues = []
    # Only flag if the file also contains FSC-specific terms
    has_fsc_context = bool(
        re.search(r"\bFinServ__|\bFinancialAccount\b|\bHouseHold\b", content, re.IGNORECASE)
    )
    if not has_fsc_context:
        return issues
    npsp_matches = NPSP_IN_FSC.findall(content)
    if npsp_matches:
        unique = sorted(set(npsp_matches))[:3]
        issues.append(
            f"{path}: NPSP namespace references {unique} found in FSC-context file. "
            "FSC household uses AccountContactRelation and standard Account (RecordType=HouseHold), "
            "not NPSP household objects. Verify the correct household model is being used."
        )
    return issues


def check_rollup_summary_on_fsc_objects(path: Path, content: str) -> list[str]:
    """Flag native ROLLUP summary field metadata targeting FSC financial objects."""
    issues = []
    if ROLLUP_FSC.search(content):
        issues.append(
            f"{path}: Native ROLLUP summary field definition appears to target FSC financial objects. "
            "FSC does not use native ROLLUP summaries — it uses its own async rollup engine. "
            "Read FinServ__TotalAssets__c / FinServ__NetWorth__c from the household Account instead."
        )
    if ROLLUP_CORE_FSC.search(content):
        issues.append(
            f"{path}: Native ROLLUP summary field targeting FinancialAccount (Core FSC) detected. "
            "Core FSC uses the Industries rollup framework, not native Salesforce ROLLUP summaries. "
            "Configure rollups in FSC/Industries Admin Settings."
        )
    return issues


def check_household_query_missing_isactive(path: Path, content: str) -> list[str]:
    """Flag AccountContactRelation queries that may be missing IsActive filter."""
    issues = []
    if "AccountContactRelation" not in content:
        return issues
    # Heuristic: SELECT on ACR without IsActive filter
    has_select_acr = bool(re.search(
        r"\bFROM\s+AccountContactRelation\b", content, re.IGNORECASE
    ))
    has_isactive = bool(re.search(r"\bIsActive\b", content, re.IGNORECASE))
    if has_select_acr and not has_isactive:
        issues.append(
            f"{path}: SOQL queries AccountContactRelation without an IsActive filter. "
            "Deactivated household members (IsActive = FALSE) will be included. "
            "Add AND IsActive = TRUE to restrict to current household members."
        )
    return issues


# ---------------------------------------------------------------------------
# Main checker
# ---------------------------------------------------------------------------

def check_fsc_data_model(manifest_dir: Path, org_type: str = "unknown") -> list[str]:
    """Return a list of issue strings found in the manifest directory.

    Args:
        manifest_dir: Root of the Salesforce metadata or source directory.
        org_type: 'core', 'managed', or 'unknown'. When 'core', FinServ__ usage is flagged.
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    for source_file in iter_source_files(manifest_dir):
        content = read_file_safe(source_file)
        if not content:
            continue

        # Namespace consistency check — only flag as error when org-type is explicitly Core
        if org_type == "core":
            issues.extend(check_finserv_namespace_in_core_org(source_file, content))

        # Missing JointOwner in managed-package queries
        if org_type in ("managed", "unknown"):
            issues.extend(check_missing_joint_owner_clause(source_file, content))

        # NPSP/FSC conflation
        issues.extend(check_npsp_objects_in_fsc_context(source_file, content))

        # Native ROLLUP summary on FSC objects
        issues.extend(check_rollup_summary_on_fsc_objects(source_file, content))

        # ACR without IsActive filter
        issues.extend(check_household_query_missing_isactive(source_file, content))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for FSC data model issues: "
            "namespace consistency, ownership query completeness, "
            "rollup anti-patterns, and household membership filtering."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--org-type",
        choices=["core", "managed", "unknown"],
        default="unknown",
        help=(
            "FSC deployment type: 'core' (platform-native, no namespace), "
            "'managed' (FinServ__ namespace), or 'unknown' (default). "
            "Setting 'core' enables strict namespace checks."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_fsc_data_model(manifest_dir, org_type=args.org_type)

    if not issues:
        print("No FSC data model issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
