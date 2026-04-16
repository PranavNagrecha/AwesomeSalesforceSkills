#!/usr/bin/env python3
"""Checker script for Commerce Inventory Data skill.

Validates OCI integration code and configuration for common inventory management issues.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_commerce_inventory_data.py --manifest-dir <path>

Exit codes:
    0 — no issues found
    1 — one or more issues found
"""

import argparse
import re
import sys
from pathlib import Path


MAX_BATCH_INVENTORY_UPDATE_SKUS = 100


def check_batch_size(path: Path) -> list[str]:
    """Warn if batchInventoryUpdate is called without a visible size limit."""
    issues = []
    for apex_file in list(path.glob("**/*.cls")) + list(path.glob("**/*.js")):
        try:
            content = apex_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "batchInventoryUpdate" in content or "availability-records" in content:
            # Check if there's any size check or chunking logic nearby
            has_chunk_logic = re.search(
                r"(subList|chunkedList|chunk|batch|slice|100|MAX_BATCH)", content
            )
            if not has_chunk_logic:
                issues.append(
                    f"WARN: {apex_file.name} calls batchInventoryUpdate or the OCI availability API "
                    f"but does not appear to chunk requests. "
                    f"batchInventoryUpdate is limited to {MAX_BATCH_INVENTORY_UPDATE_SKUS} SKU-location pairs per call. "
                    f"Add chunking logic to split larger payloads."
                )
    return issues


def check_impex_scheduling(path: Path) -> list[str]:
    """Warn if plan documents describe high-frequency full IMPEX scheduling."""
    issues = []
    high_freq_patterns = [
        r"every\s+\d+\s+(minute|min)",
        r"cron.*\*/[1-9]\s",  # cron expression with short minute interval
    ]
    for plan_file in list(path.glob("**/*.md")) + list(path.glob("**/*.txt")):
        try:
            content = plan_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "IMPEX" in content or "impex" in content.lower():
            for pattern in high_freq_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    issues.append(
                        f"WARN: {plan_file.name} appears to schedule OCI IMPEX at high frequency. "
                        f"Full IMPEX imports must have sufficient spacing between runs to avoid data corruption. "
                        f"Use batchInventoryUpdate for near-real-time updates; reserve full IMPEX for nightly snapshots."
                    )
                    break  # one warning per file
    return issues


def check_fsl_oci_confusion(path: Path) -> list[str]:
    """Warn if FSL objects and OCI APIs appear in the same file."""
    issues = []
    fsl_patterns = re.compile(r"WorkOrderLineItem|ServiceResource|ServiceTerritory", re.IGNORECASE)
    oci_patterns = re.compile(r"batchInventoryUpdate|commerce/oci|OCI|omnichannel.inventory", re.IGNORECASE)

    for code_file in list(path.glob("**/*.cls")) + list(path.glob("**/*.js")) + list(path.glob("**/*.py")):
        try:
            content = code_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if fsl_patterns.search(content) and oci_patterns.search(content):
            issues.append(
                f"WARN: {code_file.name} references both FSL objects (WorkOrderLineItem, ServiceResource) "
                f"and OCI inventory APIs. OCI is for Commerce storefront inventory; FSL inventory is for "
                f"field technician parts management. These systems should not be mixed in the same integration layer."
            )
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate OCI Commerce inventory integration code and configuration."
    )
    parser.add_argument("--manifest-dir", type=Path, default=Path("."),
                        help="Directory to scan for Apex, JS, and plan files")
    args = parser.parse_args()

    all_issues: list[str] = []

    if args.manifest_dir.exists():
        all_issues.extend(check_batch_size(args.manifest_dir))
        all_issues.extend(check_impex_scheduling(args.manifest_dir))
        all_issues.extend(check_fsl_oci_confusion(args.manifest_dir))
    else:
        all_issues.append(f"ERROR: Directory not found: {args.manifest_dir}")

    if all_issues:
        for issue in all_issues:
            print(issue)
        return 1

    print("OK: No OCI inventory integration issues detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
