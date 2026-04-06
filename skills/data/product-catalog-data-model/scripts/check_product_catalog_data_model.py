#!/usr/bin/env python3
"""Checker script for Product Catalog Data Model skill.

Validates Salesforce metadata and CSV load files for common product catalog
anti-patterns: standard pricebook ID hardcoding, UseStandardPrice misconfigurations,
and load sequence issues.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_product_catalog_data_model.py [--help]
    python3 check_product_catalog_data_model.py --manifest-dir path/to/metadata
    python3 check_product_catalog_data_model.py --csv-dir path/to/load/csvs
    python3 check_product_catalog_data_model.py --apex-dir path/to/classes
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path


# Pattern that matches a hardcoded Salesforce Pricebook2 record ID (15 or 18 char, starts with 01s)
_HARDCODED_PB_ID_RE = re.compile(r"\b01s[A-Za-z0-9]{12,15}\b")

# Pattern for UseStandardPrice in Apex/CSV context
_USE_STD_PRICE_TRUE_RE = re.compile(r"UseStandardPrice\s*[=:]\s*true", re.IGNORECASE)
_UNIT_PRICE_NONBLANK_RE = re.compile(r"UnitPrice\s*[=:]\s*['\"]?[\d.]+['\"]?", re.IGNORECASE)

# SOQL query that retrieves Standard PB via IsStandard (correct pattern)
_QUERY_STANDARD_PB_RE = re.compile(
    r"IsStandard\s*=\s*true", re.IGNORECASE
)

# Hardcoded ID in Apex (assigned to a variable)
_APEX_HARDCODED_PB_RE = re.compile(
    r"(?:Pricebook2Id|pricebookId|pbId)\s*=\s*['\"]01s[A-Za-z0-9]{12,15}['\"]",
    re.IGNORECASE,
)

# Test method without Test.getStandardPricebookId that queries Standard PB via SOQL
_APEX_TEST_SOQL_STD_PB_RE = re.compile(
    r"SELECT\s+Id\s+FROM\s+Pricebook2\s+WHERE\s+IsStandard",
    re.IGNORECASE,
)

_APEX_GET_STD_PB_METHOD_RE = re.compile(
    r"Test\.getStandardPricebookId\(\)",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check product catalog data model configuration for common issues:\n"
            "  - Hardcoded Standard Pricebook IDs\n"
            "  - UseStandardPrice=true with UnitPrice present in CSV load files\n"
            "  - SOQL query for Standard Pricebook inside Apex test methods\n"
            "  - Missing UseStandardPrice column in custom PBE CSV files\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Root directory of Salesforce metadata to scan.",
    )
    parser.add_argument(
        "--csv-dir",
        default=None,
        help="Directory containing CSV load files for product catalog (PricebookEntry etc.).",
    )
    parser.add_argument(
        "--apex-dir",
        default=None,
        help="Directory containing Apex class files to check for pricebook anti-patterns.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# CSV checks
# ---------------------------------------------------------------------------

def check_csv_file(csv_path: Path) -> list[str]:
    """Check a single CSV file for PricebookEntry loading anti-patterns."""
    issues: list[str] = []
    try:
        with csv_path.open(newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            headers = [h.strip() if h else "" for h in (reader.fieldnames or [])]
            lower_headers = [h.lower() for h in headers]

            # Only check files that look like PricebookEntry loads
            has_pricebook2_id = "pricebook2id" in lower_headers
            has_product2_id = "product2id" in lower_headers
            if not (has_pricebook2_id and has_product2_id):
                return issues

            has_use_std_price = "usestandardprice" in lower_headers
            has_unit_price = "unitprice" in lower_headers

            for i, row in enumerate(reader, start=2):  # row 1 is header
                # Normalise keys to lowercase for consistent access
                lrow = {k.lower().strip(): (v or "").strip() for k, v in row.items()}

                pb_id = lrow.get("pricebook2id", "")

                # Check for hardcoded Standard Pricebook ID pattern
                if _HARDCODED_PB_ID_RE.search(pb_id):
                    issues.append(
                        f"{csv_path.name}:row {i}: Pricebook2Id '{pb_id}' looks like a hardcoded "
                        f"record ID. Standard Pricebook IDs are org-specific — query "
                        f"'WHERE IsStandard = true' at runtime instead of embedding the ID."
                    )

                use_std = lrow.get("usestandardprice", "").lower()
                unit_price = lrow.get("unitprice", "")

                # UseStandardPrice=true with a non-blank UnitPrice is invalid
                if use_std == "true" and unit_price not in ("", "null"):
                    issues.append(
                        f"{csv_path.name}:row {i}: UseStandardPrice=true AND UnitPrice='{unit_price}' "
                        f"are mutually exclusive. Remove UnitPrice (or leave blank) when "
                        f"UseStandardPrice is true."
                    )

                # UseStandardPrice=false (or missing) without UnitPrice — likely missing price
                if use_std in ("false", "") and not unit_price:
                    # Only flag if this is not the Standard Pricebook (IsStandard rows need UnitPrice too)
                    issues.append(
                        f"{csv_path.name}:row {i}: UseStandardPrice is '{use_std or 'blank'}' but "
                        f"UnitPrice is empty. Explicit UnitPrice is required when UseStandardPrice "
                        f"is false or absent."
                    )

    except (OSError, csv.Error) as exc:
        issues.append(f"{csv_path.name}: Could not read CSV file — {exc}")

    return issues


def check_csv_dir(csv_dir: Path) -> list[str]:
    issues: list[str] = []
    csv_files = list(csv_dir.rglob("*.csv"))
    if not csv_files:
        return issues
    for csv_path in csv_files:
        issues.extend(check_csv_file(csv_path))
    return issues


# ---------------------------------------------------------------------------
# Apex checks
# ---------------------------------------------------------------------------

def check_apex_file(apex_path: Path) -> list[str]:
    issues: list[str] = []
    try:
        source = apex_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [f"{apex_path.name}: Could not read Apex file — {exc}"]

    # Check for hardcoded Standard Pricebook ID in Apex assignments
    for match in _APEX_HARDCODED_PB_RE.finditer(source):
        line_no = source[: match.start()].count("\n") + 1
        issues.append(
            f"{apex_path.name}:{line_no}: Hardcoded Pricebook2 ID detected ('{match.group()}'). "
            f"Standard Pricebook IDs are org-specific. Use "
            f"[SELECT Id FROM Pricebook2 WHERE IsStandard = true LIMIT 1].Id in production, "
            f"or Test.getStandardPricebookId() in tests."
        )

    # Check for SOQL-based Standard Pricebook query inside @isTest annotated files
    # without Test.getStandardPricebookId()
    is_test_file = "@isTest" in source or "@IsTest" in source
    if is_test_file:
        soql_queries = list(_APEX_TEST_SOQL_STD_PB_RE.finditer(source))
        uses_platform_method = bool(_APEX_GET_STD_PB_METHOD_RE.search(source))
        has_see_all_data = "SeeAllData=true" in source or "seeAllData=true" in source

        for match in soql_queries:
            if not uses_platform_method and not has_see_all_data:
                line_no = source[: match.start()].count("\n") + 1
                issues.append(
                    f"{apex_path.name}:{line_no}: Apex test queries Standard Pricebook via SOQL "
                    f"('{match.group()}'). In test context this returns 0 rows without "
                    f"SeeAllData=true. Use Test.getStandardPricebookId() instead."
                )

    return issues


def check_apex_dir(apex_dir: Path) -> list[str]:
    issues: list[str] = []
    apex_files = list(apex_dir.rglob("*.cls"))
    if not apex_files:
        return issues
    for apex_path in apex_files:
        issues.extend(check_apex_file(apex_path))
    return issues


# ---------------------------------------------------------------------------
# Manifest / generic metadata checks
# ---------------------------------------------------------------------------

def check_manifest_dir(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Scan all text-like files for hardcoded Standard Pricebook IDs
    text_extensions = {".xml", ".json", ".yaml", ".yml", ".md", ".txt", ".cls", ".trigger", ".csv"}
    for file_path in manifest_dir.rglob("*"):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in text_extensions:
            continue
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for match in _HARDCODED_PB_ID_RE.finditer(content):
            # Reduce noise: only flag if it appears in a context that looks like a pricebook reference
            surrounding = content[max(0, match.start() - 50) : match.end() + 50].lower()
            if "pricebook" in surrounding or "standard" in surrounding:
                line_no = content[: match.start()].count("\n") + 1
                issues.append(
                    f"{file_path.relative_to(manifest_dir)}:{line_no}: Potential hardcoded "
                    f"Standard Pricebook ID '{match.group()}' detected. Standard Pricebook IDs "
                    f"are org-specific and must not be embedded in metadata or code."
                )

    return issues


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    args = parse_args()
    all_issues: list[str] = []

    if args.manifest_dir:
        all_issues.extend(check_manifest_dir(Path(args.manifest_dir)))

    if args.csv_dir:
        csv_path = Path(args.csv_dir)
        if not csv_path.exists():
            all_issues.append(f"CSV directory not found: {csv_path}")
        else:
            all_issues.extend(check_csv_dir(csv_path))

    if args.apex_dir:
        apex_path = Path(args.apex_dir)
        if not apex_path.exists():
            all_issues.append(f"Apex directory not found: {apex_path}")
        else:
            all_issues.extend(check_apex_dir(apex_path))

    if not any([args.manifest_dir, args.csv_dir, args.apex_dir]):
        # Default: scan current directory for everything
        cwd = Path(".")
        all_issues.extend(check_manifest_dir(cwd))
        all_issues.extend(check_csv_dir(cwd))
        all_issues.extend(check_apex_dir(cwd))

    if not all_issues:
        print("No issues found.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
