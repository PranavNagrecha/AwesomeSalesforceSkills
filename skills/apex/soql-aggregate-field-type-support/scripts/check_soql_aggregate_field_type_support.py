#!/usr/bin/env python3
"""Checker for SOQL aggregate function / field-type compatibility.

Scans one or more SOQL queries for aggregate functions applied to field types
that don't support them, plus the LIMIT-without-GROUP-BY error. Grounded in the
official SOQL & SOSL Reference:
  - "Support for Field Types in Aggregate Functions"
  - "Aggregate Functions"

Stdlib only — no pip dependencies.

Usage:
    python3 check_soql_aggregate_field_type_support.py --soql "SELECT SUM(CloseDate) FROM Opportunity"
    python3 check_soql_aggregate_field_type_support.py --file queries.soql
    python3 check_soql_aggregate_field_type_support.py --file queries.soql --field-types types.json
    python3 check_soql_aggregate_field_type_support.py --matrix   # print the compatibility matrix

--field-types is an optional JSON object mapping a field API name (case-insensitive)
to its Salesforce data type, e.g. {"CloseDate": "date", "Amount": "currency"}.
Without it, the checker still flags AVG()/SUM() as numeric-only (advisory) and the
LIMIT-without-GROUP-BY error (error).

Exit codes: 1 if any ERROR-level finding, 2 for bad usage/input, else 0.
Advisories never fail the run.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ALL_SIX = {"AVG", "SUM", "COUNT", "COUNT_DISTINCT", "MIN", "MAX"}
COUNTS_MINMAX = {"COUNT", "COUNT_DISTINCT", "MIN", "MAX"}  # no AVG/SUM
NO_SUPPORT: set[str] = set()  # not even COUNT

# Normalized data type -> set of aggregate functions that type supports.
# Source: "Support for Field Types in Aggregate Functions" (SOQL & SOSL Reference).
SUPPORT_BY_TYPE: dict[str, set[str]] = {
    # Fully numeric types support all six, including AVG() and SUM().
    "int": ALL_SIX,
    "integer": ALL_SIX,
    "double": ALL_SIX,
    "currency": ALL_SIX,
    "percent": ALL_SIX,
    # date and dateTime support the counts, MIN, and MAX — but not AVG/SUM.
    "date": COUNTS_MINMAX,
    "datetime": COUNTS_MINMAX,
    # Text-like types mirror text behavior: counts, MIN, MAX — no AVG/SUM.
    "string": COUNTS_MINMAX,
    "reference": COUNTS_MINMAX,
    "lookup": COUNTS_MINMAX,
    "id": COUNTS_MINMAX,
    "email": COUNTS_MINMAX,
    "phone": COUNTS_MINMAX,
    "url": COUNTS_MINMAX,
    "textarea": COUNTS_MINMAX,
    "picklist": COUNTS_MINMAX,
    "combobox": COUNTS_MINMAX,
    "datacategorygroupreference": COUNTS_MINMAX,
    # These types support NO aggregate function at all (not even COUNT).
    "base64": NO_SUPPORT,
    "boolean": NO_SUPPORT,
    "time": NO_SUPPORT,
    "multipicklist": NO_SUPPORT,
    "address": NO_SUPPORT,
    "location": NO_SUPPORT,
    "encryptedstring": NO_SUPPORT,
}

# The functions that require a fully numeric field.
NUMERIC_ONLY_FUNCS = {"AVG", "SUM"}

AGG_CALL_RE = re.compile(
    r"\b(AVG|SUM|COUNT_DISTINCT|COUNT|MIN|MAX)\s*\(\s*([^)]*?)\s*\)",
    re.IGNORECASE,
)

ERROR = "ERROR"
ADVISORY = "ADVISORY"


class Finding:
    def __init__(self, level: str, message: str) -> None:
        self.level = level
        self.message = message


def normalize_type(raw: str) -> str:
    return re.sub(r"[^a-z0-9]", "", raw.strip().lower())


def split_queries(text: str) -> list[str]:
    """Split a blob into individual SOQL statements (by ';' or blank lines)."""
    chunks: list[str] = []
    for block in re.split(r";", text):
        for piece in re.split(r"\n\s*\n", block):
            stripped = piece.strip()
            if stripped and re.search(r"\bSELECT\b", stripped, re.IGNORECASE):
                chunks.append(stripped)
    return chunks


def check_query(query: str, field_types: dict[str, str] | None) -> list[Finding]:
    """field_types maps lower-cased field API name -> normalized data type string."""
    findings: list[Finding] = []
    has_group_by = re.search(r"\bGROUP\s+BY\b", query, re.IGNORECASE) is not None
    has_limit = re.search(r"\bLIMIT\b", query, re.IGNORECASE) is not None

    calls = AGG_CALL_RE.findall(query)
    if not calls:
        return findings  # no aggregate function — nothing for this skill to check

    # LIMIT is disallowed on an aggregate query that has no GROUP BY.
    if has_limit and not has_group_by:
        findings.append(
            Finding(
                ERROR,
                "LIMIT is not allowed on an aggregate query without GROUP BY "
                "(constrain rows with WHERE instead).",
            )
        )

    for raw_func, raw_arg in calls:
        func = raw_func.upper()
        field = raw_arg.strip()

        # COUNT() with no argument, or COUNT(Id): counts all rows, always valid.
        if func == "COUNT" and field.lower() in {"", "id"}:
            continue

        ftype = field_types.get(field.lower()) if (field and field_types) else None
        supported = SUPPORT_BY_TYPE.get(ftype) if ftype else None

        if ftype and supported is not None:
            # Known, listed type: check the exact (type x function) cell.
            if supported is NO_SUPPORT:
                findings.append(
                    Finding(
                        ERROR,
                        f"{func}({field}): field type '{ftype}' supports no aggregate "
                        f"functions at all — derive a supported field first.",
                    )
                )
                # The type can't be aggregated at all; downstream advisories are moot.
                continue
            elif func not in supported:
                findings.append(
                    Finding(
                        ERROR,
                        f"{func}({field}): not supported for field type '{ftype}'. "
                        f"Supported here: {', '.join(sorted(supported))}.",
                    )
                )
        elif func in NUMERIC_ONLY_FUNCS:
            # Type unknown/unlisted: AVG/SUM still deserve a numeric-only reminder.
            findings.append(
                Finding(
                    ADVISORY,
                    f"{func}({field or '?'}): AVG()/SUM() require a fully numeric field "
                    f"(int/double/currency/percent) — verify '{field or '?'}' is numeric.",
                )
            )

        # Null-handling reminder: COUNT(field) ignores nulls, unlike COUNT()/COUNT(Id).
        if func == "COUNT" and field and field.lower() != "id":
            findings.append(
                Finding(
                    ADVISORY,
                    f"COUNT({field}) ignores null values (unlike COUNT()/COUNT(Id)); "
                    f"use COUNT(Id) if you want every row.",
                )
            )

        # Picklist MIN/MAX sort-order reminder (only when the type is known to be picklist).
        if func in {"MIN", "MAX"} and ftype in {"picklist", "combobox"}:
            findings.append(
                Finding(
                    ADVISORY,
                    f"{func}({field}) on a picklist uses the picklist's defined sort "
                    f"order, not alphabetical order.",
                )
            )

        # Multi-currency reminder for an ungrouped currency aggregate.
        if ftype == "currency" and not has_group_by:
            findings.append(
                Finding(
                    ADVISORY,
                    f"{func}({field}) on a currency field defaults to the corporate "
                    f"(system) currency in multi-currency orgs; consider "
                    f"GROUP BY CurrencyIsoCode.",
                )
            )

    return findings


def load_field_types(path: Path) -> dict[str, str]:
    """Load a {fieldName: dataType} JSON map into {fieldNameLower: normalizedType}."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("--field-types JSON must be an object of field -> type")
    return {str(field).lower(): normalize_type(str(dtype)) for field, dtype in data.items()}


def print_matrix() -> None:
    rows = [
        ("Numeric (int, double, currency, percent)", "Yes Yes Yes  Yes  Yes Yes"),
        ("Date/time (date, dateTime)", "No  No  Yes  Yes  Yes Yes"),
        ("Text-like (string, reference, ID, email, phone,", ""),
        ("  url, textarea, picklist, combobox, DataCat...)", "No  No  Yes  Yes  Yes Yes"),
        ("No support (base64, boolean, time, multipicklist,", ""),
        ("  address, location, encryptedstring)", "No  No  No   No   No  No"),
        ("Calculated (formula)", "depends on the formula's return type"),
    ]
    print("Field type".ljust(51), "AVG SUM CNT  CDST MIN MAX")
    print("-" * 84)
    for label, cells in rows:
        print(label.ljust(51), cells)


def collect_queries(args: argparse.Namespace) -> list[str]:
    if args.soql:
        return split_queries(args.soql)
    if args.file:
        return split_queries(Path(args.file).read_text(encoding="utf-8"))
    return []


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check SOQL aggregate functions against field-type support.",
    )
    parser.add_argument("--soql", help="A single SOQL query string to check.")
    parser.add_argument("--file", help="Path to a file containing one or more SOQL queries.")
    parser.add_argument(
        "--field-types",
        help="Optional JSON map of field API name -> Salesforce data type.",
    )
    parser.add_argument(
        "--matrix",
        action="store_true",
        help="Print the field-type / aggregate-function compatibility matrix and exit.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.matrix:
        print_matrix()
        return 0

    queries = collect_queries(args)
    if not queries:
        print("No SOQL provided. Use --soql, --file, or --matrix. See --help.", file=sys.stderr)
        return 2

    field_types: dict[str, str] | None = None
    if args.field_types:
        try:
            field_types = load_field_types(Path(args.field_types))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"Could not load --field-types: {exc}", file=sys.stderr)
            return 2

    error_count = 0
    for i, query in enumerate(queries, start=1):
        findings = check_query(query, field_types)
        if not findings:
            continue
        one_line = " ".join(query.split())
        header = one_line if len(one_line) <= 90 else one_line[:87] + "..."
        print(f"[query {i}] {header}")
        for f in findings:
            print(f"  {f.level}: {f.message}")
            if f.level == ERROR:
                error_count += 1
        print()

    if error_count:
        print(f"{error_count} error-level finding(s).", file=sys.stderr)
        return 1
    print("No aggregate field-type errors found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
