#!/usr/bin/env python3
"""Checker for SOQL multi-select picklist query anti-patterns.

Scans Salesforce source (source-format metadata) for fragile or incorrect SOQL
against multi-select picklist fields:

  1. Discovers multi-select picklist fields from ``*.field-meta.xml`` files
     (``<type>MultiselectPicklist</type>``) and, for each, flags Apex/SOQL that:
       - filters the field with ``=`` / ``!=``      -> prefer INCLUDES / EXCLUDES
       - filters the field with ``LIKE``            -> not the containment operator
       - names the field in an ``ORDER BY`` clause  -> unsupported data type
  2. Metadata-free heuristics that always run:
       - equality against a semicolon-delimited literal (``= 'AAA;BBB'``)
       - ``INCLUDES(...)`` / ``EXCLUDES(...)`` operands that are not single-quoted
         string literals or bind variables (a missing-quotes grouping bug)

Uses the standard library only -- no pip dependencies.

Usage:
    python3 check_soql_multiselect_picklist_queries.py [--help]
    python3 check_soql_multiselect_picklist_queries.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# File types that can contain SOQL.
SOURCE_SUFFIXES = (".cls", ".trigger", ".apex", ".soql")

# INCLUDES/EXCLUDES call with a captured parenthesised operand list.
_MULTI_OP_CALL = re.compile(
    r"\b(INCLUDES|EXCLUDES)\s*\(([^)]*)\)", re.IGNORECASE
)

# Equality / inequality against a literal that contains a semicolon.
_SEMI_LITERAL_EQ = re.compile(r"(!=|=)\s*'[^']*;[^']*'")

# ORDER BY on a line (we scan line-by-line, so the field check stays local).
_ORDER_BY = re.compile(r"\bORDER\s+BY\b", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check SOQL against multi-select picklist fields for fragile "
            "operators and grammar bugs."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _local_tag(tag: str) -> str:
    """Strip an XML namespace, returning the bare local element name."""
    return tag.rsplit("}", 1)[-1]


def discover_multiselect_fields(manifest_dir: Path) -> set[str]:
    """Return the set of multi-select picklist field API names in the tree."""
    fields: set[str] = set()
    for meta in manifest_dir.rglob("*.field-meta.xml"):
        try:
            root = ET.parse(meta).getroot()
        except (ET.ParseError, OSError):
            continue
        field_type = None
        full_name = None
        for child in root.iter():
            tag = _local_tag(child.tag)
            if tag == "type" and (child.text or "").strip():
                field_type = child.text.strip()
            elif tag == "fullName" and (child.text or "").strip():
                full_name = child.text.strip()
        if field_type == "MultiselectPicklist":
            # Prefer <fullName>; fall back to the filename (Foo__c.field-meta.xml).
            name = full_name or meta.name[: -len(".field-meta.xml")]
            if name:
                fields.add(name)
    return fields


def _operand_is_safe(operand: str) -> bool:
    """True if an INCLUDES/EXCLUDES operand is a quoted literal or a bind."""
    token = operand.strip()
    if not token:
        return True
    if token.startswith("'") or token.startswith('"'):
        return True
    if token.startswith(":"):  # bind variable
        return True
    # A concatenation/dynamic expression (contains +, escaped quote, etc.) is
    # not a bare-word literal; leave it to the injection guidance rather than
    # mislabel it as a missing-quotes bug.
    if any(ch in token for ch in "+\\'\""):
        return True
    return False


def _scan_source_file(path: Path, msp_fields: set[str]) -> list[str]:
    issues: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [f"{path}: could not read file ({exc})"]

    field_patterns = {
        name: re.compile(r"\b" + re.escape(name) + r"\b") for name in msp_fields
    }

    for lineno, line in enumerate(text.splitlines(), start=1):
        # (1) INCLUDES/EXCLUDES operands must be quoted literals or binds.
        for match in _MULTI_OP_CALL.finditer(line):
            op, operands = match.group(1), match.group(2)
            for operand in operands.split(","):
                if not _operand_is_safe(operand):
                    issues.append(
                        f"{path}:{lineno}: {op.upper()} operand "
                        f"{operand.strip()!r} is not a single-quoted literal or "
                        f"bind -- quote each value, e.g. INCLUDES ('AAA;BBB')"
                    )

        # (2) Equality against a semicolon-delimited literal is fragile.
        if _SEMI_LITERAL_EQ.search(line):
            issues.append(
                f"{path}:{lineno}: equality against a semicolon-delimited "
                f"literal is a whole-string exact match -- use INCLUDES / "
                f"EXCLUDES for containment"
            )

        # (3) Field-type-aware checks (only when field metadata was found).
        has_order_by = bool(_ORDER_BY.search(line))
        for name, pat in field_patterns.items():
            if not pat.search(line):
                continue
            esc = re.escape(name)
            if re.search(r"\b" + esc + r"\s*(!=|=)(?!=)", line):
                issues.append(
                    f"{path}:{lineno}: multi-select field '{name}' filtered "
                    f"with '=' / '!=' -- prefer INCLUDES / EXCLUDES ('=' matches "
                    f"the entire stored selection only)"
                )
            if re.search(r"\b" + esc + r"\s+LIKE\b", line, re.IGNORECASE):
                issues.append(
                    f"{path}:{lineno}: multi-select field '{name}' filtered "
                    f"with LIKE -- use INCLUDES / EXCLUDES, not substring match"
                )
            if has_order_by and re.search(
                r"\bORDER\s+BY\b.*\b" + esc + r"\b", line, re.IGNORECASE
            ):
                issues.append(
                    f"{path}:{lineno}: multi-select field '{name}' in ORDER BY "
                    f"-- unsupported data type; sort on another field"
                )

    return issues


def check(manifest_dir: Path) -> tuple[list[str], int, int]:
    """Return (issues, source_files_scanned, msp_field_count)."""
    if not manifest_dir.exists():
        return ([f"Manifest directory not found: {manifest_dir}"], 0, 0)

    msp_fields = discover_multiselect_fields(manifest_dir)

    issues: list[str] = []
    scanned = 0
    for path in manifest_dir.rglob("*"):
        if path.is_file() and path.suffix in SOURCE_SUFFIXES:
            scanned += 1
            issues.extend(_scan_source_file(path, msp_fields))

    return (issues, scanned, len(msp_fields))


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues, scanned, field_count = check(manifest_dir)

    print(
        f"Scanned {scanned} source file(s); "
        f"discovered {field_count} multi-select picklist field(s).",
        file=sys.stderr,
    )

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
