#!/usr/bin/env python3
"""Checker script for Quotes and Quote Templates skill.

Scans a Salesforce metadata directory for common configuration issues
related to Quotes, Quote Templates, Quote sync, and discount approval setup.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_quotes_and_quote_templates.py [--help]
    python3 check_quotes_and_quote_templates.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Quotes and Quote Templates configuration for common issues. "
            "Scans XML metadata files in a Salesforce project directory."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_approval_process_tested_as_sysadmin(manifest_dir: Path) -> list[str]:
    """Warn if approval processes on Quote exist without a non-admin test indicator."""
    issues: list[str] = []
    approval_dir = manifest_dir / "approvalProcesses"
    if not approval_dir.exists():
        return issues

    for xml_file in sorted(approval_dir.glob("Quote*.approvalProcess-meta.xml")):
        issues.append(
            f"REMINDER [{xml_file.name}]: Approval process on Quote object detected. "
            "Ensure this was tested with a non-SysAdmin user — SysAdmins bypass "
            "approval entry criteria and will not trigger the process in testing."
        )
    return issues


def check_quote_flow_mirror_fields(manifest_dir: Path) -> list[str]:
    """Detect Quote record-triggered Flows that may only fire on one DML context."""
    issues: list[str] = []
    flow_dir = manifest_dir / "flows"
    if not flow_dir.exists():
        return issues

    for xml_file in sorted(flow_dir.glob("*.flow-meta.xml")):
        content = xml_file.read_text(encoding="utf-8", errors="replace")

        if "<object>Quote</object>" not in content:
            continue
        if "<triggerType>RecordAfterSave</triggerType>" not in content and \
           "<triggerType>RecordBeforeSave</triggerType>" not in content:
            continue
        if "Assignment" not in content and "recordUpdates" not in content:
            continue

        has_create = "CREATE" in content or "isNew" in content.lower()
        has_update = "UPDATE" in content or "isChanged" in content.lower()

        if has_create and not has_update:
            issues.append(
                f"POTENTIAL ISSUE [{xml_file.name}]: Quote record-triggered Flow "
                "appears to fire on Create only. If this Flow mirrors fields from "
                "Opportunity/Account onto Quote, it will not update when the "
                "Opportunity/Account changes after quote creation. "
                "Add an Update trigger context."
            )
        elif has_update and not has_create:
            issues.append(
                f"POTENTIAL ISSUE [{xml_file.name}]: Quote record-triggered Flow "
                "appears to fire on Update only. Mirror fields will be blank on "
                "initial quote creation. Add a Create trigger context."
            )

    return issues


def check_validation_rules_on_quote(manifest_dir: Path) -> list[str]:
    """Flag validation rules on Quote/QuoteLineItem that reference sync-sensitive fields."""
    issues: list[str] = []
    objects_dir = manifest_dir / "objects"
    if not objects_dir.exists():
        return issues

    quote_dirs = [
        objects_dir / "Quote",
        objects_dir / "QuoteLineItem",
    ]

    sync_sensitive_fields = {
        "Quantity", "UnitPrice", "TotalPrice", "Discount",
        "ListPrice", "PricebookEntryId", "Product2Id",
    }

    for obj_dir in quote_dirs:
        if not obj_dir.exists():
            continue
        val_dir = obj_dir / "validationRules"
        if not val_dir.exists():
            continue
        for xml_file in sorted(val_dir.glob("*.validationRule-meta.xml")):
            content = xml_file.read_text(encoding="utf-8", errors="replace")
            for field in sync_sensitive_fields:
                if field in content:
                    issues.append(
                        f"REVIEW [{xml_file.name}]: Validation rule references "
                        f"'{field}', which is modified during Quote sync. "
                        "Test this rule with an active synced quote to confirm "
                        "it does not silently block bidirectional sync updates."
                    )
                    break

    return issues


def check_quote_template_character_limit_risk(manifest_dir: Path) -> list[str]:
    """Flag quote template metadata files approaching the 32,000-char per-block limit."""
    issues: list[str] = []
    CHAR_LIMIT = 32_000
    WARN_THRESHOLD = 28_000

    for xml_file in sorted(manifest_dir.rglob("*.quoteTemplate-meta.xml")):
        content = xml_file.read_text(encoding="utf-8", errors="replace")
        blocks = re.findall(
            r"<richTextBody>(.*?)</richTextBody>",
            content,
            re.DOTALL,
        )
        for i, block in enumerate(blocks, start=1):
            block_len = len(block)
            if block_len > CHAR_LIMIT:
                issues.append(
                    f"ERROR [{xml_file.name} block {i}]: Rich-text block is "
                    f"{block_len:,} characters, which EXCEEDS the 32,000-character "
                    "limit. PDF generation will fail or truncate this block."
                )
            elif block_len > WARN_THRESHOLD:
                issues.append(
                    f"WARNING [{xml_file.name} block {i}]: Rich-text block is "
                    f"{block_len:,} characters ({block_len/CHAR_LIMIT:.0%} of "
                    "the 32,000-character limit). Consider splitting into "
                    "multiple blocks to avoid hitting the limit."
                )

    return issues


def check_cpq_standard_template_conflict(manifest_dir: Path) -> list[str]:
    """Warn if CPQ metadata is present and standard quote templates also exist."""
    issues: list[str] = []
    objects_dir = manifest_dir / "objects"
    if not objects_dir.exists():
        return issues

    cpq_objects = list(objects_dir.glob("SBQQ__*"))
    if not cpq_objects:
        return issues

    template_dir = manifest_dir / "quoteTemplates"
    standard_templates = list(template_dir.glob("*.quoteTemplate-meta.xml")) if template_dir.exists() else []

    if standard_templates:
        template_names = ", ".join(t.name for t in standard_templates[:5])
        issues.append(
            f"CONFLICT: CPQ (SBQQ) metadata detected AND standard quote templates "
            f"exist ({template_names}). Standard quote templates render QuoteLineItem "
            "only — they will produce blank line item sections for CPQ quotes "
            "(SBQQ__QuoteLine__c). Ensure each template is used only with its "
            "compatible quote type."
        )

    return issues


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def check_quotes_and_quote_templates(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_approval_process_tested_as_sysadmin(manifest_dir))
    issues.extend(check_quote_flow_mirror_fields(manifest_dir))
    issues.extend(check_validation_rules_on_quote(manifest_dir))
    issues.extend(check_quote_template_character_limit_risk(manifest_dir))
    issues.extend(check_cpq_standard_template_conflict(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_quotes_and_quote_templates(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
