#!/usr/bin/env python3
"""Checker script for Nonprofit Data Architecture skill.

Inspects a Salesforce metadata directory (SFDX project format) for common
NPSP data architecture anti-patterns:

  - SOQL queries on Opportunity using ContactId (wrong for NPSP HH model)
  - References to pmdm__ objects without PMM package documentation
  - CRLP Rollup__mdt record creation mixed with legacy batch job scheduling
  - npo02__ rollup fields used in financial reporting contexts
  - RecordType.Name = 'Household Account' (fragile; should use DeveloperName)
  - AccountContactRelationship used for household membership (FSC pattern, not NPSP)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_nonprofit_data_architecture.py [--help]
    python3 check_nonprofit_data_architecture.py --manifest-dir path/to/sfdx/project
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Patterns to detect
# ---------------------------------------------------------------------------

# Anti-pattern 1: Querying Opportunity via ContactId (wrong for NPSP HH model)
OPPORTUNITY_CONTACT_ID_RE = re.compile(
    r"Opportunity\b[^'\"]*WHERE[^'\"]*\bContactId\s*=",
    re.IGNORECASE | re.DOTALL,
)

# Anti-pattern 1b: SELECT ... FROM Opportunity WHERE ContactId
SOQL_CONTACT_ID_RE = re.compile(
    r"FROM\s+Opportunity\b[^;)]{0,500}WHERE[^;)]{0,300}\bContactId\s*[=!]",
    re.IGNORECASE | re.DOTALL,
)

# Anti-pattern 2: pmdm__ field or object references without package guard
PMM_NAMESPACE_RE = re.compile(
    r"\bpmdm__\w+",
    re.IGNORECASE,
)

PMM_GUARD_RE = re.compile(
    r"(containsKey|InstalledSubscriberPackage|pmdm.*installed|PMM.*installed)",
    re.IGNORECASE,
)

# Anti-pattern 3: CRLP Rollup__mdt AND RLLP_OppRollup_BATCH in same file
ROLLUP_MDT_RE = re.compile(r"\bRollup__mdt\b", re.IGNORECASE)
LEGACY_BATCH_RE = re.compile(r"\bRLLP_OppRollup_BATCH\b", re.IGNORECASE)

# Anti-pattern 4: npo02__ rollup fields used in financial/tax/audit contexts
ROLLUP_FIELD_RE = re.compile(
    r"\bnpo02__(TotalOppAmount|OppAmountThisYear|OppAmountLastYear|LastOppAmount)__c\b",
    re.IGNORECASE,
)
FINANCIAL_CONTEXT_RE = re.compile(
    r"(tax\s+(acknowledgment|receipt|letter)|audit|grant\s+report|financial\s+report|"
    r"IRS|year.end\s+letter|charitable\s+receipt)",
    re.IGNORECASE,
)

# Anti-pattern 5: RecordType.Name = 'Household Account' (fragile — should use DeveloperName)
RECORD_TYPE_DISPLAY_NAME_RE = re.compile(
    r"RecordType\.Name\s*[=!]=?\s*['\"]Household\s+Account['\"]",
    re.IGNORECASE,
)

# Anti-pattern 6: AccountContactRelationship used for NPSP household membership
ACR_HOUSEHOLD_RE = re.compile(
    r"AccountContactRelationship\b[^;)]{0,400}(household|HH_Account|nonprofit)",
    re.IGNORECASE | re.DOTALL,
)


# ---------------------------------------------------------------------------
# File extensions to check
# ---------------------------------------------------------------------------

CHECKABLE_EXTENSIONS = {".cls", ".trigger", ".flow-meta.xml", ".soql", ".py", ".js", ".ts"}


def should_check(path: Path) -> bool:
    return any(path.name.endswith(ext) for ext in CHECKABLE_EXTENSIONS)


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_opportunity_contact_id(content: str, filepath: Path) -> list[str]:
    issues = []
    if SOQL_CONTACT_ID_RE.search(content) or OPPORTUNITY_CONTACT_ID_RE.search(content):
        issues.append(
            f"{filepath}: NPSP anti-pattern — Opportunity queried by ContactId. "
            "In the NPSP Household Account model, Opportunities link to the HH Account "
            "(AccountId), not to ContactId. Use AccountId = :contact.AccountId instead. "
            "See references/examples.md > Anti-Pattern."
        )
    return issues


def check_pmm_without_guard(content: str, filepath: Path) -> list[str]:
    issues = []
    if PMM_NAMESPACE_RE.search(content) and not PMM_GUARD_RE.search(content):
        issues.append(
            f"{filepath}: PMM (pmdm__) objects referenced without package installation guard. "
            "PMM is a separate managed package from NPSP core. Add a Schema.getGlobalDescribe() "
            "containsKey('pmdm__ServiceDelivery__c') check or equivalent before accessing these objects. "
            "See references/gotchas.md > Gotcha 2."
        )
    return issues


def check_crlp_legacy_conflict(content: str, filepath: Path) -> list[str]:
    issues = []
    if ROLLUP_MDT_RE.search(content) and LEGACY_BATCH_RE.search(content):
        issues.append(
            f"{filepath}: CRLP conflict risk — file references both Rollup__mdt (CRLP) "
            "and RLLP_OppRollup_BATCH (legacy rollup). Running both engines simultaneously "
            "corrupts rollup fields. Confirm only one engine is active. "
            "See references/gotchas.md > Gotcha 3."
        )
    return issues


def check_rollup_in_financial_context(content: str, filepath: Path) -> list[str]:
    issues = []
    if ROLLUP_FIELD_RE.search(content) and FINANCIAL_CONTEXT_RE.search(content):
        issues.append(
            f"{filepath}: npo02__ rollup field used in financial/tax/audit context. "
            "NPSP rollup fields are calculated summaries and can be stale. "
            "For financial reporting, aggregate from raw Opportunity records via SOQL. "
            "See references/llm-anti-patterns.md > Anti-Pattern 6."
        )
    return issues


def check_household_account_display_name(content: str, filepath: Path) -> list[str]:
    issues = []
    if RECORD_TYPE_DISPLAY_NAME_RE.search(content):
        issues.append(
            f"{filepath}: RecordType.Name = 'Household Account' is fragile — the display name "
            "can be renamed by admins. Use RecordType.DeveloperName = 'HH_Account' instead. "
            "See references/gotchas.md > Gotcha 5."
        )
    return issues


def check_acr_household_pattern(content: str, filepath: Path) -> list[str]:
    issues = []
    if ACR_HOUSEHOLD_RE.search(content):
        issues.append(
            f"{filepath}: AccountContactRelationship used in household/nonprofit context. "
            "This is an FSC Household Group pattern, not an NPSP pattern. "
            "In NPSP, household membership is via Contact.AccountId pointing to HH_Account. "
            "See references/llm-anti-patterns.md > Anti-Pattern 5."
        )
    return issues


# ---------------------------------------------------------------------------
# Main checker
# ---------------------------------------------------------------------------

def check_nonprofit_data_architecture(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    checked_count = 0
    for filepath in manifest_dir.rglob("*"):
        if not filepath.is_file() or not should_check(filepath):
            continue

        # Skip the checker script itself and other repo tooling
        if "scripts/check_" in str(filepath).replace("\\", "/"):
            continue

        try:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        checked_count += 1
        issues.extend(check_opportunity_contact_id(content, filepath))
        issues.extend(check_pmm_without_guard(content, filepath))
        issues.extend(check_crlp_legacy_conflict(content, filepath))
        issues.extend(check_rollup_in_financial_context(content, filepath))
        issues.extend(check_household_account_display_name(content, filepath))
        issues.extend(check_acr_household_pattern(content, filepath))

    if checked_count == 0:
        issues.append(
            f"No checkable source files found in {manifest_dir}. "
            "Pass the root of an SFDX project (contains force-app/ or src/)."
        )

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for NPSP data architecture anti-patterns. "
            "Pass the root of an SFDX project directory."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce SFDX project (default: current directory).",
    )
    args = parser.parse_args()
    manifest_dir = Path(args.manifest_dir)

    issues = check_nonprofit_data_architecture(manifest_dir)

    if not issues:
        print("No NPSP data architecture issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    print(f"\n{len(issues)} issue(s) found.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
