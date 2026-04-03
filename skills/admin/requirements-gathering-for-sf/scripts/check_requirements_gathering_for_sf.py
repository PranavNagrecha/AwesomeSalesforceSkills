#!/usr/bin/env python3
"""Checker script for Requirements Gathering for Salesforce skill.

Validates a requirements document (Markdown) for common BA anti-patterns:
- User stories missing acceptance criteria
- Acceptance criteria that are not testable (too vague)
- User stories missing Salesforce object/field reference
- Fit-gap table missing or incomplete

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_requirements_gathering_for_sf.py --requirements-doc path/to/requirements.md
    python3 check_requirements_gathering_for_sf.py  # checks current directory for *.md files
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# Phrases that indicate untestable acceptance criteria
VAGUE_CRITERIA_PATTERNS = [
    r"\bshould be (fast|easy|simple|intuitive|clean|nice|good|better)\b",
    r"\bshould look\b",
    r"\bshould feel\b",
    r"\bshould work\b",
    r"\bshould be user.friendly\b",
    r"\bshould be flexible\b",
    r"\bperformant\b",
]

# Salesforce object names to check for in user stories
SF_OBJECTS = [
    "lead", "opportunity", "account", "contact", "case", "task", "event",
    "campaign", "contract", "order", "product", "pricebook", "quote",
    "custom object", "__c", "sobject", "record",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check a Salesforce requirements document for common BA anti-patterns.",
    )
    parser.add_argument(
        "--requirements-doc",
        default=None,
        help="Path to a requirements Markdown file to check.",
    )
    return parser.parse_args()


def find_requirements_docs(search_dir: Path) -> list[Path]:
    """Find candidate requirements Markdown files in the directory."""
    candidates = []
    for f in search_dir.glob("*.md"):
        text = f.read_text(encoding="utf-8", errors="ignore").lower()
        if "acceptance criteria" in text or "user story" in text or "as a " in text:
            candidates.append(f)
    return candidates


def check_user_stories(content: str) -> list[str]:
    """Check user stories for missing Salesforce object references and acceptance criteria."""
    issues: list[str] = []
    lines = content.splitlines()

    # Find user story blocks (lines starting with "As a ")
    story_starts = [i for i, line in enumerate(lines) if re.match(r"^(\*\*)?[Aa]s a\b", line.strip())]

    if not story_starts:
        return issues  # No user stories found; skip user story checks

    for story_idx, start in enumerate(story_starts):
        story_number = story_idx + 1
        # Gather the story block: up to 20 lines following the "As a" line
        block_end = min(start + 20, len(lines))
        block = "\n".join(lines[start:block_end]).lower()

        # Check for acceptance criteria section
        has_criteria = bool(re.search(r"acceptance criteria", block))
        if not has_criteria:
            issues.append(
                f"User story #{story_number} (line {start + 1}): missing 'Acceptance Criteria' section. "
                "Every Salesforce user story must have testable acceptance criteria."
            )

        # Check for Salesforce object reference
        has_sf_object = any(obj in block for obj in SF_OBJECTS)
        if not has_sf_object:
            issues.append(
                f"User story #{story_number} (line {start + 1}): no Salesforce object or field reference found. "
                "Stories should reference the specific Salesforce object (e.g., Lead, Case, Account, or custom object)."
            )

        # Check for vague acceptance criteria
        if has_criteria:
            criteria_match = re.search(r"acceptance criteria(.+?)(?=\n#|\Z)", block, re.DOTALL)
            if criteria_match:
                criteria_text = criteria_match.group(1)
                for pattern in VAGUE_CRITERIA_PATTERNS:
                    if re.search(pattern, criteria_text):
                        issues.append(
                            f"User story #{story_number} (line {start + 1}): acceptance criteria may be too vague "
                            f"(matched pattern: '{pattern}'). Criteria must be testable in a Salesforce sandbox."
                        )
                        break

    return issues


def check_fit_gap_table(content: str) -> list[str]:
    """Check that a fit-gap table is present and contains required classification columns."""
    issues: list[str] = []
    content_lower = content.lower()

    has_fit_gap = "fit-gap" in content_lower or "fit gap" in content_lower or "fit type" in content_lower
    if not has_fit_gap:
        issues.append(
            "No fit-gap analysis table found. Requirements documents should include a fit-gap table "
            "classifying each requirement as Standard Fit, Configuration Gap, Customization Gap, or Process Gap."
        )
        return issues

    # Check that the table includes Process Gap classification
    has_process_gap = "process gap" in content_lower
    if not has_process_gap:
        issues.append(
            "Fit-gap table does not appear to include 'Process Gap' classification. "
            "Requirements that have no Salesforce equivalent must be flagged as Process Gaps "
            "and escalated to stakeholders — not silently implemented as custom code."
        )

    return issues


def check_integration_requirements(content: str) -> list[str]:
    """Warn if external system references exist but no integration requirement section."""
    issues: list[str] = []
    content_lower = content.lower()

    external_system_keywords = ["erp", "billing system", "external system", "api", "integration", "sap", "netsuite", "workday"]
    mentions_external = any(kw in content_lower for kw in external_system_keywords)

    if mentions_external:
        has_integration_section = bool(
            re.search(r"(integration requirement|integration dependency|external system requirement)", content_lower)
        )
        if not has_integration_section:
            issues.append(
                "Document references external systems but has no 'Integration Requirements' or "
                "'Integration Dependency' section. External data dependencies must be captured explicitly "
                "to prevent mid-implementation blockers."
            )

    return issues


def check_document(doc_path: Path) -> list[str]:
    """Run all checks on a requirements document."""
    issues: list[str] = []

    if not doc_path.exists():
        issues.append(f"File not found: {doc_path}")
        return issues

    content = doc_path.read_text(encoding="utf-8", errors="ignore")

    issues.extend(check_user_stories(content))
    issues.extend(check_fit_gap_table(content))
    issues.extend(check_integration_requirements(content))

    return issues


def main() -> int:
    args = parse_args()

    if args.requirements_doc:
        doc_path = Path(args.requirements_doc)
        docs_to_check = [doc_path]
    else:
        docs_to_check = find_requirements_docs(Path("."))
        if not docs_to_check:
            print("No requirements documents found in current directory.")
            print("Pass --requirements-doc path/to/requirements.md to check a specific file.")
            return 0

    all_issues: list[str] = []
    for doc in docs_to_check:
        print(f"Checking: {doc}")
        doc_issues = check_document(doc)
        all_issues.extend(doc_issues)

    if not all_issues:
        print("No issues found.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
