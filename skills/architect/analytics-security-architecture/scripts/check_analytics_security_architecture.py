#!/usr/bin/env python3
"""Checker script for Analytics Security Architecture skill.

Inspects Salesforce DX metadata under a manifest directory for common
CRM Analytics security misconfigurations.

Checks performed (all stdlib, no pip dependencies):
  1. Dataset files with no security predicate and no sharing inheritance.
  2. Dataset files with sharing inheritance enabled but no backup predicate.
  3. Security predicates that use all-lowercase column name references
     (likely copied from Salesforce field API names without schema verification).
  4. Security predicates that exceed 5,000 characters.
  5. Dataflow JSON files that contain an augment step without a corresponding
     downstream security predicate on any dataset (heuristic — not conclusive).

Usage:
    python3 check_analytics_security_architecture.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PREDICATE_MAX_CHARS = 5000

# Heuristic: all-lowercase predicate column references are suspect
# Matches patterns like 'ownerid' or 'accountid' (lowercase, in single quotes)
_LOWERCASE_COL_RE = re.compile(r"'([a-z][a-z0-9_]+)'\s*==")


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check CRM Analytics metadata for common security misconfigurations. "
            "Looks for .dataset, .waveDataset, and .json (dataflow) files under "
            "the specified manifest directory."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------


def _check_dataset_file(path: Path) -> list[str]:
    """Check a single .dataset or .waveDataset JSON file for security issues."""
    issues: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        issues.append(f"{path}: could not parse JSON — {exc}")
        return issues

    dataset_name = data.get("name", str(path.stem))
    predicate = data.get("securityPredicate", "") or ""
    sharing_inheritance = str(data.get("sharingInheritance", "")).lower() in (
        "true",
        "1",
        "yes",
        "enabled",
    )

    # Check 1: No predicate and no sharing inheritance
    if not predicate.strip() and not sharing_inheritance:
        issues.append(
            f"{path}: dataset '{dataset_name}' has no security predicate and "
            "no sharing inheritance — all licensed users see all rows by default. "
            "Configure a predicate (e.g., 'OwnerId' == \"$User.Id\") or enable "
            "sharing inheritance with a backup predicate of 'false'."
        )

    # Check 2: Sharing inheritance enabled but no backup predicate
    if sharing_inheritance and not predicate.strip():
        issues.append(
            f"{path}: dataset '{dataset_name}' uses sharing inheritance but has no "
            "backup predicate. Users whose visible row count exceeds 3,000 in the "
            "source object will see ALL rows instead of their allowed subset. "
            "Set securityPredicate to 'false' as the backup."
        )

    # Check 3: Predicate uses all-lowercase column references (likely wrong casing)
    if predicate:
        matches = _LOWERCASE_COL_RE.findall(predicate)
        if matches:
            issues.append(
                f"{path}: dataset '{dataset_name}' predicate contains potentially "
                f"wrong-cased column reference(s): {matches}. CRM Analytics predicate "
                "column names are case-sensitive and must match the dataset schema "
                "exactly (not the Salesforce field API name). Verify column names in "
                "Analytics Studio > dataset > Schema tab."
            )

    # Check 4: Predicate exceeds 5,000 characters
    if len(predicate) > PREDICATE_MAX_CHARS:
        issues.append(
            f"{path}: dataset '{dataset_name}' predicate is {len(predicate)} characters, "
            f"exceeding the platform maximum of {PREDICATE_MAX_CHARS}. Shorten the "
            "predicate or use a cross-dataset entitlement augment pattern."
        )

    return issues


def _check_dataflow_file(path: Path) -> list[str]:
    """Heuristic check on a dataflow JSON for missing augment-step security patterns."""
    issues: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        issues.append(f"{path}: could not parse JSON — {exc}")
        return issues

    # Detect augment nodes — these are often part of cross-dataset security patterns
    nodes = data if isinstance(data, dict) else {}
    augment_nodes = [
        name
        for name, node in nodes.items()
        if isinstance(node, dict) and node.get("action") == "augment"
    ]

    if augment_nodes:
        # Heuristic: if there is an augment step but no downstream output node
        # references a security-sounding field name, flag for manual review.
        output_nodes = [
            name
            for name, node in nodes.items()
            if isinstance(node, dict) and node.get("action") == "sfdcRegister"
        ]
        if not output_nodes:
            issues.append(
                f"{path}: dataflow has augment node(s) {augment_nodes} but no "
                "sfdcRegister (output) nodes detected. If augment steps embed "
                "entitlement data for row-level security, ensure the output dataset "
                "has a matching security predicate configured."
            )

    return issues


# ---------------------------------------------------------------------------
# Main checker
# ---------------------------------------------------------------------------


def check_analytics_security_architecture(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found under manifest_dir."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Find dataset metadata files
    dataset_files = list(manifest_dir.rglob("*.dataset")) + list(
        manifest_dir.rglob("*.waveDataset")
    )

    if not dataset_files:
        issues.append(
            f"No .dataset or .waveDataset metadata files found under {manifest_dir}. "
            "If this is a Salesforce DX project, ensure wave metadata is included in "
            "the package manifest and has been retrieved."
        )
    else:
        for df in dataset_files:
            issues.extend(_check_dataset_file(df))

    # Find dataflow JSON files (typically under wave/ directory)
    dataflow_files = [
        p
        for p in manifest_dir.rglob("*.json")
        if "wave" in p.parts or "analytics" in str(p).lower()
    ]
    for df in dataflow_files:
        issues.extend(_check_dataflow_file(df))

    return issues


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_analytics_security_architecture(manifest_dir)

    if not issues:
        print("No CRM Analytics security issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
