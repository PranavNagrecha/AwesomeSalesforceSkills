#!/usr/bin/env python3
"""Checker script for CPQ API and Automation skill.

Scans Salesforce metadata for CPQ API anti-patterns:
  - Direct DML on SBQQ__QuoteLine__c pricing fields
  - Apex triggers on SBQQ CPQ objects that touch pricing fields
  - CalculateCallback implementations without try/catch in onCalculated
  - ServiceRouter.save calls without an intervening QuoteCalculator step after QuoteProductAdder
  - ContractAmender/ContractRenewer calls without a status guard

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_cpq_api.py [--help]
    python3 check_cpq_api.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# CPQ pricing fields that must NOT be set via direct DML
# ---------------------------------------------------------------------------
CPQ_PRICING_FIELDS = [
    "SBQQ__Discount__c",
    "SBQQ__NetPrice__c",
    "SBQQ__CustomerPrice__c",
    "SBQQ__PartnerPrice__c",
    "SBQQ__RegularPrice__c",
    "SBQQ__SpecialPrice__c",
    "SBQQ__RegularTotal__c",
    "SBQQ__NetTotal__c",
    "SBQQ__GrossTotal__c",
    "SBQQ__AdditionalDiscount__c",
    "SBQQ__UnitPrice__c",
    "SBQQ__SpecialPriceType__c",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _apex_files(manifest_dir: Path) -> list[Path]:
    """Return all .cls and .trigger files under manifest_dir."""
    return list(manifest_dir.rglob("*.cls")) + list(manifest_dir.rglob("*.trigger"))


def _read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# Check functions
# ---------------------------------------------------------------------------

def check_direct_dml_on_cpq_pricing_fields(manifest_dir: Path) -> list[str]:
    """Detect Apex files that assign CPQ pricing fields and then call update or insert."""
    issues: list[str] = []
    for apex_file in _apex_files(manifest_dir):
        text = _read_text(apex_file)
        for field in CPQ_PRICING_FIELDS:
            # Look for assignment to a CPQ pricing field (e.g. line.SBQQ__Discount__c = ...)
            assign_pattern = re.compile(
                r"\." + re.escape(field) + r"\s*=", re.IGNORECASE
            )
            if assign_pattern.search(text):
                # Also check the same file has update/insert DML (not just a ServiceRouter call)
                has_dml = bool(re.search(r"\b(update|insert)\b\s+\w", text))
                has_service_router = "ServiceRouter" in text
                # Flag if DML present; warn louder if no ServiceRouter usage at all
                if has_dml:
                    note = (
                        " (no ServiceRouter usage found — likely bypassing pricing engine)"
                        if not has_service_router
                        else " (verify DML does not target CPQ pricing fields directly)"
                    )
                    issues.append(
                        f"{apex_file}: assigns {field} and contains DML{note}"
                    )
                    break  # one issue per file is enough
    return issues


def check_triggers_on_cpq_objects(manifest_dir: Path) -> list[str]:
    """Detect Apex triggers defined on SBQQ__Quote__c or SBQQ__QuoteLine__c."""
    issues: list[str] = []
    for trigger_file in manifest_dir.rglob("*.trigger"):
        text = _read_text(trigger_file)
        if re.search(r"trigger\s+\w+\s+on\s+SBQQ__(Quote|QuoteLine)__c", text, re.IGNORECASE):
            issues.append(
                f"{trigger_file}: Apex trigger on SBQQ CPQ object detected. "
                "Triggers on SBQQ__Quote__c or SBQQ__QuoteLine__c run outside the CPQ "
                "calculation transaction and may produce overwritten or corrupt pricing data. "
                "Use CPQ plugin interfaces or ServiceRouter instead."
            )
    return issues


def check_calculate_callback_missing_try_catch(manifest_dir: Path) -> list[str]:
    """Detect CalculateCallback implementations whose onCalculated lacks try/catch."""
    issues: list[str] = []
    for apex_file in _apex_files(manifest_dir):
        text = _read_text(apex_file)
        if "SBQQ.CalculateCallback" not in text:
            continue
        # Find the onCalculated method body
        method_match = re.search(
            r"void\s+onCalculated\s*\([^)]*\)\s*\{", text, re.IGNORECASE
        )
        if not method_match:
            continue
        # Extract content after the method opening brace (rough heuristic)
        after_method = text[method_match.end():]
        # Check if try appears before the next closing brace at method top level
        first_try = after_method.find("try")
        first_close = after_method.find("}")
        if first_try == -1 or (first_close != -1 and first_close < first_try):
            issues.append(
                f"{apex_file}: implements SBQQ.CalculateCallback but onCalculated "
                "appears to lack a try/catch block. Exceptions in onCalculated are "
                "silently swallowed by the CPQ queueable framework — failures must "
                "be caught and logged explicitly."
            )
    return issues


def check_product_adder_without_calculator(manifest_dir: Path) -> list[str]:
    """Detect files that use QuoteProductAdder followed by QuoteSaver with no QuoteCalculator."""
    issues: list[str] = []
    for apex_file in _apex_files(manifest_dir):
        text = _read_text(apex_file)
        if "QuoteProductAdder" not in text:
            continue
        if "QuoteSaver" in text and "QuoteCalculator" not in text:
            issues.append(
                f"{apex_file}: uses QuoteProductAdder and QuoteSaver but no QuoteCalculator. "
                "Products added via QuoteProductAdder must be priced via QuoteCalculator before "
                "saving — omitting the calculate step produces quote lines with null/zero price fields."
            )
    return issues


def check_contract_amender_without_status_guard(manifest_dir: Path) -> list[str]:
    """Detect ContractAmender/ContractRenewer calls not preceded by a status check."""
    issues: list[str] = []
    for apex_file in _apex_files(manifest_dir):
        text = _read_text(apex_file)
        uses_amender = "ContractAmender" in text or "ContractRenewer" in text
        if not uses_amender:
            continue
        # Heuristic: look for SBQQ__Status__c or 'Activated' near the ContractAmender call
        has_status_check = bool(
            re.search(r"SBQQ__Status__c|Activated", text, re.IGNORECASE)
        )
        if not has_status_check:
            issues.append(
                f"{apex_file}: uses ContractAmender or ContractRenewer but no "
                "SBQQ__Status__c / 'Activated' check found. ContractAmender and "
                "ContractRenewer require the contract to be in Activated status — "
                "calling them on a non-activated contract produces cryptic errors or "
                "empty models. Add an explicit status guard before the ServiceRouter call."
            )
    return issues


def check_invalid_loader_strings(manifest_dir: Path) -> list[str]:
    """Detect ServiceRouter calls with unrecognized loader strings."""
    valid_read_loaders = {"QuoteReader", "ProductLoader", "ContractAmender", "ContractRenewer"}
    valid_save_loaders = {"QuoteProductAdder", "QuoteCalculator", "QuoteSaver"}
    all_valid = valid_read_loaders | valid_save_loaders

    issues: list[str] = []
    loader_pattern = re.compile(
        r"ServiceRouter\s*\.\s*(read|save)\s*\(\s*['\"](\w+)['\"]", re.IGNORECASE
    )
    for apex_file in _apex_files(manifest_dir):
        text = _read_text(apex_file)
        for match in loader_pattern.finditer(text):
            method_name = match.group(1).lower()
            loader_name = match.group(2)
            if loader_name not in all_valid:
                issues.append(
                    f"{apex_file}: ServiceRouter.{method_name}('{loader_name}', ...) — "
                    f"'{loader_name}' is not a recognized CPQ loader/saver string. "
                    f"Valid read loaders: {sorted(valid_read_loaders)}. "
                    f"Valid save loaders: {sorted(valid_save_loaders)}."
                )
            elif method_name == "read" and loader_name not in valid_read_loaders:
                issues.append(
                    f"{apex_file}: ServiceRouter.read('{loader_name}', ...) — "
                    f"'{loader_name}' is a save-phase loader; it must be used with "
                    "ServiceRouter.save(), not read()."
                )
            elif method_name == "save" and loader_name not in valid_save_loaders:
                issues.append(
                    f"{apex_file}: ServiceRouter.save('{loader_name}', ...) — "
                    f"'{loader_name}' is a read-phase loader; it must be used with "
                    "ServiceRouter.read(), not save()."
                )
    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check CPQ API and Automation metadata for common anti-patterns.",
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

    if not manifest_dir.exists():
        print(f"ERROR: Manifest directory not found: {manifest_dir}", file=sys.stderr)
        return 1

    all_issues: list[str] = []
    all_issues += check_direct_dml_on_cpq_pricing_fields(manifest_dir)
    all_issues += check_triggers_on_cpq_objects(manifest_dir)
    all_issues += check_calculate_callback_missing_try_catch(manifest_dir)
    all_issues += check_product_adder_without_calculator(manifest_dir)
    all_issues += check_contract_amender_without_status_guard(manifest_dir)
    all_issues += check_invalid_loader_strings(manifest_dir)

    if not all_issues:
        print("No CPQ API issues found.")
        return 0

    for issue in all_issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
