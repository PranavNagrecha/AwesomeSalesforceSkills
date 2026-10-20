#!/usr/bin/env python3
"""Checker script for Manufacturing Cloud Setup skill.

Grounded rules (Metadata API guide 264):
  ERROR  SalesAgreementSettings.actualsCalculationMode not Manual, Orders,
         OrdersThroughContracts or DataProcessingEngine (L128635-128639).
  ERROR  AdvAccountForecastSet.calculationFrequency not Weekly, Monthly,
         Quarterly or Yearly (L16754-16763); a measure computationMethod not
         CUSTOM, FORMULA or DATA_PROCESSING_ENGINE_DEFINITION (L128795-128801).
  WARN   displayedAgreementTermsMetrics with more than 10 names (L128662-128663).
  ERROR  settings XML that does not parse.

Heuristic rules (premises UNVERIFIED 2026-10-20, the corpus has no Manufacturing
Cloud Developer Guide), WARN only:
  - custom SalesAgreement__c / Rebate objects shadowing standard ones
  - a Term/Contract_Term/Agreement_Term field on Opportunity
  - a Batchable class that calculates rebates without native rebate objects
  - Apex that creates OrderItem without mentioning SalesAgreementId

Exit codes: ERROR findings exit 1 always; WARN findings exit 0 unless --strict;
a directory with nothing to scan prints one WARN and exits 0; a missing
directory is an ERROR and exits 1. Stdlib only.

Usage:
    python3 check_manufacturing_cloud_setup.py [--manifest-dir force-app] [--strict]
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SHADOW_OBJECT_HINTS = {
    "salesagreement__c": "SalesAgreement",
    "sales_agreement__c": "SalesAgreement",
    "rebate__c": "RebateProgram",
    "rebate_payout__c": "ProgramRebatePayout",
    "rebate_program__c": "RebateProgram",
    "account_product_forecast__c": "AccountProductForecast",
}
ACTUALS_MODES = {"Manual", "Orders", "OrdersThroughContracts", "DataProcessingEngine"}
FREQUENCIES = {"Weekly", "Monthly", "Quarterly", "Yearly"}
COMPUTATION_METHODS = {"CUSTOM", "FORMULA", "DATA_PROCESSING_ENGINE_DEFINITION"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Manufacturing Cloud Setup metadata for common issues.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of the Salesforce metadata (default: .).")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on WARN findings too.")
    return parser.parse_args()


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def texts(root: ET.Element, name: str) -> list[str]:
    return [(e.text or "").strip() for e in root.iter() if local(e.tag) == name]


def check_settings(path: Path) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [("ERROR", f"{path}: does not parse ({exc})")]
    for value in texts(root, "actualsCalculationMode"):
        if value not in ACTUALS_MODES:
            out.append(("ERROR", f"{path}: actualsCalculationMode '{value}' is not one of {sorted(ACTUALS_MODES)}"))
    for value in texts(root, "calculationFrequency"):
        if value not in FREQUENCIES:
            out.append(("ERROR", f"{path}: calculationFrequency '{value}' is not one of {sorted(FREQUENCIES)}"))
    for value in texts(root, "computationMethod"):
        if value not in COMPUTATION_METHODS:
            out.append(("ERROR", f"{path}: computationMethod '{value}' is not one of {sorted(COMPUTATION_METHODS)}"))
    for value in texts(root, "displayedAgreementTermsMetrics"):
        if len([m for m in value.split(",") if m.strip()]) > 10:
            out.append(("WARN", f"{path}: displayedAgreementTermsMetrics lists more than 10 metrics (documented maximum is 10)"))
    return out


def scan(manifest_dir: Path) -> tuple[int, list[tuple[str, str]]]:
    found: list[tuple[str, str]] = []
    seen = 0
    # The SalesAgreementSettings page names a .salesAgreementSetting file (api_meta 264
    # L128615); other settings types are retrieved as <Name>.settings in a settings
    # folder (e.g. L36396), and source format adds -meta.xml, so accept all three.
    settings = (
        sorted(manifest_dir.rglob("*.salesAgreementSetting"))
        + sorted(manifest_dir.rglob("SalesAgreement.settings"))
        + sorted(manifest_dir.rglob("SalesAgreement.settings-meta.xml"))
    )
    for p in settings + sorted(manifest_dir.rglob("*.advAccountForecastSet")) + sorted(manifest_dir.rglob("*.advAccountForecastSet-meta.xml")):
        seen += 1
        found.extend(check_settings(p))
    for obj in sorted(manifest_dir.rglob("*.object-meta.xml")) + sorted(manifest_dir.rglob("*.object")):
        seen += 1
        name = obj.name.split(".")[0].lower()
        if name in SHADOW_OBJECT_HINTS:
            found.append(("WARN", f"{obj}: custom object '{name}' may shadow Manufacturing Cloud '{SHADOW_OBJECT_HINTS[name]}'; audit Object Manager first (premise UNVERIFIED)"))
    for field in sorted(manifest_dir.rglob("*.field-meta.xml")):
        seen += 1
        owner = field.parent.parent.name.lower() if field.parent.name == "fields" else field.parent.name.lower()
        if owner == "opportunity" and re.search(r"<fullName>(Term|Contract_Term|Agreement_Term)__c</fullName>", field.read_text(encoding="utf-8", errors="ignore")):
            found.append(("WARN", f"{field}: multi-period term field on Opportunity; multi-period commitments are SalesAgreement's job (premise UNVERIFIED)"))
    rebate_re = re.compile(r"\b(rebate|payout)\b.*\b(calculate|compute|process)\b", re.IGNORECASE)
    item_re = re.compile(r"\bnew\s+OrderItem\s*\(", re.IGNORECASE)
    for code in sorted(manifest_dir.rglob("*.cls")) + sorted(manifest_dir.rglob("*.trigger")):
        seen += 1
        text = code.read_text(encoding="utf-8", errors="ignore")
        if "implements Database.Batchable" in text and rebate_re.search(text) and "RebateProgram" not in text and "ProgramRebate" not in text:
            found.append(("WARN", f"{code}: batch class appears to calculate rebates without native rebate objects (premise UNVERIFIED)"))
        if item_re.search(text) and "SalesAgreementId" not in text:
            found.append(("WARN", f"{code}: creates OrderItem without SalesAgreementId; check actualsCalculationMode (premise UNVERIFIED)"))
    return seen, found


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    if not manifest_dir.is_dir():
        print(f"ERROR: manifest directory not found: {manifest_dir}")
        sys.exit(1)
    seen, findings = scan(manifest_dir)
    if not seen:
        print(f"WARN: no settings, object, field, Apex class or trigger files under {manifest_dir}; nothing to check")
        return 0
    for level, msg in findings:
        print(f"{level}: {msg}")
    if not findings:
        print("No Manufacturing Cloud anti-patterns detected.")
    has_error = any(lv == "ERROR" for lv, _ in findings)
    has_warn = any(lv == "WARN" for lv, _ in findings)
    return 1 if has_error or (args.strict and has_warn) else 0


if __name__ == "__main__":
    sys.exit(main())
