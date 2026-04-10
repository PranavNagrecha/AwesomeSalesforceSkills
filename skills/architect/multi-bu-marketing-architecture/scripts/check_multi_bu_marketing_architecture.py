#!/usr/bin/env python3
"""Checker script for Multi-BU Marketing Architecture skill.

Validates documentation artifacts related to a multi-BU Marketing Cloud implementation:
- BU hierarchy design documents (Markdown tables)
- Shared asset registers
- User provisioning plans

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_multi_bu_marketing_architecture.py [--help]
    python3 check_multi_bu_marketing_architecture.py --manifest-dir path/to/docs
    python3 check_multi_bu_marketing_architecture.py --template path/to/filled-template.md
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Checks for a filled work template
# ---------------------------------------------------------------------------

def check_template(template_path: Path) -> list[str]:
    """Return issues found in a filled multi-BU architecture work template."""
    issues: list[str] = []

    if not template_path.exists():
        issues.append(f"Template file not found: {template_path}")
        return issues

    text = template_path.read_text(encoding="utf-8")

    # 1. Unfilled TODO placeholders
    todo_matches = re.findall(r"\(fill in[^)]*\)|\bTODO\b", text)
    if todo_matches:
        issues.append(
            f"Template contains {len(todo_matches)} unfilled placeholder(s) "
            f"('TODO' or '(fill in ...)') — complete all sections before use."
        )

    # 2. Enterprise 2.0 edition confirmation
    if "Enterprise 2.0" not in text:
        issues.append(
            "Template does not confirm 'Enterprise 2.0' org edition. "
            "Multi-BU shared DE and unlimited child BU features require Enterprise 2.0."
        )

    # 3. Hierarchy depth section present
    if "Hierarchy depth" not in text and "hierarchy depth" not in text.lower():
        issues.append(
            "Template is missing a hierarchy depth declaration. "
            "Confirm whether the design uses one tier (Parent + Children) or multiple tiers."
        )

    # 4. Shared asset register present
    if "Shared Asset Register" not in text and "shared asset register" not in text.lower():
        issues.append(
            "Template is missing a Shared Asset Register. "
            "Document all Data Extensions and content shared across BUs."
        )

    # 5. User provisioning plan present
    if "User Provisioning" not in text and "user provisioning" not in text.lower():
        issues.append(
            "Template is missing a User Provisioning Plan. "
            "Roles do not cascade — every BU requires explicit user provisioning."
        )

    # 6. SAP/DKIM checklist present
    if "DKIM" not in text:
        issues.append(
            "Template is missing sender authentication (SAP/DKIM) coverage. "
            "Each Child BU requires its own SAP and DKIM configuration."
        )

    # 7. Data segregation section present
    if "Data Segregation" not in text and "data segregation" not in text.lower():
        issues.append(
            "Template is missing a Data Segregation Confirmation section. "
            "Confirm separation mechanisms for each brand or market boundary."
        )

    # 8. Review checklist present
    if "Review Checklist" not in text and "review checklist" not in text.lower():
        issues.append(
            "Template is missing a Review Checklist. "
            "Include the standard checklist from SKILL.md before marking work complete."
        )

    return issues


# ---------------------------------------------------------------------------
# Checks for a manifest / documentation directory
# ---------------------------------------------------------------------------

def check_manifest_dir(manifest_dir: Path) -> list[str]:
    """Return issues found in a directory of multi-BU architecture documentation."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    md_files = list(manifest_dir.rglob("*.md"))

    if not md_files:
        issues.append(
            f"No Markdown files found in {manifest_dir}. "
            "Expected architecture documentation files (BU hierarchy, shared asset register, etc.)."
        )
        return issues

    all_text = "\n".join(f.read_text(encoding="utf-8", errors="replace") for f in md_files)

    # Check for key sections across all docs
    required_topics = [
        ("Enterprise 2.0", "Enterprise 2.0 org edition confirmation is missing."),
        (
            "Shared Data Extension",
            "No mention of Shared Data Extensions. "
            "Document cross-BU sharing strategy using Shared DEs in the Parent BU.",
        ),
        (
            "suppression",
            "No suppression strategy documented. "
            "Global suppression lists must be implemented as Shared DEs in the Parent BU.",
        ),
        (
            "provisioning",
            "No user provisioning documentation found. "
            "Document per-BU role assignments — roles do not cascade from the Parent BU.",
        ),
        (
            "DKIM",
            "No sender authentication (SAP/DKIM) documentation found. "
            "Each Child BU requires independent SAP and DKIM configuration.",
        ),
    ]

    for keyword, message in required_topics:
        if keyword.lower() not in all_text.lower():
            issues.append(message)

    # Warn if deeply nested hierarchy is mentioned
    nested_pattern = re.compile(
        r"grandchild\s+bu|three.tier|3.tier|nested.*hierarch|hierarch.*nested",
        re.IGNORECASE,
    )
    if nested_pattern.search(all_text):
        issues.append(
            "Documentation references a nested/grandchild BU hierarchy. "
            "Deeply nested hierarchies increase admin complexity and break Analytics Builder "
            "send attribution rollups — confirm this design decision is intentional and documented."
        )

    # Warn if role cascading language is used
    cascade_pattern = re.compile(
        r"cascade|inherit.*role|role.*inherit|automatically.*access",
        re.IGNORECASE,
    )
    if cascade_pattern.search(all_text):
        issues.append(
            "Documentation uses language suggesting role cascading or automatic access inheritance "
            "('cascade', 'inherit role', 'automatically access'). "
            "Marketing Cloud roles do NOT cascade from Parent BU to Child BUs — "
            "revise to require explicit per-BU provisioning."
        )

    # Warn if single-BU brand separation via folders is mentioned
    folder_sep_pattern = re.compile(
        r"folder.permission.*brand|brand.*folder.permission|separate.*brand.*folder",
        re.IGNORECASE,
    )
    if folder_sep_pattern.search(all_text):
        issues.append(
            "Documentation appears to rely on folder-level permissions within a single BU "
            "for brand separation. "
            "This is not a reliable data isolation boundary — use separate Child BUs instead."
        )

    return issues


# ---------------------------------------------------------------------------
# Argument parsing and main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Multi-BU Marketing Architecture documentation and templates for common issues. "
            "Pass --template to check a filled work template, or --manifest-dir to scan "
            "a directory of architecture documentation files."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Root directory of architecture documentation Markdown files.",
    )
    parser.add_argument(
        "--template",
        default=None,
        help="Path to a filled multi-bu-marketing-architecture-template.md file.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not args.manifest_dir and not args.template:
        # Default: scan current directory
        args.manifest_dir = "."

    issues: list[str] = []

    if args.template:
        issues.extend(check_template(Path(args.template)))

    if args.manifest_dir:
        issues.extend(check_manifest_dir(Path(args.manifest_dir)))

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
