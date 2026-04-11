#!/usr/bin/env python3
"""Checker script for Commerce Extension Points skill.

Validates Salesforce metadata for common Commerce extension point issues:
- RegisteredExternalService records with invalid or suspect EPN strings
- Apex classes extending CartExtension base classes that contain DML statements
- Apex classes extending CartExtension base classes that call async methods

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_commerce_extension_points.py [--help]
    python3 check_commerce_extension_points.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# ---------------------------------------------------------------------------
# Known valid Extension Point Names (EPN strings) from official documentation
# ---------------------------------------------------------------------------
KNOWN_VALID_EPNS: set[str] = {
    "Commerce_Domain_Pricing_CartCalculator",
    "Commerce_Domain_Inventory_CartCalculator",
    "Commerce_Domain_Promotions_CartCalculator",
    "Commerce_Domain_Shipping_CartCalculator",
    "Commerce_Domain_Tax_CartCalculator",
}

# ---------------------------------------------------------------------------
# Patterns that indicate prohibited operations inside extension hook methods
# ---------------------------------------------------------------------------
DML_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\binsert\s+\w", re.IGNORECASE),
    re.compile(r"\bupdate\s+\w", re.IGNORECASE),
    re.compile(r"\bdelete\s+\w", re.IGNORECASE),
    re.compile(r"\bupsert\s+\w", re.IGNORECASE),
    re.compile(r"Database\.(insert|update|delete|upsert)\s*\(", re.IGNORECASE),
]

ASYNC_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"System\.enqueueJob\s*\(", re.IGNORECASE),
    re.compile(r"Database\.executeBatch\s*\(", re.IGNORECASE),
    re.compile(r"Messaging\.sendEmail\s*\(", re.IGNORECASE),
    re.compile(r"@future", re.IGNORECASE),
]

CART_EXTENSION_BASE = re.compile(
    r"extends\s+CartExtension\.", re.IGNORECASE
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Commerce Extension Points configuration and metadata for common issues."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_registered_external_services(manifest_dir: Path) -> list[str]:
    """Validate RegisteredExternalService custom metadata records."""
    issues: list[str] = []

    # RegisteredExternalService records live in
    # customMetadata/ as *.RegisteredExternalService-meta.xml  (source format)
    # or in registeredExternalServices/ (metadata API format, older tooling)
    patterns = [
        "**/*RegisteredExternalService*.md-meta.xml",
        "**/*RegisteredExternalService*.xml",
        "**/registeredExternalServices/*.xml",
    ]

    found_files: list[Path] = []
    for pat in patterns:
        found_files.extend(manifest_dir.glob(pat))

    if not found_files:
        # Not an issue — org may not have any registered extensions yet
        return issues

    for fpath in found_files:
        try:
            tree = ET.parse(fpath)
            root = tree.getroot()
        except ET.ParseError as exc:
            issues.append(f"{fpath.name}: XML parse error — {exc}")
            continue

        # Extract field values from <values> elements
        field_values: dict[str, str] = {}
        for values_el in root.findall(".//{*}values"):
            field_el = values_el.find("{*}field")
            value_el = values_el.find("{*}value")
            if field_el is not None and value_el is not None:
                field_values[field_el.text or ""] = value_el.text or ""

        epn = field_values.get("ExtensionPointName", "")
        provider_type = field_values.get("ExternalServiceProviderType", "")
        provider = field_values.get("ExternalServiceProvider", "")

        if not epn:
            issues.append(
                f"{fpath.name}: Missing ExtensionPointName — extension will never fire."
            )
        elif epn not in KNOWN_VALID_EPNS:
            issues.append(
                f"{fpath.name}: ExtensionPointName '{epn}' is not a known valid EPN. "
                f"Valid values: {', '.join(sorted(KNOWN_VALID_EPNS))}"
            )

        if not provider_type:
            issues.append(
                f"{fpath.name}: Missing ExternalServiceProviderType — extension may not wire correctly."
            )

        if not provider:
            issues.append(
                f"{fpath.name}: Missing ExternalServiceProvider (Apex class name)."
            )

    return issues


def check_cart_extension_apex_classes(manifest_dir: Path) -> list[str]:
    """Check Apex classes that extend CartExtension base classes for prohibited patterns."""
    issues: list[str] = []

    apex_files = list(manifest_dir.glob("**/*.cls"))
    if not apex_files:
        return issues

    for fpath in apex_files:
        try:
            source = fpath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if not CART_EXTENSION_BASE.search(source):
            continue  # Not a CartExtension class — skip

        # Check for DML patterns
        for pattern in DML_PATTERNS:
            if pattern.search(source):
                issues.append(
                    f"{fpath.name}: Possible DML inside a CartExtension class "
                    f"(matched pattern: '{pattern.pattern}'). "
                    "DML is prohibited inside extension hooks and causes System.DmlException at runtime."
                )
                break  # One DML warning per file is enough

        # Check for async patterns
        for pattern in ASYNC_PATTERNS:
            if pattern.search(source):
                issues.append(
                    f"{fpath.name}: Possible async Apex inside a CartExtension class "
                    f"(matched pattern: '{pattern.pattern}'). "
                    "Async calls inside extension hooks cause System.AsyncException at runtime."
                )
                break  # One async warning per file is enough

    return issues


def check_duplicate_epns(manifest_dir: Path) -> list[str]:
    """Warn if multiple RegisteredExternalService records share the same EPN."""
    issues: list[str] = []

    patterns = [
        "**/*RegisteredExternalService*.md-meta.xml",
        "**/*RegisteredExternalService*.xml",
        "**/registeredExternalServices/*.xml",
    ]

    epn_to_files: dict[str, list[str]] = {}

    for pat in patterns:
        for fpath in manifest_dir.glob(pat):
            try:
                tree = ET.parse(fpath)
                root = tree.getroot()
            except ET.ParseError:
                continue

            for values_el in root.findall(".//{*}values"):
                field_el = values_el.find("{*}field")
                value_el = values_el.find("{*}value")
                if (
                    field_el is not None
                    and value_el is not None
                    and (field_el.text or "") == "ExtensionPointName"
                ):
                    epn = value_el.text or ""
                    epn_to_files.setdefault(epn, []).append(fpath.name)

    for epn, files in epn_to_files.items():
        if len(files) > 1:
            issues.append(
                f"Duplicate EPN '{epn}' found in {len(files)} RegisteredExternalService records: "
                f"{', '.join(files)}. Only the last deployed record will be active — "
                "the others will be silently overridden."
            )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)

    if not manifest_dir.exists():
        print(f"WARN: Manifest directory not found: {manifest_dir}", file=sys.stderr)
        return 1

    all_issues: list[str] = []
    all_issues.extend(check_registered_external_services(manifest_dir))
    all_issues.extend(check_cart_extension_apex_classes(manifest_dir))
    all_issues.extend(check_duplicate_epns(manifest_dir))

    if not all_issues:
        print("No issues found.")
        return 0

    for issue in all_issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
