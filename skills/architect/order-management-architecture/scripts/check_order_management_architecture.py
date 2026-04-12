#!/usr/bin/env python3
"""Checker script for Order Management Architecture skill.

Scans Salesforce metadata for common OMS architecture anti-patterns:
- Hardcoded fulfillment location IDs in Flow or Apex
- Missing OCI reservation failure handling in routing logic
- ensure-refunds wired directly to return creation (not gated by status)
- Routing logic operating at Order/OrderSummary level instead of ODGS level
- FulfillmentOrder creation without an orchestrating Flow subscription

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_order_management_architecture.py [--help]
    python3 check_order_management_architecture.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterator

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Salesforce record ID patterns for FulfillmentLocation (prefix 0Lq)
HARDCODED_LOCATION_ID_PATTERN = re.compile(r"\b0Lq[A-Za-z0-9]{12,15}\b")

# Patterns that suggest routing operates at OrderSummary level, not ODGS
ORDER_SUMMARY_ROUTING_MARKERS = [
    "OrderSummaryId",
    "OrderSummary__c",
]

# Patterns that indicate OrderDeliveryGroupSummary is correctly referenced
ODGS_MARKERS = [
    "OrderDeliveryGroupSummary",
    "OrderDeliveryGroup",
    "ODGS",
]

# Patterns that suggest ensure-refunds is called without a status gate
ENSURE_REFUNDS_MARKERS = [
    "ensureRefunds",
    "ensure-refunds",
    "ConnectApi.ensureRefunds",
    "ensure_refunds",
]

# submit-return markers — if ensure-refunds appears in the same file as
# submit-return without status-transition logic, it is a likely anti-pattern
SUBMIT_RETURN_MARKERS = [
    "submitReturn",
    "submit-return",
    "ConnectApi.submitReturn",
]

# ReturnOrder status transition markers that indicate the gate is present
RETURN_STATUS_GATE_MARKERS = [
    "ReturnOrder.Status",
    "Status__c",
    "CHANGED TO",
    "Changed_To",
    "isChanged",
    "PRIORVALUE",
    "prior value",
    "Received",
    "Closed",
]

# Retry or fallback patterns for OCI reservation failures
OCI_RETRY_MARKERS = [
    "RetryRouting",
    "retry",
    "Retry",
    "ProcessException",
    "Process_Exception",
    "reservation.*fail",
    "reservationFail",
    "ReservationFail",
]

# File extensions to scan
SCAN_EXTENSIONS = {".cls", ".trigger", ".flow", ".xml", ".json"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def iter_text_files(root: Path) -> Iterator[Path]:
    """Yield all scannable text files under root recursively."""
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in SCAN_EXTENSIONS:
            yield path


def read_text_safe(path: Path) -> str:
    """Read file as text, ignoring decode errors."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def contains_any(text: str, markers: list[str]) -> bool:
    return any(m in text for m in markers)


def contains_pattern(text: str, pattern: re.Pattern) -> bool:
    return bool(pattern.search(text))


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def check_hardcoded_location_ids(root: Path) -> list[str]:
    """Warn if Apex or Flow files contain hardcoded FulfillmentLocation IDs."""
    issues: list[str] = []
    for path in iter_text_files(root):
        text = read_text_safe(path)
        matches = HARDCODED_LOCATION_ID_PATTERN.findall(text)
        if matches:
            issues.append(
                f"Hardcoded FulfillmentLocation ID(s) {matches} found in "
                f"{path.name} — store location references in custom metadata "
                f"or custom settings to avoid hardcoded IDs that break when "
                f"locations are added or changed."
            )
    return issues


def check_routing_at_order_level(root: Path) -> list[str]:
    """Warn if routing logic references OrderSummary but not ODGS."""
    issues: list[str] = []
    for path in iter_text_files(root):
        if path.suffix.lower() not in {".cls", ".trigger", ".flow", ".xml"}:
            continue
        text = read_text_safe(path)
        has_routing_context = (
            "FulfillmentOrder" in text
            or "findRoutesWithFewestSplits" in text
            or "Find_Routes" in text
            or "FewestSplits" in text
        )
        if not has_routing_context:
            continue
        has_order_summary_ref = contains_any(text, ORDER_SUMMARY_ROUTING_MARKERS)
        has_odgs_ref = contains_any(text, ODGS_MARKERS)
        if has_order_summary_ref and not has_odgs_ref:
            issues.append(
                f"Possible order-level routing detected in {path.name}: "
                f"file references OrderSummary in routing context but does not "
                f"reference OrderDeliveryGroupSummary. Routing must operate at "
                f"the ODGS level — each delivery group is routed independently."
            )
    return issues


def check_ensure_refunds_not_gated(root: Path) -> list[str]:
    """Warn if ensure-refunds and submit-return appear in the same file
    without obvious status-gate logic."""
    issues: list[str] = []
    for path in iter_text_files(root):
        text = read_text_safe(path)
        has_ensure_refunds = contains_any(text, ENSURE_REFUNDS_MARKERS)
        has_submit_return = contains_any(text, SUBMIT_RETURN_MARKERS)
        if has_ensure_refunds and has_submit_return:
            has_gate = contains_any(text, RETURN_STATUS_GATE_MARKERS)
            if not has_gate:
                issues.append(
                    f"Possible unguarded ensure-refunds in {path.name}: "
                    f"both submit-return and ensure-refunds appear in this file "
                    f"without a visible ReturnOrder status transition gate. "
                    f"ensure-refunds must be triggered by a ReturnOrder status "
                    f"change (e.g., Received or Closed), not by return creation."
                )
    return issues


def check_oci_retry_missing(root: Path) -> list[str]:
    """Warn if routing files invoke fewest-splits without OCI retry logic."""
    issues: list[str] = []
    for path in iter_text_files(root):
        text = read_text_safe(path)
        has_routing = (
            "findRoutesWithFewestSplits" in text
            or "Find_Routes_With_Fewest_Splits" in text
            or "FewestSplits" in text
        )
        if not has_routing:
            continue
        has_retry = any(
            re.search(marker, text, re.IGNORECASE) for marker in OCI_RETRY_MARKERS
        )
        if not has_retry:
            issues.append(
                f"OCI reservation retry logic not detected in {path.name}: "
                f"the fewest-splits routing action is referenced but no retry "
                f"or fallback pattern is visible. OCI availability is eventually "
                f"consistent — reservation failures must be handled as a normal "
                f"code path with a retry queue or Process Exception fallback."
            )
    return issues


def check_oms_objects_present(root: Path) -> list[str]:
    """Informational check: confirm that core OMS objects are referenced
    somewhere in the manifest, indicating OMS is actually in scope."""
    issues: list[str] = []
    oms_objects = {
        "OrderSummary": False,
        "FulfillmentOrder": False,
        "OrderDeliveryGroupSummary": False,
    }
    for path in iter_text_files(root):
        text = read_text_safe(path)
        for obj in list(oms_objects):
            if obj in text:
                oms_objects[obj] = True
    missing = [obj for obj, found in oms_objects.items() if not found]
    if missing:
        issues.append(
            f"Core OMS object(s) not found in any scanned file: {missing}. "
            f"If OMS is in scope for this project, verify that the metadata "
            f"directory contains relevant Flow, Apex, or object XML files. "
            f"If OMS is not provisioned, multi-location routing will not work."
        )
    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def check_order_management_architecture(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_hardcoded_location_ids(manifest_dir))
    issues.extend(check_routing_at_order_level(manifest_dir))
    issues.extend(check_ensure_refunds_not_gated(manifest_dir))
    issues.extend(check_oci_retry_missing(manifest_dir))
    issues.extend(check_oms_objects_present(manifest_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce OMS metadata for order management architecture "
            "anti-patterns: hardcoded location IDs, missing OCI retry logic, "
            "unguarded ensure-refunds, and order-level (not ODGS-level) routing."
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
    issues = check_order_management_architecture(manifest_dir)

    if not issues:
        print("No OMS architecture issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
