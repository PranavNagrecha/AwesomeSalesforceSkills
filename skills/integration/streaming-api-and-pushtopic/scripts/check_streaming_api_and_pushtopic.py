#!/usr/bin/env python3
"""Checker script for Streaming API and PushTopic skill.

Scans Salesforce metadata (PushTopic XML files or plain-text SOQL queries)
for violations of the Streaming API PushTopic SOQL restrictions documented at:
  https://developer.salesforce.com/docs/atlas.en-us.api_streaming.meta/api_streaming/pushtopic_soql.htm

Uses stdlib only — no pip dependencies.

Exit codes:
  0 — No issues found.
  1 — One or more issues found.

Usage:
    python3 check_streaming_api_and_pushtopic.py [--help]
    python3 check_streaming_api_and_pushtopic.py --manifest-dir path/to/metadata
    python3 check_streaming_api_and_pushtopic.py --soql "SELECT Id FROM Account"
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# SOQL restriction patterns for PushTopic queries
# ---------------------------------------------------------------------------

# Aggregate function names prohibited in PushTopic SOQL (SELECT clause)
_AGGREGATE_FUNCS = re.compile(
    r'\b(COUNT|SUM|AVG|MIN|MAX|COUNT_DISTINCT)\s*\(',
    re.IGNORECASE,
)

# GROUP BY clause is not allowed
_GROUP_BY = re.compile(r'\bGROUP\s+BY\b', re.IGNORECASE)

# LIMIT clause is not allowed
_LIMIT = re.compile(r'\bLIMIT\s+\d+', re.IGNORECASE)

# OFFSET clause is not allowed
_OFFSET = re.compile(r'\bOFFSET\s+\d+', re.IGNORECASE)

# Relationship traversal in SELECT: pattern like "Parent.Field" in the SELECT list
# Heuristic: dot-notation before a comma, FROM keyword, or end of SELECT clause
_RELATIONSHIP_IN_SELECT = re.compile(
    # Match SELECT ... <Alias>.<Field> ... FROM
    r'\bSELECT\b[^)]*\b\w+\.\w+\b[^)]*\bFROM\b',
    re.IGNORECASE | re.DOTALL,
)

# Semi-join: IN ( SELECT ... ) pattern
_SEMI_JOIN = re.compile(r'\bIN\s*\(\s*SELECT\b', re.IGNORECASE)

# Minimum API version for Streaming API
_MIN_API_VERSION = 24.0

# Namespace used in PushTopic XML (Metadata API)
_SF_NAMESPACE = 'http://soap.sforce.com/2006/04/metadata'


def check_soql(soql: str, source: str = "<inline>") -> list[str]:
    """Return a list of issue strings for a single SOQL query string."""
    issues: list[str] = []

    if _AGGREGATE_FUNCS.search(soql):
        issues.append(
            f"{source}: PushTopic SOQL uses an aggregate function "
            f"(COUNT/SUM/AVG/MIN/MAX/COUNT_DISTINCT) — not allowed in Streaming API queries."
        )

    if _GROUP_BY.search(soql):
        issues.append(
            f"{source}: PushTopic SOQL contains GROUP BY — not allowed in Streaming API queries."
        )

    if _LIMIT.search(soql):
        issues.append(
            f"{source}: PushTopic SOQL contains LIMIT — not allowed in Streaming API queries."
        )

    if _OFFSET.search(soql):
        issues.append(
            f"{source}: PushTopic SOQL contains OFFSET — not allowed in Streaming API queries."
        )

    if _SEMI_JOIN.search(soql):
        issues.append(
            f"{source}: PushTopic SOQL contains a semi-join (IN with subquery) — "
            f"not allowed in Streaming API queries."
        )

    if _RELATIONSHIP_IN_SELECT.search(soql):
        issues.append(
            f"{source}: PushTopic SOQL appears to reference a relationship field "
            f"(e.g., Parent.Field__c) in the SELECT clause — "
            f"only root-object fields are allowed in Streaming API PushTopic queries."
        )

    return issues


def check_api_version(version_str: str, source: str = "<inline>") -> list[str]:
    """Return issues if the API version is below the Streaming API minimum."""
    issues: list[str] = []
    try:
        version = float(version_str.strip())
        if version < _MIN_API_VERSION:
            issues.append(
                f"{source}: ApiVersion {version} is below the Streaming API minimum "
                f"of {_MIN_API_VERSION}."
            )
    except (ValueError, AttributeError):
        issues.append(
            f"{source}: Unable to parse ApiVersion value '{version_str}' as a number."
        )
    return issues


def _ns(tag: str) -> str:
    """Wrap a tag name in the Salesforce Metadata namespace."""
    return f"{{{_SF_NAMESPACE}}}{tag}"


def check_pushtopic_xml(xml_path: Path) -> list[str]:
    """Parse a PushTopic Metadata XML file and check for SOQL violations."""
    issues: list[str] = []
    source = str(xml_path)

    try:
        tree = ET.parse(xml_path)
    except ET.ParseError as exc:
        issues.append(f"{source}: XML parse error — {exc}")
        return issues

    root = tree.getroot()

    # Support both namespaced and non-namespaced XML
    def find_text(tag: str) -> str | None:
        node = root.find(_ns(tag))
        if node is None:
            node = root.find(tag)
        return node.text.strip() if node is not None and node.text else None

    query = find_text('query')
    if query:
        issues.extend(check_soql(query, source=f"{source}[query]"))
    else:
        issues.append(f"{source}: No <query> element found in PushTopic metadata.")

    api_version = find_text('apiVersion')
    if api_version:
        issues.extend(check_api_version(api_version, source=f"{source}[apiVersion]"))

    return issues


def check_manifest_dir(manifest_dir: Path) -> list[str]:
    """Walk the manifest directory and check all PushTopic XML metadata files."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Salesforce Metadata API places PushTopics under pushTopics/ directory
    # but also accept any *.pushTopic-meta.xml or *PushTopic.xml patterns
    pushtopic_files: list[Path] = []
    pushtopic_files.extend(manifest_dir.rglob('*.pushTopic-meta.xml'))
    pushtopic_files.extend(manifest_dir.rglob('pushTopics/*.xml'))

    # Deduplicate
    seen: set[Path] = set()
    unique_files: list[Path] = []
    for p in pushtopic_files:
        resolved = p.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique_files.append(p)

    if not unique_files:
        # No PushTopic files found — not necessarily an error, just report it
        print(
            f"INFO: No PushTopic metadata files found under {manifest_dir}. "
            f"Pass --soql to check a query directly."
        )
        return issues

    for xml_path in sorted(unique_files):
        issues.extend(check_pushtopic_xml(xml_path))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce Streaming API PushTopic SOQL for restriction violations. "
            "Validates against the restrictions documented at "
            "https://developer.salesforce.com/docs/atlas.en-us.api_streaming.meta/"
            "api_streaming/pushtopic_soql.htm"
        ),
    )
    parser.add_argument(
        '--manifest-dir',
        default=None,
        help=(
            'Root directory of the Salesforce metadata to scan for PushTopic XML files. '
            'Scans recursively for *.pushTopic-meta.xml and pushTopics/*.xml.'
        ),
    )
    parser.add_argument(
        '--soql',
        default=None,
        help='A raw SOQL query string to validate directly (without reading from a file).',
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    issues: list[str] = []

    if args.soql:
        issues.extend(check_soql(args.soql, source='--soql argument'))

    if args.manifest_dir:
        issues.extend(check_manifest_dir(Path(args.manifest_dir)))

    if args.soql is None and args.manifest_dir is None:
        # Default: scan current directory
        issues.extend(check_manifest_dir(Path('.')))

    if not issues:
        print('No issues found.')
        return 0

    for issue in issues:
        print(f'ISSUE: {issue}')

    return 1


if __name__ == '__main__':
    sys.exit(main())
