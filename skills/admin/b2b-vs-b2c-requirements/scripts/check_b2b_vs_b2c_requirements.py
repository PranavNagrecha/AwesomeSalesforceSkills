#!/usr/bin/env python3
"""Checker script for B2B vs D2C Commerce Requirements skill.

Scans Salesforce metadata for patterns that indicate a platform selection
mismatch — e.g., B2B Commerce objects referenced in a D2C store context,
SFCC-specific patterns confused with Lightning-based Commerce, or WebStore
type indicators.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_b2b_vs_b2c_requirements.py [--help]
    python3 check_b2b_vs_b2c_requirements.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# B2B Commerce objects that are not available on a D2C-licensed org
B2B_ONLY_OBJECTS = re.compile(
    r"\b(BuyerGroup|CommerceEntitlementPolicy|CommerceEntitlementBuyerGroup"
    r"|CommerceEntitlementProduct|BuyerGroupMember|BuyerAccountAccess)\b"
)

# SFCC / Business Manager terms that indicate conflation with Lightning Commerce
SFCC_TERMS = re.compile(
    r"\b(BusinessManager|SiteCartridgePath|SFRA|sfra|CartridgePath"
    r"|cartridge_path|site\.cartridge|SitePreferences)\b"
)

# Guest checkout patterns that should be flagged as requiring explicit enablement
GUEST_CHECKOUT_DEFAULT = re.compile(
    r"(guest.{0,20}checkout|anonymous.{0,20}purchas|IsGuestBrowsingEnabled)",
    re.IGNORECASE,
)

# WebStore type markers
WEBSTORE_B2B_MARKER = re.compile(r'StoreType\s*[=:]\s*["\']?B2B["\']?', re.IGNORECASE)
WEBSTORE_D2C_MARKER = re.compile(r'StoreType\s*[=:]\s*["\']?B2C["\']?', re.IGNORECASE)

# ---------------------------------------------------------------------------
# File extensions to scan
# ---------------------------------------------------------------------------

SCANNABLE_EXTENSIONS = {
    ".cls",   # Apex classes
    ".trigger",
    ".flow",
    ".xml",   # Metadata XML (custom objects, layouts, flows)
    ".json",
    ".js",    # LWC JavaScript
    ".html",  # LWC HTML
    ".md",    # Documentation
    ".yaml",
    ".yml",
}


def _scan_file(path: Path) -> list[str]:
    """Return a list of issue strings found in a single file."""
    issues: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return issues

    # Check for SFCC terms alongside Lightning Commerce references
    sfcc_matches = SFCC_TERMS.findall(text)
    if sfcc_matches:
        unique = sorted(set(sfcc_matches))
        issues.append(
            f"{path}: SFCC/Business Manager term(s) detected: {unique}. "
            "Verify this is not confusing Salesforce B2C Commerce (SFCC) "
            "with D2C Commerce (Lightning WebStore). If this is an SFCC project, "
            "use admin/b2c-commerce-store-setup instead."
        )

    # Check for B2B-only objects — flag as a warning so D2C projects can catch misuse
    b2b_matches = B2B_ONLY_OBJECTS.findall(text)
    if b2b_matches:
        unique = sorted(set(b2b_matches))
        issues.append(
            f"{path}: B2B Commerce object(s) referenced: {unique}. "
            "These objects are only available with a B2B Commerce license and do not "
            "exist on D2C-licensed orgs. Confirm the org has a B2B Commerce license "
            "before referencing these objects."
        )

    # Check for guest checkout references — surface for explicit enablement reminder
    guest_matches = GUEST_CHECKOUT_DEFAULT.findall(text)
    if guest_matches:
        # Only flag if this looks like setup/config code, not a documentation file
        if path.suffix not in {".md", ".txt"}:
            issues.append(
                f"{path}: Guest checkout reference detected. "
                "Guest purchasing on B2B Commerce WebStores requires explicit "
                "enablement (Winter '24+ only) and is not on by default. "
                "Confirm org release version and check WebStore guest access settings."
            )

    return issues


def check_b2b_vs_b2c_requirements(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    found_b2b_store = False
    found_d2c_store = False

    for path in manifest_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in SCANNABLE_EXTENSIONS:
            continue

        # Detect WebStore type markers for summary reporting
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if WEBSTORE_B2B_MARKER.search(text):
            found_b2b_store = True
        if WEBSTORE_D2C_MARKER.search(text):
            found_d2c_store = True

        issues.extend(_scan_file(path))

    # Warn if both B2B and D2C WebStore types are found in the same manifest
    if found_b2b_store and found_d2c_store:
        issues.append(
            "Both B2B and D2C (B2C) WebStore types detected in metadata. "
            "A hybrid B2B2C deployment requires two separate WebStore instances "
            "and both B2B Commerce and D2C Commerce licenses. "
            "Confirm this is an intentional multi-store architecture."
        )

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for B2B vs D2C Commerce platform "
            "selection issues: SFCC/Lightning conflation, B2B-only objects on "
            "D2C orgs, guest checkout enablement gaps, and hybrid store misuse."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_b2b_vs_b2c_requirements(manifest_dir)

    if not issues:
        print("No B2B vs D2C Commerce platform selection issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
