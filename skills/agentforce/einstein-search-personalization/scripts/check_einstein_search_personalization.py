#!/usr/bin/env python3
"""Checker script for Einstein Search Personalization skill.

Validates org metadata or configuration artifacts for common Einstein Search
personalization issues. Detects NLS object scope misuse, language assumptions,
and missing FLS considerations.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_einstein_search_personalization.py [--help]
    python3 check_einstein_search_personalization.py --manifest-dir path/to/metadata
    python3 check_einstein_search_personalization.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Objects that support Natural Language Search in Einstein Search.
# Source: Salesforce Help — Einstein Search Limitations
NLS_SUPPORTED_OBJECTS = frozenset(
    {"Account", "Contact", "Opportunity", "Case", "Lead"}
)

# Fields commonly referenced in NLS queries where FLS gaps cause silent result distortion.
# Source: Salesforce Help — Get Personalized Results — Einstein Search
NLS_SENSITIVE_FIELDS: dict[str, list[str]] = {
    "Case": ["Status", "Priority", "OwnerId", "CreatedDate"],
    "Account": ["Name", "BillingCity", "Industry", "AnnualRevenue"],
    "Contact": ["Name", "AccountId", "Title"],
    "Opportunity": ["StageName", "CloseDate", "OwnerId", "Amount"],
    "Lead": ["Status", "OwnerId", "Industry"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for Einstein Search personalization "
            "configuration issues. Detects NLS object scope violations, "
            "language assumptions, and FLS risks."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def find_files_by_extension(root: Path, extension: str) -> list[Path]:
    """Return all files under root matching the given extension."""
    return list(root.rglob(f"*{extension}"))


def check_profile_fls_for_nls_fields(manifest_dir: Path) -> list[str]:
    """Check profiles for missing FLS on fields commonly used in NLS queries.

    NLS silently drops criteria for fields without FLS Read access.
    Source: Salesforce Help — Einstein Search Limitations (FLS enforcement section).
    """
    issues: list[str] = []
    profile_files = find_files_by_extension(manifest_dir, ".profile-meta.xml")

    for profile_path in profile_files:
        try:
            tree = ET.parse(profile_path)
        except ET.ParseError as exc:
            issues.append(f"Could not parse profile XML: {profile_path} — {exc}")
            continue

        root = tree.getroot()
        # Strip namespace if present
        ns = ""
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0] + "}"

        # Collect field permissions in this profile
        hidden_fields: set[str] = set()
        for fp in root.findall(f"{ns}fieldPermissions"):
            readable_el = fp.find(f"{ns}readable")
            field_el = fp.find(f"{ns}field")
            if readable_el is None or field_el is None:
                continue
            if readable_el.text and readable_el.text.strip().lower() == "false":
                hidden_fields.add(field_el.text.strip() if field_el.text else "")

        # Cross-check against NLS-sensitive fields
        for obj, fields in NLS_SENSITIVE_FIELDS.items():
            for field in fields:
                qualified = f"{obj}.{field}"
                if qualified in hidden_fields:
                    issues.append(
                        f"[FLS-NLS] Profile '{profile_path.stem}' hides {qualified} — "
                        f"NLS queries referencing this field will silently drop that criteria. "
                        f"Grant Read FLS or document this limitation for users."
                    )

    return issues


def check_search_layout_custom_objects(manifest_dir: Path) -> list[str]:
    """Check for custom objects referenced in search layouts.

    Custom objects can be in global search scope but cannot use NLS.
    Flag them so the admin knows to use filter panels instead.
    """
    issues: list[str] = []
    search_layout_files = find_files_by_extension(manifest_dir, ".searchLayout-meta.xml")

    for layout_path in search_layout_files:
        # Derive object name from filename: MyObject__c.searchLayout-meta.xml
        # Custom objects end in __c
        stem = layout_path.stem.replace(".searchLayout-meta", "")
        if "__c" in stem:
            issues.append(
                f"[NLS-SCOPE] Custom object '{stem}' has a search layout configured. "
                f"Note: Natural Language Search does NOT support custom objects. "
                f"Users expecting NLS conversational queries for '{stem}' must use filter "
                f"panels or custom LWC search components instead."
            )

    return issues


def check_object_translations_for_label_renames(manifest_dir: Path) -> list[str]:
    """Detect renamed standard object labels that may break NLS user expectations.

    NLS matches on API names, not custom labels. A renamed label creates a
    vocabulary mismatch for users.
    Source: Salesforce Help — Einstein Search Limitations.
    """
    issues: list[str] = []
    translation_files = find_files_by_extension(manifest_dir, ".objectTranslation-meta.xml")

    for trans_path in translation_files:
        # Infer object from filename: Contact-en_US.objectTranslation-meta.xml
        parts = trans_path.stem.split("-")
        if not parts:
            continue
        obj_name = parts[0]
        if obj_name not in NLS_SUPPORTED_OBJECTS:
            continue

        try:
            tree = ET.parse(trans_path)
        except ET.ParseError as exc:
            issues.append(f"Could not parse objectTranslation XML: {trans_path} — {exc}")
            continue

        root = tree.getroot()
        ns = ""
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0] + "}"

        label_el = root.find(f"{ns}label")
        if label_el is not None and label_el.text:
            custom_label = label_el.text.strip()
            if custom_label.lower() != obj_name.lower():
                issues.append(
                    f"[NLS-LABEL] Object '{obj_name}' has custom label '{custom_label}' "
                    f"in translation file '{trans_path.name}'. "
                    f"NLS parses on API name '{obj_name}', not the custom label. "
                    f"Users typing '{custom_label}' in NLS queries will fall back to "
                    f"keyword search. Document this in user training."
                )

    return issues


def check_einstein_search_personalization(manifest_dir: Path) -> list[str]:
    """Run all Einstein Search personalization checks.

    Returns a list of issue strings. Each string is a concrete, actionable finding.
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check 1: FLS gaps that silently break NLS criteria
    issues.extend(check_profile_fls_for_nls_fields(manifest_dir))

    # Check 2: Custom objects in search layouts flagged for NLS scope limitation
    issues.extend(check_search_layout_custom_objects(manifest_dir))

    # Check 3: Renamed standard object labels that break NLS user expectations
    issues.extend(check_object_translations_for_label_renames(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_einstein_search_personalization(manifest_dir)

    if not issues:
        print("No Einstein Search personalization issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    print(
        f"\n{len(issues)} issue(s) found. Review the WARN messages above.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
