#!/usr/bin/env python3
"""Checker script for Knowledge Article Import skill.

Validates a Knowledge article import ZIP package or a directory containing
the CSV, .properties, and HTML files before uploading to Salesforce.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_knowledge_article_import.py --zip path/to/import.zip
    python3 check_knowledge_article_import.py --dir path/to/import_folder
    python3 check_knowledge_article_import.py --csv path/to/articles.csv
"""

from __future__ import annotations

import argparse
import csv
import io
import os
import sys
import zipfile
from pathlib import Path

# Hard platform limit for the ZIP file
ZIP_SIZE_LIMIT_BYTES = 20 * 1024 * 1024  # 20 MB

# Required CSV columns
REQUIRED_CSV_COLUMNS = {"Title", "URLName", "RecordTypeId", "IsMasterLanguage", "Language"}

# Required .properties keys
REQUIRED_PROPERTIES_KEYS = {"ArticleType", "Encoding", "CSVFile"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a Salesforce Knowledge article import package. "
            "Checks ZIP size, .properties keys, CSV columns, URLName uniqueness, "
            "data category delimiter usage, and ArticleType API name format."
        ),
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--zip",
        dest="zip_path",
        help="Path to the import ZIP file to validate.",
    )
    group.add_argument(
        "--dir",
        dest="dir_path",
        help="Path to a directory containing the import files (CSV, .properties, html/).",
    )
    group.add_argument(
        "--csv",
        dest="csv_path",
        help="Path to just the CSV file for column and content validation.",
    )
    return parser.parse_args()


def parse_properties(content: str) -> dict[str, str]:
    """Parse a Java-style .properties file into a dict."""
    props: dict[str, str] = {}
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            props[key.strip()] = value.strip()
    return props


def check_properties(props: dict[str, str], issues: list[str]) -> None:
    """Validate .properties file content."""
    for key in REQUIRED_PROPERTIES_KEYS:
        if key not in props:
            issues.append(f".properties is missing required key: {key}")

    article_type = props.get("ArticleType", "")
    if article_type and not article_type.endswith("__kav"):
        issues.append(
            f".properties ArticleType '{article_type}' does not end in '__kav'. "
            "Use the metadata API name (e.g. FAQ__kav), not the display label."
        )

    encoding = props.get("Encoding", "")
    if encoding and encoding.upper() != "UTF-8":
        issues.append(
            f".properties Encoding is '{encoding}'. Salesforce Knowledge import requires UTF-8."
        )


def check_csv_content(csv_text: str, issues: list[str]) -> None:
    """Validate CSV column headers and common content issues."""
    try:
        reader = csv.DictReader(io.StringIO(csv_text))
        fieldnames = set(reader.fieldnames or [])
    except Exception as exc:
        issues.append(f"CSV could not be parsed: {exc}")
        return

    # Check required columns
    missing = REQUIRED_CSV_COLUMNS - fieldnames
    for col in sorted(missing):
        issues.append(f"CSV is missing required column: {col}")

    # Check data category columns for wrong delimiter
    dc_columns = [f for f in fieldnames if f.startswith("datacategorygroup__")]
    rows = list(reader)

    url_names: list[str] = []
    for i, row in enumerate(rows, start=2):  # row 1 is header
        url_name = row.get("URLName", "").strip()
        if url_name:
            url_names.append(url_name)

        # Check for commas or semicolons in data category cells
        for col in dc_columns:
            val = row.get(col, "").strip()
            if "," in val:
                issues.append(
                    f"Row {i}, column '{col}': value '{val}' contains a comma. "
                    "Use '+' as the delimiter for multiple categories (e.g. CRM+Analytics)."
                )
            if ";" in val:
                issues.append(
                    f"Row {i}, column '{col}': value '{val}' contains a semicolon. "
                    "Use '+' as the delimiter for multiple categories."
                )

        # Check RecordTypeId length (18 chars)
        record_type_id = row.get("RecordTypeId", "").strip()
        if record_type_id and len(record_type_id) not in (15, 18):
            issues.append(
                f"Row {i}: RecordTypeId '{record_type_id}' is {len(record_type_id)} characters. "
                "Expected 15 or 18 characters."
            )

        # Check IsMasterLanguage value
        is_master = row.get("IsMasterLanguage", "").strip().lower()
        if is_master and is_master not in ("true", "false"):
            issues.append(
                f"Row {i}: IsMasterLanguage '{is_master}' is not 'true' or 'false'."
            )

        # Check URLName for spaces or unsafe characters
        if url_name and (" " in url_name or any(c.isupper() for c in url_name)):
            issues.append(
                f"Row {i}: URLName '{url_name}' contains spaces or uppercase letters. "
                "URLName must be lowercase with hyphens only."
            )

    # Warn on duplicate URLNames within this CSV
    seen: dict[str, int] = {}
    for i, url in enumerate(url_names, start=2):
        if url in seen:
            issues.append(
                f"Duplicate URLName '{url}' found at rows {seen[url]} and {i}. "
                "URLName must be unique across the org."
            )
        else:
            seen[url] = i


def check_zip(zip_path: Path, issues: list[str]) -> None:
    """Validate a ZIP import package."""
    if not zip_path.exists():
        issues.append(f"ZIP file not found: {zip_path}")
        return

    # Check file size
    size = zip_path.stat().st_size
    if size > ZIP_SIZE_LIMIT_BYTES:
        issues.append(
            f"ZIP file size {size / 1024 / 1024:.1f} MB exceeds the 20 MB platform limit. "
            "Split the import into multiple batches."
        )
    else:
        size_mb = size / 1024 / 1024
        if size_mb > 18:
            issues.append(
                f"ZIP file size {size_mb:.1f} MB is close to the 20 MB limit. "
                "Consider splitting to reduce risk of failure."
            )

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()

            # Find .properties file
            prop_files = [n for n in names if n.endswith(".properties")]
            if not prop_files:
                issues.append("ZIP does not contain a .properties file.")
            else:
                prop_content = zf.read(prop_files[0]).decode("utf-8", errors="replace")
                props = parse_properties(prop_content)
                check_properties(props, issues)

                # Validate CSV file referenced in properties
                csv_file_name = props.get("CSVFile", "")
                if csv_file_name:
                    if csv_file_name not in names:
                        issues.append(
                            f".properties references CSVFile='{csv_file_name}' "
                            f"but that file is not found in the ZIP. "
                            f"Files in ZIP: {names}"
                        )
                    else:
                        csv_content = zf.read(csv_file_name).decode("utf-8", errors="replace")
                        check_csv_content(csv_content, issues)

            # Check for CSV files not referenced
            csv_files = [n for n in names if n.endswith(".csv")]
            if not csv_files:
                issues.append("ZIP does not contain any CSV file.")

    except zipfile.BadZipFile:
        issues.append(f"File is not a valid ZIP archive: {zip_path}")


def check_directory(dir_path: Path, issues: list[str]) -> None:
    """Validate a directory of import files."""
    if not dir_path.exists() or not dir_path.is_dir():
        issues.append(f"Directory not found: {dir_path}")
        return

    prop_files = list(dir_path.glob("*.properties"))
    csv_files = list(dir_path.glob("*.csv"))

    if not prop_files:
        issues.append(f"No .properties file found in {dir_path}")
    else:
        props = parse_properties(prop_files[0].read_text(encoding="utf-8", errors="replace"))
        check_properties(props, issues)

        csv_file_name = props.get("CSVFile", "")
        if csv_file_name:
            csv_path = dir_path / csv_file_name
            if not csv_path.exists():
                issues.append(
                    f".properties references CSVFile='{csv_file_name}' "
                    f"but that file does not exist in {dir_path}"
                )
            else:
                check_csv_content(csv_path.read_text(encoding="utf-8", errors="replace"), issues)

    if not csv_files:
        issues.append(f"No CSV file found in {dir_path}")

    html_dir = dir_path / "html"
    if not html_dir.exists():
        issues.append(
            f"No 'html/' folder found in {dir_path}. "
            "Article body HTML files should be placed in html/ and referenced by relative path in the CSV."
        )


def check_csv_file(csv_path: Path, issues: list[str]) -> None:
    """Validate a standalone CSV file."""
    if not csv_path.exists():
        issues.append(f"CSV file not found: {csv_path}")
        return
    check_csv_content(csv_path.read_text(encoding="utf-8", errors="replace"), issues)


def main() -> int:
    args = parse_args()
    issues: list[str] = []

    if args.zip_path:
        check_zip(Path(args.zip_path), issues)
    elif args.dir_path:
        check_directory(Path(args.dir_path), issues)
    elif args.csv_path:
        check_csv_file(Path(args.csv_path), issues)
    else:
        print(
            "Usage: check_knowledge_article_import.py [--zip FILE | --dir DIR | --csv FILE]\n"
            "No input specified. Pass --zip, --dir, or --csv to validate an import package.",
            file=sys.stderr,
        )
        return 1

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
