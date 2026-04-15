#!/usr/bin/env python3
"""Checker script for Nonprofit Data Quality skill.

Scans Salesforce metadata (retrieved via SFDX/sf cli or stored as XML files)
for patterns that indicate NPSP data quality anti-patterns:
  - Flows or triggers that write directly to Contact mailing address fields
  - Duplicate Rules referenced without NPSP Contact Matching Rule context
  - Apex code using Database.merge() on Contact objects (bypasses NPSP triggers)
  - Address verification batch size recommendations exceeding safe callout limits

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_nonprofit_data_quality.py [--manifest-dir path/to/metadata]
    python3 check_nonprofit_data_quality.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Patterns that indicate likely NPSP data quality anti-patterns
# ---------------------------------------------------------------------------

# Direct Contact mailing field assignments in Apex (bypasses npsp__Address__c)
DIRECT_CONTACT_ADDRESS_FIELD_PATTERN = re.compile(
    r"\b(Contact|c)\s*\.\s*(MailingStreet|MailingCity|MailingState|MailingPostalCode"
    r"|MailingCountry|MailingStateCode|MailingCountryCode)\s*=",
    re.IGNORECASE,
)

# Database.merge() on Contact — bypasses NPSP TDTM trigger chain
DATABASE_MERGE_CONTACT_PATTERN = re.compile(
    r"Database\s*\.\s*merge\s*\(",
    re.IGNORECASE,
)

# Batch sizes > 25 when ADDR_Addresses_TDTM is referenced nearby
# (catches executeBatch calls with large batch sizes in the same file)
ADDR_BATCH_LARGE_SIZE_PATTERN = re.compile(
    r"executeBatch\s*\(\s*new\s+ADDR_Addresses_TDTM\s*\(\s*\)\s*,\s*([0-9]+)\s*\)",
    re.IGNORECASE,
)

# Standard Salesforce Duplicate Rule XML — warn if present without NPSP context note
DUPLICATE_RULE_XML_MARKER = re.compile(
    r"<DuplicateRule\b|<fullName>.*DuplicateRule",
    re.IGNORECASE,
)

# Flow XML that sets Contact mailing address fields via assignment elements
FLOW_CONTACT_MAILING_ASSIGNMENT = re.compile(
    r"<field>Mailing(?:Street|City|State|PostalCode|Country)</field>",
    re.IGNORECASE,
)

# Hardcoded API keys for geocoding services (should be in Named Credentials)
HARDCODED_API_KEY_PATTERN = re.compile(
    r"(key=|apiKey\s*=\s*['\"]|auth-id\s*=\s*['\"]|api_key\s*=\s*['\"])"
    r"[A-Za-z0-9_\-]{16,}",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# File type routing
# ---------------------------------------------------------------------------

APEX_EXTENSIONS = {".cls", ".trigger"}
FLOW_EXTENSIONS = {".flow-meta.xml"}
XML_EXTENSIONS = {".xml"}


def check_apex_file(file_path: Path) -> list[str]:
    """Check an Apex class or trigger for NPSP data quality anti-patterns."""
    issues: list[str] = []
    try:
        source = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return issues

    lines = source.splitlines()

    for line_num, line in enumerate(lines, start=1):
        # Anti-pattern: direct Contact mailing address field assignment
        if DIRECT_CONTACT_ADDRESS_FIELD_PATTERN.search(line):
            issues.append(
                f"{file_path}:{line_num}: Direct Contact mailing address field assignment detected. "
                f"In NPSP orgs, address updates must target npsp__Address__c records — "
                f"direct Contact field updates are overwritten by NPSP address sync. "
                f"(NPSP Address Management: https://help.salesforce.com/s/articleView?id=sfdo.NPSP_Addresses_Overview.htm)"
            )

        # Anti-pattern: Database.merge() — bypasses NPSP TDTM
        if DATABASE_MERGE_CONTACT_PATTERN.search(line):
            issues.append(
                f"{file_path}:{line_num}: Database.merge() detected. "
                f"In NPSP orgs, Contact merge via Database.merge() bypasses NPSP TDTM triggers — "
                f"rollup fields (npo02__TotalOppAmount__c etc.) will not recalculate. "
                f"Use NPSP Contact Merge (/apex/NPSP__merge) instead. "
                f"(Configure Duplicate Detection and NPSP Contact Merge: "
                f"https://help.salesforce.com/s/articleView?id=sfdo.NPSP_Contact_Merge.htm)"
            )

        # Anti-pattern: hardcoded API keys
        if HARDCODED_API_KEY_PATTERN.search(line):
            issues.append(
                f"{file_path}:{line_num}: Possible hardcoded API key detected. "
                f"Geocoding service credentials (Google API key, SmartyStreets auth-id) "
                f"should be stored in Named Credentials, not inline in Apex."
            )

    # Check batch size for ADDR_Addresses_TDTM — callout limit is 100 per transaction
    for match in ADDR_BATCH_LARGE_SIZE_PATTERN.finditer(source):
        batch_size = int(match.group(1))
        if batch_size > 25:
            line_num = source[: match.start()].count("\n") + 1
            issues.append(
                f"{file_path}:{line_num}: ADDR_Addresses_TDTM batch size {batch_size} exceeds "
                f"recommended maximum of 25. Each address record may trigger an external HTTP callout. "
                f"Salesforce enforces a 100-callout-per-transaction limit. "
                f"Reduce batch size to 20–25 to avoid callout limit exceptions."
            )

    return issues


def check_flow_file(file_path: Path) -> list[str]:
    """Check a Flow metadata file for NPSP address field assignment anti-patterns."""
    issues: list[str] = []
    try:
        source = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return issues

    lines = source.splitlines()
    for line_num, line in enumerate(lines, start=1):
        if FLOW_CONTACT_MAILING_ASSIGNMENT.search(line):
            issues.append(
                f"{file_path}:{line_num}: Flow assigns Contact mailing address field directly. "
                f"In NPSP orgs, Contact mailing address fields are managed by NPSP and will be "
                f"overwritten by the NPSP address sync process. Target npsp__Address__c records instead. "
                f"(NPSP Address Management: https://help.salesforce.com/s/articleView?id=sfdo.NPSP_Addresses_Overview.htm)"
            )

    return issues


def check_xml_file(file_path: Path) -> list[str]:
    """Check XML metadata files (e.g., Duplicate Rules) for NPSP context issues."""
    issues: list[str] = []

    # Only check files that look like Duplicate Rule metadata
    if "duplicateRule" not in file_path.name.lower() and "DuplicateRule" not in file_path.name:
        return issues

    try:
        source = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return issues

    if DUPLICATE_RULE_XML_MARKER.search(source):
        issues.append(
            f"{file_path}: Standard Salesforce Duplicate Rule metadata found. "
            f"In NPSP orgs, standard Duplicate Rules do not integrate with the NPSP Data Importer's "
            f"batch processing model. Ensure NPSP Contact Matching Rules are also configured "
            f"(NPSP Settings > Contacts) for import-time duplicate prevention. "
            f"Standard Duplicate Rules may supplement but should not be the sole deduplication gate."
        )

    return issues


def check_nonprofit_data_quality(manifest_dir: Path) -> list[str]:
    """Walk the manifest directory and check all relevant files for NPSP data quality issues."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    if not manifest_dir.is_dir():
        issues.append(f"Path is not a directory: {manifest_dir}")
        return issues

    files_checked = 0

    for file_path in manifest_dir.rglob("*"):
        if not file_path.is_file():
            continue

        suffix = file_path.suffix.lower()
        name_lower = file_path.name.lower()

        if suffix in APEX_EXTENSIONS:
            files_checked += 1
            issues.extend(check_apex_file(file_path))

        elif name_lower.endswith(".flow-meta.xml"):
            files_checked += 1
            issues.extend(check_flow_file(file_path))

        elif suffix in XML_EXTENSIONS and "duplicaterule" in name_lower:
            files_checked += 1
            issues.extend(check_xml_file(file_path))

    if files_checked == 0:
        issues.append(
            f"No Apex (.cls/.trigger), Flow (.flow-meta.xml), or Duplicate Rule XML files "
            f"found under {manifest_dir}. Nothing to check."
        )

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for NPSP data quality anti-patterns: "
            "direct Contact address field writes, Database.merge() bypassing NPSP triggers, "
            "unsafe ADDR_Addresses_TDTM batch sizes, and standard Duplicate Rules without "
            "NPSP Contact Matching Rule context."
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
    issues = check_nonprofit_data_quality(manifest_dir)

    if not issues:
        print("No NPSP data quality anti-patterns detected.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    print(f"\n{len(issues)} issue(s) found.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
