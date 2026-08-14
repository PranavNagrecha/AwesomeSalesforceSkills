#!/usr/bin/env python3
"""Checker script for Data Cloud Query Api skill.

Checks org metadata or configuration relevant to Data Cloud Query Api.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_data_cloud_query_api.py [--help]
    python3 check_data_cloud_query_api.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Data 360 SQL surfaces. Their pagination models are mutually incompatible:
#   V2            -> opaque nextBatchId cursor, 3-minute inter-batch expiry
#   V3 (current)  -> queryId + /chunks/{chunkId} or /rows; no synchronous mode
#   Query Connect -> stored queryId paged by rowLimit/offset
V2_QUERY = "api/v2/query"
V3_QUERY = "api/v3/query"

# sfsqlquery shipped in Summer '26 / API version 67.0. Availability follows the
# apiVersion in the class's .cls-meta.xml, NOT the org's release.
SFSQLQUERY_MIN_API_VERSION = 67.0
APEX_LEGACY_QUERY_METHODS = ("queryANSISql", "queryAnsiSqlV2", "nextBatchAnsiSqlV2")
API_VERSION_RE = re.compile(r"<apiVersion>\s*([\d.]+)\s*</apiVersion>")


def _cls_api_version(cls_file: Path) -> float | None:
    """Return the apiVersion from the sibling .cls-meta.xml, or None if unreadable."""
    meta = cls_file.parent / (cls_file.name + "-meta.xml")
    try:
        match = API_VERSION_RE.search(meta.read_text(encoding="utf-8", errors="ignore"))
    except OSError:
        return None
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Data Cloud Query Api configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_data_cloud_query_api(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory.

    TODO: Implement real checks relevant to this skill.
    Each returned string should describe a concrete, actionable issue.
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check client code that calls the Data 360 SQL query endpoints
    py_files = list(manifest_dir.rglob("*.py"))
    for py_file in py_files:
        try:
            text = py_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        uses_v2 = V2_QUERY in text
        uses_v3 = V3_QUERY in text
        if not (uses_v2 or uses_v3):
            continue

        # Detect use of instance_url for Data Cloud calls (should be dcInstanceUrl)
        if "instance_url" in text and "dcInstanceUrl" not in text:
            issues.append(
                f"{py_file}: Uses instance_url for Data Cloud Query API — "
                "should use dcInstanceUrl from /services/a360/token response."
            )

        # Detect SOQL patterns in Data Cloud query strings
        soql_patterns = ["FROM Contact", "FROM Account", "FROM Lead", "FROM Opportunity"]
        for pattern in soql_patterns:
            if pattern in text:
                issues.append(
                    f"{py_file}: Possible SOQL object name '{pattern}' in Data Cloud query — "
                    "use Data Cloud DMO API names (e.g., ssot__Individual__dlm)."
                )

        # V2: missing nextBatchId pagination silently truncates the result set
        if uses_v2 and not uses_v3 and "nextBatchId" not in text:
            issues.append(
                f"{py_file}: Query API V2 call found but no 'nextBatchId' pagination — "
                "result set may be silently truncated."
            )

        if uses_v3:
            # V3 has no batch cursor; a nextBatchId loop against it cannot paginate
            if "nextBatchId" in text:
                issues.append(
                    f"{py_file}: 'nextBatchId' used alongside {V3_QUERY} — Query API V3 has no "
                    "batch cursor. Retrieve by queryId via /chunks/{chunkId} (preferred) or /rows."
                )
            # V3 doesn't support synchronous execution: submit returns a queryId, not rows
            if "queryId" not in text:
                issues.append(
                    f"{py_file}: {V3_QUERY} call found with no 'queryId' handling — Query API V3 "
                    "doesn't support synchronous execution; poll GET /api/v3/query/{queryId} "
                    "for status, then read /chunks/{chunkId} or /rows."
                )
            # Unaliased expressions are named 1, 2 in V3 — not _col0, _col1 as in V1/V2
            if "_col0" in text or "_col1" in text:
                issues.append(
                    f"{py_file}: Reads '_col0'/'_col1' from a Query API V3 response — V3 names "
                    "unaliased expression columns '1', '2'. Alias every expression explicitly."
                )

    # Apex: sfsqlquery supersedes ConnectApi.CdpQuery for classes at API 67.0+
    for cls_file in manifest_dir.rglob("*.cls"):
        try:
            text = cls_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "ConnectApi.CdpQuery" not in text and not any(
            m in text for m in APEX_LEGACY_QUERY_METHODS
        ):
            continue
        api_version = _cls_api_version(cls_file)
        if api_version is None:
            issues.append(
                f"{cls_file}: Uses ConnectApi.CdpQuery but the .cls-meta.xml apiVersion could not "
                f"be read — confirm it. At {SFSQLQUERY_MIN_API_VERSION}+ Salesforce recommends the "
                "sfsqlquery namespace for all new development; below it, CdpQuery is the only option."
            )
        elif api_version >= SFSQLQUERY_MIN_API_VERSION:
            issues.append(
                f"{cls_file}: Class apiVersion {api_version} supports the sfsqlquery namespace, but "
                "the code uses ConnectApi.CdpQuery. Prefer sfsqlquery.SqlStatement / SqlRowIterator, "
                "or extend sfsqlquery.SqlQueueable for chained async pagination."
            )

    # Check for connected app XML missing cdp_api scope
    xml_files = list(manifest_dir.rglob("*.connectedApp-meta.xml"))
    for xml_file in xml_files:
        try:
            text = xml_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "cdp_api" not in text and "DataCloud" in text:
            issues.append(
                f"{xml_file}: Connected app may be missing 'cdp_api' OAuth scope — "
                "required for Data Cloud Query API access."
            )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_data_cloud_query_api(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
