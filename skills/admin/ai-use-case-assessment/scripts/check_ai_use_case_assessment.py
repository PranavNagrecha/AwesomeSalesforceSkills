#!/usr/bin/env python3
"""Checker script for AI Use Case Assessment skill.

Validates that an assessment output document (Markdown) meets the structural
requirements defined in the AI Use Case Assessment skill framework.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_ai_use_case_assessment.py --help
    python3 check_ai_use_case_assessment.py --assessment-file path/to/assessment.md
    python3 check_ai_use_case_assessment.py --assessment-file path/to/assessment.md --strict
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Required sections expected in a completed assessment document
# ---------------------------------------------------------------------------
REQUIRED_SECTIONS = [
    "License Inventory",
    "Candidate Use Case List",
    "Impact-Effort Matrix",
    "Feasibility Scorecard",
    "Prioritized Shortlist",
    "Blocked Use Cases",
    "ROI Narrative",
]

# ---------------------------------------------------------------------------
# Required data readiness sub-dimensions
# ---------------------------------------------------------------------------
DATA_READINESS_SUBDIMENSIONS = [
    "Availability",
    "Quality",
    "Unification",
    "Governance",
]

# ---------------------------------------------------------------------------
# Forbidden patterns — signal that the assessment document contains
# implementation content that should not be in a pre-implementation assessment
# ---------------------------------------------------------------------------
IMPLEMENTATION_BLEED_PATTERNS = [
    r"Setup\s*>\s*Einstein",
    r"Permission\s+Set\s+Assignment",
    r"Enable\s+in\s+Setup",
    r"deploy\s+(to|from)\s+production",
    r"git\s+push",
    r"sfdx\s+force:",
    r"sf\s+deploy",
    r"```apex",
    r"```javascript",
    r"```java",
    r"public\s+class\s+\w+",
    r"@AuraEnabled",
    r"LightningElement",
]

# ---------------------------------------------------------------------------
# Warning patterns — signal common LLM anti-patterns in the document
# ---------------------------------------------------------------------------
FINANCIAL_PROJECTION_PATTERNS = [
    r"\$[\d,]+",
    r"\d+%\s+(reduction|improvement|increase)\b",
    r"expected\s+(savings|revenue|ROI)\s*:\s*\$",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check an AI Use Case Assessment output document for structural "
            "completeness and LLM anti-pattern markers."
        ),
    )
    parser.add_argument(
        "--assessment-file",
        default=None,
        help="Path to the Markdown assessment output file to check.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help=(
            "Root directory to scan for assessment files when --assessment-file "
            "is not provided (default: current directory)."
        ),
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Treat financial projection patterns and implementation bleed as errors "
            "rather than warnings."
        ),
    )
    return parser.parse_args()


def _find_assessment_files(manifest_dir: Path) -> list[Path]:
    """Return all Markdown files under manifest_dir that look like assessment outputs."""
    candidates = list(manifest_dir.rglob("*.md"))
    return [
        p for p in candidates
        if "assessment" in p.name.lower() or "ai-use-case" in p.name.lower()
    ]


def check_required_sections(content: str) -> list[str]:
    """Return a list of issues for missing required sections."""
    issues: list[str] = []
    for section in REQUIRED_SECTIONS:
        # Case-insensitive heading match (## or ###)
        pattern = re.compile(
            r"^#{1,4}\s+" + re.escape(section),
            re.IGNORECASE | re.MULTILINE,
        )
        if not pattern.search(content):
            issues.append(
                f"Missing required section: '{section}'. "
                "The assessment document must include this section per the skill framework."
            )
    return issues


def check_data_readiness_subdimensions(content: str) -> list[str]:
    """Return issues for missing data readiness sub-dimension labels."""
    issues: list[str] = []
    for subdim in DATA_READINESS_SUBDIMENSIONS:
        if subdim.lower() not in content.lower():
            issues.append(
                f"Data readiness sub-dimension '{subdim}' not found in document. "
                "All four sub-dimensions (Availability, Quality, Unification, Governance) "
                "must be scored per the framework."
            )
    return issues


def check_implementation_bleed(content: str, strict: bool) -> list[str]:
    """Return warnings (or errors in strict mode) for implementation content."""
    issues: list[str] = []
    for pattern in IMPLEMENTATION_BLEED_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
        if matches:
            prefix = "ERROR" if strict else "WARN"
            issues.append(
                f"{prefix}: Implementation bleed detected — pattern '{pattern}' matched. "
                "Assessment documents must not contain implementation steps, code, or "
                "Setup navigation paths. Route implementation guidance to the appropriate "
                "implementation skill."
            )
    return issues


def check_financial_projections(content: str, strict: bool) -> list[str]:
    """Return warnings (or errors in strict mode) for specific financial projections."""
    issues: list[str] = []
    for pattern in FINANCIAL_PROJECTION_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            prefix = "ERROR" if strict else "WARN"
            issues.append(
                f"{prefix}: Potential financial projection found (pattern: '{pattern}'). "
                "Assessment ROI output should be a narrative with payback categories, "
                "not specific dollar amounts or percentage improvements stated as facts. "
                "Replace with benchmark references and payback period categories."
            )
    return issues


def check_data_blocked_gate(content: str) -> list[str]:
    """Warn if the Blocked Use Cases section appears empty."""
    issues: list[str] = []
    blocked_section = re.search(
        r"##\s+.*Blocked Use Cases.*\n([\s\S]*?)(?=^##|\Z)",
        content,
        re.MULTILINE | re.IGNORECASE,
    )
    if blocked_section:
        section_content = blocked_section.group(1).strip()
        # If the section is empty or only contains the table header, warn
        non_header_lines = [
            line for line in section_content.splitlines()
            if line.strip() and not line.strip().startswith("|---") and not line.strip().startswith("| Use Case")
        ]
        if not non_header_lines:
            issues.append(
                "WARN: 'Blocked Use Cases' section appears empty. "
                "If all use cases passed data readiness, document that explicitly. "
                "An empty section may indicate the data readiness gate was skipped."
            )
    return issues


def check_assessment_file(file_path: Path, strict: bool = False) -> list[str]:
    """Run all checks against a single assessment Markdown file."""
    issues: list[str] = []

    if not file_path.exists():
        issues.append(f"Assessment file not found: {file_path}")
        return issues

    content = file_path.read_text(encoding="utf-8")

    if not content.strip():
        issues.append(f"Assessment file is empty: {file_path}")
        return issues

    issues.extend(check_required_sections(content))
    issues.extend(check_data_readiness_subdimensions(content))
    issues.extend(check_implementation_bleed(content, strict=strict))
    issues.extend(check_financial_projections(content, strict=strict))
    issues.extend(check_data_blocked_gate(content))

    return issues


def main() -> int:
    args = parse_args()

    if args.assessment_file:
        target_files = [Path(args.assessment_file)]
    else:
        manifest_dir = Path(args.manifest_dir)
        if not manifest_dir.exists():
            print(
                f"WARN: Manifest directory not found: {manifest_dir}",
                file=sys.stderr,
            )
            return 1
        target_files = _find_assessment_files(manifest_dir)
        if not target_files:
            print(
                "No assessment files found. Pass --assessment-file to check a specific file.",
                file=sys.stdout,
            )
            return 0

    all_issues: list[str] = []
    for file_path in target_files:
        file_issues = check_assessment_file(file_path, strict=args.strict)
        for issue in file_issues:
            print(f"[{file_path}] {issue}", file=sys.stderr)
        all_issues.extend(file_issues)

    if not all_issues:
        print("No issues found.")
        return 0

    # Return non-zero only if there are ERROR-level issues
    error_issues = [i for i in all_issues if i.startswith("ERROR") or not i.startswith("WARN")]
    return 1 if error_issues else 0


if __name__ == "__main__":
    sys.exit(main())
