#!/usr/bin/env python3
"""Checker script for NFR Definition for Salesforce skill.

Validates that an NFR register document (Markdown table format) meets the
quality criteria defined in the skill: every NFR must have a metric,
threshold, measurement method, and owner. Detects vague adjectives,
missing regulation decomposition, and missing NFR categories.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_nfr_definition_for_salesforce.py --help
    python3 check_nfr_definition_for_salesforce.py --nfr-doc path/to/nfr-register.md
    python3 check_nfr_definition_for_salesforce.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Vague adjectives that indicate an untestable NFR.
VAGUE_TERMS = [
    "fast",
    "quickly",
    "responsive",
    "highly available",
    "secure",
    "compliant",
    "reliable",
    "scalable",
    "performant",
    "stable",
    "robust",
]

# Required NFR category keywords — a complete register should mention all of these.
REQUIRED_CATEGORIES = [
    ("performance", ["perf", "performance", "load time", "response time", "latency"]),
    ("scalability", ["scale", "scalability", "governor", "limit", "volume", "throughput"]),
    ("availability", ["availab", "uptime", "sla", "rto", "rpo"]),
    ("security", ["security", "sec", "encrypt", "auth", "gdpr", "hipaa", "pci"]),
    ("usability", ["usability", "ux", "mobile", "layout", "field count", "accessibility", "wcag"]),
]

# Regulation keywords that should generate multiple NFR rows, not one.
SINGLE_REGULATION_ANTI_PATTERNS = ["gdpr", "hipaa", "pci-dss", "pci dss", "soc 2", "sox"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate an NFR register for the nfr-definition-for-salesforce skill. "
            "Checks for vague thresholds, missing NFR categories, and single-row regulation entries."
        ),
    )
    parser.add_argument(
        "--nfr-doc",
        default=None,
        help="Path to a Markdown NFR register document to validate.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Root directory of Salesforce metadata (reserved for future metadata checks).",
    )
    return parser.parse_args()


def _normalise(text: str) -> str:
    return text.lower()


def check_nfr_document(nfr_doc_path: Path) -> list[str]:
    """Validate a Markdown NFR register document.

    Returns a list of issue strings; empty list means the document passes all checks.
    """
    issues: list[str] = []

    if not nfr_doc_path.exists():
        issues.append(f"NFR document not found: {nfr_doc_path}")
        return issues

    content = nfr_doc_path.read_text(encoding="utf-8")
    content_lower = _normalise(content)
    lines = content.splitlines()

    # --- Check 1: Vague adjective detection ---
    # Look for vague terms in table rows (lines containing | characters).
    table_lines = [ln for ln in lines if "|" in ln]
    for vague in VAGUE_TERMS:
        pattern = re.compile(r"\b" + re.escape(vague) + r"\b", re.IGNORECASE)
        for i, line in enumerate(table_lines, 1):
            if pattern.search(line):
                # Allow the term in the "Description" column (first content cell) but
                # flag it if it appears in the Threshold column without a number nearby.
                if not re.search(r"\d", line):
                    issues.append(
                        f"Possible vague threshold: line contains '{vague}' "
                        f"with no numeric value — NFR may not be measurable. "
                        f"Context: {line.strip()[:120]}"
                    )
                    break  # one warning per vague term is enough

    # --- Check 2: Required NFR categories coverage ---
    for category_name, keywords in REQUIRED_CATEGORIES:
        found = any(kw in content_lower for kw in keywords)
        if not found:
            issues.append(
                f"Missing NFR category: no '{category_name}' NFRs detected. "
                f"A complete register must cover performance, scalability, availability, "
                f"security/compliance, and usability."
            )

    # --- Check 3: Single-row regulation anti-pattern ---
    for regulation in SINGLE_REGULATION_ANTI_PATTERNS:
        occurrences = content_lower.count(regulation)
        if occurrences == 1:
            issues.append(
                f"Possible single-row regulation: '{regulation.upper()}' appears only once. "
                f"Regulations must be decomposed into per-control NFRs — "
                f"a single '{regulation.upper()} compliant' row is untestable."
            )

    # --- Check 4: Availability shared responsibility split ---
    has_salesforce_sla = "trust.salesforce.com" in content_lower or "99.9%" in content_lower
    has_customer_availability = any(
        kw in content_lower for kw in ["rto", "rpo", "team-owned", "customer-owned", "application availability"]
    )
    if has_salesforce_sla and not has_customer_availability:
        issues.append(
            "Availability section references Salesforce SLA but has no customer-owned "
            "availability row (RPO, RTO, or application availability). "
            "The shared responsibility split must be documented explicitly."
        )
    if not has_salesforce_sla and not has_customer_availability:
        issues.append(
            "No availability NFRs detected. Every register must include both "
            "Salesforce infrastructure SLA reference and customer-owned application availability."
        )

    # --- Check 5: Owner column presence ---
    # Heuristic: table rows should contain a non-empty owner cell.
    # A table row with multiple empty cells (|  |  |) suggests draft rows with no owner.
    empty_cell_rows = [ln for ln in table_lines if re.search(r"\|\s*\|\s*\|", ln)]
    if len(empty_cell_rows) > 3:
        issues.append(
            f"{len(empty_cell_rows)} table rows have consecutive empty cells — "
            "NFR rows may be missing owners, metrics, or thresholds. "
            "Every NFR must have a metric, threshold, measurement method, and owner."
        )

    # --- Check 6: TODO markers remaining ---
    todo_count = content_lower.count("todo")
    if todo_count > 0:
        issues.append(
            f"NFR document contains {todo_count} TODO marker(s). "
            "All TODO placeholders must be replaced with real content before sign-off."
        )

    # --- Check 7: Governor limit utilisation mention ---
    # Scalability NFRs should reference specific limits.
    has_scalability = any(kw in content_lower for kw in ["scale", "scalability", "governor"])
    has_utilisation = any(kw in content_lower for kw in ["%", "utilisation", "utilization", "allocation", "headroom"])
    if has_scalability and not has_utilisation:
        issues.append(
            "Scalability NFRs detected but no utilisation percentages found. "
            "Translate business volume targets to governor limit utilisation percentages "
            "(e.g. '500,000 records/day = 50% of daily API allocation')."
        )

    return issues


def check_manifest_dir(manifest_dir: Path) -> list[str]:
    """Reserved for future metadata checks against a Salesforce project directory.

    Currently performs a basic check that the directory exists and contains
    recognisable Salesforce metadata structures.
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check for SFDX project marker — if present, confirm it is a Salesforce project.
    sfdx_json = manifest_dir / "sfdx-project.json"
    force_app = manifest_dir / "force-app"
    if not sfdx_json.exists() and not force_app.exists():
        issues.append(
            "Directory does not appear to be a Salesforce DX project "
            "(no sfdx-project.json or force-app/ found). "
            "Pass the root of a Salesforce DX project with --manifest-dir."
        )

    # Future checks could validate that security settings, profiles, and permission sets
    # reference the controls defined in the NFR register.

    return issues


def main() -> int:
    args = parse_args()
    all_issues: list[str] = []

    if args.nfr_doc:
        nfr_path = Path(args.nfr_doc)
        doc_issues = check_nfr_document(nfr_path)
        all_issues.extend(doc_issues)

    if args.manifest_dir:
        manifest_path = Path(args.manifest_dir)
        manifest_issues = check_manifest_dir(manifest_path)
        all_issues.extend(manifest_issues)

    if not args.nfr_doc and not args.manifest_dir:
        print(
            "Usage: python3 check_nfr_definition_for_salesforce.py --nfr-doc path/to/register.md\n"
            "       python3 check_nfr_definition_for_salesforce.py --manifest-dir path/to/sfdx-project\n"
            "       python3 check_nfr_definition_for_salesforce.py --help"
        )
        return 0

    if not all_issues:
        print("No issues found.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
