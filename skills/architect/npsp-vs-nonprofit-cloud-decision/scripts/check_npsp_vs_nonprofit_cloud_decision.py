#!/usr/bin/env python3
"""Checker script for NPSP vs. Nonprofit Cloud Decision skill.

Validates that a decision document or migration plan file:
- Does not assert an in-place upgrade path from NPSP to NPC
- Does not assert a hard NPSP EOL date without citing an official source
- Mentions the net-new org requirement if migration is recommended
- Mentions the Person Account / Household Account model difference
  if a data migration is referenced

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_npsp_vs_nonprofit_cloud_decision.py [--help]
    python3 check_npsp_vs_nonprofit_cloud_decision.py --file path/to/decision-doc.md
    python3 check_npsp_vs_nonprofit_cloud_decision.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Text-level heuristic patterns
# ---------------------------------------------------------------------------

# Patterns that indicate the "in-place upgrade" anti-pattern
UPGRADE_ANTI_PATTERNS = [
    re.compile(r"upgrade\s+(your\s+)?NPSP\s+org\s+to\s+(Nonprofit\s+Cloud|NPC)", re.IGNORECASE),
    re.compile(r"in[- ]place\s+(migration|upgrade|conversion)\s+(from|of)\s+NPSP", re.IGNORECASE),
    re.compile(r"install\s+NPC\s+(on|in|into)\s+(your\s+)?(existing|current)\s+org", re.IGNORECASE),
    re.compile(r"convert\s+(your\s+)?NPSP\s+org\s+to\s+(Nonprofit\s+Cloud|NPC)", re.IGNORECASE),
    re.compile(r"migration\s+tool\s+(to\s+)?convert\s+NPSP", re.IGNORECASE),
]

# Patterns that assert a specific EOL date for NPSP without qualification
EOL_ANTI_PATTERNS = [
    re.compile(r"NPSP\s+(support\s+)?ends?\s+in\s+20\d\d", re.IGNORECASE),
    re.compile(r"NPSP\s+is\s+being\s+discontinued\s+in\s+20\d\d", re.IGNORECASE),
    re.compile(r"NPSP\s+(EOL|end.of.life)\s+(date|deadline)[^.]*20\d\d", re.IGNORECASE),
    re.compile(r"must\s+migrate\s+(to\s+NPC\s+)?by\s+20\d\d", re.IGNORECASE),
]

# Patterns that indicate migration is being discussed (triggers additional checks)
MIGRATION_INDICATORS = [
    re.compile(r"\bmigrat(e|ion|ing)\b", re.IGNORECASE),
    re.compile(r"\bNPC\b"),
    re.compile(r"\bNonprofit\s+Cloud\b", re.IGNORECASE),
]

# Patterns confirming the net-new org requirement is stated
NET_NEW_ORG_PATTERNS = [
    re.compile(r"net.new\s+org", re.IGNORECASE),
    re.compile(r"new\s+(Salesforce\s+)?org", re.IGNORECASE),
    re.compile(r"provision\s+(a\s+)?new\s+org", re.IGNORECASE),
    re.compile(r"new\s+org\s+(with\s+NPC|provisioned)", re.IGNORECASE),
]

# Patterns confirming Account model difference is mentioned
ACCOUNT_MODEL_PATTERNS = [
    re.compile(r"Person\s+Account", re.IGNORECASE),
    re.compile(r"Household\s+Account", re.IGNORECASE),
]


def check_text_content(text: str, file_path: Path) -> list[str]:
    """Return a list of issue strings found in the text content."""
    issues: list[str] = []
    label = str(file_path)

    # Check for in-place upgrade anti-pattern
    for pattern in UPGRADE_ANTI_PATTERNS:
        match = pattern.search(text)
        if match:
            issues.append(
                f"{label}: Anti-pattern detected — in-place upgrade claim: "
                f"'{match.group(0).strip()}'. "
                "There is no in-place migration path from NPSP to Nonprofit Cloud. "
                "Migration requires a net-new org."
            )

    # Check for unsupported EOL date assertions
    for pattern in EOL_ANTI_PATTERNS:
        match = pattern.search(text)
        if match:
            issues.append(
                f"{label}: Anti-pattern detected — unverified NPSP EOL date claim: "
                f"'{match.group(0).strip()}'. "
                "No hard NPSP EOL date has been officially announced. "
                "Verify against current Salesforce Help documentation before asserting a date."
            )

    # If migration is being discussed, check that net-new org requirement is stated
    migration_mentioned = any(p.search(text) for p in MIGRATION_INDICATORS)
    if migration_mentioned:
        net_new_stated = any(p.search(text) for p in NET_NEW_ORG_PATTERNS)
        if not net_new_stated:
            issues.append(
                f"{label}: Migration is referenced but the net-new org requirement "
                "is not mentioned. Any NPC migration recommendation must explicitly "
                "state that a new Salesforce org must be provisioned — not an upgrade "
                "of the existing NPSP org."
            )

        # Check that Account model difference is addressed
        account_model_stated = any(p.search(text) for p in ACCOUNT_MODEL_PATTERNS)
        if not account_model_stated:
            issues.append(
                f"{label}: Migration is referenced but the Account model difference "
                "(Person Accounts in NPC vs. Household Accounts in NPSP) is not "
                "mentioned. This is a critical architectural difference that must be "
                "addressed in any migration plan."
            )

    return issues


def check_markdown_file(file_path: Path) -> list[str]:
    """Check a single Markdown decision document."""
    issues: list[str] = []
    if not file_path.exists():
        issues.append(f"File not found: {file_path}")
        return issues
    if not file_path.is_file():
        issues.append(f"Not a file: {file_path}")
        return issues

    text = file_path.read_text(encoding="utf-8", errors="replace")
    issues.extend(check_text_content(text, file_path))
    return issues


def check_manifest_dir(manifest_dir: Path) -> list[str]:
    """Check Markdown and text files in a directory for anti-patterns."""
    issues: list[str] = []
    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Scan .md and .txt files (decision docs, migration plans, architecture docs)
    candidate_files = list(manifest_dir.rglob("*.md")) + list(manifest_dir.rglob("*.txt"))

    # Exclude files that intentionally document anti-patterns (e.g. llm-anti-patterns.md)
    # so the checker does not flag its own examples as issues.
    excluded_names = {"llm-anti-patterns.md"}
    candidate_files = [f for f in candidate_files if f.name not in excluded_names]

    if not candidate_files:
        # No documents to check — not necessarily an error
        return issues

    for file_path in candidate_files:
        issues.extend(check_markdown_file(file_path))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check NPSP vs. Nonprofit Cloud decision documents for common anti-patterns, "
            "including false upgrade path claims and unverified NPSP EOL date assertions."
        ),
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=None,
        help="Path to a single Markdown decision document to check.",
    )
    parser.add_argument(
        "--manifest-dir",
        type=Path,
        default=None,
        help="Root directory containing decision documents or migration plans to scan.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    issues: list[str] = []

    if args.file:
        issues.extend(check_markdown_file(args.file))
    elif args.manifest_dir:
        issues.extend(check_manifest_dir(args.manifest_dir))
    else:
        # Default: check current directory for Markdown files
        issues.extend(check_manifest_dir(Path(".")))

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
