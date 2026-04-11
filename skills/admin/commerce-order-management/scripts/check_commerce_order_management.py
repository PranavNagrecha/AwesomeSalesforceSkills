#!/usr/bin/env python3
"""Checker script for Commerce Order Management skill.

Scans Salesforce metadata (XML) for common OMS anti-patterns:
  - Direct DML on OrderItemSummary in contexts that suggest MANAGED mode
  - Use of submit-cancel on fulfilled items (pattern detection in Flow metadata)
  - Missing ProcessExceptionEvent subscription alongside ensure-funds/ensure-refunds usage
  - Apex files that update OrderItemSummary fields directly

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_commerce_order_management.py [--help]
    python3 check_commerce_order_management.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# ── Constants ────────────────────────────────────────────────────────────────

# Apex patterns that indicate direct DML on OMS financial objects in MANAGED mode
MANAGED_DML_PATTERNS: list[tuple[str, str]] = [
    ("OrderItemSummary", "Direct DML on OrderItemSummary detected — use Connect API actions in MANAGED mode"),
    ("OrderItemAdjustmentLineSummary", "Direct DML on OrderItemAdjustmentLineSummary detected — use Connect API actions"),
    ("OrderItemTaxLineItemSummary", "Direct DML on OrderItemTaxLineItemSummary detected — use Connect API actions"),
]

# Markers that suggest a file is working with OMS objects
OMS_OBJECT_MARKERS = [
    "OrderSummary",
    "FulfillmentOrder",
    "ReturnOrder",
    "OrderItemSummary",
]

# Async payment action names — if found, ProcessExceptionEvent should also be present
ASYNC_PAYMENT_ACTIONS = [
    "ensureFundsAsync",
    "ensure-funds-async",
    "ensureRefundsAsync",
    "ensure-refunds-async",
]

PROCESS_EXCEPTION_EVENT_MARKER = "ProcessExceptionEvent"


# ── Helpers ──────────────────────────────────────────────────────────────────

def find_files(root: Path, extension: str) -> list[Path]:
    """Recursively find all files with the given extension under root."""
    return list(root.rglob(f"*{extension}"))


def file_text(path: Path) -> str:
    """Return file contents as a string, or empty string on read error."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def check_apex_for_dml_on_oms_objects(apex_files: list[Path]) -> list[str]:
    """Flag Apex files that contain DML statements targeting OMS financial objects."""
    issues: list[str] = []
    dml_keywords = ("insert ", "update ", "delete ", "upsert ")

    for fpath in apex_files:
        text = file_text(fpath)
        # Only check files that appear to work with OMS objects
        if not any(marker in text for marker in OMS_OBJECT_MARKERS):
            continue

        lines = text.splitlines()
        for lineno, line in enumerate(lines, start=1):
            stripped = line.strip()
            for obj, message in MANAGED_DML_PATTERNS:
                if obj in stripped and any(kw in stripped for kw in dml_keywords):
                    issues.append(
                        f"{fpath.name}:{lineno} — {message} (line: {stripped[:120]})"
                    )

    return issues


def check_async_payment_without_process_exception(all_files: list[Path]) -> list[str]:
    """Warn if async payment actions appear but ProcessExceptionEvent is not found anywhere."""
    issues: list[str] = []
    async_action_files: list[Path] = []
    process_exception_found = False

    for fpath in all_files:
        text = file_text(fpath)
        if PROCESS_EXCEPTION_EVENT_MARKER in text:
            process_exception_found = True
        if any(action in text for action in ASYNC_PAYMENT_ACTIONS):
            async_action_files.append(fpath)

    if async_action_files and not process_exception_found:
        file_names = ", ".join(f.name for f in async_action_files[:5])
        issues.append(
            f"ensure-funds-async or ensure-refunds-async found in [{file_names}] "
            f"but no ProcessExceptionEvent subscription detected anywhere in the manifest. "
            f"Payment job failures will be invisible without a ProcessExceptionEvent handler."
        )

    return issues


def check_flow_metadata(flow_files: list[Path]) -> list[str]:
    """Check Flow XML for OMS-related configuration issues."""
    issues: list[str] = []

    for fpath in flow_files:
        text = file_text(fpath)

        # Check for submit-cancel used in a context that mentions fulfillment status
        if "submitCancel" in text or "submit-cancel" in text:
            if "Fulfilled" in text or "Shipped" in text:
                issues.append(
                    f"{fpath.name} — Flow uses submit-cancel and references Fulfilled/Shipped status. "
                    f"submit-cancel only works on pre-fulfillment quantities; "
                    f"use submit-return for fulfilled items."
                )

        # Check for OrderSummary creation without OrderLifeCycleType
        if "OrderSummary" in text and "OrderLifeCycleType" not in text:
            try:
                root = ET.fromstring(text)
            except ET.ParseError:
                continue

            # Look for create-record elements that reference OrderSummary
            for elem in root.iter():
                if elem.tag.endswith("object") and elem.text == "OrderSummary":
                    parent = elem.getparent() if hasattr(elem, "getparent") else None
                    # ElementTree does not support getparent(); use text scan instead
                    issues.append(
                        f"{fpath.name} — Flow creates an OrderSummary record but "
                        f"OrderLifeCycleType is not referenced. Confirm the lifecycle type "
                        f"is set explicitly — it is immutable after creation."
                    )
                    break

    return issues


def check_cpq_oms_mix(all_files: list[Path]) -> list[str]:
    """Warn if CPQ-related classes/flows reference OMS OrderSummary creation."""
    issues: list[str] = []
    cpq_markers = ("SBQQ__", "CPQ", "Cpq", "cpq")

    for fpath in all_files:
        text = file_text(fpath)
        has_cpq = any(marker in text for marker in cpq_markers)
        has_order_summary_create = (
            "OrderSummary" in text and
            ("insert " in text.lower() or "create" in text.lower())
        )
        if has_cpq and has_order_summary_create:
            issues.append(
                f"{fpath.name} — File references both CPQ objects (SBQQ__ / CPQ) and "
                f"OrderSummary creation. CPQ Orders do NOT automatically trigger OMS "
                f"OrderSummary creation. Verify this is an explicit integration, not an "
                f"assumption that CPQ activation feeds OMS."
            )

    return issues


# ── Main ─────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for Commerce Order Management anti-patterns. "
            "Scans Apex and Flow files for direct DML on OMS financial objects, "
            "missing ProcessExceptionEvent subscriptions, and CPQ/OMS mixing."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_commerce_order_management(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    apex_files = find_files(manifest_dir, ".cls") + find_files(manifest_dir, ".trigger")
    flow_files = find_files(manifest_dir, ".flow-meta.xml") + find_files(manifest_dir, ".flow")
    all_files = apex_files + flow_files + find_files(manifest_dir, ".xml")

    if not any([apex_files, flow_files]):
        # No recognizable metadata found — not an error, just informational
        return issues

    issues.extend(check_apex_for_dml_on_oms_objects(apex_files))
    issues.extend(check_async_payment_without_process_exception(all_files))
    issues.extend(check_flow_metadata(flow_files))
    issues.extend(check_cpq_oms_mix(all_files))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_commerce_order_management(manifest_dir)

    if not issues:
        print("No OMS issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
