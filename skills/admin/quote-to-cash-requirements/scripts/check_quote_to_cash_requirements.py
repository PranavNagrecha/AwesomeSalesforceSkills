#!/usr/bin/env python3
"""Checker script for Quote-to-Cash Requirements skill.

Inspects Salesforce metadata exported via Metadata API (SFDX project or unpackaged
retrieve) to detect common quote-to-cash configuration issues.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_quote_to_cash_requirements.py [--manifest-dir path/to/metadata]
    python3 check_quote_to_cash_requirements.py --manifest-dir force-app/main/default

Checks performed:
  1. Multiple Approval Processes active on Quote object (should be one)
  2. Approval Process Final Actions referencing unsupported record-create patterns
  3. Flow present for Order creation from Quote Status change
  4. Validation rule or Flow guarding against >100 line items on Quote
  5. Order object metadata present when Quote Approval Processes exist
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SF_NS = "http://soap.sforce.com/2006/04/metadata"


def _tag(name: str) -> str:
    return f"{{{SF_NS}}}{name}"


def _find_text(element: ET.Element, tag: str) -> str:
    child = element.find(_tag(tag))
    return child.text.strip() if child is not None and child.text else ""


def check_multiple_quote_approval_processes(manifest_dir: Path) -> list[str]:
    """Flag if more than one active Approval Process targets the Quote object."""
    issues: list[str] = []
    approvals_dir = manifest_dir / "approvalProcesses"
    if not approvals_dir.exists():
        return issues

    quote_processes: list[str] = []
    for xml_file in sorted(approvals_dir.glob("Quote*.approvalProcess-meta.xml")):
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            active_node = root.find(_tag("active"))
            is_active = active_node is None or (
                active_node.text and active_node.text.strip().lower() == "true"
            )
            if is_active:
                quote_processes.append(xml_file.name)
        except ET.ParseError:
            issues.append(f"Could not parse approval process file: {xml_file.name}")

    if len(quote_processes) > 1:
        issues.append(
            f"WARN: {len(quote_processes)} active Approval Processes found targeting Quote "
            f"({', '.join(quote_processes)}). Salesforce only runs one approval process per "
            f"record at a time. Use a single process with multiple steps for multi-tier routing."
        )
    return issues


def check_approval_process_final_actions(manifest_dir: Path) -> list[str]:
    """Detect Approval Process Final Actions that may attempt unsupported record creation."""
    issues: list[str] = []
    approvals_dir = manifest_dir / "approvalProcesses"
    if not approvals_dir.exists():
        return issues

    for xml_file in sorted(approvals_dir.glob("Quote*.approvalProcess-meta.xml")):
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            for action_ref in root.iter(_tag("finalApprovalActions")):
                for action in action_ref.iter(_tag("action")):
                    action_type = _find_text(action, "type")
                    action_name = _find_text(action, "name")
                    if action_type.lower() in ("flow", "apex"):
                        continue
                    if "order" in action_name.lower() or "create" in action_name.lower():
                        issues.append(
                            f"WARN: Approval Process '{xml_file.stem}' Final Approval action "
                            f"'{action_name}' (type: {action_type}) may be attempting record "
                            f"creation. Approval Process actions cannot create records natively. "
                            f"Use a Record-Triggered Flow on Quote Status change instead."
                        )
        except ET.ParseError:
            issues.append(f"Could not parse approval process file: {xml_file.name}")

    return issues


def check_flows_for_quote_order_creation(manifest_dir: Path) -> list[str]:
    """Check if any Flow handles Order creation from Quote Status changes."""
    issues: list[str] = []
    flows_dir = manifest_dir / "flows"
    approvals_dir = manifest_dir / "approvalProcesses"
    has_quote_approval = (
        approvals_dir.exists()
        and any(approvals_dir.glob("Quote*.approvalProcess-meta.xml"))
    )
    if not has_quote_approval or not flows_dir.exists():
        return issues

    found_order_flow = False
    for xml_file in sorted(flows_dir.glob("*.flow-meta.xml")):
        try:
            content = xml_file.read_text(encoding="utf-8").lower()
            if "quote" in content and "order" in content and "accepted" in content:
                found_order_flow = True
                break
        except OSError:
            continue

    if not found_order_flow:
        issues.append(
            "INFO: Approval Processes for Quote found but no Flow detected that creates Orders "
            "on Quote Status = 'Accepted'. If Order creation is required, implement a "
            "Record-Triggered Flow on Quote (trigger: Status changes to Accepted)."
        )
    return issues


def check_quote_line_item_volume_guard(manifest_dir: Path) -> list[str]:
    """Check for a validation rule or flow guarding against >100 line items on Quote."""
    issues: list[str] = []
    vr_dir = manifest_dir / "objects" / "Quote" / "validationRules"
    flows_dir = manifest_dir / "flows"

    has_volume_guard = False

    if vr_dir.exists():
        for vr_file in vr_dir.glob("*.validationRule-meta.xml"):
            try:
                content = vr_file.read_text(encoding="utf-8").lower()
                if ("quotelinescount" in content or "quotelineitem" in content) and (
                    "100" in content or "90" in content
                ):
                    has_volume_guard = True
                    break
            except OSError:
                continue

    if not has_volume_guard and flows_dir.exists():
        for flow_file in flows_dir.glob("*.flow-meta.xml"):
            try:
                content = flow_file.read_text(encoding="utf-8").lower()
                if "quotelineitem" in content and ("100" in content or "90" in content):
                    has_volume_guard = True
                    break
            except OSError:
                continue

    if not has_volume_guard:
        issues.append(
            "INFO: No validation rule or Flow detected guarding against Quote line item volume "
            "exceeding the 100-item PDF rendering limit. Consider adding a validation rule "
            "or in-app warning when QuoteLineItem count approaches 100."
        )
    return issues


def check_order_object_configured(manifest_dir: Path) -> list[str]:
    """Check if Order object metadata is present when Quote approval processes exist."""
    issues: list[str] = []
    approvals_dir = manifest_dir / "approvalProcesses"
    has_quote_approval = (
        approvals_dir.exists()
        and any(approvals_dir.glob("Quote*.approvalProcess-meta.xml"))
    )
    if not has_quote_approval:
        return issues

    order_dir = manifest_dir / "objects" / "Order"
    if not order_dir.exists():
        issues.append(
            "INFO: Quote Approval Processes detected but no Order object metadata found. "
            "If Orders are generated from Quotes, verify Order object is included in the "
            "metadata retrieve and that Order management is enabled in Setup."
        )
    return issues


def check_quote_to_cash_requirements(manifest_dir: Path) -> list[str]:
    """Run all checks and return a consolidated list of issues."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_multiple_quote_approval_processes(manifest_dir))
    issues.extend(check_approval_process_final_actions(manifest_dir))
    issues.extend(check_flows_for_quote_order_creation(manifest_dir))
    issues.extend(check_quote_line_item_volume_guard(manifest_dir))
    issues.extend(check_order_object_configured(manifest_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for common quote-to-cash configuration issues. "
            "Targets metadata retrieved via Metadata API or SFDX project structure."
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
    issues = check_quote_to_cash_requirements(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1 if any("WARN" in i or "not found" in i for i in issues) else 0


if __name__ == "__main__":
    sys.exit(main())
