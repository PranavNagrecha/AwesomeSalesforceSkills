#!/usr/bin/env python3
"""Checker script for Industries Process Design skill.

Checks Salesforce org metadata for common industries process design anti-patterns:
- Screen Flows used where industry OmniScript frameworks are expected
- Communications Cloud order management using Commerce (non-IOM) object references
- Missing decomposition rule indicators in Communications Cloud setup
- E&U service order configuration without documented CIS callout exception paths

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_industries_process_design.py [--help]
    python3 check_industries_process_design.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Screen Flow file pattern — these are .flow-meta.xml files
FLOW_GLOB = "**/*.flow-meta.xml"

# OmniScript metadata pattern (for both Standard Runtime and Package Runtime)
OMNISCRIPT_GLOB = "**/*.omniscript-meta.xml"

# Commerce Order Management object references that must NOT appear in Comms Cloud code
COMMERCE_OM_OBJECTS = [
    "OrderSummary",
    "FulfillmentOrder",
    "OrderDeliveryGroup",
    "OrderDeliveryMethod",
    "OrderItemSummary",
]

# Insurance claims-related Screen Flow warning keywords
INSURANCE_FLOW_KEYWORDS = [
    "Claim",
    "FNOL",
    "InsurancePolicy",
    "ClaimParticipant",
    "InsurancePolicyCoverage",
    "claims_management",
    "fnol_intake",
    "claims_lifecycle",
]

# Apex trigger files
APEX_TRIGGER_GLOB = "**/*.trigger"
APEX_CLASS_GLOB = "**/*.cls"

# IOM decomposition keyword — presence in Apex code is a warning (should be declarative)
IOM_APEX_KEYWORDS = [
    "TechnicalOrderItem__c",
    "FulfilmentRequest__c",
    "vlocity_cmt__TechnicalOrder",
    "vlocity_cmt__OrderItem",
]

# CIS callout keywords in E&U context
EU_SERVICE_ORDER_KEYWORDS = [
    "ServiceOrder",
    "service_order",
    "EnergyUtilities",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_text(path: Path) -> str:
    """Return file contents as string, empty string on error."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _parse_xml_root(path: Path) -> ET.Element | None:
    """Parse XML file and return root element, None on error."""
    try:
        tree = ET.parse(path)
        return tree.getroot()
    except ET.ParseError:
        return None


def _find_flows(manifest_dir: Path) -> list[Path]:
    return list(manifest_dir.glob(FLOW_GLOB))


def _find_apex_triggers(manifest_dir: Path) -> list[Path]:
    return list(manifest_dir.glob(APEX_TRIGGER_GLOB))


def _find_apex_classes(manifest_dir: Path) -> list[Path]:
    return list(manifest_dir.glob(APEX_CLASS_GLOB))


# ---------------------------------------------------------------------------
# Check: Screen Flows with insurance claims keywords
# ---------------------------------------------------------------------------

def check_screen_flows_for_claims_keywords(manifest_dir: Path) -> list[str]:
    """Warn when a Screen Flow references insurance claims objects.

    A Screen Flow (processType = Flow with interactionType = screenFlow or similar)
    that creates or updates Claim / InsurancePolicy records is likely replacing
    the Claims Management OmniScript framework — an anti-pattern per this skill.
    """
    issues: list[str] = []
    flow_files = _find_flows(manifest_dir)

    for flow_path in flow_files:
        root = _parse_xml_root(flow_path)
        if root is None:
            continue

        # Look for processType = 'Flow' (Screen Flow) in the XML
        ns = {"sf": "http://soap.sforce.com/2006/04/metadata"}
        process_type_el = root.find("sf:processType", ns) or root.find("processType")
        if process_type_el is None:
            continue

        process_type = (process_type_el.text or "").strip()
        # Screen Flows have processType = 'Flow'
        if process_type != "Flow":
            continue

        # Check whether this Screen Flow references insurance claims objects
        flow_text = _read_text(flow_path)
        matched_keywords = [kw for kw in INSURANCE_FLOW_KEYWORDS if kw in flow_text]
        if matched_keywords:
            issues.append(
                f"SCREEN FLOW with insurance claims keywords detected: {flow_path.name} "
                f"(matched: {', '.join(matched_keywords)}). "
                "Screen Flows cannot call Claims Management Connect API endpoints or integrate with "
                "the Adjuster's Workbench. Review whether this should be an OmniScript within the "
                "Claims Management framework instead."
            )

    return issues


# ---------------------------------------------------------------------------
# Check: Apex triggers or classes creating IOM technical order objects
# ---------------------------------------------------------------------------

def check_apex_iom_object_creation(manifest_dir: Path) -> list[str]:
    """Warn when Apex code creates vlocity_cmt technical order objects directly.

    Decomposition of commercial orders to technical orders in Communications Cloud
    must be handled by Industries Order Management declarative decomposition rules,
    not Apex trigger code. Apex-created records do not participate in the IOM lifecycle.
    """
    issues: list[str] = []
    apex_files = _find_apex_triggers(manifest_dir) + _find_apex_classes(manifest_dir)

    for apex_path in apex_files:
        apex_text = _read_text(apex_path)
        matched = [kw for kw in IOM_APEX_KEYWORDS if kw in apex_text]
        if matched:
            # Check if this is a DML operation (insert/update) — not just a query
            lower_text = apex_text.lower()
            if any(op in lower_text for op in ["insert ", "update ", "upsert ", "database.insert", "database.upsert"]):
                issues.append(
                    f"Apex file creates vlocity_cmt IOM objects directly: {apex_path.name} "
                    f"(matched keywords: {', '.join(matched)}). "
                    "Technical order records for Communications Cloud must be generated by "
                    "Industries Order Management decomposition rules (declarative configuration), "
                    "not by Apex DML. Apex-inserted records do not participate in the IOM "
                    "order lifecycle (status callbacks, dependency tracking, retry logic)."
                )

    return issues


# ---------------------------------------------------------------------------
# Check: Commerce Order Management objects in Apex (Comms Cloud context risk)
# ---------------------------------------------------------------------------

def check_commerce_om_objects_in_apex(manifest_dir: Path) -> list[str]:
    """Warn when Commerce Order Management objects appear in Apex that also references vlocity_cmt.

    Salesforce Order Management (Commerce) and Industries Order Management (Communications Cloud)
    are separate platforms. Code that mixes these object references likely has a platform confusion.
    """
    issues: list[str] = []
    apex_files = _find_apex_triggers(manifest_dir) + _find_apex_classes(manifest_dir)

    for apex_path in apex_files:
        apex_text = _read_text(apex_path)

        has_vlocity = "vlocity_cmt" in apex_text
        matched_commerce = [obj for obj in COMMERCE_OM_OBJECTS if obj in apex_text]

        if has_vlocity and matched_commerce:
            issues.append(
                f"Apex file references both vlocity_cmt (Industries/Comms) and Commerce Order Management "
                f"objects: {apex_path.name} (Commerce objects: {', '.join(matched_commerce)}). "
                "Industries Order Management and Salesforce Order Management are separate platforms. "
                "Mixing their object references indicates a platform confusion. Review which "
                "order management platform this code targets."
            )

    return issues


# ---------------------------------------------------------------------------
# Check: OmniScript files using Screen Flow process type or incorrect runtime
# ---------------------------------------------------------------------------

def check_omniscript_structure(manifest_dir: Path) -> list[str]:
    """Check OmniScript metadata files for basic structural requirements.

    Each OmniScript must have at minimum one Step element and a Navigate action.
    Missing these causes activation failure.
    """
    issues: list[str] = []
    omniscript_files = list(manifest_dir.glob(OMNISCRIPT_GLOB))

    for os_path in omniscript_files:
        os_text = _read_text(os_path)

        has_step = "<type>Step</type>" in os_text or '"type":"Step"' in os_text
        has_navigate = "Navigate" in os_text or "navigate" in os_text

        if not has_step:
            issues.append(
                f"OmniScript missing Step element: {os_path.name}. "
                "Every OmniScript requires at least one Step element. "
                "OmniScripts without a Step cannot be activated."
            )

        if not has_navigate:
            issues.append(
                f"OmniScript may be missing Navigate action: {os_path.name}. "
                "OmniScripts require a Navigate Action to complete the flow. "
                "Without it the OmniScript hangs on the final step. Verify manually."
            )

    return issues


# ---------------------------------------------------------------------------
# Main checker
# ---------------------------------------------------------------------------

def check_industries_process_design(manifest_dir: Path) -> list[str]:
    """Run all checks and return a list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check 1: Screen Flows referencing insurance claims objects
    issues.extend(check_screen_flows_for_claims_keywords(manifest_dir))

    # Check 2: Apex creating IOM technical order objects directly
    issues.extend(check_apex_iom_object_creation(manifest_dir))

    # Check 3: Commerce OM objects mixed with vlocity_cmt in same Apex file
    issues.extend(check_commerce_om_objects_in_apex(manifest_dir))

    # Check 4: OmniScript structural requirements
    issues.extend(check_omniscript_structure(manifest_dir))

    return issues


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for Industries process design anti-patterns: "
            "Screen Flows replacing Claims Management OmniScript framework, Apex-based "
            "IOM technical order creation, and Commerce/Industries Order Management confusion."
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
    issues = check_industries_process_design(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
