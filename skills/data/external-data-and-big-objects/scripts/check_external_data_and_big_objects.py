#!/usr/bin/env python3
"""Checker script for External Data and Big Objects skill.

Scans a Salesforce metadata directory for common Big Object and External Object
configuration issues described in references/gotchas.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_external_data_and_big_objects.py [--help]
    python3 check_external_data_and_big_objects.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Big Object and External Object metadata for common issues:\n"
            "  - Big Objects missing a composite index definition\n"
            "  - External Objects with no external data source reference\n"
            "  - Apex files containing SOQL queries against __b objects (synchronous)\n"
            "  - Apex files querying __x objects inside a for-loop (callout limit risk)\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Metadata checks
# ---------------------------------------------------------------------------

def check_big_object_indexes(manifest_dir: Path) -> list[str]:
    """Warn if any __b object metadata file has no <indexes> element."""
    issues: list[str] = []
    objects_dir = manifest_dir / "objects"
    if not objects_dir.exists():
        return issues

    for obj_file in objects_dir.rglob("*.object-meta.xml"):
        if "__b" not in obj_file.stem:
            continue
        try:
            tree = ET.parse(obj_file)
            root = tree.getroot()
            # Strip namespace for simplicity
            ns_match = re.match(r"\{(.+?)\}", root.tag)
            ns = f"{{{ns_match.group(1)}}}" if ns_match else ""
            indexes = root.findall(f"{ns}indexes")
            if not indexes:
                issues.append(
                    f"Big Object '{obj_file.name}' has no <indexes> element. "
                    "Big Objects are unqueryable via Async SOQL without a composite index."
                )
            else:
                # Check that at least one index has at least one <fields> child
                for idx in indexes:
                    fields = idx.findall(f"{ns}fields")
                    if not fields:
                        issues.append(
                            f"Big Object '{obj_file.name}': index '{idx.findtext(f'{ns}fullName', 'unknown')}' "
                            "has no <fields> entries. Add at least one field to the composite index."
                        )
        except ET.ParseError as exc:
            issues.append(f"Could not parse '{obj_file}': {exc}")

    return issues


def check_external_object_datasource(manifest_dir: Path) -> list[str]:
    """Warn if any __x object metadata file lacks an <externalDataSource> element."""
    issues: list[str] = []
    objects_dir = manifest_dir / "objects"
    if not objects_dir.exists():
        return issues

    for obj_file in objects_dir.rglob("*.object-meta.xml"):
        if "__x" not in obj_file.stem:
            continue
        try:
            tree = ET.parse(obj_file)
            root = tree.getroot()
            ns_match = re.match(r"\{(.+?)\}", root.tag)
            ns = f"{{{ns_match.group(1)}}}" if ns_match else ""
            datasource = root.findtext(f"{ns}externalDataSource")
            if not datasource:
                issues.append(
                    f"External Object '{obj_file.name}' has no <externalDataSource> element. "
                    "External Objects require a Salesforce Connect data source reference."
                )
        except ET.ParseError as exc:
            issues.append(f"Could not parse '{obj_file}': {exc}")

    return issues


# ---------------------------------------------------------------------------
# Apex source checks
# ---------------------------------------------------------------------------

# Regex: finds SOQL inline queries against __b objects in Apex source
_BIG_OBJECT_SOQL_RE = re.compile(
    r"\[\s*SELECT\b[^\]]*\bFROM\s+\w+__b\b",
    re.IGNORECASE | re.DOTALL,
)

# Regex: finds for-loop patterns followed (within ~10 lines) by an __x SOQL query
# We use a simple heuristic: __x SOQL inside a for(...) block
_FOR_LOOP_RE = re.compile(r"\bfor\s*\(", re.IGNORECASE)
_EXT_OBJ_SOQL_RE = re.compile(
    r"\[\s*SELECT\b[^\]]*\bFROM\s+\w+__x\b",
    re.IGNORECASE | re.DOTALL,
)


def check_apex_big_object_sync_soql(manifest_dir: Path) -> list[str]:
    """Warn if Apex files contain synchronous SOQL queries against __b objects."""
    issues: list[str] = []
    classes_dir = manifest_dir / "classes"
    if not classes_dir.exists():
        return issues

    for apex_file in classes_dir.rglob("*.cls"):
        try:
            source = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if _BIG_OBJECT_SOQL_RE.search(source):
            issues.append(
                f"Apex class '{apex_file.name}' contains a synchronous SOQL query against a Big Object (__b). "
                "Synchronous SOQL on Big Objects returns zero results at production scale. "
                "Use the Async SOQL REST API (POST /async-queries/) instead."
            )

    return issues


def check_apex_external_object_in_loop(manifest_dir: Path) -> list[str]:
    """Warn if Apex files appear to query __x objects inside a for-loop (callout limit risk)."""
    issues: list[str] = []
    classes_dir = manifest_dir / "classes"
    if not classes_dir.exists():
        return issues

    for apex_file in classes_dir.rglob("*.cls"):
        try:
            source = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        # Simple heuristic: file contains both a for-loop and an __x SOQL query.
        # This will produce false positives for well-structured code, but it flags
        # files that warrant manual review.
        if _FOR_LOOP_RE.search(source) and _EXT_OBJ_SOQL_RE.search(source):
            issues.append(
                f"Apex class '{apex_file.name}' may query an External Object (__x) inside a for-loop. "
                "Each External Object SOQL query fires a live callout; querying inside a loop can "
                "exhaust the 100-callout-per-transaction limit. "
                "Collect IDs first, then issue a single IN-clause query outside the loop."
            )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_external_data_and_big_objects(manifest_dir: Path) -> list[str]:
    """Run all checks and return a combined list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_big_object_indexes(manifest_dir))
    issues.extend(check_external_object_datasource(manifest_dir))
    issues.extend(check_apex_big_object_sync_soql(manifest_dir))
    issues.extend(check_apex_external_object_in_loop(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_external_data_and_big_objects(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
