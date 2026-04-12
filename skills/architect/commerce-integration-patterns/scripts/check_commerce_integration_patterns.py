#!/usr/bin/env python3
"""Checker script for Commerce Integration Patterns skill.

Scans Salesforce Apex source files and custom metadata XML in a metadata directory
for common anti-patterns documented in references/gotchas.md and
references/llm-anti-patterns.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_commerce_integration_patterns.py [--help]
    python3 check_commerce_integration_patterns.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Patterns: CartExtension callout-after-DML anti-pattern
# ---------------------------------------------------------------------------

# DML keywords that create uncommitted work
_DML_PATTERN = re.compile(
    r"\b(insert|update|upsert|delete|undelete|merge)\s+",
    re.IGNORECASE,
)

# HTTP callout indicators
_CALLOUT_PATTERN = re.compile(
    r"\b(new\s+Http\s*\(\s*\)|Http\s*\(\s*\)|\.send\s*\(|HttpRequest\s*\(\s*\))",
    re.IGNORECASE,
)

# CartExtension calculator base class — indicates file is in scope for phase check
_CART_EXT_CALCULATOR = re.compile(
    r"extends\s+CartExtension\s*\.\s*(Pricing|Shipping|Inventory|Tax)CartCalculator",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Patterns: raw card data in Apex
# ---------------------------------------------------------------------------

_CARD_DATA_FIELD_PATTERN = re.compile(
    r"\b(cardNumber|card_number|pan\b|cvv\b|cvv2\b|cvc\b|expiry|expirationDate|"
    r"creditCard|credit_card|rawCard)\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Patterns: hardcoded credentials
# ---------------------------------------------------------------------------

_HARDCODED_CRED_PATTERN = re.compile(
    r"(\"Bearer\s+[A-Za-z0-9\-_\.]{20,}\"|"
    r"\"Basic\s+[A-Za-z0-9+/=]{20,}\"|"
    r"'Bearer\s+[A-Za-z0-9\-_\.]{20,}'|"
    r"[Aa]pi[_\-]?[Kk]ey\s*=\s*['\"][A-Za-z0-9\-_]{16,}['\"]|"
    r"[Ss]ecret\s*=\s*['\"][A-Za-z0-9\-_]{16,}['\"])",
)

# ---------------------------------------------------------------------------
# Patterns: legacy payment interface in LWR store context
# ---------------------------------------------------------------------------

_LEGACY_PAYMENT_INTERFACE = re.compile(
    r"implements\s+sfdc_checkout\s*\.\s*CartPaymentAuthorize",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Patterns: Product2 insert without External ID
# ---------------------------------------------------------------------------

_PRODUCT2_INSERT = re.compile(
    r"\binsert\s+\w*[Pp]roduct2\b|\binsert\s+\w*[Pp]roduct\w*\b",
)

_PRODUCT2_UPSERT_WITH_EXT_ID = re.compile(
    r"Database\.upsert\s*\(.*Product2\.",
    re.DOTALL,
)

# ---------------------------------------------------------------------------
# Patterns: RegisteredExternalService duplicate EPN check (XML metadata)
# ---------------------------------------------------------------------------

_EPN_PATTERN = re.compile(
    r"<ExtensionPointName>(.*?)</ExtensionPointName>",
    re.IGNORECASE,
)

_STORE_PATTERN = re.compile(
    r"<StoreIntegratedService>(.*?)</StoreIntegratedService>",
    re.IGNORECASE,
)


def _check_apex_file(path: Path) -> list[str]:
    """Check a single .cls or .trigger file for commerce integration anti-patterns."""
    issues: list[str] = []
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return issues

    # --- Callout-after-DML in CartExtension calculators ---
    if _CART_EXT_CALCULATOR.search(source):
        lines = source.splitlines()
        first_dml_line = None
        first_callout_line = None
        for i, line in enumerate(lines, start=1):
            if first_dml_line is None and _DML_PATTERN.search(line):
                first_dml_line = i
            if first_callout_line is None and _CALLOUT_PATTERN.search(line):
                first_callout_line = i

        if first_dml_line is not None and first_callout_line is not None:
            if first_callout_line > first_dml_line:
                issues.append(
                    f"{path}: CartExtension calculator has an HTTP callout (line "
                    f"{first_callout_line}) after a DML statement (line "
                    f"{first_dml_line}). This will throw "
                    f"System.CalloutException at runtime. Move all callouts "
                    f"before any DML in the calculate() method."
                )

    # --- Raw card data in Apex ---
    if _CARD_DATA_FIELD_PATTERN.search(source):
        matches = [
            (i + 1, line.strip())
            for i, line in enumerate(source.splitlines())
            if _CARD_DATA_FIELD_PATTERN.search(line)
        ]
        for lineno, line_text in matches[:3]:  # cap at 3 to avoid noise
            issues.append(
                f"{path}:{lineno}: Possible raw card data field reference "
                f"({line_text!r:.80}). Raw card data must never transit Salesforce. "
                f"Only opaque tokens or nonces should appear in Apex payment code."
            )

    # --- Hardcoded credentials ---
    if _HARDCODED_CRED_PATTERN.search(source):
        issues.append(
            f"{path}: Possible hardcoded API credential detected. Use Named "
            f"Credentials with 'callout:<NamedCredential>/...' endpoint syntax "
            f"instead of embedding secrets in Apex or Custom Settings."
        )

    # --- Legacy payment interface ---
    if _LEGACY_PAYMENT_INTERFACE.search(source):
        issues.append(
            f"{path}: Implements sfdc_checkout.CartPaymentAuthorize — this is "
            f"the legacy Aura B2B Commerce payment interface. Modern LWR-based "
            f"B2B and D2C stores require CommercePayments.PaymentGatewayAdapter. "
            f"Confirm the store runtime before using this interface."
        )

    # --- Product2 insert without External ID ---
    if _PRODUCT2_INSERT.search(source) and not _PRODUCT2_UPSERT_WITH_EXT_ID.search(source):
        issues.append(
            f"{path}: Uses 'insert' on Product2 records without a corresponding "
            f"Database.upsert() with an External ID field. In PIM sync scenarios "
            f"this produces duplicate Product2 records on repeated runs. Use "
            f"Database.upsert(list, Product2.<ExternalId>__c, false) instead."
        )

    return issues


def _check_metadata_dir(manifest_dir: Path) -> list[str]:
    """Check CustomMetadata XML files for duplicate EPN registrations."""
    issues: list[str] = []

    # Collect all RegisteredExternalService metadata records
    custom_metadata_dirs = list(manifest_dir.rglob("customMetadata"))
    xml_files: list[Path] = []
    for d in custom_metadata_dirs:
        xml_files.extend(d.glob("RegisteredExternalService.*.md-meta.xml"))

    # Also check the top-level customMetadata directory style
    xml_files.extend(
        manifest_dir.rglob("RegisteredExternalService.*.md-meta.xml")
    )

    # Deduplicate
    xml_files = list({str(f): f for f in xml_files}.values())

    # Build a map of (EPN, store) -> list of files
    epn_store_map: dict[tuple[str, str], list[Path]] = {}
    for xml_file in xml_files:
        try:
            content = xml_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        epn_match = _EPN_PATTERN.search(content)
        store_match = _STORE_PATTERN.search(content)
        if epn_match:
            epn = epn_match.group(1).strip()
            store = store_match.group(1).strip() if store_match else "__unknown__"
            key = (epn, store)
            epn_store_map.setdefault(key, []).append(xml_file)

    for (epn, store), files in epn_store_map.items():
        if len(files) > 1:
            file_names = ", ".join(f.name for f in files)
            issues.append(
                f"Duplicate RegisteredExternalService registrations for EPN "
                f"'{epn}' on store '{store}': {file_names}. Only one class per "
                f"EPN per store is honored. Consolidate to a single dispatcher class."
            )

    return issues


def check_commerce_integration_patterns(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check Apex source files
    apex_files = list(manifest_dir.rglob("*.cls")) + list(manifest_dir.rglob("*.trigger"))
    for apex_file in apex_files:
        issues.extend(_check_apex_file(apex_file))

    # Check custom metadata for duplicate EPN registrations
    issues.extend(_check_metadata_dir(manifest_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce Commerce integration metadata and Apex for "
            "anti-patterns documented in the commerce-integration-patterns skill."
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
    issues = check_commerce_integration_patterns(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
