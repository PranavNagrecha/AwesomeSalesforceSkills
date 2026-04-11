#!/usr/bin/env python3
"""Checker script for FSC Compliant Data Sharing API skill.

Scans Salesforce metadata and Apex source files for patterns that bypass
Compliant Data Sharing (CDS) or indicate common CDS misconfigurations.

Checks performed:
  1. Direct AccountShare/OpportunityShare DML with RowCause = 'CompliantDataSharing'
  2. Direct AccountShare/OpportunityShare delete DML (CDS revocation bypass)
  3. AccountParticipant/OpportunityParticipant inserts without ParticipantRoleId
  4. AccountShare DML with RowCause = 'Apex' in files that also reference AccountParticipant
  5. IndustriesSettings metadata missing CDS enable flags

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_fsc_compliant_sharing_api.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Matches: new AccountShare(...) or new OpportunityShare(...)
RE_SHARE_CONSTRUCTOR = re.compile(
    r'\bnew\s+(Account|Opportunity)Share\s*\(',
    re.IGNORECASE,
)

# Matches RowCause = 'CompliantDataSharing' or RowCause = "CompliantDataSharing"
RE_ROW_CAUSE_CDS = re.compile(
    r'RowCause\s*=\s*[\'"]CompliantDataSharing[\'"]',
    re.IGNORECASE,
)

# Matches RowCause = 'Apex' or Schema.AccountShare.rowCause.Apex
RE_ROW_CAUSE_APEX = re.compile(
    r'RowCause\s*=\s*[\'"]Apex[\'"]'
    r'|rowCause\.Apex\b',
    re.IGNORECASE,
)

# Matches delete DML targeting AccountShare or OpportunityShare lists/variables
RE_DELETE_SHARE = re.compile(
    r'\bdelete\b[^;]*?(Account|Opportunity)Share',
    re.IGNORECASE | re.DOTALL,
)

# Matches AccountParticipant or OpportunityParticipant constructor
RE_PARTICIPANT_CONSTRUCTOR = re.compile(
    r'\bnew\s+(Account|Opportunity)Participant\s*\(',
    re.IGNORECASE,
)

# Matches ParticipantRoleId = inside a constructor block
RE_PARTICIPANT_ROLE_ID = re.compile(
    r'ParticipantRoleId\s*=',
    re.IGNORECASE,
)

# IndustriesSettings CDS flags
RE_CDS_ACCOUNT_FLAG = re.compile(
    r'enableCompliantDataSharingForAccount\s*>\s*true',
    re.IGNORECASE,
)
RE_CDS_OPPORTUNITY_FLAG = re.compile(
    r'enableCompliantDataSharingForOpportunity\s*>\s*true',
    re.IGNORECASE,
)
RE_CDS_CUSTOM_FLAG = re.compile(
    r'enableCompliantDataSharingForCustomObjects\s*>\s*true',
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# File collection helpers
# ---------------------------------------------------------------------------


def collect_apex_files(manifest_dir: Path) -> list[Path]:
    """Return all .cls and .trigger files under manifest_dir."""
    apex_files: list[Path] = []
    for ext in ("*.cls", "*.trigger"):
        apex_files.extend(manifest_dir.rglob(ext))
    return apex_files


def collect_settings_files(manifest_dir: Path) -> list[Path]:
    """Return all IndustriesSettings metadata files."""
    return list(manifest_dir.rglob("IndustriesSettings.settings-meta.xml"))


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------


def check_direct_cds_row_cause(apex_files: list[Path]) -> list[str]:
    """Detect AccountShare/OpportunityShare DML using RowCause = 'CompliantDataSharing'."""
    issues: list[str] = []
    for path in apex_files:
        content = path.read_text(encoding="utf-8", errors="replace")
        if RE_SHARE_CONSTRUCTOR.search(content) and RE_ROW_CAUSE_CDS.search(content):
            issues.append(
                f"{path}: Direct AccountShare/OpportunityShare DML with RowCause='CompliantDataSharing' detected. "
                "This row cause is reserved for platform-internal CDS use. "
                "Insert AccountParticipant/OpportunityParticipant records instead."
            )
    return issues


def check_share_delete_bypass(apex_files: list[Path]) -> list[str]:
    """Detect delete DML on AccountShare/OpportunityShare rows (CDS revocation bypass)."""
    issues: list[str] = []
    for path in apex_files:
        content = path.read_text(encoding="utf-8", errors="replace")
        if RE_DELETE_SHARE.search(content):
            issues.append(
                f"{path}: delete DML targeting AccountShare or OpportunityShare detected. "
                "In CDS-enabled orgs, share rows are platform-managed and regenerated on recalculation. "
                "Revoke access by deleting AccountParticipant/OpportunityParticipant records instead."
            )
    return issues


def check_participant_missing_role_id(apex_files: list[Path]) -> list[str]:
    """Detect AccountParticipant/OpportunityParticipant inserts that may be missing ParticipantRoleId."""
    issues: list[str] = []
    for path in apex_files:
        content = path.read_text(encoding="utf-8", errors="replace")
        if RE_PARTICIPANT_CONSTRUCTOR.search(content) and not RE_PARTICIPANT_ROLE_ID.search(content):
            issues.append(
                f"{path}: AccountParticipant or OpportunityParticipant constructor found but "
                "ParticipantRoleId assignment not detected in this file. "
                "ParticipantRoleId is a required field — verify it is set before insert."
            )
    return issues


def check_apex_row_cause_in_cds_file(apex_files: list[Path]) -> list[str]:
    """Detect AccountShare with RowCause='Apex' in files that also reference AccountParticipant."""
    issues: list[str] = []
    for path in apex_files:
        content = path.read_text(encoding="utf-8", errors="replace")
        has_participant = RE_PARTICIPANT_CONSTRUCTOR.search(content)
        has_apex_row_cause = (
            RE_SHARE_CONSTRUCTOR.search(content) and RE_ROW_CAUSE_APEX.search(content)
        )
        if has_participant and has_apex_row_cause:
            issues.append(
                f"{path}: AccountShare with RowCause='Apex' found alongside AccountParticipant usage. "
                "In CDS-enabled orgs, all Account/Opportunity sharing should flow through participant records. "
                "Direct Apex-managed share rows bypass the CDS audit trail."
            )
    return issues


def check_industries_settings(settings_files: list[Path]) -> list[str]:
    """Check IndustriesSettings for missing CDS enable flags."""
    issues: list[str] = []
    if not settings_files:
        # Settings file not present — informational only
        return issues
    for path in settings_files:
        content = path.read_text(encoding="utf-8", errors="replace")
        if not RE_CDS_ACCOUNT_FLAG.search(content):
            issues.append(
                f"{path}: enableCompliantDataSharingForAccount is not set to true. "
                "CDS will not write AccountShare rows until this flag is enabled."
            )
        if not RE_CDS_OPPORTUNITY_FLAG.search(content):
            issues.append(
                f"{path}: enableCompliantDataSharingForOpportunity is not set to true. "
                "CDS will not write OpportunityShare rows until this flag is enabled."
            )
    return issues


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def check_fsc_compliant_sharing_api(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    apex_files = collect_apex_files(manifest_dir)
    settings_files = collect_settings_files(manifest_dir)

    if not apex_files and not settings_files:
        # Nothing to check — not necessarily an error
        return issues

    issues.extend(check_direct_cds_row_cause(apex_files))
    issues.extend(check_share_delete_bypass(apex_files))
    issues.extend(check_participant_missing_role_id(apex_files))
    issues.extend(check_apex_row_cause_in_cds_file(apex_files))
    issues.extend(check_industries_settings(settings_files))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Salesforce metadata for CDS anti-patterns: direct share DML, "
            "revocation bypasses, missing ParticipantRoleId, and IndustriesSettings gaps."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_fsc_compliant_sharing_api(manifest_dir)

    if not issues:
        print("No CDS issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
