#!/usr/bin/env python3
"""Checker script for B2B vs B2C Commerce Architecture skill.

Scans Salesforce metadata for patterns that indicate a platform architecture
mismatch — e.g., Commerce Extension classes referenced in an environment
that appears to be SFCC-oriented, or SFCC-specific references mixed with
B2B Commerce on Core objects.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_b2b_vs_b2c_architecture.py [--help]
    python3 check_b2b_vs_b2c_architecture.py --manifest-dir path/to/metadata
    python3 check_b2b_vs_b2c_architecture.py --manifest-dir path/to/metadata --verbose
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Patterns that indicate B2B Commerce on Core usage
# ---------------------------------------------------------------------------
B2B_CORE_PATTERNS = [
    # Commerce Extension Apex interface
    (re.compile(r"sfdc_checkout\.CartExtension", re.IGNORECASE), "Commerce Extension (sfdc_checkout.CartExtension) — B2B/D2C on Core only"),
    (re.compile(r"sfdc_checkout\.CartCalculate", re.IGNORECASE), "Commerce Extension (sfdc_checkout.CartCalculate) — B2B/D2C on Core only"),
    # Core commerce objects in SOQL or Apex
    (re.compile(r"\bBuyerGroup\b"), "BuyerGroup object reference — B2B Commerce on Core only"),
    (re.compile(r"\bCommerceEntitlementPolicy\b"), "CommerceEntitlementPolicy object reference — B2B Commerce on Core only"),
    (re.compile(r"\bWebCart\b"), "WebCart object reference — B2B/D2C Commerce on Core only"),
    (re.compile(r"\bOrderSummary\b"), "OrderSummary object reference — Salesforce Order Management on Core only"),
    (re.compile(r"\bWebStore\b"), "WebStore object reference — B2B/D2C Commerce on Core only"),
    # Flow checkout type reference
    (re.compile(r"CheckoutFlow", re.IGNORECASE), "CheckoutFlow type — B2B/D2C Commerce on Core checkout only"),
]

# ---------------------------------------------------------------------------
# Patterns that indicate SFCC / B2C Commerce Cloud usage
# ---------------------------------------------------------------------------
SFCC_PATTERNS = [
    # SFRA and Business Manager references
    (re.compile(r"\bSFRA\b"), "SFRA reference — Salesforce B2C Commerce (SFCC) only"),
    (re.compile(r"BusinessManager", re.IGNORECASE), "Business Manager reference — SFCC only"),
    (re.compile(r"\bOCAPI\b"), "OCAPI reference — SFCC Open Commerce API only"),
    (re.compile(r"\bSCAPI\b"), "SCAPI reference — SFCC Shopper Commerce API only"),
    # SFCC script API namespace
    (re.compile(r"\bdw\.order\b"), "dw.order namespace — SFCC server-side script API only"),
    (re.compile(r"\bdw\.catalog\b"), "dw.catalog namespace — SFCC server-side script API only"),
    (re.compile(r"\bdw\.system\b"), "dw.system namespace — SFCC server-side script API only"),
    # Cartridge references
    (re.compile(r"cartridge", re.IGNORECASE), "Cartridge reference — SFCC SFRA customization model only"),
    # SFCC-specific pipeline/controller pattern
    (re.compile(r"\.isml\b", re.IGNORECASE), ".isml template reference — SFCC only"),
]

# ---------------------------------------------------------------------------
# Patterns that indicate a likely architecture confusion (both platforms mixed)
# These patterns check for known incorrect cross-platform combinations.
# ---------------------------------------------------------------------------
CONFUSION_PATTERNS = [
    # Commerce Extensions in the context of SFCC (wrong)
    (
        re.compile(r"sfdc_checkout", re.IGNORECASE),
        re.compile(r"(?:SFRA|OCAPI|SCAPI|cartridge|Business\s*Manager|dw\.order)", re.IGNORECASE),
        "Commerce Extension class (sfdc_checkout.*) mixed with SFCC-specific term — possible platform confusion. "
        "Commerce Extensions apply ONLY to B2B/D2C Commerce on Core, not SFCC.",
    ),
    # BuyerGroup referenced alongside SFCC concepts (wrong)
    (
        re.compile(r"\bBuyerGroup\b"),
        re.compile(r"(?:SFRA|OCAPI|SCAPI|cartridge|Business\s*Manager)", re.IGNORECASE),
        "BuyerGroup object mixed with SFCC-specific term — BuyerGroup is a B2B Commerce on Core object and does not exist in SFCC.",
    ),
    # OrderSummary referenced as if available in SFCC (wrong — needs integration)
    (
        re.compile(r"\bOrderSummary\b"),
        re.compile(r"(?:SFRA|OCAPI|SCAPI|dw\.order)", re.IGNORECASE),
        "OrderSummary object mixed with SFCC-specific term — OrderSummary is a Salesforce Core object. "
        "SFCC orders do NOT automatically create OrderSummary records; an explicit integration is required.",
    ),
]


def _find_files(manifest_dir: Path, extensions: tuple[str, ...]) -> list[Path]:
    """Recursively find files with the given extensions under manifest_dir."""
    result: list[Path] = []
    for ext in extensions:
        result.extend(manifest_dir.rglob(f"*{ext}"))
    return sorted(result)


def _read_file(path: Path) -> str | None:
    """Read file contents; return None on error."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def check_b2b_vs_b2c_architecture(manifest_dir: Path, verbose: bool = False) -> list[str]:
    """Return a list of issue strings found in the manifest directory.

    Checks for:
    1. Commerce Extension Apex classes referenced outside a Core-platform context.
    2. SFCC-specific references mixed with Core-platform commerce object names.
    3. OrderSummary implied to be natively available in SFCC without an integration.
    4. BuyerGroup / CommerceEntitlementPolicy referenced in SFCC-context files.
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Scan Apex, Flow metadata, XML, and documentation files
    target_extensions = (".cls", ".trigger", ".flow", ".flow-meta.xml", ".xml", ".md", ".json", ".yaml", ".yml", ".js")
    files = _find_files(manifest_dir, target_extensions)

    if not files:
        if verbose:
            print(f"INFO: No scannable files found under {manifest_dir}")
        return issues

    b2b_core_files: list[tuple[Path, str]] = []
    sfcc_files: list[tuple[Path, str]] = []

    for path in files:
        content = _read_file(path)
        if content is None:
            continue

        file_has_b2b_core = False
        file_has_sfcc = False

        # Collect B2B Core signals
        for pattern, label in B2B_CORE_PATTERNS:
            if pattern.search(content):
                file_has_b2b_core = True
                if verbose:
                    print(f"INFO: B2B-on-Core pattern '{label}' found in {path}")
                break

        # Collect SFCC signals
        for pattern, label in SFCC_PATTERNS:
            if pattern.search(content):
                file_has_sfcc = True
                if verbose:
                    print(f"INFO: SFCC pattern '{label}' found in {path}")
                break

        if file_has_b2b_core:
            b2b_core_files.append((path, content))
        if file_has_sfcc:
            sfcc_files.append((path, content))

        # Check for cross-platform confusion within a single file
        for core_pattern, sfcc_pattern, message in CONFUSION_PATTERNS:
            if core_pattern.search(content) and sfcc_pattern.search(content):
                issues.append(
                    f"{path}: {message}"
                )

    # Cross-file check: if both B2B-on-Core and SFCC patterns appear in the same
    # manifest directory, flag it as a potential mixed-platform architecture.
    if b2b_core_files and sfcc_files:
        b2b_paths = ", ".join(str(p) for p, _ in b2b_core_files[:3])
        sfcc_paths = ", ".join(str(p) for p, _ in sfcc_files[:3])
        issues.append(
            f"Both B2B Commerce on Core patterns and SFCC patterns detected in the same manifest. "
            f"B2B-on-Core files (sample): {b2b_paths}. "
            f"SFCC files (sample): {sfcc_paths}. "
            "This may indicate a mixed-platform architecture. Confirm that this is intentional "
            "(e.g., a hybrid integration design document) and not a platform conflation."
        )

    # Specific check: Commerce Extensions in Apex class but no B2B Commerce license indicator
    for path, content in b2b_core_files:
        if re.search(r"sfdc_checkout\.CartExtension", content, re.IGNORECASE):
            # Check if this file also has SFCC references (wrong context)
            if re.search(r"(?:SFRA|OCAPI|SCAPI|Business\s*Manager|dw\.order)", content, re.IGNORECASE):
                issues.append(
                    f"{path}: Commerce Extension class (sfdc_checkout.CartExtension) found alongside SFCC-specific terms. "
                    "Commerce Extensions are a B2B/D2C Commerce on Core feature. "
                    "If this is an SFCC project, Commerce Extensions cannot be used — implement via SFRA cartridge hooks instead."
                )

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for B2B vs B2C Commerce architecture issues. "
            "Detects platform confusion between B2B Commerce on Core and Salesforce B2C Commerce (SFCC)."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata or project files (default: current directory).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="Print informational messages about patterns found (default: off).",
    )
    args = parser.parse_args()

    manifest_dir = Path(args.manifest_dir)
    issues = check_b2b_vs_b2c_architecture(manifest_dir, verbose=args.verbose)

    if not issues:
        print("No B2B vs B2C Commerce architecture issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    print(f"\n{len(issues)} issue(s) found.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
