#!/usr/bin/env python3
"""Checker script for Commerce LWC Components skill.

Validates LWC component bundles intended for B2B Commerce / D2C LWR storefronts.
Checks for:
  - Missing lightningCommunity__RelaxedCSP capability in .js-meta.xml files
  - Use of lightning/uiRecordApi or lightning/uiObjectInfoApi in store components
  - Cart/wishlist mutation calls outside user-gesture event handlers
  - Product2.FieldName format in commerce/productApi wire adapter fields params
  - Apex imports for operations that have Commerce API equivalents

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_commerce_lwc_components.py [--help]
    python3 check_commerce_lwc_components.py --manifest-dir path/to/lwc
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# LDS modules that should not appear in Commerce storefront components
_LDS_MODULE_PATTERN = re.compile(
    r"""from\s+['"]lightning/(uiRecordApi|uiObjectInfoApi|uiListsApi|uiRelatedListApi)['"]"""
)

# Commerce wire adapters — presence indicates this is a storefront component
_COMMERCE_IMPORT_PATTERN = re.compile(
    r"""from\s+['"]commerce/"""
)

# Cart / wishlist mutation function names
_MUTATION_FUNCTIONS = (
    "addItemToCart",
    "removeItemFromCart",
    "updateCartItem",
    "addToWishlist",
    "removeFromWishlist",
)

# Lifecycle hooks where mutations should not be called
_LIFECYCLE_HOOKS = re.compile(
    r"""\b(connectedCallback|disconnectedCallback|renderedCallback|constructor)\s*\(\s*\)"""
)

# Product2.FieldName format inside fields arrays for commerce adapters
_DOTTED_FIELD_IN_COMMERCE = re.compile(
    r"""(['"])Product2\.\w+\1"""
)

# Apex imports for cart/wishlist operations
_APEX_CART_PATTERN = re.compile(
    r"""from\s+['"]@salesforce/apex/\w*[Cc]art\w*['"]"""
)
_APEX_WISHLIST_PATTERN = re.compile(
    r"""from\s+['"]@salesforce/apex/\w*[Ww]ishlist\w*['"]"""
)

# innerHTML assignment without obvious sanitization
_INNER_HTML_PATTERN = re.compile(r"""\.innerHTML\s*=""")


# ---------------------------------------------------------------------------
# Per-file checks
# ---------------------------------------------------------------------------

def check_js_file(path: Path, issues: list[str]) -> None:
    """Check a .js LWC controller for Commerce-specific issues."""
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        issues.append(f"{path}: cannot read file — {exc}")
        return

    is_storefront_component = bool(_COMMERCE_IMPORT_PATTERN.search(content))

    # Only apply LDS and Commerce-specific checks if the file imports from commerce/*
    if is_storefront_component:
        # Check for LDS imports
        for match in _LDS_MODULE_PATTERN.finditer(content):
            issues.append(
                f"{path}: imports '{match.group(0).strip()}' — "
                "lightning/uiRecordApi and related LDS adapters are unavailable in LWR storefronts. "
                "Use commerce/productApi, commerce/cartApi, or commerce/wishlistApi instead."
            )

        # Check for dotted field names in commerce adapter calls
        if _DOTTED_FIELD_IN_COMMERCE.search(content):
            issues.append(
                f"{path}: contains 'Product2.FieldName' style field references — "
                "commerce/productApi requires bare field API names (e.g., 'Name', not 'Product2.Name')."
            )

        # Check for Apex cart/wishlist imports
        if _APEX_CART_PATTERN.search(content):
            issues.append(
                f"{path}: imports an Apex CartController — "
                "use commerce/cartApi (addItemToCart, removeItemFromCart) instead of custom Apex for cart operations."
            )
        if _APEX_WISHLIST_PATTERN.search(content):
            issues.append(
                f"{path}: imports an Apex WishlistController — "
                "use commerce/wishlistApi (addToWishlist, removeFromWishlist) instead of custom Apex for wishlist operations."
            )

        # Heuristic: mutation function calls inside lifecycle hooks
        # Find lifecycle hook bodies and check for mutation function names within them
        # Simple line-range heuristic: flag files that contain both a lifecycle hook AND a mutation function name
        has_mutation = any(fn in content for fn in _MUTATION_FUNCTIONS)
        has_lifecycle = bool(_LIFECYCLE_HOOKS.search(content))
        if has_mutation and has_lifecycle:
            issues.append(
                f"{path}: contains both lifecycle hooks and cart/wishlist mutation function calls — "
                "verify that mutations (addItemToCart, addToWishlist, etc.) are only called from "
                "user-gesture event handlers (onclick, onkeydown), not from connectedCallback or renderedCallback."
            )

        # innerHTML without sanitization
        if _INNER_HTML_PATTERN.search(content):
            issues.append(
                f"{path}: uses innerHTML assignment — "
                "LWR storefronts disable Lightning Locker and LWS; sanitize all HTML before assigning to innerHTML."
            )


def check_meta_xml_file(path: Path, issues: list[str]) -> None:
    """Check a .js-meta.xml file for Commerce-specific requirements."""
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        issues.append(f"{path}: cannot read file — {exc}")
        return

    # Only check files that expose to community/Experience Builder targets
    if "lightningCommunity__Page" not in content and "lightningCommunity__" not in content:
        return  # Not a store-targeted component; skip

    if "lightningCommunity__RelaxedCSP" not in content:
        issues.append(
            f"{path}: missing <capability>lightningCommunity__RelaxedCSP</capability> — "
            "all components deployed to B2B/D2C LWR stores must declare this capability "
            "or they may fail to render on cart and checkout pages."
        )

    if "isExposed" not in content or "<isExposed>true</isExposed>" not in content:
        issues.append(
            f"{path}: isExposed is not set to true — "
            "set <isExposed>true</isExposed> to make the component available in Experience Builder."
        )


# ---------------------------------------------------------------------------
# Directory traversal
# ---------------------------------------------------------------------------

def check_commerce_lwc_components(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    js_files = list(manifest_dir.rglob("*.js"))
    meta_files = list(manifest_dir.rglob("*.js-meta.xml"))

    if not js_files and not meta_files:
        issues.append(
            f"No LWC files found under {manifest_dir}. "
            "Pass the path to your lwc/ metadata directory with --manifest-dir."
        )
        return issues

    for js_path in js_files:
        # Skip test files
        if "__tests__" in js_path.parts or js_path.name.endswith(".test.js"):
            continue
        check_js_file(js_path, issues)

    for meta_path in meta_files:
        check_meta_xml_file(meta_path, issues)

    return issues


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check LWC components for B2B/D2C Commerce storefront compliance: "
            "missing RelaxedCSP capability, wrong wire adapter imports, unsafe mutations, "
            "and Apex usage that should use Commerce APIs."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the LWC metadata (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_commerce_lwc_components(manifest_dir)

    if not issues:
        print("No Commerce LWC issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())