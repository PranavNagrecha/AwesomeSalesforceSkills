#!/usr/bin/env python3
"""Checker script for Multi-Org Strategy skill.

Scans a Salesforce project directory or a description file for multi-org
architecture anti-patterns:

1. Salesforce-to-Salesforce (S2S) usage — flagged as legacy; should be migrated
   to REST API + Named Credentials.
2. Hard-coded Salesforce org IDs — 15- or 18-character IDs embedded in Apex
   source, Custom Metadata XML, or Custom Settings XML; these should be
   stored in Named Credentials or Custom Metadata Types.
3. Cross-org callouts without Named Credential usage — Apex callout endpoints
   that use a literal URL (http:// or https://) instead of a Named Credential
   reference (callout:NamedCredentialName) for cross-org communication.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_multi_org.py --help
    python3 check_multi_org.py --project-dir path/to/force-app
    python3 check_multi_org.py --description-file path/to/architecture-notes.txt
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Detection patterns
# ---------------------------------------------------------------------------

# Salesforce-to-Salesforce: connection XML uses PartnerNetworkConnection type
# and PartnerNetworkRecordConnection objects. Detect common S2S patterns in
# metadata XML and description text.
S2S_XML_PATTERN = re.compile(
    r'PartnerNetworkConnection|PartnerNetworkRecordConnection|salesforce_to_salesforce',
    re.IGNORECASE,
)

S2S_TEXT_PATTERN = re.compile(
    r'\bsalesforce[\s_-]to[\s_-]salesforce\b|\bS2S\b|\bpartner\s+network\s+connection\b',
    re.IGNORECASE,
)

# Hard-coded Salesforce org ID: 15- or 18-char alphanumeric starting with '00D'
# (the standard org ID key prefix). Wrapped in single or double quotes.
# This is stricter than a generic ID check — org IDs always start with 00D.
ORG_ID_PATTERN = re.compile(
    r"""(?<![A-Za-z0-9_])['"]00D[A-Za-z0-9]{12}(?:[A-Za-z0-9]{3})?['"](?![A-Za-z0-9_])"""
)

# More general hard-coded Salesforce record ID (any key prefix starting with 0)
# Used as a supplementary check.
GENERIC_SF_ID_PATTERN = re.compile(
    r"""(?<![A-Za-z0-9_])['"]0[A-Za-z0-9]{14}(?:[A-Za-z0-9]{3})?['"](?![A-Za-z0-9_])"""
)

# Apex HttpRequest.setEndpoint with a literal URL (not a Named Credential)
# Named Credentials use the callout: scheme, e.g. callout:MyNC/path
LITERAL_ENDPOINT_PATTERN = re.compile(
    r'setEndpoint\s*\(\s*[\'"]https?://',
    re.IGNORECASE,
)

# Named Credential usage in Apex — correct pattern
NAMED_CRED_ENDPOINT_PATTERN = re.compile(
    r'setEndpoint\s*\(\s*[\'"]callout:',
    re.IGNORECASE,
)

# Cross-org indicators in a literal endpoint (salesforce.com domains)
SALESFORCE_DOMAIN_PATTERN = re.compile(
    r'https?://[^\'"]*\.salesforce\.com',
    re.IGNORECASE,
)

APEX_EXTENSIONS = {'.cls', '.trigger'}
METADATA_XML_EXTENSIONS = {'.xml'}


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _strip_apex_comments(source: str) -> str:
    """Remove single-line and block comments from Apex source (best-effort)."""
    source = re.sub(r'/\*.*?\*/', '', source, flags=re.DOTALL)
    source = re.sub(r'//[^\n]*', '', source)
    return source


def _line_number(content: str, match_start: int) -> int:
    """Return the 1-based line number for a character offset in content."""
    return content.count('\n', 0, match_start) + 1


# ---------------------------------------------------------------------------
# Per-file checkers
# ---------------------------------------------------------------------------

def check_apex_file(path: Path) -> list[str]:
    """Return issues found in a single Apex source file."""
    issues: list[str] = []
    try:
        raw = path.read_text(encoding='utf-8', errors='replace')
    except OSError as exc:
        return [f"{path}: cannot read — {exc}"]

    source = _strip_apex_comments(raw)
    raw_lines = raw.splitlines()

    # Check for hard-coded org IDs (00D prefix)
    for i, line in enumerate(raw_lines, start=1):
        stripped = line.strip()
        if stripped.startswith('//') or stripped.startswith('*'):
            continue
        for match in ORG_ID_PATTERN.finditer(line):
            candidate = match.group(0).strip("'\"")
            issues.append(
                f"{path}:{i}: Hard-coded Salesforce org ID '{candidate}' — "
                "org IDs are environment-specific; store in Named Credential "
                "endpoint URL or Custom Metadata Type instead"
            )

    # Check for literal callout endpoints (not using Named Credentials)
    for match in LITERAL_ENDPOINT_PATTERN.finditer(source):
        lineno = _line_number(source, match.start())
        # Determine if the endpoint targets a Salesforce org
        # Get surrounding context (up to 200 chars after match start)
        context = source[match.start():match.start() + 200]
        if SALESFORCE_DOMAIN_PATTERN.search(context):
            issues.append(
                f"{path}:{lineno}: Cross-org callout uses a literal "
                "salesforce.com URL in setEndpoint() — use a Named Credential "
                "(callout:NamedCredentialName) instead; literal endpoints "
                "expose URLs in source code and break across environments"
            )
        else:
            issues.append(
                f"{path}:{lineno}: Callout uses a literal URL in setEndpoint() "
                "instead of a Named Credential (callout:NamedCredentialName) — "
                "if this is a cross-org callout, move the endpoint to a Named "
                "Credential to keep credentials out of source code"
            )

    # Check for S2S patterns in Apex (unusual but possible via API calls)
    if S2S_TEXT_PATTERN.search(source):
        issues.append(
            f"{path}: Reference to Salesforce-to-Salesforce (S2S) pattern "
            "detected in Apex source — S2S is a legacy integration approach "
            "that uses SOAP API and does not scale; replace with REST API + "
            "Named Credentials or Bulk API 2.0"
        )

    return issues


def check_xml_file(path: Path) -> list[str]:
    """Return issues found in a Salesforce metadata XML file."""
    issues: list[str] = []
    try:
        raw = path.read_text(encoding='utf-8', errors='replace')
    except OSError as exc:
        return [f"{path}: cannot read — {exc}"]

    # Check for S2S metadata references
    if S2S_XML_PATTERN.search(raw):
        issues.append(
            f"{path}: Salesforce-to-Salesforce (S2S) metadata detected "
            "(PartnerNetworkConnection or PartnerNetworkRecordConnection) — "
            "S2S is a legacy feature that consumes SOAP API limits on both orgs; "
            "migrate to REST API + Named Credentials or Bulk API 2.0"
        )

    # Check for hard-coded org IDs in XML attribute values and element text
    raw_lines = raw.splitlines()
    for i, line in enumerate(raw_lines, start=1):
        for match in ORG_ID_PATTERN.finditer(line):
            candidate = match.group(0).strip("'\"")
            issues.append(
                f"{path}:{i}: Hard-coded Salesforce org ID '{candidate}' in "
                "metadata XML — store environment-specific org IDs in Custom "
                "Metadata Types or Named Credential endpoint configuration, "
                "not in metadata XML files"
            )

    return issues


def check_description_file(path: Path) -> list[str]:
    """Return issues found in a plain-text architecture description file."""
    issues: list[str] = []
    try:
        raw = path.read_text(encoding='utf-8', errors='replace')
    except OSError as exc:
        return [f"{path}: cannot read — {exc}"]

    raw_lines = raw.splitlines()

    # Check for S2S references in description text
    for i, line in enumerate(raw_lines, start=1):
        if S2S_TEXT_PATTERN.search(line):
            issues.append(
                f"{path}:{i}: Salesforce-to-Salesforce (S2S) referenced in "
                "architecture description — S2S is a legacy feature; confirm "
                "whether this is a new design or existing legacy usage; if new, "
                "replace with REST API + Named Credentials; if legacy, add a "
                "migration plan to the architecture decision record"
            )

    # Check for hard-coded org IDs in description text
    for i, line in enumerate(raw_lines, start=1):
        for match in ORG_ID_PATTERN.finditer(line):
            candidate = match.group(0).strip("'\"")
            issues.append(
                f"{path}:{i}: Hard-coded Salesforce org ID '{candidate}' in "
                "architecture description — document the Named Credential or "
                "Custom Metadata Type where this value will be stored at runtime"
            )

    # Check for literal Salesforce endpoints mentioned without Named Credential context
    for i, line in enumerate(raw_lines, start=1):
        if SALESFORCE_DOMAIN_PATTERN.search(line):
            if 'named credential' not in line.lower() and 'callout:' not in line.lower():
                issues.append(
                    f"{path}:{i}: Literal salesforce.com URL mentioned without "
                    "reference to a Named Credential — cross-org callout endpoints "
                    "must be stored in Named Credentials, not hard-coded in "
                    "configuration or architecture notes"
                )

    return issues


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------

def find_apex_files(project_dir: Path) -> list[Path]:
    return [
        p for p in project_dir.rglob('*')
        if p.suffix in APEX_EXTENSIONS and p.is_file()
    ]


def find_xml_files(project_dir: Path) -> list[Path]:
    """Find Salesforce metadata XML files (custom metadata, custom settings, etc.)."""
    return [
        p for p in project_dir.rglob('*.xml')
        if p.is_file()
        # Exclude files that are clearly not Salesforce metadata (e.g., pom.xml)
        and not p.name.startswith('pom')
        and not p.name.startswith('build')
    ]


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a Salesforce project or architecture description for "
            "multi-org anti-patterns: Salesforce-to-Salesforce (legacy) usage, "
            "hard-coded org IDs, and cross-org callouts without Named Credentials."
        ),
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--project-dir',
        help='Root directory of the Salesforce project (scans Apex and XML files).',
    )
    group.add_argument(
        '--description-file',
        help='Path to a plain-text architecture description or notes file.',
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    all_issues: list[str] = []
    total_files = 0

    if args.project_dir:
        project_dir = Path(args.project_dir)
        if not project_dir.exists():
            print(f"ISSUE: Project directory not found: {project_dir}")
            return 1

        apex_files = find_apex_files(project_dir)
        xml_files = find_xml_files(project_dir)
        total_files = len(apex_files) + len(xml_files)

        if total_files == 0:
            print(f"No Apex or metadata XML files found under {project_dir}.")
            return 0

        for apex_file in sorted(apex_files):
            all_issues.extend(check_apex_file(apex_file))

        for xml_file in sorted(xml_files):
            all_issues.extend(check_xml_file(xml_file))

        file_summary = (
            f"{len(apex_files)} Apex file(s) and {len(xml_files)} metadata XML file(s)"
        )

    else:
        desc_path = Path(args.description_file)
        if not desc_path.exists():
            print(f"ISSUE: Description file not found: {desc_path}")
            return 1

        total_files = 1
        all_issues.extend(check_description_file(desc_path))
        file_summary = "1 description file"

    if not all_issues:
        print(
            f"No multi-org anti-patterns found across {file_summary}."
        )
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")

    print(
        f"\n{len(all_issues)} issue(s) found across {total_files} file(s) "
        f"({file_summary})."
    )
    return 1


if __name__ == '__main__':
    sys.exit(main())
