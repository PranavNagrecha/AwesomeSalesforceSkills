#!/usr/bin/env python3
"""Checker script for Clinical Data Quality skill — Health Cloud Person Account merge safety.

Scans Salesforce metadata in a local SFDX project directory for:
1. Account merge patterns (Apex files) that lack a pre-merge clinical record reassignment step
2. Duplicate Rule metadata that targets Contact instead of Account (wrong object for Person Accounts)
3. Apex merge statements that may be missing pre-reassignment guards
4. Assumptions of a native Salesforce MPI in Apex/comments

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_clinical_data_quality.py --manifest-dir path/to/sfdx/project
    python3 check_clinical_data_quality.py --manifest-dir .
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from xml.etree import ElementTree


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CLINICAL_OBJECTS = [
    "EpisodeOfCare",
    "PatientMedication",
    "ClinicalEncounter",
    "CareObservation",
    "CoveredBenefit",
]

# Regex patterns
MERGE_STMT_PATTERN = re.compile(r"\bmerge\s+\w+\s+\w+\s*;", re.IGNORECASE)
REASSIGNMENT_HINT = re.compile(
    r"(PreMerge|reassign|reparent|clinical.*reassign|reassign.*clinical)",
    re.IGNORECASE,
)
MPI_ASSUMPTION_PATTERN = re.compile(
    r"(native\s+MPI|built.in\s+(master\s+patient|MPI)|MasterPatientIndex|PatientIdentityResolution)",
    re.IGNORECASE,
)
CONTACT_MERGE_PATTERN = re.compile(
    r"\bmerge\s+\w*[Cc]ontact\w*\s+\w*[Cc]ontact\w*\s*;",
    re.IGNORECASE,
)

# Duplicate Rule XML namespace
SF_NS = "http://soap.sforce.com/2006/04/metadata"


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def check_apex_merge_without_reassignment(manifest_dir: Path) -> list[str]:
    """Find Apex files that call merge on Account/patient records
    but do not reference a clinical record reassignment step."""
    issues: list[str] = []
    apex_files = list(manifest_dir.rglob("*.cls")) + list(manifest_dir.rglob("*.trigger"))

    for apex_file in apex_files:
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        merge_matches = MERGE_STMT_PATTERN.findall(content)
        if not merge_matches:
            continue

        # Check if any merge call is on an Account-like record
        account_merge = any(
            re.search(r"\bmerge\s+\w*[Aa]ccount\w*\s+\w+\s*;", content)
            for _ in merge_matches
        )
        if not account_merge:
            continue

        # Now check if the file references a reassignment step
        if not REASSIGNMENT_HINT.search(content):
            # Check if any clinical object is referenced anywhere in the file
            clinical_referenced = any(obj in content for obj in CLINICAL_OBJECTS)
            if not clinical_referenced:
                issues.append(
                    f"WARN [{apex_file}]: Account merge statement found but no clinical record "
                    f"reassignment reference detected. Verify that EpisodeOfCare, PatientMedication, "
                    f"ClinicalEncounter, and other clinical objects are reassigned BEFORE merge. "
                    f"Clinical records are NOT automatically reparented on Person Account merge."
                )

    return issues


def check_contact_merge_for_person_accounts(manifest_dir: Path) -> list[str]:
    """Find Apex files that merge Contact records — wrong for Person Account patients."""
    issues: list[str] = []
    apex_files = list(manifest_dir.rglob("*.cls")) + list(manifest_dir.rglob("*.trigger"))

    for apex_file in apex_files:
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if CONTACT_MERGE_PATTERN.search(content):
            # Only flag if there's Health Cloud context nearby
            if re.search(r"(PersonAccount|IsPersonAccount|Health\s*Cloud|Patient)", content, re.IGNORECASE):
                issues.append(
                    f"WARN [{apex_file}]: Contact merge statement found in a file with Health Cloud / "
                    f"Person Account references. Person Account patients must be merged via the Account "
                    f"merge path (merge masterAccount duplicateAccount), not Contact merge."
                )

    return issues


def check_duplicate_rule_on_contact_not_account(manifest_dir: Path) -> list[str]:
    """Check Duplicate Rule metadata files to ensure they target Account (not Contact)
    for Person Account patient deduplication."""
    issues: list[str] = []
    dup_rule_files = list(manifest_dir.rglob("*.duplicateRule"))

    for rule_file in dup_rule_files:
        try:
            tree = ElementTree.parse(rule_file)
        except (ElementTree.ParseError, OSError):
            continue

        root = tree.getroot()

        # Strip namespace if present
        def tag(name: str) -> str:
            return f"{{{SF_NS}}}{name}" if SF_NS in root.tag else name

        # Look for sobjectType in matchingRules references or masterLabel context
        # DuplicateRule XML: <SObjectType> or within <duplicateRuleMatchRules> > <matchRuleSObjectType>
        sobj_elements = root.findall(f".//{tag('SObjectType')}")
        for elem in sobj_elements:
            if elem.text and elem.text.strip().lower() == "contact":
                # Check if this rule looks like it might be intended for patients
                full_text = ElementTree.tostring(root, encoding="unicode")
                if re.search(r"(patient|person.account|health.cloud)", full_text, re.IGNORECASE):
                    issues.append(
                        f"WARN [{rule_file}]: Duplicate Rule targets Contact object but references "
                        f"patient/PersonAccount context. Person Account patient deduplication must "
                        f"target the Account object, not Contact."
                    )

    return issues


def check_mpi_assumptions_in_apex(manifest_dir: Path) -> list[str]:
    """Find Apex code or comments that assume a native Salesforce MPI exists.

    Only scans Apex class, trigger, and flow metadata files — not Markdown
    documentation files, which may legitimately discuss the absence of an MPI.
    """
    issues: list[str] = []
    apex_files = (
        list(manifest_dir.rglob("*.cls"))
        + list(manifest_dir.rglob("*.trigger"))
        + list(manifest_dir.rglob("*.flow-meta.xml"))
    )

    for apex_file in apex_files:
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        match = MPI_ASSUMPTION_PATTERN.search(content)
        if match:
            issues.append(
                f"WARN [{apex_file}]: Reference to native MPI or built-in patient identity resolution "
                f"detected ('{match.group(0)}'). Salesforce Health Cloud has no native Master Patient "
                f"Index. Enterprise-scale patient identity requires a third-party ISV (e.g., "
                f"ReltioConnect, Veeva Network, Informatica MDM for Salesforce)."
            )

    return issues


def check_missing_post_merge_audit(manifest_dir: Path) -> list[str]:
    """Warn if Account merge Apex files lack post-merge audit or count-check queries."""
    issues: list[str] = []
    apex_files = list(manifest_dir.rglob("*.cls")) + list(manifest_dir.rglob("*.trigger"))

    for apex_file in apex_files:
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if not re.search(r"\bmerge\s+\w*[Aa]ccount\w*\s+\w+\s*;", content):
            continue

        # Look for any post-merge count or audit query
        has_audit = re.search(
            r"(SELECT\s+COUNT|postMerge|post_merge|auditLog|MergeAudit|after.*merge)",
            content,
            re.IGNORECASE,
        )
        if not has_audit:
            issues.append(
                f"INFO [{apex_file}]: Account merge statement found but no post-merge audit query "
                f"or count check detected. Consider adding post-merge SOQL queries to verify zero "
                f"orphaned clinical records and, for HIPAA-regulated orgs, logging the merge event "
                f"to an audit object."
            )

    return issues


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def check_clinical_data_quality(manifest_dir: Path) -> list[str]:
    """Run all checks and return a combined list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_apex_merge_without_reassignment(manifest_dir))
    issues.extend(check_contact_merge_for_person_accounts(manifest_dir))
    issues.extend(check_duplicate_rule_on_contact_not_account(manifest_dir))
    issues.extend(check_mpi_assumptions_in_apex(manifest_dir))
    issues.extend(check_missing_post_merge_audit(manifest_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Health Cloud Salesforce metadata for clinical data quality issues: "
            "missing pre-merge clinical record reassignment, incorrect Contact-scoped Duplicate Rules, "
            "native MPI assumptions, and missing post-merge audit patterns."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce SFDX project or metadata (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_clinical_data_quality(manifest_dir)

    if not issues:
        print("No clinical data quality issues found.")
        return 0

    warn_count = sum(1 for i in issues if i.startswith("WARN"))
    info_count = sum(1 for i in issues if i.startswith("INFO"))

    for issue in issues:
        if issue.startswith("WARN"):
            print(issue, file=sys.stderr)
        else:
            print(issue)

    print(
        f"\nSummary: {warn_count} warning(s), {info_count} info(s) found.",
        file=sys.stderr if warn_count else sys.stdout,
    )

    return 1 if warn_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
